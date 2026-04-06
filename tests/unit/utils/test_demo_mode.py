"""backend.utils.demo_mode — demo_site。"""

from unittest.mock import MagicMock, patch

import pytest

from backend.common.exception import errors
from backend.core.conf import settings
from backend.utils.demo_mode import demo_site


@pytest.mark.asyncio
async def test_demo_site_off_no_block() -> None:
    req = MagicMock()
    req.method = 'POST'
    req.url.path = '/api/v1/x'
    with patch.object(settings, 'DEMO_MODE', False):
        await demo_site(req)


@pytest.mark.asyncio
async def test_demo_site_allows_get_when_enabled() -> None:
    req = MagicMock()
    req.method = 'GET'
    req.url.path = '/api/v1/x'
    with patch.object(settings, 'DEMO_MODE', True):
        await demo_site(req)


@pytest.mark.asyncio
async def test_demo_site_allows_options_when_enabled() -> None:
    req = MagicMock()
    req.method = 'OPTIONS'
    req.url.path = '/api/v1/x'
    with patch.object(settings, 'DEMO_MODE', True):
        await demo_site(req)


@pytest.mark.asyncio
async def test_demo_site_blocks_non_get_when_enabled() -> None:
    req = MagicMock()
    req.method = 'POST'
    req.url.path = '/api/v1/x'
    with patch.object(settings, 'DEMO_MODE', True), patch.object(settings, 'DEMO_MODE_EXCLUDE', set()):
        with pytest.raises(errors.ForbiddenError):
            await demo_site(req)


@pytest.mark.asyncio
async def test_demo_site_respects_exclude() -> None:
    req = MagicMock()
    req.method = 'POST'
    req.url.path = '/api/v1/special'
    exclude = {('POST', '/api/v1/special')}
    with patch.object(settings, 'DEMO_MODE', True), patch.object(settings, 'DEMO_MODE_EXCLUDE', exclude):
        await demo_site(req)
