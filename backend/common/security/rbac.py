from fastapi import Depends, Request

from backend.common.context import ctx
from backend.common.enums import MethodType
from backend.common.exception import errors
from backend.common.log import log
from backend.common.security.jwt import DependsJwtAuth
from backend.core.conf import settings
from backend.utils.dynamic_import import import_module_cached


async def rbac_verify(request: Request, _token: str = DependsJwtAuth) -> None:  # noqa: C901
    """
    RBAC 权限校验（鉴权顺序很重要，谨慎修改）

    :param request: FastAPI 请求对象
    :param _token: JWT 令牌
    :return:
    """
    path = request.url.path

    # API 鉴权白名单
    if path in settings.TOKEN_REQUEST_PATH_EXCLUDE:
        return
    for pattern in settings.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN:
        if pattern.match(path):
            return

    # JWT 授权状态强制校验
    if not request.auth.scopes:
        raise errors.TokenError

    # 超级管理员免校验
    if request.user.is_superuser:
        return

    # 检测用户角色
    user_roles = request.user.roles
    if not user_roles or all(status == 0 for status in user_roles):
        raise errors.AuthorizationError(msg='error.user_no_role')

    # 检测后台管理操作权限
    method = request.method
    if (method != MethodType.GET or method != MethodType.OPTIONS) and not request.user.is_staff:
        raise errors.AuthorizationError(msg='error.user_backend_forbidden')

    # RBAC 鉴权（无菜单时仅校验 is_staff，不校验菜单权限）
    if settings.RBAC_ROLE_MENU_MODE:
        path_auth_perm = ctx.permission
        if not path_auth_perm:
            return
        if path_auth_perm in settings.RBAC_ROLE_MENU_EXCLUDE:
            return
        # 无菜单模块时，仅依赖 is_staff，已在上方校验
        return
    else:
        try:
            casbin_rbac = import_module_cached('backend.plugin.casbin_rbac.rbac')
            casbin_verify = casbin_rbac.casbin_verify
        except (ImportError, AttributeError) as e:
            log.error(f'正在通过 casbin 执行 RBAC 权限校验，但此插件不存在: {e}')
            raise errors.ServerError(msg='error.permission_check_failed')

        await casbin_verify(request)


# RBAC 授权依赖注入
DependsRBAC = Depends(rbac_verify)
