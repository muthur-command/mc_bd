"""
完整应用集成测试：依赖真实 PostgreSQL/MySQL 与 Redis。

运行前：
- 配置 `backend/.env`（或项目约定的环境变量）；
- `RUN_INTEGRATION=1 uv run pytest tests/integration/`

未设置 `RUN_INTEGRATION` 时，本目录用例在收集阶段会被跳过（见 `tests/conftest.py`）。
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.core.conf import settings

pytestmark = pytest.mark.integration


def test_openapi_schema_available(integration_client: TestClient) -> None:
    """OpenAPI JSON 可访问且包含路由表（验证应用与路由注册）。"""
    url = settings.FASTAPI_OPENAPI_URL
    if not url:
        pytest.skip("当前配置关闭了 OpenAPI（FASTAPI_OPENAPI_URL 为空）")
    r = integration_client.get(url)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("openapi")
    paths = data.get("paths") or {}
    assert len(paths) > 0


def test_login_captcha_route_hits_db_and_redis(integration_client: TestClient) -> None:
    """登录验证码：DB 会话、Redis、限流与业务链路与生产一致。"""
    path = f"{settings.FASTAPI_API_V1_PATH}/auth/captcha"
    r = integration_client.get(path)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("code") == 200
    data = body.get("data") or {}
    assert "uuid" in data
    assert "image" in data
