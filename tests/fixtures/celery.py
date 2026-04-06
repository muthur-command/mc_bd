"""Celery 应用桩（控制面 / inspect 等）。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def celery_app_mock() -> MagicMock:
    """`celery_app` 常用属性占位；按需 `patch(..., celery_app_mock)`。"""
    app = MagicMock()
    app.control = MagicMock()
    app.control.inspect = MagicMock(return_value={})
    app.conf = MagicMock()
    return app
