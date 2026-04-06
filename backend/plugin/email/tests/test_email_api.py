"""Email 插件 HTTP：验证码邮件路由（mock Redis / send_email / ctx.ip）。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.conf import settings

if TYPE_CHECKING:
    from starlette.testclient import TestClient

_BASE = f'{settings.FASTAPI_API_V1_PATH}/emails'


def test_send_email_captcha_success(
    email_api_client: TestClient,
    email_auth_headers: dict[str, str],
) -> None:
    mock_ctx = MagicMock()
    mock_ctx.ip = '203.0.113.10'

    with patch('backend.plugin.email.api.v1.email.ctx', mock_ctx):
        with patch(
            'backend.plugin.email.api.v1.email.redis_client.set',
            new_callable=AsyncMock,
        ) as redis_set:
            with patch(
                'backend.plugin.email.api.v1.email.send_email',
                new_callable=AsyncMock,
            ) as send:
                r = email_api_client.post(
                    f'{_BASE}/captcha',
                    headers=email_auth_headers,
                    json={'recipients': 'user@example.com'},
                )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get('code') == 200
    redis_set.assert_awaited_once()
    key = redis_set.await_args[0][0]
    assert key == f'{settings.EMAIL_CAPTCHA_REDIS_PREFIX}:{mock_ctx.ip}'
    send.assert_awaited_once()
    _db, recipients, subject, content, template = send.await_args[0]
    assert recipients == 'user@example.com'
    assert subject == 'MC 验证码'
    assert template == 'captcha.html'
    assert isinstance(content, dict)
    assert len(content.get('code', '')) == 6
    assert content.get('expired') == int(settings.EMAIL_CAPTCHA_EXPIRE_SECONDS / 60)


def test_send_email_captcha_accepts_recipient_list(
    email_api_client: TestClient,
    email_auth_headers: dict[str, str],
) -> None:
    mock_ctx = MagicMock()
    mock_ctx.ip = '198.51.100.1'

    with patch('backend.plugin.email.api.v1.email.ctx', mock_ctx):
        with patch('backend.plugin.email.api.v1.email.redis_client.set', new_callable=AsyncMock):
            with patch('backend.plugin.email.api.v1.email.send_email', new_callable=AsyncMock) as send:
                r = email_api_client.post(
                    f'{_BASE}/captcha',
                    headers=email_auth_headers,
                    json={'recipients': ['a@x.com', 'b@x.com']},
                )

    assert r.status_code == 200, r.text
    assert send.await_args[0][1] == ['a@x.com', 'b@x.com']
