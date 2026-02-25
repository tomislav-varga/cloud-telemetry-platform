"""Entry point for the edge telemetry service."""

from __future__ import annotations

import logging
import time

from edge.application.sensor_service import SensorService
from edge.application.transmission_service import TransmissionService
from edge.config import AppConfig
from edge.domain.validators import InvalidSensorData
from edge.infrastructure.dht_reader import DHT22Reader, SensorReadError
from edge.infrastructure.http_client import HTTPDataTransmitter
from edge.infrastructure.logging_config import configure_logging

logger = logging.getLogger(__name__)


def run() -> None:
    """Run the edge telemetry loop."""
    config = AppConfig.from_env()

    sensor_reader = DHT22Reader(max_retries=config.MAX_SENSOR_RETRIES)
    transmitter = HTTPDataTransmitter(
        api_url=config.API_URL,
        timeout_seconds=config.HTTP_TIMEOUT,
        max_retries=config.MAX_HTTP_RETRIES,
    )

    sensor_service = SensorService(sensor_reader=sensor_reader, device_id=config.DEVICE_ID)
    transmission_service = TransmissionService(transmitter=transmitter)

    logger.info("Edge telemetry service started for device_id=%s", config.DEVICE_ID)

    while True:
        try:
            reading = sensor_service.capture_reading()
            success = transmission_service.transmit(reading)

            if success:
                logger.info("Telemetry cycle completed successfully")
            else:
                logger.error("Telemetry cycle failed to send payload")

        except (SensorReadError, InvalidSensorData) as error:
            logger.warning("Telemetry cycle skipped due to recoverable error: %s", error)
        except Exception as error:  # defensive catch to keep service alive
            logger.error("Unexpected runtime error in telemetry loop: %s", error, exc_info=True)

        time.sleep(config.READ_INTERVAL_SECONDS)


def main() -> int:
    """Initialize and run service, returning process exit code."""
    try:
        configure_logging()
        run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by keyboard interrupt")
        return 0
    except Exception as error:
        logging.getLogger(__name__).error("Fatal initialization failure: %s", error, exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
