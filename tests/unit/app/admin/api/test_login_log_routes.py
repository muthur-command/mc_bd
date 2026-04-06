"""Admin 登录日志分页列表。"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings


def test_get_login_logs_paginated(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    row = SimpleNamespace(
        id=1,
        user_uuid='u1',
        username='admin',
        status=1,
        ip='127.0.0.1',
        country=None,
        region=None,
        city=None,
        user_agent='',
        browser='',
        os='',
        device='',
        msg='登录成功',
        login_time=datetime(2026, 1, 1, 12, 0, 0),
        created_time=datetime(2026, 1, 1, 12, 0, 0),
    )
    page = {
        'items': [row],
        'total': 1,
        'page': 1,
        'size': 20,
        'total_pages': 1,
        'links': {'first': '', 'last': '', 'self': '', 'next': None, 'prev': None},
    }
    with patch('backend.app.admin.api.v1.log.login_log.login_log_service.get_list', new_callable=AsyncMock) as m:
        m.return_value = page
        with patch('backend.app.admin.api.v1.log.login_log.t', side_effect=lambda key, default=None: default or key):
            r = admin_client.get(
                f'{settings.FASTAPI_API_V1_PATH}/logs/login',
                headers=auth_headers,
                params={'page': 1, 'size': 20},
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body.get('code') == 200
            data = body.get('data') or {}
            assert data.get('total') == 1
            items = data.get('items') or []
            assert len(items) == 1
            assert 'msg_display' in items[0]
        m.assert_awaited_once()
