"""收集阶段前注入 `python_on_whales` 桩，避免未装 Docker 时导入失败。"""

from __future__ import annotations

import sys
import types

from typing import Any
from unittest.mock import MagicMock


def install_python_on_whales_stub() -> tuple[Any | None, Any | None]:
    old_dpw = sys.modules.pop('python_on_whales', None)
    old_dpw_exc = sys.modules.pop('python_on_whales.exceptions', None)
    stub = types.ModuleType('python_on_whales')
    stub.DockerClient = type('DockerClient', (), {})
    stub.docker = MagicMock()
    sys.modules['python_on_whales'] = stub
    exc_mod = types.ModuleType('python_on_whales.exceptions')

    class DockerException(Exception):
        pass

    exc_mod.DockerException = DockerException
    sys.modules['python_on_whales.exceptions'] = exc_mod
    return old_dpw, old_dpw_exc


def restore_python_on_whales(saved: tuple[Any | None, Any | None]) -> None:
    old_dpw, old_dpw_exc = saved
    sys.modules.pop('python_on_whales', None)
    sys.modules.pop('python_on_whales.exceptions', None)
    if old_dpw_exc is not None:
        sys.modules['python_on_whales.exceptions'] = old_dpw_exc
    if old_dpw is not None:
        sys.modules['python_on_whales'] = old_dpw
