import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.metrics import INGESTED_RECORD_COUNT
from backend.models.device import Device
from backend.repositories.telemetry import DuplicateTelemetryError, TelemetryRepository
from backend.schemas.telemetry import TelemetryCreate, TelemetryResponse
from backend.security.api_key import get_current_device

router = APIRouter(prefix="/telemetry", tags=["telemetry"])
logger = logging.getLogger(__name__)
repo = TelemetryRepository()


def _validate_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="datetime values must include timezone and be UTC",
        )
    normalized = value.astimezone(UTC)
    if normalized != value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="datetime values must be in UTC",
        )
    return normalized


@router.post("", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
async def create_telemetry(
    telemetry: TelemetryCreate,
    session: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device),
) -> TelemetryResponse:
    telemetry_with_authenticated_device = telemetry.model_copy(
        update={"device_id": current_device.device_id}
    )

    try:
        record = await repo.create_telemetry(session, telemetry_with_authenticated_device)
    except DuplicateTelemetryError as exc:
        logger.warning(
            "telemetry_duplicate",
            extra={"device_id": current_device.device_id, "path": "/telemetry", "status_code": 409},
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    INGESTED_RECORD_COUNT.inc()
    logger.info(
        "telemetry_ingested",
        extra={"device_id": current_device.device_id, "path": "/telemetry", "status_code": 201},
    )
    return TelemetryResponse.model_validate(record)


@router.get("/{device_id}/latest", response_model=TelemetryResponse)
async def get_latest_by_device(device_id: str, session: AsyncSession = Depends(get_db)) -> TelemetryResponse:
    record = await repo.get_latest_by_device(session, device_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemetry not found")
    return TelemetryResponse.model_validate(record)


@router.get("/{device_id}", response_model=list[TelemetryResponse])
async def get_telemetry_range(
    device_id: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    session: AsyncSession = Depends(get_db),
) -> list[TelemetryResponse]:
    start_utc = _validate_utc(start)
    end_utc = _validate_utc(end)

    if start_utc > end_utc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start must be before or equal to end",
        )

    records = await repo.get_range(session, device_id, start_utc, end_utc)
    return [TelemetryResponse.model_validate(item) for item in records]