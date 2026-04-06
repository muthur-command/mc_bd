"""mc_bd 测试共享工具（纯函数 / 上下文管理器）。

跨用例的 **pytest fixture** 放在 `tests/fixtures/` 并由仓库根 `conftest.py` 的 `pytest_plugins` 加载；此处为无 fixture 形态的可调用工具。
"""

from tests.helpers.fastapi_testing import (
    apply_mock_db_dependency_overrides,
    build_app_with_pagination_and_mock_db,
    noop_rate_limiter_call,
    starlette_test_client,
)
from tests.helpers.http_headers import bearer_auth_headers
from tests.helpers.mocks import async_db_mock
from tests.helpers.paths import backend_dotenv_path, tests_dir
from tests.helpers.python_on_whales_stub import (
    install_python_on_whales_stub,
    restore_python_on_whales,
)

__all__ = [
    "apply_mock_db_dependency_overrides",
    "async_db_mock",
    "backend_dotenv_path",
    "bearer_auth_headers",
    "build_app_with_pagination_and_mock_db",
    "install_python_on_whales_stub",
    "noop_rate_limiter_call",
    "restore_python_on_whales",
    "starlette_test_client",
    "tests_dir",
]
