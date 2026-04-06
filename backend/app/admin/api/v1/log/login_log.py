from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.app.admin.schema.login_log import DeleteLoginLogParam, GetLoginLogDetail
from backend.app.admin.service.login_log_service import login_log_service
from backend.common.i18n import t
from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()

# 登录日志 msg 可能存 i18n key（如 error.xxx）或已翻译文案（如「登录成功」）。
# 此处列出「已翻译文案 -> key」，便于按当前语言展示。
LOGIN_LOG_MSG_TO_I18N_KEY = {
    # 登录成功
    '登录成功': 'success.login.success',
    'Login success': 'success.login.success',
    '登录成功（OAuth2）': 'success.login.oauth2_success',
    'Login success (OAuth2)': 'success.login.oauth2_success',
    # 验证码（auth 中部分用 t() 传入，存的是译文）
    '验证码错误': 'error.captcha.error',
    'Captcha error': 'error.captcha.error',
    '验证码无效，请重新获取': 'error.captcha.invalid',
    'Captcha is invalid, please try again': 'error.captcha.invalid',
    '验证码已过期，请重新获取': 'error.captcha.expired',
    'Captcha has expired, please try again': 'error.captcha.expired',
    # 用户名/密码等（若某处用 t() 写入日志则能识别）
    '用户名或密码有误': 'error.username_or_password_wrong',
    'Incorrect username or password': 'error.username_or_password_wrong',
    '用户名不存在': 'error.username_not_found',
    'Username does not exist': 'error.username_not_found',
    '用户不存在': 'error.user_not_found',
    'User not found': 'error.user_not_found',
    '用户已被锁定，请联系系统管理员': 'error.user_locked_contact_admin',
    'User is locked, please contact administrator': 'error.user_locked_contact_admin',
    '此用户已在异地登录，请重新登录并及时修改密码': 'error.user_remote_login',
    'This account has been logged in elsewhere, please login again and change password': 'error.user_remote_login',
    'Refresh Token 已过期，请重新登录': 'error.refresh_token_expired',
    'Refresh token has expired, please login again': 'error.refresh_token_expired',
    'Token 无效': 'error.token_invalid',
    'Invalid token': 'error.token_invalid',
    'Token 已过期': 'error.token_expired',
    'Token has expired': 'error.token_expired',
    '验证码已失效，请重新获取': 'error.captcha_expired',
}


def _login_log_msg_display(msg: str) -> str:
    """按当前请求语言返回登录日志消息的展示文案。"""
    if not msg:
        return msg or '—'
    key = LOGIN_LOG_MSG_TO_I18N_KEY.get(msg)
    if key:
        return t(key, default=msg)
    # 可能本身就是 i18n key（如 error.username_or_password_wrong）
    return t(msg, default=msg)


@router.get(
    '',
    summary='分页获取登录日志',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_login_logs_paginated(
    db: CurrentSession,
    username: Annotated[str | None, Query(description='用户名')] = None,
    status: Annotated[int | None, Query(description='状态')] = None,
    ip: Annotated[str | None, Query(description='IP 地址')] = None,
) -> ResponseSchemaModel[PageData[GetLoginLogDetail]]:
    page_data = await login_log_service.get_list(db=db, username=username, status=status, ip=ip)
    items = []
    for row in page_data['items']:
        detail = GetLoginLogDetail.model_validate(row)
        detail.msg_display = _login_log_msg_display(detail.msg)
        items.append(detail)
    page_data['items'] = items
    return response_base.success(data=page_data)


@router.delete(
    '',
    summary='批量删除登录日志',
    dependencies=[
        Depends(RequestPermission('log:login:del')),
        DependsRBAC,
    ],
)
async def delete_login_logs(db: CurrentSessionTransaction, obj: DeleteLoginLogParam) -> ResponseModel:
    count = await login_log_service.delete(db=db, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '/all',
    summary='清空登录日志',
    dependencies=[
        Depends(RequestPermission('log:login:clear')),
        DependsRBAC,
    ],
)
async def delete_all_login_logs(db: CurrentSessionTransaction) -> ResponseModel:
    await login_log_service.delete_all(db=db)
    return response_base.success()
