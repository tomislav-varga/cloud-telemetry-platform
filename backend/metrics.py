from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "telemetry_api_requests_total",
    "Total number of requests",
    ["method", "path"],
)

ERROR_COUNT = Counter(
    "telemetry_api_errors_total",
    "Total number of error responses",
    ["method", "path", "status_code"],
)

REQUEST_DURATION_SECONDS = Histogram(
    "telemetry_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "path", "status_code"],
)

INGESTED_RECORD_COUNT = Counter(
    "telemetry_records_ingested_total",
    "Total number of ingested telemetry records",
)

AUTHENTICATION_FAILURES_TOTAL = Counter(
    "authentication_failures_total",
    "Total number of failed authentication attempts",
    ["reason"],
)

AUTHENTICATED_REQUESTS_TOTAL = Counter(
    "authenticated_requests_total",
    "Total number of successfully authenticated requests",
)
