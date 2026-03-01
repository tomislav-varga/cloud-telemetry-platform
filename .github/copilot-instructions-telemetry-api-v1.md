📘 Copilot Instructions — Telemetry API (FastAPI + PostgreSQL)
🎯 Goal

Implement a production-ready telemetry ingestion API using:

FastAPI

PostgreSQL

SQLAlchemy 2.0 (async)

Alembic for migrations

No authentication in v1, but architecture must support future auth.

1️⃣ Functional Requirements
Endpoint

POST /telemetry

JSON Payload
{
  "device_id": "pi-lab-01",
  "temperature": 22.4,
  "humidity": 51.2,
  "timestamp": "2026-02-14T12:00:00Z"
}
Behavior

Validate payload using Pydantic

Store data in PostgreSQL

Generate UUID for id

Set created_at automatically (UTC)

Return 201 Created

Return stored object

2️⃣ Architecture Rules (Very Important)

Copilot must follow these architectural principles:

✅ Separation of Concerns

Structure project like this:

app/
├── main.py
├── config.py
├── db.py
├── models/
│   └── telemetry.py
├── schemas/
│   └── telemetry.py
├── repositories/
│   └── telemetry.py
├── api/
│   └── telemetry.py

API layer → request/response handling

Schema layer → validation

Model layer → database models

Repository layer → DB interaction

No SQL inside API routes

3️⃣ Database Design
PostgreSQL Table

Table: telemetry

Columns:

Column	Type	Constraints
id	UUID	PK
device_id	VARCHAR	NOT NULL
temperature	FLOAT	NOT NULL
humidity	FLOAT	NOT NULL
timestamp	TIMESTAMP WITH TIME ZONE	NOT NULL
created_at	TIMESTAMP WITH TIME ZONE	DEFAULT now()
Indexes

Add:

CREATE INDEX idx_telemetry_device_id ON telemetry(device_id);
CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp);
CREATE INDEX idx_telemetry_device_timestamp ON telemetry(device_id, timestamp DESC);

Use Alembic migration for schema creation.

4️⃣ Data Validation Rules

Using Pydantic:

device_id → min length 3

temperature → realistic range (-50 to 100 °C)

humidity → 0–100 %

timestamp → must be timezone-aware UTC

Reject invalid values with 422.

5️⃣ FastAPI Endpoint Requirements

File: api/telemetry.py

POST /telemetry

Async route

Uses dependency injection for DB session

Calls repository layer

Returns response model

Response model must exclude internal DB state.

6️⃣ Database Layer (Async)

Use:

asyncpg

SQLAlchemy 2.0 async engine

AsyncSession

Connection string from environment:

DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/telemetry

Use connection pooling.

7️⃣ Repository Pattern

Create TelemetryRepository class with:

async def create_telemetry(session, telemetry_data)
async def get_latest_by_device(session, device_id)
async def get_range(session, device_id, start, end)

Never expose ORM models directly to API.

8️⃣ Additional Features Worth Implementing

These should be scaffolded even in v1.

✅ 1. GET Endpoints

Add:

GET /telemetry/{device_id}/latest
GET /telemetry/{device_id}?start=...&end=...

Use indexed queries.

✅ 2. Rate Limiting (Preparation)

Even if not implemented fully, structure app to allow:

SlowAPI or Redis-based limiter

Device-based rate limiting

Telemetry ingestion endpoints are common DDoS targets.

✅ 3. Device Registry Table (Optional but Recommended)

Future-ready design:

Table: devices

Column	Type
id	UUID
device_id	string unique
created_at	timestamp

This allows:

Device validation

Authentication per device

API keys later

✅ 4. Future Authentication Preparation

Even though v1 has no auth:

Structure routes like:

async def create_telemetry(
    telemetry: TelemetryCreate,
    session: AsyncSession = Depends(get_db),
    current_device: Device = Depends(optional_device_dependency)
)

Where:

optional_device_dependency currently returns None

Later replaced with API key validation

Do NOT hardcode authentication logic into route.

✅ 5. Logging

Add structured logging:

Log device_id

Log ingestion success

Log validation errors

Use Python logging module, JSON format if possible.

✅ 6. Health Endpoint

Add:

GET /health

Checks:

DB connectivity

Returns status OK

✅ 7. Metrics Endpoint (Prometheus Ready)

Add:

GET /metrics

Expose:

Total telemetry records

Requests count

Error count

Use prometheus-client.

✅ 8. Idempotency Protection (Advanced but Recommended)

Optional:

Prevent duplicate inserts for same:

device_id + timestamp

Add unique constraint:

UNIQUE(device_id, timestamp)

On conflict → ignore or update.

9️⃣ Performance Considerations

Use bulk insert capability if needed later

Partition table by time (future optimization)

Avoid SELECT before INSERT

Use proper indexing

🔟 Production Considerations

Use UTC everywhere

Never trust client timestamp blindly

Consider server-side timestamp override option

Use Docker

Add .env support

Add proper exception handlers

1️⃣1️⃣ Testing Requirements

Add:

pytest

httpx async client

Test:

valid payload

invalid temperature

missing field

range query

latest query

1️⃣2️⃣ Example Pydantic Schemas
class TelemetryBase(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    timestamp: datetime

class TelemetryCreate(TelemetryBase):
    pass

class TelemetryResponse(TelemetryBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
1️⃣3️⃣ Expected Status Codes
Scenario	Code
Created	201
Validation error	422
Device not found (future)	404
Duplicate telemetry	409 (optional)
🧠 Engineering Principles

Copilot must:

Prefer clarity over magic

Avoid global DB sessions

Avoid blocking calls

Use async everywhere

Keep functions small

Add type hints everywhere

Follow clean architecture

🚀 End Result

You should end up with:

Production-ready ingestion API

Proper database schema

Indexed queries

Clean architecture

Future-ready authentication

Observability ready

Testable structure