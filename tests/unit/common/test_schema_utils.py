"""backend.common.schema — CustomEmailStr、ser_string。"""

from __future__ import annotations

import pytest

from backend.common.schema import CustomEmailStr, ser_string


def test_custom_email_empty_returns_none() -> None:
    assert CustomEmailStr._validate("") is None  # type: ignore[arg-type]


def test_custom_email_valid() -> None:
    v = CustomEmailStr._validate("a@b.co")  # type: ignore[arg-type]
    assert v == "a@b.co"


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("x", "x"),
        ("", ""),
        (None, None),
    ],
)
def test_ser_string(inp: object, expected: str | None) -> None:
    assert ser_string(inp) == expected
