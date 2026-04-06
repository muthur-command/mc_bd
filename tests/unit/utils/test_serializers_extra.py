"""backend.utils.serializers — 列序列化与 MsgSpecJSONResponse。"""

import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.utils.serializers import MsgSpecJSONResponse, select_columns_serialize, select_list_serialize


def test_select_columns_serialize_with_mock_row() -> None:
    table = MagicMock()
    table.columns.keys.return_value = ["id", "amount"]
    row = SimpleNamespace(__table__=table, id=1, amount=Decimal("10.5"))
    row.id = 1
    row.amount = Decimal("10.5")
    d = select_columns_serialize(row)
    assert d["id"] == 1
    assert d["amount"] == 10.5


def test_select_list_serialize() -> None:
    table = MagicMock()
    table.columns.keys.return_value = ["x"]
    row = SimpleNamespace(__table__=table, x="a")
    assert select_list_serialize([row]) == [{"x": "a"}]


def test_msgspec_json_response_render() -> None:
    r = MsgSpecJSONResponse(content={"a": 1})
    raw = r.render({"b": 2})
    assert json.loads(raw.decode()) == {"b": 2}
