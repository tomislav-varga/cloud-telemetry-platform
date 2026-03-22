import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.metrics import AUTHENTICATED_REQUESTS_TOTAL, AUTHENTICATION_FAILURES_TOTAL
from backend.models.device import Device
from backend.repositories.device import DeviceNotFoundError, DeviceRepository
from backend.security.hashing import verify_api_key

logger = logging.getLogger(__name__)
repo = DeviceRepository()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _auth_failed(status_code: int, key_prefix: str | None, reason: str) -> None:
    AUTHENTICATION_FAILURES_TOTAL.labels(reason=reason).inc()
    logger.warning(
        "device_authentication_failed",
        extra={"key_prefix": key_prefix, "status_code": status_code, "reason": reason},
    )
    raise HTTPException(status_code=status_code, detail="Invalid API Key")


async def get_current_device(
    api_key: str | None = Security(api_key_header),
    session: AsyncSession = Depends(get_db),
) -> Device:
    if not api_key:
        _auth_failed(status.HTTP_401_UNAUTHORIZED, None, "missing_header")

    prefix, separator, secret = api_key.partition(".")
    if not separator or not prefix or not secret:
        _auth_failed(status.HTTP_401_UNAUTHORIZED, prefix or None, "malformed_key")

    try:
        device = await repo.get_by_key_prefix(session, prefix)
    except DeviceNotFoundError:
        _auth_failed(status.HTTP_401_UNAUTHORIZED, prefix, "unknown_prefix")

    if not verify_api_key(api_key, device.api_key_hash):
        _auth_failed(status.HTTP_401_UNAUTHORIZED, prefix, "hash_mismatch")

    if not device.is_active:
        _auth_failed(status.HTTP_403_FORBIDDEN, prefix, "inactive_device")

    await repo.update_last_used(session, device)
    AUTHENTICATED_REQUESTS_TOTAL.inc()
    logger.info(
        "device_authenticated",
        extra={"device_id": device.device_id, "key_prefix": device.key_prefix},
    )
    return device
