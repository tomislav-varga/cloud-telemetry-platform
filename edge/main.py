"""Entry point for the edge telemetry service."""

from __future__ import annotations

import logging
from time import perf_counter, sleep

from prometheus_client import start_http_server

from application.sensor_service import SensorService
from application.transmission_service import TransmissionService
from config import AppConfig
from domain.validators import InvalidSensorData
from infrastructure.dht_reader import DHT22Reader, SensorReadError
from infrastructure.http_client import HTTPDataTransmitter
from infrastructure.logging_config import configure_logging
from metrics import EdgeMetrics

logger = logging.getLogger(__name__)


def run() -> None:
    """Run the edge telemetry loop."""
    config = AppConfig.from_env()

    metrics = EdgeMetrics(device_id=config.DEVICE_ID)

    sensor_reader = DHT22Reader(max_retries=config.MAX_SENSOR_RETRIES)
    transmitter = HTTPDataTransmitter(
        api_url=config.API_URL,
        api_key=config.API_KEY,
        timeout_seconds=config.HTTP_TIMEOUT,
        max_retries=config.MAX_HTTP_RETRIES,
        metrics=metrics,
    )

    sensor_service = SensorService(sensor_reader=sensor_reader, device_id=config.DEVICE_ID)
    transmission_service = TransmissionService(transmitter=transmitter)

    start_http_server(port=config.METRICS_PORT, addr=config.METRICS_BIND_ADDRESS)

    logger.info("Edge telemetry service started for device_id=%s", config.DEVICE_ID)
    logger.info(
        "Edge metrics endpoint started on %s:%s",
        config.METRICS_BIND_ADDRESS,
        config.METRICS_PORT,
    )

    while True:
        sensor_started = perf_counter()
        try:
            reading = sensor_service.capture_reading()
            metrics.record_sensor_success(
                temperature=reading.temperature,
                humidity=reading.humidity,
                duration_seconds=perf_counter() - sensor_started,
            )
            success = transmission_service.transmit(reading)

            if success:
                logger.info("Telemetry cycle completed successfully")
            else:
                logger.error("Telemetry cycle failed to send payload")

        except (SensorReadError, InvalidSensorData) as error:
            metrics.record_sensor_failure(
                reason=error.__class__.__name__,
                duration_seconds=perf_counter() - sensor_started,
            )
            logger.warning("Telemetry cycle skipped due to recoverable error: %s", error)
        except Exception as error:  # defensive catch to keep service alive
            logger.error("Unexpected runtime error in telemetry loop: %s", error, exc_info=True)

        sleep(config.READ_INTERVAL_SECONDS)


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
