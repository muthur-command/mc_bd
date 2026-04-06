"""app 聚合路由：至少包含若干子路由。"""

from fastapi import APIRouter
from fastapi.routing import APIRoute, APIWebSocketRoute

from backend.app.admin.api.router import v1 as admin_v1
from backend.app.task.api.router import v1 as task_v1


def _count_api_routes(router) -> int:
    n = 0
    for r in router.routes:
        if isinstance(r, (APIRoute, APIWebSocketRoute)):
            n += 1
        elif isinstance(r, APIRouter):
            n += _count_api_routes(r)
    return n


def test_admin_v1_has_routes() -> None:
    assert _count_api_routes(admin_v1) >= 1


def test_task_v1_has_routes() -> None:
    assert _count_api_routes(task_v1) >= 1
