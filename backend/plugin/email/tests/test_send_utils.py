"""`backend.plugin.email.utils.send`：渲染与 SMTP 发送（全部 mock 外部 IO）。"""

from __future__ import annotations

import base64
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.plugin.email.utils.send import render_message, send_email


def _first_base64_mime_body(raw: bytes) -> str:
    m = re.search(rb"Content-Transfer-Encoding: base64\r?\n\r?\n([A-Za-z0-9+/=]+)", raw)
    assert m, raw
    return base64.b64decode(m.group(1)).decode("utf-8")


@pytest.mark.asyncio
async def test_render_message_plain_text() -> None:
    raw = await render_message("主题", "from@example.com", "正文一行", None)
    assert b"Subject" in raw
    assert b"=?utf-8?" in raw or "主题".encode("utf-8") in raw
    assert "正文一行" in _first_base64_mime_body(raw)


@pytest.mark.asyncio
async def test_render_message_html_template() -> None:
    class _FakeFile:
        async def read(self) -> str:
            return "<p>Code: {{ code }} / {{ expired }}</p>"

    class _AsyncCM:
        def __init__(self) -> None:
            self._f = _FakeFile()

        async def __aenter__(self) -> _FakeFile:
            return self._f

        async def __aexit__(self, *args: object) -> None:
            return None

    async def _open_file_mock(*args: object, **kwargs: object) -> _AsyncCM:
        return _AsyncCM()

    with patch("backend.plugin.email.utils.send.open_file", side_effect=_open_file_mock):
        raw = await render_message(
            "验证码",
            "noreply@example.com",
            {"code": "123456", "expired": 5},
            "captcha.html",
        )
    html = _first_base64_mime_body(raw)
    assert "123456" in html
    assert "5" in html


@pytest.mark.asyncio
async def test_send_email_loads_config_renders_and_sends() -> None:
    msg_bytes = b"fake-mime-bytes"

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.login = AsyncMock()
    mock_smtp_instance.sendmail = AsyncMock()
    mock_smtp_instance.__aenter__ = AsyncMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "backend.plugin.email.utils.send.load_email_config",
        new_callable=AsyncMock,
    ) as load_cfg:
        with patch(
            "backend.plugin.email.utils.send.render_message",
            new_callable=AsyncMock,
            return_value=msg_bytes,
        ) as render:
            with patch(
                "backend.plugin.email.utils.send.SMTP",
                return_value=mock_smtp_instance,
            ) as smtp_cls:
                db = AsyncMock()
                await send_email(db, "to@example.com", "Hi", "body", None)

    load_cfg.assert_awaited_once_with(db)
    render.assert_awaited_once()
    smtp_cls.assert_called_once()
    mock_smtp_instance.login.assert_awaited_once()
    mock_smtp_instance.sendmail.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_email_list_recipients_passed_to_sendmail() -> None:
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.login = AsyncMock()
    mock_smtp_instance.sendmail = AsyncMock()
    mock_smtp_instance.__aenter__ = AsyncMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.plugin.email.utils.send.load_email_config", new_callable=AsyncMock):
        with patch(
            "backend.plugin.email.utils.send.render_message",
            new_callable=AsyncMock,
            return_value=b"x",
        ):
            with patch("backend.plugin.email.utils.send.SMTP", return_value=mock_smtp_instance):
                db = AsyncMock()
                await send_email(db, ["a@x.com", "b@x.com"], "S", "plain", None)

    call = mock_smtp_instance.sendmail.await_args
    assert call is not None
    _from, recipients, _msg = call[0]
    assert recipients == ["a@x.com", "b@x.com"]


@pytest.mark.asyncio
async def test_send_email_logs_on_smtp_failure() -> None:
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__aenter__ = AsyncMock(side_effect=OSError("smtp down"))
    mock_smtp_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.plugin.email.utils.send.load_email_config", new_callable=AsyncMock):
        with patch(
            "backend.plugin.email.utils.send.render_message",
            new_callable=AsyncMock,
            return_value=b"x",
        ):
            with patch("backend.plugin.email.utils.send.SMTP", return_value=mock_smtp_instance):
                with patch("backend.plugin.email.utils.send.log") as log_mock:
                    db = AsyncMock()
                    await send_email(db, "t@x.com", "S", "b", None)

    log_mock.error.assert_called_once()
