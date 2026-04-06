"""全局 pytest 配置与共享 fixture（对齐 core：根 conftest + 分域 conftest）。

`@pytest.mark.slow` 的跳过逻辑在**仓库根** `conftest.py`（`SKIP_SLOW=1`），以便 `backend/plugin/**/tests` 也能生效。
"""

from __future__ import annotations

import os
import warnings

import pytest

from tests.helpers.paths import backend_dotenv_path


@pytest.fixture(scope="session", autouse=True)
def _session_env_hint() -> None:
    """缺少 .env 时提示。"""
    env = backend_dotenv_path()
    if not env.is_file():
        warnings.warn(
            f"未找到 {env}，部分用例可能失败；可从 .env.example 复制。",
            stacklevel=2,
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """未设置 RUN_INTEGRATION=1 时跳过 @pytest.mark.integration。"""
    if os.environ.get("RUN_INTEGRATION", "").strip().lower() in ("1", "true", "yes"):
        return
    skip_int = pytest.mark.skip(reason="设置 RUN_INTEGRATION=1 以运行集成测试")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_int)
