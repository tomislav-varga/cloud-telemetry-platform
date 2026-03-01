import pytest


@pytest.mark.asyncio
async def test_create_telemetry_valid_key(client, device_factory):
    device = await device_factory(device_id="pi-lab-01")
    headers = {"X-API-Key": device["raw_key"]}
    payload = {
        "device_id": "pi-lab-01",
        "temperature": 22.4,
        "humidity": 51.2,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post("/telemetry", json=payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == device["device_id"]
    assert data["temperature"] == payload["temperature"]
    assert data["humidity"] == payload["humidity"]
    assert data["timestamp"] == payload["timestamp"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_telemetry_invalid_temperature(client, device_factory):
    device = await device_factory(device_id="pi-lab-01")
    headers = {"X-API-Key": device["raw_key"]}
    payload = {
        "device_id": "pi-lab-01",
        "temperature": 1000,
        "humidity": 51.2,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post("/telemetry", json=payload, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_telemetry_missing_field(client, device_factory):
    device = await device_factory(device_id="pi-lab-01")
    headers = {"X-API-Key": device["raw_key"]}
    payload = {
        "device_id": "pi-lab-01",
        "temperature": 22.4,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post("/telemetry", json=payload, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_telemetry_missing_header(client):
    payload = {
        "device_id": "pi-lab-01",
        "temperature": 22.4,
        "humidity": 51.2,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API Key"


@pytest.mark.asyncio
async def test_create_telemetry_malformed_key(client):
    payload = {
        "device_id": "pi-lab-01",
        "temperature": 22.4,
        "humidity": 51.2,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post("/telemetry", json=payload, headers={"X-API-Key": "dev_badformat"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API Key"


@pytest.mark.asyncio
async def test_create_telemetry_invalid_key(client, device_factory):
    device = await device_factory(device_id="pi-lab-04")
    prefix = device["key_prefix"]
    invalid_key = f"{prefix}.wrong-secret"
    payload = {
        "device_id": "pi-lab-04",
        "temperature": 22.4,
        "humidity": 51.2,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post("/telemetry", json=payload, headers={"X-API-Key": invalid_key})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API Key"


@pytest.mark.asyncio
async def test_create_telemetry_inactive_device(client, device_factory):
    device = await device_factory(device_id="pi-lab-inactive", is_active=False)
    payload = {
        "device_id": "pi-lab-inactive",
        "temperature": 22.4,
        "humidity": 51.2,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post(
        "/telemetry", json=payload, headers={"X-API-Key": device["raw_key"]}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid API Key"


@pytest.mark.asyncio
async def test_spoofed_device_id_attempt_is_overridden(client, device_factory):
    device = await device_factory(device_id="pi-authenticated-01")
    payload = {
        "device_id": "spoofed-device",
        "temperature": 22.4,
        "humidity": 51.2,
        "timestamp": "2026-02-14T12:00:00Z",
    }

    response = await client.post(
        "/telemetry", json=payload, headers={"X-API-Key": device["raw_key"]}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == "pi-authenticated-01"


@pytest.mark.asyncio
async def test_get_range_query(client, device_factory):
    device = await device_factory(device_id="pi-lab-02")
    headers = {"X-API-Key": device["raw_key"]}
    await client.post(
        "/telemetry",
        json={
            "device_id": "pi-lab-02",
            "temperature": 18.0,
            "humidity": 45.0,
            "timestamp": "2026-02-14T10:00:00Z",
        },
        headers=headers,
    )
    await client.post(
        "/telemetry",
        json={
            "device_id": "pi-lab-02",
            "temperature": 19.5,
            "humidity": 48.0,
            "timestamp": "2026-02-14T11:00:00Z",
        },
        headers=headers,
    )

    response = await client.get(
        "/telemetry/pi-lab-02",
        params={
            "start": "2026-02-14T09:00:00Z",
            "end": "2026-02-14T12:00:00Z",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["timestamp"] == "2026-02-14T10:00:00Z"
    assert payload[1]["timestamp"] == "2026-02-14T11:00:00Z"


@pytest.mark.asyncio
async def test_get_latest_query(client, device_factory):
    device = await device_factory(device_id="pi-lab-03")
    headers = {"X-API-Key": device["raw_key"]}
    await client.post(
        "/telemetry",
        json={
            "device_id": "pi-lab-03",
            "temperature": 20.0,
            "humidity": 49.0,
            "timestamp": "2026-02-14T08:00:00Z",
        },
        headers=headers,
    )
    await client.post(
        "/telemetry",
        json={
            "device_id": "pi-lab-03",
            "temperature": 21.0,
            "humidity": 50.0,
            "timestamp": "2026-02-14T09:00:00Z",
        },
        headers=headers,
    )

    response = await client.get("/telemetry/pi-lab-03/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["temperature"] == 21.0
    assert payload["timestamp"] == "2026-02-14T09:00:00Z"
