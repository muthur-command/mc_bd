"""Admin 系统用户路由（JWT + 超级管理员 + RBAC 删除）。"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from backend.common.enums import StatusType, UserPermissionType
from backend.core.conf import settings
from tests.helpers.admin_test_user import default_admin_jwt_user

_BASE = f"{settings.FASTAPI_API_V1_PATH}/sys/users"


def _page_empty() -> dict:
    return {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 20,
        "total_pages": 0,
        "links": {"first": "", "last": "", "self": "", "next": None, "prev": None},
    }


def test_get_me_returns_current_user(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    r = admin_client.get(f"{_BASE}/me", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("code") == 200
    data = body.get("data") or {}
    assert data.get("username") == "pytest_admin"
    assert data.get("roles") == ["pytest_role"]


def test_get_my_preferences(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    pref = {"locale": "zh", "theme": "dark"}
    with patch(
        "backend.app.admin.api.v1.sys.user.user_preference_service.get_preferences",
        new_callable=AsyncMock,
        return_value=pref,
    ) as m:
        r = admin_client.get(f"{_BASE}/me/preferences", headers=auth_headers)
        assert r.status_code == 200
        data = r.json().get("data") or {}
        assert data.get("locale") == "zh" and data.get("theme") == "dark"
        m.assert_awaited_once()


def test_save_my_preferences(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_preference_service.save_preferences",
        new_callable=AsyncMock,
        return_value={"locale": "en", "theme": "light"},
    ) as m:
        r = admin_client.put(
            f"{_BASE}/me/preferences",
            headers=auth_headers,
            json={"locale": "en", "theme": "light"},
        )
        assert r.status_code == 200
        data = r.json().get("data") or {}
        assert data.get("locale") == "en" and data.get("theme") == "light"
        m.assert_awaited_once()


def test_get_userinfo(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    u = default_admin_jwt_user()
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.get_userinfo",
        new_callable=AsyncMock,
        return_value=u,
    ) as m:
        r = admin_client.get(f"{_BASE}/2", headers=auth_headers)
        assert r.status_code == 200
        assert (r.json().get("data") or {}).get("id") == 1
        m.assert_awaited_once()


def test_get_user_roles(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    roles = [
        SimpleNamespace(
            id=1,
            name="r1",
            status=StatusType.enable,
            remark=None,
            created_time=datetime(2026, 1, 1, 12, 0, 0),
            updated_time=None,
        )
    ]
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.get_roles",
        new_callable=AsyncMock,
        return_value=roles,
    ) as m:
        r = admin_client.get(f"{_BASE}/2/roles", headers=auth_headers)
        assert r.status_code == 200
        data = r.json().get("data") or []
        assert len(data) == 1
        assert data[0].get("name") == "r1"
        m.assert_awaited_once()


def test_get_users_paginated(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    page = _page_empty()
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.get_list",
        new_callable=AsyncMock,
        return_value=page,
    ) as m:
        r = admin_client.get(
            f"{_BASE}",
            headers=auth_headers,
            params={"page": 1, "size": 20, "username": "a"},
        )
        assert r.status_code == 200
        assert r.json().get("code") == 200
        m.assert_awaited_once()


def test_create_user(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    created = default_admin_jwt_user()
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.create",
        new_callable=AsyncMock,
    ) as c:
        with patch(
            "backend.app.admin.api.v1.sys.user.user_service.get_userinfo",
            new_callable=AsyncMock,
            return_value=created,
        ) as g:
            r = admin_client.post(
                f"{_BASE}",
                headers=auth_headers,
                json={
                    "username": "newu",
                    "password": "secret12",
                    "roles": [1],
                },
            )
            assert r.status_code == 200, r.text
            assert (r.json().get("data") or {}).get("username") == "pytest_admin"
            c.assert_awaited_once()
            g.assert_awaited()


def test_update_user_success(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.update",
        new_callable=AsyncMock,
        return_value=1,
    ) as m:
        r = admin_client.put(
            f"{_BASE}/3",
            headers=auth_headers,
            json={
                "username": "u",
                "nickname": "n",
                "avatar": None,
                "email": None,
                "phone": None,
                "roles": [1],
            },
        )
        assert r.status_code == 200
        assert r.json().get("code") == 200
        m.assert_awaited_once()


def test_update_user_no_rows_returns_fail(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.update",
        new_callable=AsyncMock,
        return_value=0,
    ):
        r = admin_client.put(
            f"{_BASE}/3",
            headers=auth_headers,
            json={
                "username": "u",
                "nickname": "n",
                "avatar": None,
                "email": None,
                "phone": None,
                "roles": [1],
            },
        )
        assert r.status_code == 200
        assert r.json().get("code") != 200


def test_update_user_permission(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.update_permission",
        new_callable=AsyncMock,
        return_value=1,
    ) as m:
        r = admin_client.put(
            f"{_BASE}/4/permissions",
            headers=auth_headers,
            params={"type": UserPermissionType.staff.value},
        )
        assert r.status_code == 200
        assert r.json().get("code") == 200
        m.assert_awaited_once()


def test_update_me_password(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.update_password",
        new_callable=AsyncMock,
        return_value=1,
    ) as m:
        r = admin_client.put(
            f"{_BASE}/me/password",
            headers=auth_headers,
            json={"old_password": "a", "new_password": "b", "confirm_password": "b"},
        )
        assert r.status_code == 200
        assert r.json().get("code") == 200
        m.assert_awaited_once()


def test_reset_user_password(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.reset_password",
        new_callable=AsyncMock,
        return_value=1,
    ) as m:
        r = admin_client.put(
            f"{_BASE}/5/password",
            headers=auth_headers,
            json={"password": "new-secret"},
        )
        assert r.status_code == 200
        assert r.json().get("code") == 200
        m.assert_awaited_once()


def test_update_me_nickname(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.update_nickname",
        new_callable=AsyncMock,
        return_value=1,
    ) as m:
        r = admin_client.put(
            f"{_BASE}/me/nickname",
            headers=auth_headers,
            json={"nickname": "nn"},
        )
        assert r.status_code == 200
        m.assert_awaited_once()


def test_update_me_avatar_with_url(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.update_avatar",
        new_callable=AsyncMock,
        return_value=(1, "https://example.com/a.png"),
    ):
        r = admin_client.put(
            f"{_BASE}/me/avatar",
            headers=auth_headers,
            json={"avatar": "https://example.com/in.png"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("code") == 200
        assert (body.get("data") or {}).get("avatar") == "https://example.com/a.png"


def test_update_me_email(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.update_email",
        new_callable=AsyncMock,
        return_value=1,
    ) as m:
        r = admin_client.put(
            f"{_BASE}/me/email",
            headers=auth_headers,
            json={"captcha": "123456", "email": "u@example.com"},
        )
        assert r.status_code == 200
        m.assert_awaited_once()


def test_delete_user(admin_client: TestClient, auth_headers: dict[str, str]) -> None:
    with patch(
        "backend.app.admin.api.v1.sys.user.user_service.delete",
        new_callable=AsyncMock,
        return_value=1,
    ) as m:
        r = admin_client.delete(f"{_BASE}/6", headers=auth_headers)
        assert r.status_code == 200
        assert r.json().get("code") == 200
        m.assert_awaited_once()
