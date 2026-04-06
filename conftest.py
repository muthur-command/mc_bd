"""仓库根级 pytest 入口：为所有 testpaths 注册共享 fixture（含 `backend/plugin/**/tests`）。"""

from __future__ import annotations

import os

import pytest

from tests.helpers.python_on_whales_stub import (
    install_python_on_whales_stub,
    restore_python_on_whales,
)

# 在模块加载阶段注入桩（早于各 conftest 对 backend.plugin.docker 的 import）；仅跑 plugin 子目录测试时也需要。
_dpw_restore: tuple[object | None, object | None] = install_python_on_whales_stub()


def pytest_unconfigure(config: pytest.Config) -> None:
    global _dpw_restore
    if _dpw_restore is not None:
        restore_python_on_whales(_dpw_restore)
        _dpw_restore = None


pytest_plugins = (
    "tests.fixtures.db",
    "tests.fixtures.redis",
    "tests.fixtures.admin_models",
    "tests.fixtures.fastapi_minimal",
    "tests.fixtures.crypto_keys",
    "tests.fixtures.http_headers_fixtures",
    "tests.fixtures.celery",
    "tests.fixtures.jwt_context",
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """设置 `SKIP_SLOW=1` 时跳过 `@pytest.mark.slow`（与 `-m "not slow"` 二选一）。"""
    if os.environ.get("SKIP_SLOW", "").strip().lower() not in ("1", "true", "yes"):
        return
    skip = pytest.mark.skip(
        reason="已设置 SKIP_SLOW：跳过慢测；完整套件请 unset SKIP_SLOW 或仅对子集运行",
    )
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)
