"""Admin Auth 路由：logout、codes 等。"""

from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings


def test_logout_returns_success(admin_client: TestClient) -> None:
    r = admin_client.post(f"{settings.FASTAPI_API_V1_PATH}/auth/logout")
    assert r.status_code == 200
    body = r.json()
    assert body.get("code") == 200


def test_get_codes_returns_success(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch("backend.app.admin.api.v1.auth.auth.auth_service.get_codes", new_callable=AsyncMock) as m:
        m.return_value = ["sys:menu:list"]
        r = admin_client.get(f"{settings.FASTAPI_API_V1_PATH}/auth/codes", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body.get("code") == 200
        assert body.get("data") == ["sys:menu:list"]
        m.assert_awaited_once()
