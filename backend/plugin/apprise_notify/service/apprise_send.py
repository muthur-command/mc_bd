"""Apprise 发送与 URL 脱敏"""

from __future__ import annotations

import apprise


def mask_apprise_url(url: str) -> str:
    """列表展示用：隐藏 userinfo 中的敏感信息"""
    if not url:
        return ''
    if '://' not in url:
        return url[:48] + ('…' if len(url) > 48 else '')
    scheme, rest = url.split('://', 1)
    if '@' in rest:
        _userinfo, hostpath = rest.rsplit('@', 1)
        return f'{scheme}://***@{hostpath}'
    return url if len(url) <= 96 else url[:96] + '…'


def send_apprise(url: str, title: str, body: str) -> tuple[bool, str | None]:
    """
    使用 Apprise 发送一条通知。

    :return: (是否成功, 失败时简短原因，供日志；成功为 None)
    """
    obj = apprise.Apprise()
    if not obj.add(url):
        return False, 'invalid_apprise_url'
    try:
        ok = obj.notify(title=title or None, body=body or '')
    except Exception as exc:
        return False, str(exc)[:2000]
    if not ok:
        return False, 'notify_rejected'
    return True, None
