"""backend.common.security.permission / rbac — 依赖可调用体与分支。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.common.exception import errors
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import rbac_verify


@pytest.mark.asyncio
async def test_request_permission_sets_ctx_when_rbac_menu_mode() -> None:
    perm = RequestPermission('sys:test:perm')
    req = MagicMock()
    fake_ctx = SimpleNamespace(permission=None)
    with patch('backend.common.security.permission.settings') as s:
        s.RBAC_ROLE_MENU_MODE = True
        with patch('backend.common.security.permission.ctx', fake_ctx):
            await perm(req)
            assert fake_ctx.permission == 'sys:test:perm'


@pytest.mark.asyncio
async def test_request_permission_non_str_raises_server_error() -> None:
    p = object.__new__(RequestPermission)
    p.value = 123  # type: ignore[assignment]
    with patch('backend.common.security.permission.settings') as s:
        s.RBAC_ROLE_MENU_MODE = True
        with pytest.raises(errors.ServerError):
            await p(MagicMock())


@pytest.mark.asyncio
async def test_rbac_verify_skips_excluded_path() -> None:
    req = MagicMock()
    req.url.path = '/api/v1/auth/login'
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = ('/api/v1/auth/login',)
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        await rbac_verify(req, _token='x')


@pytest.mark.asyncio
async def test_rbac_verify_raises_without_auth_scopes() -> None:
    req = MagicMock()
    req.url.path = '/api/v1/sys/users'
    req.auth = MagicMock(scopes=[])
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = []
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        with pytest.raises(errors.TokenError):
            await rbac_verify(req, _token='t')


@pytest.mark.asyncio
async def test_rbac_verify_superuser_short_circuit() -> None:
    req = MagicMock()
    req.url.path = '/api/v1/x'
    req.auth = MagicMock(scopes=['authenticated'])
    req.user = MagicMock(is_superuser=True)
    req.method = 'DELETE'
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = []
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        s.RBAC_ROLE_MENU_MODE = True
        await rbac_verify(req, _token='t')


@pytest.mark.asyncio
async def test_rbac_verify_no_roles_raises() -> None:
    req = MagicMock()
    req.url.path = '/api/v1/x'
    req.auth = MagicMock(scopes=['x'])
    req.user = MagicMock(is_superuser=False, roles=[])
    req.method = 'GET'
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = []
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        with pytest.raises(errors.AuthorizationError):
            await rbac_verify(req, _token='t')


@pytest.mark.asyncio
async def test_rbac_verify_non_get_without_staff_raises() -> None:
    role = MagicMock()
    role.status = 1
    req = MagicMock()
    req.url.path = '/api/v1/x'
    req.auth = MagicMock(scopes=['x'])
    req.user = MagicMock(is_superuser=False, roles=[role], is_staff=False)
    req.method = 'POST'
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = []
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        with pytest.raises(errors.AuthorizationError) as ei:
            await rbac_verify(req, _token='t')
        assert 'backend_forbidden' in str(ei.value.msg)


@pytest.mark.asyncio
async def test_rbac_verify_menu_mode_returns_when_no_ctx_permission() -> None:
    role = MagicMock()
    role.status = 1
    req = MagicMock()
    req.url.path = '/api/v1/x'
    req.auth = MagicMock(scopes=['x'])
    req.user = MagicMock(is_superuser=False, roles=[role], is_staff=True)
    req.method = 'GET'
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = []
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        s.RBAC_ROLE_MENU_MODE = True
        s.RBAC_ROLE_MENU_EXCLUDE = []
        with patch('backend.common.security.rbac.ctx', SimpleNamespace(permission=None)):
            await rbac_verify(req, _token='t')


@pytest.mark.asyncio
async def test_rbac_verify_casbin_missing_raises_server_error() -> None:
    role = MagicMock()
    role.status = 1
    req = MagicMock()
    req.url.path = '/api/v1/x'
    req.auth = MagicMock(scopes=['x'])
    req.user = MagicMock(is_superuser=False, roles=[role], is_staff=True)
    req.method = 'GET'
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = []
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        s.RBAC_ROLE_MENU_MODE = False
        with patch(
            'backend.common.security.rbac.import_module_cached',
            side_effect=ImportError('no casbin'),
        ):
            with pytest.raises(errors.ServerError):
                await rbac_verify(req, _token='t')


@pytest.mark.asyncio
async def test_rbac_verify_casbin_invoked() -> None:
    role = MagicMock()
    role.status = 1
    req = MagicMock()
    req.url.path = '/api/v1/x'
    req.auth = MagicMock(scopes=['x'])
    req.user = MagicMock(is_superuser=False, roles=[role], is_staff=True)
    req.method = 'GET'
    cas = MagicMock()
    cas.casbin_verify = AsyncMock()
    with patch('backend.common.security.rbac.settings') as s:
        s.TOKEN_REQUEST_PATH_EXCLUDE = []
        s.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN = []
        s.RBAC_ROLE_MENU_MODE = False
        with patch(
            'backend.common.security.rbac.import_module_cached',
            return_value=cas,
        ):
            await rbac_verify(req, _token='t')
    cas.casbin_verify.assert_awaited_once_with(req)
