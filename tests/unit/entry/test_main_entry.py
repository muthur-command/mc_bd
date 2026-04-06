"""backend.main — 导入时副作用在首次加载前打桩。"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def unload_main_module() -> None:
    sys.modules.pop("backend.main", None)
    yield


class _ProgressStub:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def __enter__(self) -> _ProgressStub:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def add_task(self, *args: object, **kwargs: object) -> int:
        return 1

    def update(self, *args: object, **kwargs: object) -> None:
        return None

    def advance(self, *args: object, **kwargs: object) -> None:
        return None


def test_main_module_exposes_app_after_stripped_import(unload_main_module: None) -> None:
    fake_app = MagicMock()
    with (
        patch("backend.plugin.core.get_plugins", return_value=[]),
        patch("backend.plugin.requirements.install_requirements"),
        patch("backend.core.registrar.register_app", return_value=fake_app),
        patch("rich.progress.Progress", _ProgressStub),
        patch("rich.text.Text", side_effect=lambda *a, **k: a[0] if a else ""),
        patch("backend.utils.console.console.print"),
    ):
        mod = importlib.import_module("backend.main")

    assert mod.app is fake_app
