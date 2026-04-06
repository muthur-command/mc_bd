"""backend.utils.format"""

from backend.utils.format import fmt_bytes, fmt_seconds


def test_fmt_seconds() -> None:
    assert '天' in fmt_seconds(90000)
    assert fmt_seconds(0) == '0 秒'


def test_fmt_bytes() -> None:
    assert 'B' in fmt_bytes(512)
    assert fmt_bytes(0) == '0.00 B'
