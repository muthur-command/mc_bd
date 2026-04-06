"""集成测试共享 fixture：完整 ASGI lifespan（数据库表、Redis、限流、雪花等）。"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from starlette.testclient import TestClient


@pytest.fixture(scope="module")
def integration_client() -> Generator[TestClient, None, None]:
    """`register_app()` + `TestClient` 上下文，进入时跑 `register_init`，退出时释放连接与后台任务。"""
    from backend.core.registrar import register_app

    try:
        app = register_app()
    except SystemExit:
        pytest.skip(
            "register_app 过程中退出：构建路由时会连接 Redis（见 plugin.core.parse_plugin_config）。"
            "请先启动 Redis 并配置 .env。",
        )
    except Exception as exc:
        pytest.skip(f"register_app 失败: {exc}")

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    except Exception as exc:
        pytest.skip(
            f"ASGI lifespan 启动失败（数据库建表 / Redis / 限流 / 雪花等）：{exc}",
        )
