"""Validation logic for edge telemetry domain objects."""

from __future__ import annotations


class InvalidSensorData(ValueError):
    """Raised when a sensor reading is invalid."""


def validate_sensor_data(temperature: float | None, humidity: float | None) -> None:
    """Validate raw sensor values.

    Args:
        temperature: Temperature in Celsius.
        humidity: Relative humidity in percent.

    Raises:
        InvalidSensorData: If values are missing or outside valid ranges.
    """
    if temperature is None:
        raise InvalidSensorData("temperature is required")

    if humidity is None:
        raise InvalidSensorData("humidity is required")

    if not -40 <= temperature <= 80:
        raise InvalidSensorData("temperature must be between -40 and 80 °C")

    if not 0 <= humidity <= 100:
        raise InvalidSensorData("humidity must be between 0 and 100 %")
