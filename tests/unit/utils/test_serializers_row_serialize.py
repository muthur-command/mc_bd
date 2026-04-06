"""backend.utils.serializers — select_columns_serialize / select_list_serialize。"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

from backend.utils.serializers import select_columns_serialize, select_list_serialize


def test_select_columns_serialize_basic() -> None:
    row = MagicMock()
    row.__table__ = MagicMock()
    row.__table__.columns.keys.return_value = ("id", "name")
    row.id = 1
    row.name = "n"
    assert select_columns_serialize(row) == {"id": 1, "name": "n"}


def test_select_columns_serialize_decimal() -> None:
    row = MagicMock()
    row.__table__ = MagicMock()
    row.__table__.columns.keys.return_value = ("price",)
    row.price = Decimal("1.5")
    out = select_columns_serialize(row)
    assert out["price"] == 1.5


def test_select_list_serialize() -> None:
    row = MagicMock()
    row.__table__ = MagicMock()
    row.__table__.columns.keys.return_value = ("id",)
    row.id = 7
    assert select_list_serialize([row]) == [{"id": 7}]
