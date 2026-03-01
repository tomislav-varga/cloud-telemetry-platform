from collections.abc import AsyncGenerator
from pathlib import Path
import sys
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import Base, get_db
from backend.main import app
from backend.models.device import Device
from backend.security.hashing import generate_api_key


@pytest.fixture()
async def db_sessionmaker() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    test_sessionmaker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_sessionmaker

    await engine.dispose()


@pytest.fixture()
async def client(db_sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()

@pytest.fixture()
def device_factory(db_sessionmaker: async_sessionmaker[AsyncSession]):
    async def _create(device_id: str | None = None, is_active: bool = True) -> dict[str, str]:
        resolved_device_id = device_id or f"device-{uuid.uuid4().hex[:8]}"
        prefix, raw_key, hashed = generate_api_key()

        async with db_sessionmaker() as session:
            device = Device(
                device_id=resolved_device_id,
                key_prefix=prefix,
                api_key_hash=hashed,
                is_active=is_active,
            )
            session.add(device)
            await session.commit()

        return {
            "device_id": resolved_device_id,
            "key_prefix": prefix,
            "raw_key": raw_key,
        }

    return _create
