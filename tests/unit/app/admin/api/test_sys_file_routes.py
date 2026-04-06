"""Admin 本地上传路由（RBAC + 文件桩）。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

from backend.core.conf import settings

if TYPE_CHECKING:
    from starlette.testclient import TestClient

_UPLOAD = f'{settings.FASTAPI_API_V1_PATH}/sys/files/upload'


def test_upload_file_returns_static_url(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch('backend.app.admin.api.v1.sys.file.upload_file_verify'):
        with patch(
            'backend.app.admin.api.v1.sys.file.upload_file',
            new_callable=AsyncMock,
            return_value='doc_123.txt',
        ) as up:
            r = admin_client.post(
                _UPLOAD,
                headers=auth_headers,
                files={'file': ('hello.txt', b'hello', 'text/plain')},
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body.get('code') == 200
            assert (body.get('data') or {}).get('url') == '/static/upload/doc_123.txt'
            up.assert_awaited_once()
