"""StateMiddleware：在 ContextMiddleware 下写入 ctx。"""

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette_context.middleware import ContextMiddleware
from starlette_context.plugins import RequestIdPlugin

from backend.common.context import ctx
from backend.common.dataclasses import IpInfo, UserAgentInfo
from backend.middleware.state_middleware import StateMiddleware


def test_state_middleware_populates_context() -> None:
    app = FastAPI()
    app.add_middleware(StateMiddleware)
    app.add_middleware(ContextMiddleware, plugins=[RequestIdPlugin(validate=False)])

    ip_info = IpInfo(ip='10.0.0.1', country='C', region='R', city='City')
    ua_info = UserAgentInfo(
        user_agent='UA/1.0',
        os='Linux',
        browser='Firefox',
        device='desktop',
    )

    @app.get('/ctx')
    async def _ctx() -> dict:
        return {
            'ip': ctx.ip,
            'country': ctx.country,
            'city': ctx.city,
            'browser': ctx.browser,
        }

    with patch('backend.middleware.state_middleware.parse_ip_info', new_callable=AsyncMock, return_value=ip_info):
        with patch('backend.middleware.state_middleware.parse_user_agent_info', return_value=ua_info):
            client = TestClient(app)
            r = client.get('/ctx')
            assert r.status_code == 200
            data = r.json()
            assert data['ip'] == '10.0.0.1'
            assert data['country'] == 'C'
            assert data['city'] == 'City'
            assert data['browser'] == 'Firefox'
