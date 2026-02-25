Copilot Instructions — Edge Device (Raspberry Pi DHT22)
Context

You are generating production-grade Python code for an edge device (Raspberry Pi) that:

Reads temperature and humidity from a DHT22 sensor

Validates and timestamps readings

Formats data as JSON

Logs operational events

Sends data to a FastAPI backend

Runs reliably as a systemd service

Is resilient against:

Sensor read errors

Network failures

API downtime

Follow Clean Architecture and SOLID principles strictly.

This is not a script.
This is a small distributed system component.

1️⃣ Architectural Requirements

Use layered structure:

edge/
│
├── domain/
│   ├── models.py
│   ├── validators.py
│
├── application/
│   ├── sensor_service.py
│   ├── transmission_service.py
│
├── infrastructure/
│   ├── dht_reader.py
│   ├── http_client.py
│   ├── logging_config.py
│
├── config.py
├── main.py
Rules

Domain layer must not depend on infrastructure.

Infrastructure may depend on domain.

Application coordinates use cases.

No hardware logic inside main.py.

2️⃣ Domain Layer
models.py

Create a SensorReading dataclass:

temperature: float

humidity: float

timestamp: ISO 8601 string (UTC)

device_id: string

Add:

def to_dict(self) -> dict
def to_json(self) -> str

JSON must be deterministic and valid.

validators.py

Implement validation logic:

temperature must be between -40 and 80 °C

humidity must be between 0 and 100 %

reject None values

raise domain-specific exception InvalidSensorData

Validation must be separate from hardware logic.

3️⃣ Infrastructure Layer
dht_reader.py

Responsibilities:

Encapsulate interaction with adafruit-circuitpython-dht

Use GPIO4 by default

Catch RuntimeError from sensor

Retry up to 3 times with short delay

Never crash the process

Raise custom exception if retries fail

No validation logic here.

http_client.py

Responsibilities:

Send POST request to API

Use requests or httpx

JSON payload

Configurable timeout

Handle:

timeouts

connection errors

5xx responses

Implement:

Exponential backoff retry strategy

Max retry limit

Log all failures

Never crash on network errors.

logging_config.py

Use Python logging.

Requirements:

Structured log format

Include timestamp

Include log level

Include module name

Log to:

stdout (systemd journal will capture it)

Log levels:

INFO → normal operation

WARNING → transient failures

ERROR → persistent failures

No print statements anywhere.

4️⃣ Application Layer
sensor_service.py

Responsibilities:

Call DHT reader

Validate data

Attach UTC timestamp

Attach device_id from config

Return SensorReading object

This layer orchestrates domain + infrastructure.

transmission_service.py

Responsibilities:

Accept SensorReading

Convert to JSON

Send via HTTP client

Handle retry strategy

Return success/failure

5️⃣ main.py

Responsibilities:

Initialize logging

Load configuration

Initialize services

Run infinite loop

Loop behavior:

Read sensor

If valid → send to API

If failure → log

Sleep 30–60 seconds

Never terminate on runtime errors.

Use:

if __name__ == "__main__":
6️⃣ Resilience Requirements
Sensor Resilience

Retry failed reads (max 3)

Continue loop on failure

Log warning

Do not exit

Network Resilience

Exponential backoff (1s, 2s, 4s, ...)

Cap retries

Drop packet after max retries

Continue next cycle

Optional (Bonus if implemented)

Local JSON file buffering if API unreachable

Flush buffer when connection restored

7️⃣ Configuration

Use config.py:

API_URL

DEVICE_ID

READ_INTERVAL_SECONDS

MAX_SENSOR_RETRIES

MAX_HTTP_RETRIES

HTTP_TIMEOUT

Do not hardcode values.

8️⃣ SOLID Principles Enforcement

Single Responsibility:

Each module has one reason to change.

Open/Closed:

Retry strategy configurable without modifying core logic.

Liskov:

Define interfaces (Protocols) for:

SensorReader

DataTransmitter

Dependency Inversion:

Application layer depends on abstractions, not concrete DHT or HTTP implementations.

9️⃣ Systemd Compatibility

Requirements:

Application must not daemonize itself.

Log only to stdout.

Exit only on fatal initialization failure.

Clean KeyboardInterrupt handling.

Provide example systemd unit file:

[Unit]
Description=Edge DHT22 Sensor Service
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/edge
ExecStart=/home/pi/edge/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
🔟 Coding Standards

Python 3.10+

Type hints everywhere

No global mutable state

No business logic in infrastructure layer

Docstrings required

Use dataclasses

Follow PEP8

Mental Model

This edge device is:

A data producer

Part of a distributed system

Potentially unreliable

Resource constrained

Design for:

Failure

Observability

Recoverability

Not for “it works once”.

If Copilot generates:

tightly coupled code

print-based debugging

no retries

logic inside main

hardcoded constants

Refactor immediately.

This is an edge system component — treat it like production infrastructure, not a hobby script.