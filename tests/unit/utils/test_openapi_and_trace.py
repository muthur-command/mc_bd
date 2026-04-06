"""utils.openapi、utils.trace_id。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from backend.core.conf import settings
from backend.utils.openapi import ensure_unique_route_names, simplify_operation_ids
from backend.utils.trace_id import get_request_trace_id


def test_simplify_operation_ids_matches_route_name() -> None:
    app = FastAPI()

    @app.get("/x", name="named_route")
    async def _x() -> dict:
        return {}

    simplify_operation_ids(app)
    routes = [r for r in app.routes if isinstance(r, APIRoute)]
    assert len(routes) == 1
    assert routes[0].operation_id == "named_route"


def test_ensure_unique_route_names_raises_on_duplicate() -> None:
    app = FastAPI()

    @app.get("/a", name="dup")
    async def _a() -> dict:
        return {}

    @app.get("/b", name="dup")
    async def _b() -> dict:
        return {}

    with pytest.raises(ValueError, match="Non-unique route name"):
        ensure_unique_route_names(app)


def test_get_request_trace_id_without_context() -> None:
    # 显式 new=MagicMock()，避免 patch 用真实 ctx 做 spec 时触发 starlette_context
    mock_ctx = MagicMock()
    mock_ctx.exists.return_value = False
    with patch("backend.utils.trace_id.ctx", new=mock_ctx):
        assert get_request_trace_id() == settings.TRACE_ID_LOG_DEFAULT_VALUE


def test_get_request_trace_id_from_context() -> None:
    mock_ctx = MagicMock()
    mock_ctx.exists.return_value = True
    mock_ctx.get.return_value = "trace-xyz"
    with patch("backend.utils.trace_id.ctx", new=mock_ctx):
        assert get_request_trace_id() == "trace-xyz"
        mock_ctx.get.assert_called_once()
