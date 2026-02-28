"""Abstractions used by the application layer."""

from __future__ import annotations

from typing import Protocol


class SensorReader(Protocol):
    """Abstraction for reading raw sensor data."""

    def read(self) -> tuple[float | None, float | None]:
        """Read temperature and humidity values."""


class DataTransmitter(Protocol):
    """Abstraction for transmitting serialized sensor readings."""

    def send(self, payload: str) -> bool:
        """Send a serialized payload and return success status."""
