"""Application service for sensor data transmission."""

from __future__ import annotations

from domain.models import SensorReading
from domain.ports import DataTransmitter


class TransmissionService:
    """Coordinates payload serialization and transmission."""

    def __init__(self, transmitter: DataTransmitter) -> None:
        self.transmitter = transmitter

    def transmit(self, reading: SensorReading) -> bool:
        """Serialize and transmit a reading payload."""
        return self.transmitter.send(reading.to_json())
