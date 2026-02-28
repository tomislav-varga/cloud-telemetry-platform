from prometheus_client import Counter

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

INGESTED_RECORD_COUNT = Counter(
    "telemetry_records_ingested_total",
    "Total number of ingested telemetry records",
)
