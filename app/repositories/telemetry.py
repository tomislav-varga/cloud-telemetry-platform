from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryCreate


class DuplicateTelemetryError(Exception):
    pass


class TelemetryRepository:
    async def create_telemetry(
        self, session: AsyncSession, telemetry_data: TelemetryCreate
    ) -> Telemetry:
        record = Telemetry(**telemetry_data.model_dump())
        session.add(record)

        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise DuplicateTelemetryError(
                "Telemetry already exists for device_id and timestamp"
            ) from exc

        await session.refresh(record)
        return record

    async def get_latest_by_device(self, session: AsyncSession, device_id: str) -> Telemetry | None:
        stmt = (
            select(Telemetry)
            .where(Telemetry.device_id == device_id)
            .order_by(Telemetry.timestamp.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_range(
        self,
        session: AsyncSession,
        device_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Telemetry]:
        stmt = (
            select(Telemetry)
            .where(
                Telemetry.device_id == device_id,
                Telemetry.timestamp >= start,
                Telemetry.timestamp <= end,
            )
            .order_by(Telemetry.timestamp.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_records(self, session: AsyncSession) -> int:
        stmt = select(func.count(Telemetry.id))
        result = await session.execute(stmt)
        return int(result.scalar_one())
