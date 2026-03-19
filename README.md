# cloud-telemetry-platform

Production-grade telemetry platform with:

- Edge telemetry component for Raspberry Pi + DHT22
- Telemetry ingestion API built with FastAPI + PostgreSQL

## Files and Folder Structure

```
alembic/
├── env.py
└── versions/
backend/
├── api/
├── models/
├── repositories/
├── schemas/
├── security/
└── main.py
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
├── config.py
└── main.py
tests/
└── test_telemetry_api.py
```

## Features

- DHT22 read retries for transient sensor errors.
- Domain validation for temperature/humidity constraints.
- Deterministic JSON serialization for telemetry payloads.
- HTTP POST with timeout + exponential backoff retries.
- Structured logging to stdout (systemd journal compatible).
- Continuous runtime loop with recoverable error handling.

## Observability

- Observability contract and baseline alert thresholds: `docs/observability-contract.md`

## Edge configuration

Environment variables:

- `API_URL` (default: `http://100.95.7.29:8000/telemetry`)
- `API_KEY` (required for authenticated telemetry ingestion)
- `DEVICE_ID` (default: `raspberrypi-edge-01`)
- `READ_INTERVAL_SECONDS` (default: `30`)
- `MAX_SENSOR_RETRIES` (default: `3`)
- `MAX_HTTP_RETRIES` (default: `3`)
- `HTTP_TIMEOUT` (default: `5.0`)
- `METRICS_BIND_ADDRESS` (default: `0.0.0.0`)
- `METRICS_PORT` (default: `9102`)

For Tailscale-based connectivity to a backend exposed from Kubernetes over HTTPS, set:

```env
API_URL=https://backend-dev.<your-tailnet>.ts.net/telemetry
```

## Run edge service

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## systemd

Use a dedicated least-privilege service account instead of `pi`.

### 1) Create service user (no login shell) and grant GPIO access

```bash
NOLOGIN_BIN="$(command -v nologin)"
sudo useradd \
  --system \
  --no-create-home \
  --shell "$NOLOGIN_BIN" \
  --user-group \
  edge-dht22
sudo usermod -aG gpio edge-dht22
```

### 2) Install edge app under `/opt`

```bash
sudo mkdir -p /opt/cloud-telemetry-platform
sudo rsync -a --delete /path/to/cloud-telemetry-platform/edge/ /opt/cloud-telemetry-platform/edge/
```

### 3) Create runtime virtualenv and install dependencies

```bash
sudo python3 -m venv /opt/cloud-telemetry-platform/edge/.venv
sudo /opt/cloud-telemetry-platform/edge/.venv/bin/pip install --upgrade pip
sudo /opt/cloud-telemetry-platform/edge/.venv/bin/pip install -r /opt/cloud-telemetry-platform/edge/requirements.txt
```

### 4) Lock down application files (read/execute only)

```bash
sudo chown -R root:root /opt/cloud-telemetry-platform/edge
sudo chmod -R a=rX /opt/cloud-telemetry-platform/edge
```

### 5) Create root-only env file (contains API key)

```bash
sudo install -d -m 0750 -o root -g root /etc/edge-dht22
sudo tee /etc/edge-dht22/env >/dev/null <<'EOF'
API_URL=https://backend-dev.<your-tailnet>.ts.net/telemetry
API_KEY=dev_xxxxxx.your-generated-secret
DEVICE_ID=raspberrypi-edge-01
READ_INTERVAL_SECONDS=30
MAX_SENSOR_RETRIES=3
MAX_HTTP_RETRIES=3
HTTP_TIMEOUT=5.0
EOF
sudo chmod 0600 /etc/edge-dht22/env
```

### 6) Create and validate `/etc/systemd/system/edge-dht22.service`

```bash
sudo tee /etc/systemd/system/edge-dht22.service >/dev/null <<'EOF'
[Unit]
Description=Edge DHT22 Sensor Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=edge-dht22
Group=edge-dht22
SupplementaryGroups=gpio
WorkingDirectory=/opt/cloud-telemetry-platform/edge
EnvironmentFile=/etc/edge-dht22/env
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=/opt/cloud-telemetry-platform/edge/.venv/bin/python main.py
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
LockPersonality=true
RestrictNamespaces=true
RestrictSUIDSGID=true
SystemCallArchitectures=native
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=
AmbientCapabilities=
UMask=0077

[Install]
WantedBy=multi-user.target
EOF
sudo systemd-analyze verify /etc/systemd/system/edge-dht22.service
```

### 7) Enable, start, and inspect logs

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now edge-dht22.service
sudo systemctl status edge-dht22.service --no-pager
journalctl -u edge-dht22.service -f
```

### Edge metrics endpoint

After startup, the service exposes Prometheus metrics on:

```text
http://<edge-host>:9102/metrics
```

Quick check:

```bash
curl http://127.0.0.1:9102/metrics | head
```

In Kubernetes, add edge Tailscale hostnames to
`prometheus.prometheusSpec.additionalScrapeConfigs[0].static_configs[0].targets`
in `infrastructure/clusters/dev/infrastructure/monitoring/helmrelease.yaml`.

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

### Run backend in Docker

Build image from repository root:

```bash
docker build -t cloud-telemetry-backend:dev .
```

If you also run PostgreSQL in Docker, use a shared network so the backend
container can reach the database by container name:

```bash
docker network create telemetry-net

docker run --name telemetry-db \
  --network telemetry-net \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -e POSTGRES_DB=telemetry \
  -d postgres:16
```

Run API container:

```bash
docker run --rm \
  --name telemetry-api \
  --network telemetry-net \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@telemetry-db:5432/telemetry \
  -e LOG_LEVEL=INFO \
  cloud-telemetry-backend:dev
```

Run migrations with the same image:

```bash
docker run --rm \
  --network telemetry-net \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@telemetry-db:5432/telemetry \
  cloud-telemetry-backend:dev \
  alembic upgrade head
```

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