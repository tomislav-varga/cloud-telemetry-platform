# cloud-telemetry-platform

Production-grade edge telemetry component for Raspberry Pi + DHT22.

## Architecture

```
edge/
├── domain/
│   ├── models.py
│   ├── ports.py
│   └── validators.py
├── application/
│   ├── sensor_service.py
│   └── transmission_service.py
├── infrastructure/
│   ├── dht_reader.py
│   ├── http_client.py
│   └── logging_config.py
└── config.py
main.py
```

## Features

- DHT22 read retries for transient sensor errors.
- Domain validation for temperature/humidity constraints.
- Deterministic JSON serialization for telemetry payloads.
- HTTP POST with timeout + exponential backoff retries.
- Structured logging to stdout (systemd journal compatible).
- Continuous runtime loop with recoverable error handling.

## Configuration

Environment variables:

- `API_URL` (default: `http://127.0.0.1:8000/telemetry`)
- `DEVICE_ID` (default: `raspberrypi-edge-01`)
- `READ_INTERVAL_SECONDS` (default: `30`)
- `MAX_SENSOR_RETRIES` (default: `3`)
- `MAX_HTTP_RETRIES` (default: `3`)
- `HTTP_TIMEOUT` (default: `5.0`)

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## systemd

Example unit file is provided at `edge-dht22.service`.

Install it:

```bash
sudo cp edge-dht22.service /etc/systemd/system/edge-dht22.service
sudo systemctl daemon-reload
sudo systemctl enable --now edge-dht22.service
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
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
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