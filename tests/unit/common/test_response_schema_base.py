"""backend.common.response.response_schema — ResponseBase 与 fast_success。"""

from __future__ import annotations

import json

from backend.common.response.response_code import CustomResponseCode
from backend.common.response.response_schema import ResponseBase, response_base


def test_response_base_success_default() -> None:
    m = response_base.success(data={'x': 1})
    d = m.model_dump()
    assert d['code'] == CustomResponseCode.HTTP_200.code
    assert d['data'] == {'x': 1}


def test_response_base_fail_custom_code() -> None:
    m = response_base.fail(res=CustomResponseCode.HTTP_500)
    assert m.model_dump()['code'] == CustomResponseCode.HTTP_500.code


def test_fast_success_returns_msgspec_response() -> None:
    resp = ResponseBase.fast_success(data={'a': 2})
    body = json.loads(resp.body.decode())
    assert body['code'] == CustomResponseCode.HTTP_200.code
    assert body['data'] == {'a': 2}
