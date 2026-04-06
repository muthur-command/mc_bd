"""Docker 插件 HTTP 路由：mock docker_service / DB，不依赖本机 Docker。"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from backend.core.conf import settings
from backend.database.db import get_db
from backend.plugin.docker.model.docker_config import DockerConfig

_BASE = f"{settings.FASTAPI_API_V1_PATH}/docker"


def _scalar_result(row: object | None) -> MagicMock:
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=row)
    return r


def test_list_containers_returns_data(
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    payload = [
        {
            "id": "abc",
            "name": "c1",
            "image": "nginx:latest",
            "status": "running",
            "created": None,
            "ports": [],
            "stack": None,
            "ip_address": None,
            "ownership": None,
        }
    ]
    with patch(
        "backend.plugin.docker.api.v1.containers.docker_service.list_containers",
        return_value=payload,
    ):
        r = docker_api_client.get(
            f"{_BASE}/containers",
            headers=docker_auth_headers,
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("code") == 200
    assert body.get("data") == payload


def test_get_system_info_returns_data(
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    info = {
        "containers": 1,
        "containers_running": 1,
        "containers_paused": 0,
        "containers_stopped": 0,
        "images": 2,
        "driver": "overlay2",
        "memory_limit": True,
        "mem_total": 8 * 1024**3,
        "cpus": 4,
        "kernel_version": "6.0",
        "operating_system": "Linux",
        "os_type": "linux",
        "architecture": "x86_64",
        "docker_version": "24.0.0",
    }
    with patch(
        "backend.plugin.docker.api.v1.system.docker_service.get_system_info",
        return_value=info,
    ):
        r = docker_api_client.get(
            f"{_BASE}/system/info",
            headers=docker_auth_headers,
        )
    assert r.status_code == 200, r.text
    assert r.json().get("data") == info


def test_get_disk_usage_returns_data(
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    usage = {
        "images_size": 100,
        "containers_size": 200,
        "volumes_size": 50,
        "build_cache_size": 10,
        "total_size": 360,
    }
    with patch(
        "backend.plugin.docker.api.v1.system.docker_service.get_disk_usage",
        return_value=usage,
    ):
        r = docker_api_client.get(
            f"{_BASE}/system/df",
            headers=docker_auth_headers,
        )
    assert r.status_code == 200, r.text
    assert r.json().get("data") == usage


def test_get_connected_status_via_api(
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    with patch(
        "backend.plugin.docker.api.v1.system.docker_service.get_connected_status",
        new_callable=AsyncMock,
        return_value=True,
    ) as m:
        r = docker_api_client.get(
            f"{_BASE}/system/connected",
            headers=docker_auth_headers,
        )
    assert r.status_code == 200, r.text
    assert r.json().get("data") == {"connected": True}
    m.assert_awaited_once()


def test_set_connected_status_via_api(
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    with patch(
        "backend.plugin.docker.api.v1.system.docker_service.set_connected_status",
        new_callable=AsyncMock,
        return_value=True,
    ) as m:
        r = docker_api_client.post(
            f"{_BASE}/system/connected",
            headers=docker_auth_headers,
            json={"connected": True},
        )
    assert r.status_code == 200, r.text
    assert r.json().get("code") == 200
    m.assert_awaited_once()


def test_set_connected_status_fail_returns_fail(
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    with patch(
        "backend.plugin.docker.api.v1.system.docker_service.set_connected_status",
        new_callable=AsyncMock,
        return_value=False,
    ):
        r = docker_api_client.post(
            f"{_BASE}/system/connected",
            headers=docker_auth_headers,
            json={"connected": False},
        )
    assert r.status_code == 200
    assert r.json().get("code") != 200


def test_list_registries_seeds_default_when_no_row(
    docker_api_app: FastAPI,
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_scalar_result(None))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    async def _db() -> AsyncMock:
        yield mock_db

    docker_api_app.dependency_overrides[get_db] = _db
    r = docker_api_client.get(f"{_BASE}/registries", headers=docker_auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("code") == 200
    data = body.get("data") or []
    assert len(data) >= 1
    assert any(x.get("is_default") for x in data)
    mock_db.add.assert_called_once()
    added = mock_db.add.call_args[0][0]
    assert isinstance(added, DockerConfig)
    mock_db.commit.assert_awaited_once()


def test_list_registries_returns_stored_json(
    docker_api_app: FastAPI,
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    stored = [
        {
            "id": "custom-1",
            "name": "Custom",
            "url": "registry.example.com",
            "is_default": False,
        }
    ]
    cfg = MagicMock()
    cfg.value = json.dumps(stored, ensure_ascii=False)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_scalar_result(cfg))

    async def _db() -> AsyncMock:
        yield mock_db

    docker_api_app.dependency_overrides[get_db] = _db
    r = docker_api_client.get(f"{_BASE}/registries", headers=docker_auth_headers)
    assert r.status_code == 200, r.text
    assert r.json().get("data") == stored


def test_create_registry_rejects_duplicate_name(
    docker_api_app: FastAPI,
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    registries = [
        {
            "id": "a",
            "name": "Dup",
            "url": "a.io",
            "is_default": False,
        }
    ]
    cfg = MagicMock()
    cfg.value = json.dumps(registries, ensure_ascii=False)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_scalar_result(cfg))

    async def _db() -> AsyncMock:
        yield mock_db

    docker_api_app.dependency_overrides[get_db] = _db
    r = docker_api_client.post(
        f"{_BASE}/registries",
        headers=docker_auth_headers,
        json={"name": "Dup", "url": "other.io"},
    )
    assert r.status_code == 200
    assert r.json().get("code") != 200


def test_update_registry_rejects_default_source(
    docker_api_app: FastAPI,
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    registries = [
        {
            "id": "docker-hub-anonymous",
            "name": "Docker Hub (anonymous)",
            "url": "docker.io",
            "is_default": True,
        }
    ]
    cfg = MagicMock()
    cfg.value = json.dumps(registries, ensure_ascii=False)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_scalar_result(cfg))

    async def _db() -> AsyncMock:
        yield mock_db

    docker_api_app.dependency_overrides[get_db] = _db
    r = docker_api_client.put(
        f"{_BASE}/registries/docker-hub-anonymous",
        headers=docker_auth_headers,
        json={"name": "X"},
    )
    assert r.status_code == 200
    assert r.json().get("code") != 200


def test_delete_registry_rejects_default_source(
    docker_api_app: FastAPI,
    docker_api_client: TestClient,
    docker_auth_headers: dict[str, str],
) -> None:
    registries = [
        {
            "id": "docker-hub-anonymous",
            "name": "Hub",
            "url": "docker.io",
            "is_default": True,
        }
    ]
    cfg = MagicMock()
    cfg.value = json.dumps(registries, ensure_ascii=False)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_scalar_result(cfg))

    async def _db() -> AsyncMock:
        yield mock_db

    docker_api_app.dependency_overrides[get_db] = _db
    r = docker_api_client.delete(
        f"{_BASE}/registries/docker-hub-anonymous",
        headers=docker_auth_headers,
    )
    assert r.status_code == 200
    assert r.json().get("code") != 200
