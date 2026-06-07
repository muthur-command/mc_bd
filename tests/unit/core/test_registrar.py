"""backend.core.registrar — 应用注册与 lifespan 启动流程（大量打桩，不连真实 Redis/DB）。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastapi import APIRouter, FastAPI
from starlette.routing import Mount

from backend.core.conf import settings
from backend.core.registrar import (
    register_app,
    register_init,
    register_logger,
    register_middleware,
    register_page,
    register_router,
    register_socket_app,
    register_static_file,
)


def test_register_app_invokes_all_register_steps_and_lifespan() -> None:
    with (
        patch('backend.core.registrar.register_logger') as m_log,
        patch('backend.core.registrar.register_socket_app') as m_sock,
        patch('backend.core.registrar.register_static_file') as m_static,
        patch('backend.core.registrar.register_middleware') as m_mid,
        patch('backend.core.registrar.register_router') as m_route,
        patch('backend.core.registrar.register_page') as m_page,
        patch('backend.core.registrar.register_exception') as m_exc,
    ):
        app = register_app()

    assert isinstance(app, FastAPI)
    assert app.router.lifespan_context is register_init
    m_log.assert_called_once_with()
    m_sock.assert_called_once_with(app)
    m_static.assert_called_once_with(app)
    m_mid.assert_called_once_with(app)
    m_route.assert_called_once_with(app)
    m_page.assert_called_once_with(app)
    m_exc.assert_called_once_with(app)


def test_register_logger_calls_setup() -> None:
    with (
        patch('backend.core.registrar.setup_logging') as su,
        patch('backend.core.registrar.set_custom_logfile') as sc,
    ):
        register_logger()
    su.assert_called_once_with()
    sc.assert_called_once_with()


def test_register_static_file_creates_upload_dir_and_mounts(tmp_path) -> None:
    static = tmp_path / 'static'
    upload = static / 'upload'
    app = FastAPI()
    with (
        patch('backend.core.registrar.UPLOAD_DIR', upload),
        patch('backend.core.registrar.STATIC_DIR', static),
        patch.object(settings, 'FASTAPI_STATIC_FILES', False),
    ):
        register_static_file(app)

    assert upload.is_dir()
    mounts = [r for r in app.routes if isinstance(r, Mount)]
    assert any(m.path == '/static/upload' for m in mounts)


def test_register_static_file_adds_core_static_when_enabled(tmp_path) -> None:
    static = tmp_path / 'static'
    upload = static / 'upload'
    upload.mkdir(parents=True)
    app = FastAPI()
    with (
        patch('backend.core.registrar.UPLOAD_DIR', upload),
        patch('backend.core.registrar.STATIC_DIR', static),
        patch.object(settings, 'FASTAPI_STATIC_FILES', True),
    ):
        register_static_file(app)

    mounts = [r for r in app.routes if isinstance(r, Mount)]
    paths = {m.path for m in mounts}
    assert '/static/upload' in paths
    assert '/static' in paths


def test_register_middleware_order_without_cors() -> None:
    app = FastAPI()
    with patch.object(settings, 'MIDDLEWARE_CORS', False):
        register_middleware(app)
    names = [m.cls.__name__ for m in app.user_middleware]
    assert names == [
        'ContextMiddleware',
        'AccessMiddleware',
        'I18nMiddleware',
        'AuthenticationMiddleware',
        'StateMiddleware',
        'OperaLogMiddleware',
    ]


def test_register_middleware_prepends_cors_when_enabled() -> None:
    app = FastAPI()
    with patch.object(settings, 'MIDDLEWARE_CORS', True):
        register_middleware(app)
    assert app.user_middleware[0].cls.__name__ == 'CORSMiddleware'


def test_register_router_demo_mode_sets_dependencies() -> None:
    router = APIRouter()
    app = FastAPI()
    with (
        patch('backend.core.registrar.build_final_router', return_value=router),
        patch('backend.core.registrar.ensure_unique_route_names') as eu,
        patch('backend.core.registrar.simplify_operation_ids') as so,
        patch.object(settings, 'DEMO_MODE', True),
        patch.object(app, 'include_router', wraps=app.include_router) as inc,
    ):
        register_router(app)

    eu.assert_called_once_with(app)
    so.assert_called_once_with(app)
    inc.assert_called_once()
    assert inc.call_args.kwargs.get('dependencies') is not None


def test_register_router_no_demo_mode_no_router_level_dependencies() -> None:
    router = APIRouter()
    app = FastAPI()
    with (
        patch('backend.core.registrar.build_final_router', return_value=router),
        patch('backend.core.registrar.ensure_unique_route_names'),
        patch('backend.core.registrar.simplify_operation_ids'),
        patch.object(settings, 'DEMO_MODE', False),
        patch.object(app, 'include_router', wraps=app.include_router) as inc,
    ):
        register_router(app)

    inc.assert_called_once()
    assert inc.call_args.kwargs.get('dependencies') is None


def test_register_page_calls_add_pagination() -> None:
    app = FastAPI()
    with patch('backend.core.registrar.add_pagination') as ap:
        register_page(app)
    ap.assert_called_once_with(app)


def test_register_socket_app_mounts_ws() -> None:
    app = FastAPI()
    fake_asgi = MagicMock()
    with (
        patch('backend.common.socketio.server.sio', MagicMock()),
        patch('backend.core.registrar.socketio.ASGIApp', return_value=fake_asgi),
    ):
        register_socket_app(app)

    mounts = [r for r in app.routes if isinstance(r, Mount)]
    assert any(m.path == '/ws' and m.app is fake_asgi for m in mounts)


@pytest.mark.asyncio
async def test_register_init_startup_and_shutdown() -> None:
    app = MagicMock()
    mock_task = MagicMock()

    def _consume_task(coro):
        if hasattr(coro, 'close'):
            coro.close()
        return mock_task

    with (
        patch('backend.core.registrar.create_tables', new_callable=AsyncMock) as ct,
        patch('backend.core.registrar.redis_client') as rc,
        patch('backend.core.registrar.FastAPILimiter') as lim,
        patch('backend.core.registrar.snowflake') as sf,
        patch('backend.core.registrar.create_task', side_effect=_consume_task) as ctask,
    ):
        rc.init = AsyncMock()
        rc.aclose = AsyncMock()
        lim.init = AsyncMock()
        sf.init = AsyncMock()
        sf.shutdown = AsyncMock()
        call_order: list[str] = []

        async def _redis_init() -> None:
            call_order.append('redis')

        async def _create_tables() -> None:
            call_order.append('create_tables')

        rc.init.side_effect = _redis_init
        ct.side_effect = _create_tables

        async with register_init(app):
            ct.assert_awaited_once()
            rc.init.assert_awaited_once()
            lim.init.assert_awaited_once()
            sf.init.assert_awaited_once()
            ctask.assert_called_once()
            assert call_order == ['redis', 'create_tables']

        sf.shutdown.assert_awaited_once()
        rc.aclose.assert_awaited_once()
