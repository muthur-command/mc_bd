"""backend.common.security.jwt — 编解码基础行为。"""

import pytest

from backend.common.exception.errors import TokenError
from backend.common.security.jwt import jwt_decode, jwt_encode


def test_jwt_encode_well_formed_segments(jwt_claims_sample: dict[str, str | int]) -> None:
    token = jwt_encode(jwt_claims_sample)
    assert token.count('.') == 2


def test_jwt_decode_invalid_token() -> None:
    with pytest.raises(TokenError):
        jwt_decode('not-a-jwt')
