📘 Copilot Instructions — API Authentication (Device API Key, FastAPI + PostgreSQL)
🎯 Goal

Implement production-grade device authentication for the Telemetry API using:

FastAPI

PostgreSQL

SQLAlchemy 2.0 (async)

Clean Architecture

API Key per device (header-based)

Secure key hashing

Dependency injection

Scalable & gateway-ready design

Authentication must be:

Stateless

Horizontally scalable

Secure by default

Rotatable

Compatible with future API Gateway (e.g., Tyk)

🏗 Architectural Principles (Mandatory)

Copilot must follow:

✅ Separation of Concerns
✅ Dependency Injection
✅ No authentication logic inside route handlers
✅ No direct DB access in API layer
✅ No plaintext API key storage
✅ No global DB sessions
✅ Async everywhere
✅ Small, testable functions

📂 Required Folder Structure Update

Add the following structure inside backend/:

backend/
├── security/
│   ├── __init__.py
│   ├── api_key.py
│   ├── hashing.py
│   └── dependencies.py
├── repositories/
│   ├── device.py

Authentication logic must NOT be placed in:

api/

models/

schemas/

Security concerns live in security/.

1️⃣ Device Authentication Strategy
Authentication Type

Header-based API Key:

X-API-Key: dev_abc123.<random_32_bytes>

Structure:

<key_prefix>.<secret>

Example:

dev_a1b2c3.ZXhhbXBsZVNlY3JldFN0cmluZw

Why prefix?

Enables indexed DB lookup

Avoids scanning all devices

Allows efficient key rotation

Industry best practice (Stripe-style pattern)

2️⃣ Database Requirements
Update devices Table

Columns:

Column	Type	Constraints
id	UUID	PK
device_id	VARCHAR	UNIQUE, NOT NULL
key_prefix	VARCHAR	UNIQUE, NOT NULL
api_key_hash	VARCHAR	NOT NULL
is_active	BOOLEAN	DEFAULT true
last_used_at	TIMESTAMP WITH TIME ZONE	NULL
created_at	TIMESTAMP WITH TIME ZONE	DEFAULT now()

Add index:

CREATE UNIQUE INDEX idx_devices_key_prefix ON devices(key_prefix);

Alembic migration required.

3️⃣ Secure API Key Handling
File: backend/security/hashing.py

Requirements:

Use bcrypt

Never store plaintext

Use constant-time comparison

Provide:

hash_api_key(raw_key: str) -> str
verify_api_key(raw_key: str, hashed: str) -> bool

Do NOT implement manual hashing logic.

4️⃣ Device Repository Layer

Create:

backend/repositories/device.py

Class:

class DeviceRepository:
    async def get_by_key_prefix(session, prefix)
    async def update_last_used(session, device)

Repository must:

Use AsyncSession

Never return None silently

Never expose internal SQL

Only query by key_prefix

5️⃣ Authentication Dependency

File:

backend/security/api_key.py

Use:

from fastapi.security import APIKeyHeader

Create header extractor:

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)

Create main dependency:

async def get_current_device(
    api_key: str = Security(api_key_header),
    session: AsyncSession = Depends(get_db)
)

Behavior:

If header missing → 401

Split key into prefix + secret

Fetch device by prefix

Verify hash

Check is_active

Update last_used_at

Return Device model

Errors:

Condition	Status
Missing header	401
Invalid format	401
Unknown prefix	401
Hash mismatch	401
Inactive device	403

Do NOT leak which part failed.

Always return generic:

"Invalid API Key"
6️⃣ Route Integration (Clean)

Update backend/api/telemetry.py

Replace:

current_device: Device = Depends(optional_device_dependency)

With:

current_device: Device = Depends(get_current_device)

Remove:

device_id from payload trust

Instead:

Override telemetry.device_id with:

current_device.device_id

Never trust client-provided device_id.

This prevents spoofing.

7️⃣ Telemetry Table Security Rule

You must enforce:

UNIQUE(device_id, timestamp)

This ensures:

Idempotency

No duplicate injection

Strong integrity

8️⃣ Logging Requirements

Use structured logging (already scaffolded).

Log:

device_id

key_prefix

authentication failures

successful authentication

disabled device attempts

Never log full API key.

Only log prefix.

9️⃣ Rate Limiting Preparation

Prepare system to allow future integration with:

SlowAPI

Redis-based rate limiter

Design requirement:

Rate limiting must be device-based.

Future example:

100 requests per minute per device

Authentication dependency must run BEFORE rate limiting.

🔟 API Key Generation Utility

Create utility function (not endpoint yet):

generate_api_key() -> tuple[prefix, raw_key, hashed]

Implementation:

prefix: "dev_" + 6 random alphanumeric chars

secret: secrets.token_urlsafe(32)

raw_key = f"{prefix}.{secret}"

hash raw_key

store prefix + hash

Return raw_key only once.

Never store secret.

1️⃣1️⃣ Health & Metrics Impact

Metrics endpoint must include:

authentication_failures_total

authenticated_requests_total

Prometheus-ready counters.

1️⃣2️⃣ Testing Requirements

Add tests:

valid key

invalid key

inactive device

missing header

malformed key

spoofed device_id attempt

telemetry insertion with auth

Use:

pytest

httpx AsyncClient
