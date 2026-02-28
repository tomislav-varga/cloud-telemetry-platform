"""Application service for sensor reading orchestration."""

from __future__ import annotations

from datetime import datetime, timezone

from domain.models import SensorReading
from domain.ports import SensorReader
from domain.validators import validate_sensor_data


class SensorService:
    """Coordinates sensor reading, validation, and payload assembly."""

    def __init__(self, sensor_reader: SensorReader, device_id: str) -> None:
        self.sensor_reader = sensor_reader
        self.device_id = device_id

    def capture_reading(self) -> SensorReading:
        """Capture and validate sensor values and return a domain object."""
        temperature, humidity = self.sensor_reader.read()
        validate_sensor_data(temperature=temperature, humidity=humidity)

        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return SensorReading(
            temperature=float(temperature),
            humidity=float(humidity),
            timestamp=timestamp,
            device_id=self.device_id,
        )
