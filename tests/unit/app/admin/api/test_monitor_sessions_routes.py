"""Admin 会话监控：在线列表、强制下线。"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.core.conf import settings

_SESSIONS = f"{settings.FASTAPI_API_V1_PATH}/monitors/sessions"


def test_get_sessions_empty_redis(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.monitor.online.redis_client.get_prefix",
        new_callable=AsyncMock,
        return_value=[],
    ) as gp:
        with patch(
            "backend.app.admin.api.v1.monitor.online.redis_client.smembers",
            new_callable=AsyncMock,
            return_value=set(),
        ):
            r = admin_client.get(_SESSIONS, headers=auth_headers)
            assert r.status_code == 200, r.text
            assert r.json().get("code") == 200
            assert r.json().get("data") == []
            gp.assert_awaited_once()


def test_get_sessions_one_token_without_extra(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    exp = datetime(2030, 1, 1, 0, 0, 0)
    payload = SimpleNamespace(id=9, session_uuid="sess-uuid-1", expire_time=exp)
    with patch(
        "backend.app.admin.api.v1.monitor.online.redis_client.get_prefix",
        new_callable=AsyncMock,
        return_value=["tok:key1"],
    ):
        with patch(
            "backend.app.admin.api.v1.monitor.online.redis_client.smembers",
            new_callable=AsyncMock,
            return_value=set(),
        ):
            with patch(
                "backend.app.admin.api.v1.monitor.online.redis_client.get",
                new_callable=AsyncMock,
                side_effect=["jwt-string", None],
            ):
                with patch(
                    "backend.app.admin.api.v1.monitor.online.jwt_decode",
                    return_value=payload,
                ):
                    r = admin_client.get(_SESSIONS, headers=auth_headers)
                    assert r.status_code == 200, r.text
                    data = r.json().get("data") or []
                    assert len(data) == 1
                    row = data[0]
                    assert row["id"] == 9
                    assert row["session_uuid"] == "sess-uuid-1"
                    assert row["username"] == "未知"


def test_get_sessions_filters_by_username_query(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    exp = datetime(2030, 1, 1, 0, 0, 0)
    payload = SimpleNamespace(id=3, session_uuid="s2", expire_time=exp)
    extra = '{"username": "alice", "swagger": null}'
    with patch(
        "backend.app.admin.api.v1.monitor.online.redis_client.get_prefix",
        new_callable=AsyncMock,
        return_value=["k1"],
    ):
        with patch(
            "backend.app.admin.api.v1.monitor.online.redis_client.smembers",
            new_callable=AsyncMock,
            return_value={"s2"},
        ):
            with patch(
                "backend.app.admin.api.v1.monitor.online.redis_client.get",
                new_callable=AsyncMock,
                side_effect=["token", extra],
            ):
                with patch(
                    "backend.app.admin.api.v1.monitor.online.jwt_decode",
                    return_value=payload,
                ):
                    r = admin_client.get(_SESSIONS, headers=auth_headers, params={"username": "alice"})
                    assert r.status_code == 200
                    data = r.json().get("data") or []
                    assert len(data) == 1
                    assert data[0]["username"] == "alice"


def test_delete_session_calls_revoke(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.monitor.online.revoke_token",
        new_callable=AsyncMock,
    ) as rv:
        r = admin_client.delete(
            f"{_SESSIONS}/7",
            headers=auth_headers,
            params={"session_uuid": "su-1"},
        )
        assert r.status_code == 200
        assert r.json().get("code") == 200
        rv.assert_awaited_once_with(7, "su-1")
