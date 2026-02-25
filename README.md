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
```