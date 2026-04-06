"""PluginService 单元测试（纯逻辑与设置门禁）。"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.admin.service.plugin_service import PluginService
from backend.common.enums import PluginType
from backend.common.exception import errors
from backend.core.conf import settings


def test_parse_remote_response_variants() -> None:
    assert PluginService._parse_remote_response([{'a': 1}]) == [{'a': 1}]
    assert PluginService._parse_remote_response({'plugins': [{'x': 1}]}) == [{'x': 1}]
    assert PluginService._parse_remote_response({'data': [1, 2]}) == [1, 2]
    assert PluginService._parse_remote_response({'data': {}}) == []
    assert PluginService._parse_remote_response({}) == []


@pytest.mark.asyncio
async def test_install_raises_outside_dev() -> None:
    with patch.object(settings, 'ENVIRONMENT', 'prod'):
        with pytest.raises(errors.RequestError) as ei:
            await PluginService.install(type=PluginType.zip, file=None, repo_url=None)
        assert ei.value.msg == 'error.plugin_install_dev_only'


@pytest.mark.asyncio
async def test_get_remote_list_urls_from_json_list() -> None:
    with patch('backend.app.admin.service.plugin_service.redis_client') as redis:
        redis.get = AsyncMock(return_value='["https://a.example/list.json","https://b.example/l.json"]')
        urls = await PluginService.get_remote_list_urls()
        assert urls == ['https://a.example/list.json', 'https://b.example/l.json']


@pytest.mark.asyncio
async def test_get_remote_list_urls_fallback_single_key() -> None:
    with patch('backend.app.admin.service.plugin_service.redis_client') as redis:
        redis.get = AsyncMock(side_effect=[None, '  https://only.example/x.json  '])
        urls = await PluginService.get_remote_list_urls()
        assert urls == ['https://only.example/x.json']


@pytest.mark.asyncio
async def test_get_all_empty_when_no_redis_keys() -> None:
    async def empty_scan(_pattern: str):
        if False:  # pragma: no cover
            yield ''

    with patch('backend.app.admin.service.plugin_service.redis_client') as redis:
        redis.scan_iter = empty_scan
        out = await PluginService.get_all()
        assert out == []
