"""任务结果 HTTP 路由。"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings

_PAGE_SHELL = {
    "items": [],
    "total": 0,
    "page": 1,
    "size": 20,
    "total_pages": 0,
    "links": {"first": "", "last": "", "self": "", "next": None, "prev": None},
}


def test_get_task_result_detail(task_client: TestClient, task_auth_headers: dict[str, str]) -> None:
    fake = SimpleNamespace(
        id=1,
        task_id="uuid",
        status="SUCCESS",
        result=None,
        date_done=datetime(2026, 1, 1, 0, 0, 0),
        traceback=None,
        name="n",
        args=None,
        kwargs=None,
        worker="w",
        retries=0,
        queue="q",
    )
    with patch("backend.app.task.api.v1.result.task_result_service.get", new_callable=AsyncMock) as m:
        m.return_value = fake
        r = task_client.get(f"{settings.FASTAPI_API_V1_PATH}/task-results/1", headers=task_auth_headers)
        assert r.status_code == 200
        assert (r.json().get("data") or {}).get("task_id") == "uuid"


def test_get_task_results_paginated(task_client: TestClient, task_auth_headers: dict[str, str]) -> None:
    page = {**_PAGE_SHELL, "items": []}
    with patch("backend.app.task.api.v1.result.task_result_service.get_list", new_callable=AsyncMock) as m:
        m.return_value = page
        r = task_client.get(
            f"{settings.FASTAPI_API_V1_PATH}/task-results",
            headers=task_auth_headers,
            params={"page": 1, "size": 20},
        )
        assert r.status_code == 200, r.text
        assert r.json().get("code") == 200
