"""backend.utils.serializers — MsgSpecJSONResponse.render。"""

from __future__ import annotations

import json

from backend.utils.serializers import MsgSpecJSONResponse


def test_msgspec_json_response_render_encodes_dict() -> None:
    r = MsgSpecJSONResponse(content={"code": 200, "msg": "ok", "data": {"n": 1}})
    raw = r.render({"code": 200, "msg": "ok", "data": {"n": 1}})
    assert json.loads(raw.decode()) == {"code": 200, "msg": "ok", "data": {"n": 1}}
