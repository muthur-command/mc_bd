from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.app.admin.schema.opera_log import DeleteOperaLogParam, GetOperaLogDetail
from backend.app.admin.service.opera_log_service import opera_log_service
from backend.common.i18n import t
from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()

# 操作日志「操作标题」与 i18n key 的映射（与 locale 中 api.summary 对应，覆盖所有接口 summary）
OPERA_LOG_TITLE_I18N_KEYS = {
    # 操作日志
    '分页获取操作日志': 'api.summary.opera_log_get_paginated',
    '批量删除操作日志': 'api.summary.opera_log_delete_batch',
    '清空操作日志': 'api.summary.opera_log_clear_all',
    # 登录日志
    '分页获取登录日志': 'api.summary.login_log_get_paginated',
    '批量删除登录日志': 'api.summary.login_log_delete_batch',
    '清空登录日志': 'api.summary.login_log_clear_all',
    # 用户
    '获取当前用户信息': 'api.summary.user_get_me',
    '获取当前用户偏好': 'api.summary.user_get_preferences',
    '保存当前用户偏好': 'api.summary.user_put_preferences',
    '获取用户信息': 'api.summary.user_get_by_pk',
    '获取用户所有角色': 'api.summary.user_get_roles',
    '分页获取所有用户': 'api.summary.user_get_paginated',
    '创建用户': 'api.summary.user_create',
    '更新用户信息': 'api.summary.user_update',
    '更新用户权限': 'api.summary.user_update_permissions',
    '更新当前用户密码': 'api.summary.user_update_my_password',
    '重置用户密码': 'api.summary.user_reset_password',
    '更新当前用户昵称': 'api.summary.user_update_nickname',
    '更新当前用户头像': 'api.summary.user_update_avatar',
    '更新当前用户邮箱': 'api.summary.user_update_email',
    '删除用户': 'api.summary.user_delete',
    # 角色
    '获取所有角色': 'api.summary.role_get_all',
    '获取角色详情': 'api.summary.role_get_detail',
    '分页获取所有角色': 'api.summary.role_get_paginated',
    '创建角色': 'api.summary.role_create',
    '更新角色': 'api.summary.role_update',
    '批量删除角色': 'api.summary.role_delete_batch',
    # 插件
    '获取所有插件': 'api.summary.plugin_get_all',
    '是否存在插件变更': 'api.summary.plugin_get_changed',
    '获取远程插件列表地址（单条，兼容）': 'api.summary.plugin_get_remote_url',
    '获取远程插件列表地址列表': 'api.summary.plugin_get_remote_urls',
    '设置远程插件列表地址（单条，兼容）': 'api.summary.plugin_put_remote_url',
    '设置远程插件列表地址列表': 'api.summary.plugin_put_remote_urls',
    '获取远程插件列表': 'api.summary.plugin_get_remote',
    '安装插件': 'api.summary.plugin_install',
    '卸载插件': 'api.summary.plugin_uninstall',
    '更新插件状态': 'api.summary.plugin_update_status',
    '下载插件': 'api.summary.plugin_download',
    # 系统监控
    'server 监控': 'api.summary.monitor_server',
    'redis 监控': 'api.summary.monitor_redis',
    # 卡片
    '获取卡片列表': 'api.summary.card_get_list',
    # Bento 布局
    '保存 Bento 布局': 'api.summary.bento_layout_save',
    '获取 Bento 布局': 'api.summary.bento_layout_get',
    '删除 Bento 布局': 'api.summary.bento_layout_delete',
    '列出已保存的布局': 'api.summary.bento_layout_list',
    # Apprise 通知
    '列出 Apprise 通知通道': 'api.summary.apprise_notify_channels_list',
    '获取 Apprise 通知通道详情': 'api.summary.apprise_notify_channel_get',
    '创建 Apprise 通知通道': 'api.summary.apprise_notify_channel_create',
    '更新 Apprise 通知通道': 'api.summary.apprise_notify_channel_update',
    '删除 Apprise 通知通道': 'api.summary.apprise_notify_channel_delete',
    '测试 Apprise 通知通道': 'api.summary.apprise_notify_channel_test',
    '向指定通道发送通知': 'api.summary.apprise_notify_send',
    '分页获取通知发送历史': 'api.summary.apprise_notify_logs_list',
    # OAuth2
    '获取用户已绑定的社交账号': 'api.summary.oauth2_get_bindings',
    '获取绑定授权链接': 'api.summary.oauth2_get_binding_url',
    '解绑用户社交账号': 'api.summary.oauth2_unbinding',
    '获取 google 授权链接': 'api.summary.oauth2_google_url',
    'google 授权自动重定向': 'api.summary.oauth2_google_redirect',
    '获取 Github 授权链接': 'api.summary.oauth2_github_url',
    'Github 授权自动重定向': 'api.summary.oauth2_github_redirect',
    # 邮件
    '发送电子邮件验证码': 'api.summary.email_send_captcha',
    # 任务
    '获取任务结果详情': 'api.summary.task_result_detail',
    '分页获取所有任务结果': 'api.summary.task_result_get_paginated',
    '批量删除任务结果': 'api.summary.task_result_delete_batch',
    '获取所有任务调度': 'api.summary.task_scheduler_get_all',
    '获取任务调度详情': 'api.summary.task_scheduler_detail',
    '分页获取所有任务调度': 'api.summary.task_scheduler_get_paginated',
    '创建任务调度': 'api.summary.task_scheduler_create',
    '更新任务调度': 'api.summary.task_scheduler_update',
    '更新任务调度状态': 'api.summary.task_scheduler_update_status',
    '删除任务调度': 'api.summary.task_scheduler_delete',
    '执行任务': 'api.summary.task_scheduler_run',
    '获取已注册的任务': 'api.summary.task_get_registered',
    '撤销任务': 'api.summary.task_revoke',
    # 文件
    '本地文件上传': 'api.summary.file_upload',
    # 在线用户
    '获取在线用户': 'api.summary.online_get',
    '强制下线': 'api.summary.online_force_logout',
    # 认证
    '用户登录': 'api.summary.auth_login',
    '用户登出': 'api.summary.auth_logout',
    '刷新 token': 'api.summary.auth_refresh_token',
    '获取所有授权码': 'api.summary.auth_get_codes',
    '获取登录验证码': 'api.summary.auth_captcha',
    'swagger 调试专用': 'api.summary.auth_swagger_login',
    'OAuth2 用户登录': 'api.summary.oauth2_login',
    'OAuth2 登录或绑定': 'api.summary.oauth2_login_or_bind',
}


