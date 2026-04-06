"""backend.common.socketio — 连接逻辑与任务通知（Redis / jwt 打桩）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.common.socketio import actions as socketio_actions


@pytest.mark.asyncio
async def test_task_notification_emits_event() -> None:
    with patch("backend.common.socketio.actions.sio") as sio:
        sio.emit = AsyncMock()
        await socketio_actions.task_notification("done")
        sio.emit.assert_awaited_once_with("task_notification", {"msg": "done"})


@pytest.mark.asyncio
async def test_connect_rejects_without_auth() -> None:
    from backend.common.socketio import server as socketio_server

    ok = await socketio_server.connect("sid1", {}, None)
    assert ok is False


@pytest.mark.asyncio
async def test_connect_no_auth_marker_skips_jwt() -> None:
    from backend.common.socketio import server as socketio_server

    with patch("backend.common.socketio.server.settings") as s:
        s.WS_NO_AUTH_MARKER = "INSECURE"
        s.TOKEN_ONLINE_REDIS_PREFIX = "online:"
        with patch("backend.common.socketio.server.redis_client") as r:
            r.sadd = AsyncMock()
            out = await socketio_server.connect(
                "sid2",
                {},
                {"token": "INSECURE", "session_uuid": "su1"},
            )
            assert out is True
            r.sadd.assert_awaited()


@pytest.mark.asyncio
async def test_connect_jwt_success() -> None:
    from backend.common.socketio import server as socketio_server

    with patch("backend.common.socketio.server.jwt_authentication", new_callable=AsyncMock):
        with patch("backend.common.socketio.server.settings") as s:
            s.TOKEN_ONLINE_REDIS_PREFIX = "online:"
            with patch("backend.common.socketio.server.redis_client") as r:
                r.sadd = AsyncMock()
                ok = await socketio_server.connect(
                    "sid3",
                    {},
                    {"token": "real.jwt", "session_uuid": "su2"},
                )
                assert ok is True


@pytest.mark.asyncio
async def test_connect_jwt_failure_returns_false() -> None:
    from backend.common.socketio import server as socketio_server

    with patch(
        "backend.common.socketio.server.jwt_authentication",
        new_callable=AsyncMock,
        side_effect=RuntimeError("bad token"),
    ):
        ok = await socketio_server.connect(
            "sid4",
            {},
            {"token": "bad", "session_uuid": "su3"},
        )
        assert ok is False


@pytest.mark.asyncio
async def test_disconnect_calls_spop() -> None:
    from backend.common.socketio import server as socketio_server

    with patch("backend.common.socketio.server.settings") as s:
        s.TOKEN_ONLINE_REDIS_PREFIX = "online:"
        with patch("backend.common.socketio.server.redis_client") as r:
            r.spop = AsyncMock()
            await socketio_server.disconnect("sid5")
            r.spop.assert_awaited_once_with("online:")
