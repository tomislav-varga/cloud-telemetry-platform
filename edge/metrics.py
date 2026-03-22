"""Prometheus metrics for the edge telemetry service."""

from __future__ import annotations

from time import time

from prometheus_client import Counter, Gauge, Histogram

_SENSOR_READ_TOTAL = Counter(
    "edge_sensor_read_total",
    "Total number of sensor reads by result",
    ["device_id", "result"],
)

_SENSOR_READ_DURATION_SECONDS = Histogram(
    "edge_sensor_read_duration_seconds",
    "Duration of sensor reads in seconds by result",
    ["device_id", "result"],
)

_TRANSMISSION_TOTAL = Counter(
    "edge_transmission_total",
    "Total number of transmission attempts by result",
    ["device_id", "result"],
)

_TRANSMISSION_DURATION_SECONDS = Histogram(
    "edge_transmission_duration_seconds",
    "Duration of end-to-end transmission attempts in seconds by result",
    ["device_id", "result"],
)

_TRANSMISSION_RETRIES_TOTAL = Counter(
    "edge_transmission_retries_total",
    "Total number of transmission retries by reason",
    ["device_id", "reason"],
)

_TEMPERATURE_CELSIUS = Gauge(
    "edge_temperature_celsius",
    "Last successful temperature reading in celsius",
    ["device_id"],
)

_HUMIDITY_PERCENT = Gauge(
    "edge_humidity_percent",
    "Last successful humidity reading in percent",
    ["device_id"],
)

_LAST_SUCCESS_UNIXTIME = Gauge(
    "edge_last_success_unixtime",
    "Unix time of last successful telemetry transmission",
    ["device_id"],
)


class EdgeMetrics:
    """Typed wrapper around edge metric families."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id

    def record_sensor_success(self, temperature: float, humidity: float, duration_seconds: float) -> None:
        _SENSOR_READ_TOTAL.labels(device_id=self.device_id, result="success").inc()
        _SENSOR_READ_DURATION_SECONDS.labels(device_id=self.device_id, result="success").observe(
            duration_seconds
        )
        _TEMPERATURE_CELSIUS.labels(device_id=self.device_id).set(temperature)
        _HUMIDITY_PERCENT.labels(device_id=self.device_id).set(humidity)

    def record_sensor_failure(self, reason: str, duration_seconds: float) -> None:
        _ = reason  # reason stays in logs for now to keep bounded label set.
        _SENSOR_READ_TOTAL.labels(device_id=self.device_id, result="failure").inc()
        _SENSOR_READ_DURATION_SECONDS.labels(device_id=self.device_id, result="failure").observe(
            duration_seconds
        )

    def record_transmission_success(self, duration_seconds: float) -> None:
        _TRANSMISSION_TOTAL.labels(device_id=self.device_id, result="success").inc()
        _TRANSMISSION_DURATION_SECONDS.labels(device_id=self.device_id, result="success").observe(
            duration_seconds
        )
        _LAST_SUCCESS_UNIXTIME.labels(device_id=self.device_id).set(time())

    def record_transmission_failure(self, reason: str, duration_seconds: float) -> None:
        _ = reason  # reason stays in logs for now to keep bounded label set.
        _TRANSMISSION_TOTAL.labels(device_id=self.device_id, result="failure").inc()
        _TRANSMISSION_DURATION_SECONDS.labels(device_id=self.device_id, result="failure").observe(
            duration_seconds
        )

    def record_transmission_retry(self, reason: str) -> None:
        _TRANSMISSION_RETRIES_TOTAL.labels(device_id=self.device_id, reason=reason).inc()
