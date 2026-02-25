# cloud-telemetry-platform

Telemetry ingestion API built with FastAPI, async SQLAlchemy, PostgreSQL, and Alembic.

## Prerequisites

- Python 3.12+
- Docker (for local PostgreSQL)

## 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2) Start the database server (PostgreSQL)

Run PostgreSQL in Docker:

```bash
docker run --name telemetry-db \
	-e POSTGRES_USER=user \
	-e POSTGRES_PASSWORD=pass \
	-e POSTGRES_DB=telemetry \
	-p 5432:5432 \
	-d postgres:16
```

If the container already exists:

```bash
docker start telemetry-db
```

## 3) Configure environment variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Default local value in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/telemetry
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
LOG_LEVEL=INFO
```

## 4) Run database migrations

```bash
alembic upgrade head
```

## 5) Start the API server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API base URL: `http://localhost:8000`

## Useful endpoints

- Health: `GET /health`
- Metrics: `GET /metrics`
- Create telemetry: `POST /telemetry`
- Latest by device: `GET /telemetry/{device_id}/latest`
- Range by device: `GET /telemetry/{device_id}?start=...&end=...`

## Quick test

```bash
pytest -q
```