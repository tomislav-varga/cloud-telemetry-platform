# cloud-telemetry-platform

Production-grade telemetry platform with:

- Edge telemetry component for Raspberry Pi + DHT22
- Telemetry ingestion API built with FastAPI + PostgreSQL

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

## Edge configuration

Environment variables:

- `API_URL` (default: `http://127.0.0.1:8000/telemetry`)
- `API_KEY` (required for authenticated telemetry ingestion)
- `DEVICE_ID` (default: `raspberrypi-edge-01`)
- `READ_INTERVAL_SECONDS` (default: `30`)
- `MAX_SENSOR_RETRIES` (default: `3`)
- `MAX_HTTP_RETRIES` (default: `3`)
- `HTTP_TIMEOUT` (default: `5.0`)

## Run edge service

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
```

---

## Telemetry API

### Prerequisites

- Python 3.12+
- Docker (for local PostgreSQL)

### 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2) Start the database server (PostgreSQL)

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

### 3) Configure environment variables

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

### 4) Run database migrations

```bash
alembic upgrade head
```

### 5) Start the API server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

API base URL: `http://localhost:8000`

### 6) Generate and register an API key for an edge device

Use the backend utility to generate a key and store only prefix + hash in the `devices` table:

```bash
python - <<'PY'
import asyncio

from backend.db import SessionLocal
from backend.models.device import Device
from backend.security.hashing import generate_api_key

DEVICE_ID = "raspberrypi-edge-01"

async def main() -> None:
    prefix, raw_key, hashed = generate_api_key()
    async with SessionLocal() as session:
        session.add(
            Device(
                device_id=DEVICE_ID,
                key_prefix=prefix,
                api_key_hash=hashed,
                is_active=True,
            )
        )
        await session.commit()

    print("SAVE THIS KEY NOW (shown once):")
    print(raw_key)

asyncio.run(main())
PY
```

Important:

- Save the printed raw key securely (password manager or secret store).
- Never store or log plaintext API keys in your backend database.
- `DEVICE_ID` must match the edge device identity you use for ingestion.

### 7) Configure the edge device with the API key

On the edge device, store the raw key in an environment variable:

```bash
export API_KEY='dev_xxxxxx.your-generated-secret'
```

For systemd, add it to your unit override:

```bash
sudo systemctl edit edge-dht22.service
```

Then set:

```ini
[Service]
Environment="API_KEY=dev_xxxxxx.your-generated-secret"
```

Apply and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart edge-dht22.service
```

If you are using the built-in edge transmitter, make sure requests include `X-API-Key`.
Update `edge/infrastructure/http_client.py` headers so each POST sends:

```python
headers={
    "Content-Type": "application/json",
    "X-API-Key": os.environ["API_KEY"],
}
```

### 8) Verify key usage from edge device

Use a quick request with the API key header:

```bash
curl -X POST "http://<api-host>:8000/telemetry" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "device_id": "raspberrypi-edge-01",
    "temperature": 22.4,
    "humidity": 51.2,
    "timestamp": "2026-03-01T12:00:00Z"
  }'
```

Expected response codes:

- `201` for valid key and payload
- `401` for missing/invalid key
- `403` for inactive device key

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