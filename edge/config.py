"""Runtime configuration for the edge telemetry service."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    """Application configuration values."""

    API_URL: str
    DEVICE_ID: str
    READ_INTERVAL_SECONDS: int
    MAX_SENSOR_RETRIES: int
    MAX_HTTP_RETRIES: int
    HTTP_TIMEOUT: float

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables with defaults."""
        config = cls(
            API_URL=os.getenv("API_URL", "http://100.95.7.29:8000/telemetry"),
            DEVICE_ID=os.getenv("DEVICE_ID", "raspberrypi-edge-01"),
            READ_INTERVAL_SECONDS=int(os.getenv("READ_INTERVAL_SECONDS", "3")),
            MAX_SENSOR_RETRIES=int(os.getenv("MAX_SENSOR_RETRIES", "3")),
            MAX_HTTP_RETRIES=int(os.getenv("MAX_HTTP_RETRIES", "3")),
            HTTP_TIMEOUT=float(os.getenv("HTTP_TIMEOUT", "5.0")),
        )
        config._validate()
        return config

    def _validate(self) -> None:
        if self.READ_INTERVAL_SECONDS <= 0:
            raise ValueError("READ_INTERVAL_SECONDS must be > 0")
        if self.MAX_SENSOR_RETRIES <= 0:
            raise ValueError("MAX_SENSOR_RETRIES must be > 0")
        if self.MAX_HTTP_RETRIES <= 0:
            raise ValueError("MAX_HTTP_RETRIES must be > 0")
        if self.HTTP_TIMEOUT <= 0:
            raise ValueError("HTTP_TIMEOUT must be > 0")
        if not self.API_URL:
            raise ValueError("API_URL is required")
        if not self.DEVICE_ID:
            raise ValueError("DEVICE_ID is required")