@router.get(
    '',
    summary='分页获取操作日志',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_opera_logs_paginated(
    db: CurrentSession,
    username: Annotated[str | None, Query(description='用户名')] = None,
    status: Annotated[int | None, Query(description='状态')] = None,
    ip: Annotated[str | None, Query(description='IP 地址')] = None,
) -> ResponseSchemaModel[PageData[GetOperaLogDetail]]:
    page_data = await opera_log_service.get_list(db=db, username=username, status=status, ip=ip)
    # 按当前请求语言填充 title_display，供前端国际化展示
    items = []
    for row in page_data['items']:
        detail = GetOperaLogDetail.model_validate(row)
        i18n_key = OPERA_LOG_TITLE_I18N_KEYS.get(detail.title)
        # default=detail.title 避免翻译未加载或 key 缺失时把 key 字符串展示给前端
        detail.title_display = t(i18n_key, default=detail.title) if i18n_key else detail.title
        items.append(detail)
    page_data['items'] = items
    return response_base.success(data=page_data)


@router.delete(
    '',
    summary='批量删除操作日志',
    dependencies=[
        Depends(RequestPermission('log:opera:del')),
        DependsRBAC,
    ],
)
async def delete_opera_logs(db: CurrentSessionTransaction, obj: DeleteOperaLogParam) -> ResponseModel:
    count = await opera_log_service.delete(db=db, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '/all',
    summary='清空操作日志',
    dependencies=[
        Depends(RequestPermission('log:opera:clear')),
        DependsRBAC,
    ],
)
async def delete_all_opera_logs(db: CurrentSessionTransaction) -> ResponseModel:
    await opera_log_service.delete_all(db=db)
    return response_base.success()
