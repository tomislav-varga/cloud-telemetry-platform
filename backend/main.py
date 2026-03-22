import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi import Depends
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.telemetry import router as telemetry_router
from backend.config import get_settings
from backend.db import check_db_health, get_db
from backend.metrics import ERROR_COUNT, REQUEST_COUNT, REQUEST_DURATION_SECONDS
from backend.repositories.telemetry import TelemetryRepository
from backend.logging_config import configure_logging
from backend.request_context import reset_trace_id, set_trace_id

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

TOTAL_TELEMETRY_RECORDS = Gauge(
    "telemetry_records_total",
    "Total telemetry records currently stored",
)

app = FastAPI(title=settings.app_name)
app.include_router(telemetry_router)
repo = TelemetryRepository()


@app.middleware("http")
async def track_metrics(request: Request, call_next):
    trace_id = str(uuid4())
    token = set_trace_id(trace_id)
    response: Response | None = None

    method = request.method
    path = request.url.path
    REQUEST_COUNT.labels(method=method, path=path).inc()
    started = perf_counter()

    try:
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        if response.status_code >= 400:
            ERROR_COUNT.labels(method=method, path=path, status_code=str(response.status_code)).inc()
        return response
    finally:
        elapsed = perf_counter() - started
        if response is not None:
            status_code = str(response.status_code)
        else:
            status_code = "500"
            ERROR_COUNT.labels(method=method, path=path, status_code=status_code).inc()

        REQUEST_DURATION_SECONDS.labels(
            method=method,
            path=path,
            status_code=status_code,
        ).observe(elapsed)
        reset_trace_id(token)


@app.get("/health")
async def health() -> JSONResponse:
    healthy = await check_db_health()
    if not healthy:
        logger.error("healthcheck_failed", extra={"path": "/health", "status_code": 503})
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return JSONResponse(status_code=200, content={"status": "ok"})


@app.get("/metrics")
async def metrics(session: AsyncSession = Depends(get_db)):
    total = await repo.get_total_records(session)
    TOTAL_TELEMETRY_RECORDS.set(total)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(
        "validation_error",
        extra={"path": request.url.path, "status_code": 422},
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
