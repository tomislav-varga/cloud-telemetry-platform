"""DHT22 sensor reader adapter."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class SensorReadError(RuntimeError):
    """Raised when sensor readings cannot be obtained after retries."""


class DHT22Reader:
    """Reads temperature and humidity from a DHT22 sensor."""

    def __init__(self, max_retries: int = 3, retry_delay_seconds: float = 0.5, gpio_pin: str = "D4") -> None:
        """Initialize DHT22 reader.

        Args:
            max_retries: Number of sensor read retries.
            retry_delay_seconds: Delay between retries in seconds.
            gpio_pin: Board pin symbol name, default D4.

        Raises:
            RuntimeError: If required hardware libraries are unavailable.
        """
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self._sensor: Any = self._initialize_sensor(gpio_pin=gpio_pin)

    def _initialize_sensor(self, gpio_pin: str) -> Any:
        try:
            import adafruit_dht
            import board
        except ImportError as error:
            raise RuntimeError("Missing hardware dependencies: adafruit-circuitpython-dht and board") from error

        pin = getattr(board, gpio_pin, None)
        if pin is None:
            raise RuntimeError(f"Invalid GPIO pin symbol: {gpio_pin}")

        return adafruit_dht.DHT22(pin)

    def read(self) -> tuple[float | None, float | None]:
        """Read temperature and humidity with retry on transient sensor errors."""
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                temperature = self._sensor.temperature
                humidity = self._sensor.humidity
                return temperature, humidity
            except RuntimeError as error:
                last_error = error
                logger.warning(
                    "Transient sensor read error on attempt %s/%s: %s",
                    attempt,
                    self.max_retries,
                    error,
                )
                time.sleep(self.retry_delay_seconds)
            except Exception as error:  # defensive catch for hardware edge cases
                last_error = error
                logger.error("Unexpected sensor error on attempt %s/%s: %s", attempt, self.max_retries, error)
                time.sleep(self.retry_delay_seconds)

        raise SensorReadError(f"Failed to read sensor after {self.max_retries} attempts") from last_error
