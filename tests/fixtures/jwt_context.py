"""JWT 测试用固定 claims（与业务字段对齐的最小集）。"""

from __future__ import annotations

import pytest


@pytest.fixture
def jwt_claims_sample() -> dict[str, str | int]:
    """可传入 `jwt_encode` 的稳定载荷。"""
    return {
        "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "sub": "42",
        "exp": 9_999_999_999,
    }
