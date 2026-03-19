"""HTTP client adapter for sensor data transmission."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import requests
from requests import Response

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from metrics import EdgeMetrics


class HTTPDataTransmitter:
    """Transmits sensor data to an HTTP endpoint with retry/backoff."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout_seconds: float = 5.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 1.0,
        metrics: "EdgeMetrics | None" = None,
    ) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.metrics = metrics

    def _post(self, payload: str) -> Response:
        return requests.post(
            self.api_url,
            data=payload,
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key},
            timeout=self.timeout_seconds,
        )

    def send(self, payload: str) -> bool:
        """Send payload with exponential backoff on retryable failures."""
        started = time.perf_counter()
        last_reason = "unknown_error"

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._post(payload)

                if 500 <= response.status_code <= 599:
                    last_reason = "server_error"
                    raise requests.HTTPError(f"Server error {response.status_code}")

                if 400 <= response.status_code <= 499:
                    last_reason = "client_error"
                    logger.error(
                        "Dropping payload due to client error (status=%s, body=%s)",
                        response.status_code,
                        response.text,
                    )
                    if self.metrics is not None:
                        self.metrics.record_transmission_failure(
                            reason=last_reason,
                            duration_seconds=time.perf_counter() - started,
                        )
                    return False

                logger.info("Payload sent successfully with status %s", response.status_code)
                if self.metrics is not None:
                    self.metrics.record_transmission_success(time.perf_counter() - started)
                return True

            except requests.Timeout as error:
                last_reason = "timeout"
                logger.warning(
                    "Transmission attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    error,
                )
            except requests.ConnectionError as error:
                last_reason = "connection_error"
                logger.warning(
                    "Transmission attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    error,
                )
            except requests.HTTPError as error:
                last_reason = "server_error"
                logger.warning(
                    "Transmission attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    error,
                )
            except requests.RequestException as error:
                last_reason = "request_exception"
                logger.error("Non-retryable request exception: %s", error)
                if self.metrics is not None:
                    self.metrics.record_transmission_failure(
                        reason=last_reason,
                        duration_seconds=time.perf_counter() - started,
                    )
                return False

            if attempt == self.max_retries:
                break

            if self.metrics is not None:
                self.metrics.record_transmission_retry(reason=last_reason)

            sleep_seconds = self.backoff_base_seconds * (2 ** (attempt - 1))
            time.sleep(sleep_seconds)

        logger.error("Dropping payload after %s failed transmission attempts", self.max_retries)
        if self.metrics is not None:
            self.metrics.record_transmission_failure(
                reason=last_reason,
                duration_seconds=time.perf_counter() - started,
            )
        return False
