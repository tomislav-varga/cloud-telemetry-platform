from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _ensure_utc_strict(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")

    normalized = value.astimezone(UTC)
    if normalized != value:
        raise ValueError("timestamp must be provided in UTC")

    return normalized


def _normalize_to_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class TelemetryBase(BaseModel):
    device_id: str = Field(min_length=3)
    temperature: float = Field(ge=-50, le=100)
    humidity: float = Field(ge=0, le=100)
    timestamp: datetime


class TelemetryCreate(TelemetryBase):
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_utc(cls, value: datetime) -> datetime:
        return _ensure_utc_strict(value)


class TelemetryResponse(TelemetryBase):
    id: UUID
    created_at: datetime

    @field_validator("timestamp", "created_at")
    @classmethod
    def normalize_output_timestamps(cls, value: datetime) -> datetime:
        return _normalize_to_utc(value)

    model_config = ConfigDict(from_attributes=True)
