"""头像处理工具：将 base64 data URI 保存到文件系统并返回访问 URL"""

import base64
import re
import uuid
from pathlib import Path

from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.core.path_conf import UPLOAD_DIR
from backend.utils.timezone import timezone


# data URI 格式: data:image/png;base64,iVBORw0KGgo...
DATA_URI_PATTERN = re.compile(r'^data:image/(\w+);base64,(.+)$')
AVATAR_SUBDIR = 'avatar'
COVER_SUBDIR = 'cover'
UPLOAD_URL_PREFIX = '/static/upload/'
# base64 约 4/3 倍于二进制，5MB 图片 ≈ 6.67M 字符
AVATAR_BASE64_MAX_LENGTH = int(settings.UPLOAD_IMAGE_SIZE_MAX * 4 / 3) + 1024


def remove_upload_file_if_local(
    url: str | None,
    *,
    allowed_subdirs: tuple[str, ...] = (AVATAR_SUBDIR, COVER_SUBDIR),
) -> None:
    """
    若 URL 指向本地上传目录下的文件则删除该文件，避免重新上传后旧文件残留。

    :param url: 存储的访问 URL，如 /static/upload/avatar/xxx.png
    :param allowed_subdirs: 允许删除的子目录名（默认 avatar、cover），防止误删其他上传
    """
    if not url or not url.strip():
        return
    url = url.strip()
    if not url.startswith(UPLOAD_URL_PREFIX):
        return
    rel = url[len(UPLOAD_URL_PREFIX) :].lstrip('/')
    if not rel or '..' in rel:
        return
    parts = rel.split('/')
    if not parts or parts[0] not in allowed_subdirs:
        return
    file_path = UPLOAD_DIR / rel
    try:
        if file_path.is_file():
            file_path.unlink()
            log.debug(f'已删除旧上传文件: {file_path}')
    except OSError as e:
        log.warning(f'删除旧上传文件失败 {file_path}: {e!s}')


def save_avatar_from_data_uri(data_uri: str, user_id: int) -> str:
    """
    将 base64 data URI 头像保存到文件系统，返回可访问的 URL 路径。

    :param data_uri: data:image/png;base64,xxxx 格式的字符串
    :param user_id: 用户 ID，用于生成唯一文件名
    :return: 访问 URL，如 /static/upload/avatar/xxx.png
    """
    match = DATA_URI_PATTERN.match(data_uri.strip())
    if not match:
        raise errors.RequestError(msg='error.invalid_avatar_format')

    ext, b64_data = match.groups()
    ext = ext.lower()
    if ext not in settings.UPLOAD_IMAGE_EXT_INCLUDE:
        raise errors.RequestError(msg='error.avatar_format_not_supported')

    if len(b64_data) > AVATAR_BASE64_MAX_LENGTH:
        raise errors.RequestError(msg='error.avatar_size_exceeded')

    try:
        image_bytes = base64.b64decode(b64_data, validate=True)
    except Exception as e:
        log.warning(f'头像 base64 解码失败: {e!s}')
        raise errors.RequestError(msg='error.invalid_avatar_base64')

    if len(image_bytes) > settings.UPLOAD_IMAGE_SIZE_MAX:
        raise errors.RequestError(msg='error.avatar_size_exceeded')

    avatar_dir = UPLOAD_DIR / AVATAR_SUBDIR
    avatar_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(timezone.now().timestamp())
    filename = f'{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}'
    file_path = avatar_dir / filename

    try:
        file_path.write_bytes(image_bytes)
    except Exception as e:
        log.error(f'保存头像失败: {e!s}')
        raise errors.RequestError(msg='error.avatar_save_failed')

    return f'/static/upload/{AVATAR_SUBDIR}/{filename}'


def process_avatar_input(avatar: str | None, user_id: int) -> str | None:
    """
    处理头像输入：若是 data URI 则保存到文件并返回 URL，否则原样返回。

    :param avatar: 头像内容，可为 URL 或 data URI
    :param user_id: 用户 ID
    :return: 最终存储的 URL 或 None（空输入时返回 None 表示清除头像）
    """
    if not avatar or not avatar.strip():
        return None
    avatar = avatar.strip()
    if avatar.startswith('data:image/'):
        return save_avatar_from_data_uri(avatar, user_id)
    if len(avatar) > 5000:
        raise errors.RequestError(msg='error.avatar_url_too_long')
    return avatar


def save_cover_from_data_uri(data_uri: str, user_id: int) -> str:
    """
    将 base64 data URI 背景图保存到文件系统，返回可访问的 URL 路径。

    :param data_uri: data:image/png;base64,xxxx 格式的字符串
    :param user_id: 用户 ID，用于生成唯一文件名
    :return: 访问 URL，如 /static/upload/cover/xxx.png
    """
    match = DATA_URI_PATTERN.match(data_uri.strip())
    if not match:
        raise errors.RequestError(msg='error.invalid_avatar_format')

    ext, b64_data = match.groups()
    ext = ext.lower()
    if ext not in settings.UPLOAD_IMAGE_EXT_INCLUDE:
        raise errors.RequestError(msg='error.avatar_format_not_supported')

    if len(b64_data) > AVATAR_BASE64_MAX_LENGTH:
        raise errors.RequestError(msg='error.avatar_size_exceeded')

    try:
        image_bytes = base64.b64decode(b64_data, validate=True)
    except Exception as e:
        log.warning(f'背景图 base64 解码失败: {e!s}')
        raise errors.RequestError(msg='error.invalid_avatar_base64')

    if len(image_bytes) > settings.UPLOAD_IMAGE_SIZE_MAX:
        raise errors.RequestError(msg='error.avatar_size_exceeded')

    cover_dir = UPLOAD_DIR / COVER_SUBDIR
    cover_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(timezone.now().timestamp())
    filename = f'{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}'
    file_path = cover_dir / filename

    try:
        file_path.write_bytes(image_bytes)
    except Exception as e:
        log.error(f'保存背景图失败: {e!s}')
        raise errors.RequestError(msg='error.avatar_save_failed')

    return f'/static/upload/{COVER_SUBDIR}/{filename}'


def process_cover_input(cover: str | None, user_id: int) -> str | None:
    """
    处理背景图输入：若是 data URI 则保存到文件并返回 URL，否则原样返回。

    :param cover: 背景图内容，可为 URL 或 data URI
    :param user_id: 用户 ID
    :return: 最终存储的 URL 或 None（空输入时返回 None 表示清除）
    """
    if not cover or not cover.strip():
        return None
    cover = cover.strip()
    if cover.startswith('data:image/'):
        return save_cover_from_data_uri(cover, user_id)
    if len(cover) > 5000:
        raise errors.RequestError(msg='error.avatar_url_too_long')
    return cover
