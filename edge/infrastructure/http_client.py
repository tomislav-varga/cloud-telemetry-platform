"""HTTP client adapter for sensor data transmission."""

from __future__ import annotations

import logging
import time

import requests
from requests import Response

logger = logging.getLogger(__name__)


class HTTPDataTransmitter:
    """Transmits sensor data to an HTTP endpoint with retry/backoff."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout_seconds: float = 5.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 1.0,
    ) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def _post(self, payload: str) -> Response:
        return requests.post(
            self.api_url,
            data=payload,
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key},
            timeout=self.timeout_seconds,
        )

    def send(self, payload: str) -> bool:
        """Send payload with exponential backoff on retryable failures."""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._post(payload)

                if 500 <= response.status_code <= 599:
                    raise requests.HTTPError(f"Server error {response.status_code}")

                if 400 <= response.status_code <= 499:
                    logger.error(
                        "Dropping payload due to client error (status=%s, body=%s)",
                        response.status_code,
                        response.text,
                    )
                    return False

                logger.info("Payload sent successfully with status %s", response.status_code)
                return True

            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as error:
                logger.warning(
                    "Transmission attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    error,
                )
                if attempt == self.max_retries:
                    break

                sleep_seconds = self.backoff_base_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_seconds)
            except requests.RequestException as error:
                logger.error("Non-retryable request exception: %s", error)
                return False

        logger.error("Dropping payload after %s failed transmission attempts", self.max_retries)
        return False
