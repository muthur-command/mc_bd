"""Admin 验证码路由。"""

from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings


def test_get_captcha_returns_payload(admin_client: TestClient) -> None:
    with patch("backend.app.admin.api.v1.auth.captcha.load_login_config", new_callable=AsyncMock):
        with patch("backend.app.admin.api.v1.auth.captcha.redis_client") as redis:
            redis.set = AsyncMock()
            with patch("backend.app.admin.api.v1.auth.captcha.run_in_threadpool", new_callable=AsyncMock) as rip:
                rip.return_value = ("base64img", "AB12")
                r = admin_client.get(f"{settings.FASTAPI_API_V1_PATH}/auth/captcha")
                assert r.status_code == 200
                body = r.json()
                assert body.get("code") == 200
                data = body.get("data") or {}
                assert data.get("uuid")
                assert data.get("image") == "base64img"
                assert data.get("is_enabled") == settings.LOGIN_CAPTCHA_ENABLED
                redis.set.assert_awaited()
