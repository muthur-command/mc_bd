"""Admin 操作日志分页列表。"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.common.enums import StatusType
from backend.core.conf import settings


def test_get_opera_logs_paginated(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    now = datetime(2026, 1, 1, 12, 0, 0)
    row = SimpleNamespace(
        id=1,
        trace_id="t1",
        username="admin",
        method="GET",
        title="分页获取操作日志",
        path="/api",
        ip="127.0.0.1",
        country=None,
        region=None,
        city=None,
        user_agent="",
        browser="",
        os="",
        device="",
        args=None,
        status=StatusType.enable,
        code="200",
        msg=None,
        cost_time=0.01,
        opera_time=now,
        created_time=now,
    )
    page = {
        "items": [row],
        "total": 1,
        "page": 1,
        "size": 20,
        "total_pages": 1,
        "links": {"first": "", "last": "", "self": "", "next": None, "prev": None},
    }
    with patch("backend.app.admin.api.v1.log.opera_log.opera_log_service.get_list", new_callable=AsyncMock) as m:
        m.return_value = page
        with patch("backend.app.admin.api.v1.log.opera_log.t", side_effect=lambda key, default=None: default or key):
            r = admin_client.get(
                f"{settings.FASTAPI_API_V1_PATH}/logs/opera",
                headers=auth_headers,
                params={"page": 1, "size": 20},
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body.get("code") == 200
            items = (body.get("data") or {}).get("items") or []
            assert len(items) == 1
            assert "title_display" in items[0]
        m.assert_awaited_once()
