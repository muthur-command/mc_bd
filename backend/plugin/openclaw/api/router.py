"""OpenClaw 插件：提供 Gateway 配置（baseUrl / wsUrl）供 mc_fd 前端连接 WebSocket。"""
from fastapi import APIRouter

from backend.core.conf import settings
from backend.plugin.core import load_plugin_config

v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/openclaw', tags=['OpenClaw 网关'])


@v1.get('/config')
async def get_openclaw_config():
    """返回 Gateway 的 baseUrl 与 wsUrl，供前端建立 WebSocket 连接。"""
    data = load_plugin_config('openclaw')
    plugin_settings = data.get('settings') or {}
    base_url = (plugin_settings.get('OPENCLAW_GATEWAY_BASE_URL') or 'http://127.0.0.1:18789').strip().rstrip('/')
    ws_url = base_url.replace('https://', 'wss://', 1).replace('http://', 'ws://', 1)
    return {'baseUrl': base_url, 'wsUrl': ws_url}
