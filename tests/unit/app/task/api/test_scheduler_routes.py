"""任务调度 HTTP 路由（仅 Jwt / 分页）。"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings

_PAGE_SHELL = {
    'items': [],
    'total': 0,
    'page': 1,
    'size': 20,
    'total_pages': 0,
    'links': {'first': '', 'last': '', 'self': '', 'next': None, 'prev': None},
}


def test_get_all_schedulers(task_client: TestClient, task_auth_headers: dict[str, str]) -> None:
    with patch('backend.app.task.api.v1.scheduler.task_scheduler_service.get_all', new_callable=AsyncMock) as m:
        m.return_value = []
        r = task_client.get(f'{settings.FASTAPI_API_V1_PATH}/schedulers/all', headers=task_auth_headers)
        assert r.status_code == 200
        assert r.json().get('code') == 200
        assert r.json().get('data') == []


def test_get_scheduler_detail(task_client: TestClient, task_auth_headers: dict[str, str]) -> None:
    fake = SimpleNamespace(
        id=1,
        name='ping',
        task='t.ping',
        args=None,
        kwargs=None,
        queue=None,
        exchange=None,
        routing_key=None,
        start_time=None,
        expire_time=None,
        expire_seconds=None,
        type=0,
        interval_every=None,
        interval_period=None,
        crontab='* * * * *',
        one_off=False,
        remark=None,
        enabled=True,
        total_run_count=0,
        last_run_time=None,
        created_time=datetime(2026, 1, 1, 0, 0, 0),
        updated_time=None,
    )
    with patch('backend.app.task.api.v1.scheduler.task_scheduler_service.get', new_callable=AsyncMock) as m:
        m.return_value = fake
        r = task_client.get(f'{settings.FASTAPI_API_V1_PATH}/schedulers/1', headers=task_auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body.get('code') == 200
        assert (body.get('data') or {}).get('id') == 1


def test_get_schedulers_paginated(task_client: TestClient, task_auth_headers: dict[str, str]) -> None:
    page = {**_PAGE_SHELL, 'items': []}
    with patch('backend.app.task.api.v1.scheduler.task_scheduler_service.get_list', new_callable=AsyncMock) as m:
        m.return_value = page
        r = task_client.get(
            f'{settings.FASTAPI_API_V1_PATH}/schedulers',
            headers=task_auth_headers,
            params={'page': 1, 'size': 20, 'name': 'x', 'type': 0},
        )
        assert r.status_code == 200, r.text
        assert r.json().get('code') == 200
        m.assert_awaited_once()
