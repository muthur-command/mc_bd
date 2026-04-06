"""backend.utils.limiter — http_limit_callback。"""

from unittest.mock import MagicMock

import pytest

from backend.common.exception import errors
from backend.utils.limiter import http_limit_callback


@pytest.mark.asyncio
async def test_http_limit_callback_raises_429_with_retry_after() -> None:
    req = MagicMock()
    resp = MagicMock()
    with pytest.raises(errors.HTTPError) as ei:
        await http_limit_callback(req, resp, expire=2500)
    assert ei.value.status_code == 429
    assert ei.value.headers['Retry-After'] == '3'
