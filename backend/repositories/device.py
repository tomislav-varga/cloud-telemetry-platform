from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.device import Device


class DeviceNotFoundError(Exception):
    pass


class DeviceRepository:
    async def get_by_key_prefix(self, session: AsyncSession, prefix: str) -> Device:
        stmt = select(Device).where(Device.key_prefix == prefix)
        result = await session.execute(stmt)
        device = result.scalar_one_or_none()
        if device is None:
            raise DeviceNotFoundError("Device not found")
        return device

    async def update_last_used(self, session: AsyncSession, device: Device) -> Device:
        device.last_used_at = datetime.now(UTC)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device
