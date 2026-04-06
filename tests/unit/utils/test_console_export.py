"""backend.utils.console — rich console 单例。"""

from __future__ import annotations

from backend.utils.console import console


def test_console_is_rich_console() -> None:
    assert console is not None
    assert hasattr(console, 'print')
