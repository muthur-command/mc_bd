"""backend.common.exception.exception_handler — 纯函数分支。"""

from __future__ import annotations

from backend.common.exception.exception_handler import _get_exception_code
from backend.common.response.response_code import StandardResponseCode


def test_get_exception_code_known_status() -> None:
    assert _get_exception_code(404) == 404


def test_get_exception_code_unknown_status_maps_to_400() -> None:
    assert _get_exception_code(99999) == StandardResponseCode.HTTP_400
