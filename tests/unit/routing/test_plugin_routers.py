"""各插件 API 聚合路由至少挂载一条子路由。"""

import pytest
from fastapi import APIRouter
from fastapi.routing import APIRoute, APIWebSocketRoute

from backend.plugin.apprise_notify.api.router import v1 as apprise_v1
from backend.plugin.bento_layout.api.router import v1 as bento_v1
from backend.plugin.card.api.router import v1 as card_v1
from backend.plugin.docker.api.router import v1 as docker_v1
from backend.plugin.email.api.router import v1 as email_v1
from backend.plugin.oauth2.api.router import v1 as oauth2_v1
from backend.plugin.system_monitor.api.router import v1 as monitor_v1


def _count_api_routes(router) -> int:
    n = 0
    for r in router.routes:
        if isinstance(r, (APIRoute, APIWebSocketRoute)):
            n += 1
        elif isinstance(r, APIRouter):
            n += _count_api_routes(r)
    return n


@pytest.mark.parametrize(
    "name,router",
    [
        ("apprise", apprise_v1),
        ("bento_layout", bento_v1),
        ("card", card_v1),
        ("docker", docker_v1),
        ("email", email_v1),
        ("oauth2", oauth2_v1),
        ("system_monitor", monitor_v1),
    ],
)
def test_plugin_v1_has_routes(name: str, router) -> None:
    assert _count_api_routes(router) >= 1, name
