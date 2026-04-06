"""HTTP 请求头构造。"""

from __future__ import annotations


def bearer_auth_headers(token: str = 'pytest-bearer-token') -> dict[str, str]:
    """满足 `HTTPBearer` 非空校验等场景。"""
    return {'Authorization': f'Bearer {token}'}
