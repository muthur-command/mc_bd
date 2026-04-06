"""Admin 插件只读接口（仅 Jwt）。"""

from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings


def test_get_all_plugins(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch("backend.app.admin.api.v1.sys.plugin.plugin_service.get_all", new_callable=AsyncMock) as m:
        m.return_value = [{"plugin": {"name": "docker"}}]
        r = admin_client.get(f"{settings.FASTAPI_API_V1_PATH}/sys/plugins", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body.get("code") == 200
        assert body.get("data") == [{"plugin": {"name": "docker"}}]
        m.assert_awaited_once()


def test_plugin_changed(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch("backend.app.admin.api.v1.sys.plugin.plugin_service.changed", new_callable=AsyncMock) as m:
        m.return_value = "1"
        r = admin_client.get(f"{settings.FASTAPI_API_V1_PATH}/sys/plugins/changed", headers=auth_headers)
        assert r.status_code == 200
        assert r.json().get("data") is True


def test_get_remote_list_urls_route(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch("backend.app.admin.api.v1.sys.plugin.plugin_service.get_remote_list_urls", new_callable=AsyncMock) as m:
        m.return_value = ["https://example.com/p.json"]
        r = admin_client.get(f"{settings.FASTAPI_API_V1_PATH}/sys/plugins/remote/urls", headers=auth_headers)
        assert r.status_code == 200
        assert r.json().get("data") == ["https://example.com/p.json"]
