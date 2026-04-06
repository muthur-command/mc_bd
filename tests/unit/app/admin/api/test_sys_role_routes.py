"""Admin 系统角色路由（仅 Jwt + 分页，无 RBAC）。"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.common.enums import StatusType
from backend.core.conf import settings


def test_get_all_roles(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch("backend.app.admin.api.v1.sys.role.role_service.get_all", new_callable=AsyncMock) as m:
        m.return_value = []
        r = admin_client.get(f"{settings.FASTAPI_API_V1_PATH}/sys/roles/all", headers=auth_headers)
        assert r.status_code == 200
        assert r.json().get("code") == 200
        assert r.json().get("data") == []
        m.assert_awaited_once()


def test_get_role_detail(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    fake = SimpleNamespace(
        id=1,
        name="admin",
        status=StatusType.enable,
        remark=None,
        created_time=datetime(2026, 1, 1, 12, 0, 0),
        updated_time=None,
    )
    with patch("backend.app.admin.api.v1.sys.role.role_service.get", new_callable=AsyncMock) as m:
        m.return_value = fake
        r = admin_client.get(f"{settings.FASTAPI_API_V1_PATH}/sys/roles/1", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body.get("code") == 200
        data = body.get("data") or {}
        assert data.get("id") == 1
        assert data.get("name") == "admin"
        m.assert_awaited_once()


def test_get_roles_paginated(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    page = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 20,
        "total_pages": 0,
        "links": {"first": "", "last": "", "self": "", "next": None, "prev": None},
    }
    with patch("backend.app.admin.api.v1.sys.role.role_service.get_list", new_callable=AsyncMock) as m:
        m.return_value = page
        r = admin_client.get(
            f"{settings.FASTAPI_API_V1_PATH}/sys/roles",
            headers=auth_headers,
            params={"page": 1, "size": 20},
        )
        assert r.status_code == 200
        assert r.json().get("code") == 200
        m.assert_awaited_once()
