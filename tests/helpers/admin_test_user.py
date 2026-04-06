"""Admin API 单测用：与 `JwtAuthMiddleware` 配合的固定 `GetUserInfoWithRelationDetail`。"""

from __future__ import annotations

from datetime import datetime

from backend.app.admin.schema.role import GetRoleDetail
from backend.app.admin.schema.user import GetUserInfoWithRelationDetail
from backend.common.enums import StatusType


def default_admin_jwt_user() -> GetUserInfoWithRelationDetail:
    """超级管理员桩，满足 `DependsSuperUser` 与 `rbac_verify` 早退分支。"""
    now = datetime(2026, 1, 1, 12, 0, 0)
    role = GetRoleDetail(
        id=1,
        name='pytest_role',
        status=StatusType.enable,
        remark=None,
        created_time=now,
        updated_time=None,
    )
    return GetUserInfoWithRelationDetail(
        id=1,
        uuid='00000000-0000-4000-8000-000000000001',
        username='pytest_admin',
        nickname='pytest',
        avatar=None,
        email=None,
        phone=None,
        status=StatusType.enable,
        is_superuser=True,
        is_staff=True,
        is_multi_login=True,
        join_time=now,
        last_login_time=None,
        roles=[role],
    )
