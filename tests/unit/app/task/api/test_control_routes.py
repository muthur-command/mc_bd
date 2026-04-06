"""任务控制：已注册任务列表。"""

from unittest.mock import AsyncMock, MagicMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings


def test_get_task_registered(task_client: TestClient, task_auth_headers: dict[str, str]) -> None:
    """tasks.get 返回 None 时走字符串分支，响应可 JSON 序列化。"""
    mock_app = MagicMock()
    mock_app.control.inspect.return_value = MagicMock()
    mock_app.tasks.get.return_value = None

    with patch('backend.app.task.api.v1.control.run_in_threadpool', new_callable=AsyncMock) as rip:
        rip.return_value = {'worker@host': ['some.registered.task']}
        with patch('backend.app.task.api.v1.control.celery_app', mock_app):
            r = task_client.get(f'{settings.FASTAPI_API_V1_PATH}/tasks/registered', headers=task_auth_headers)
            assert r.status_code == 200, r.text
            body = r.json()
            assert body.get('code') == 200
            data = body.get('data') or []
            assert len(data) == 1
            assert data[0].get('name') == 'some.registered.task'
            assert data[0].get('task') == 'some.registered.task'
