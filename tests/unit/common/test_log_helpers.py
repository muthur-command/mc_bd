"""backend.common.log — 格式化与拦截器（不调用 setup_logging 以免污染全局）。"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from backend.common.log import InterceptHandler, default_formatter, request_id_filter


def test_intercept_handler_emit_forwards_to_loguru() -> None:
    handler = InterceptHandler()
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
    with patch("backend.common.log.logger") as loguru:
        lvl = MagicMock()
        lvl.name = "INFO"
        loguru.level.return_value = lvl
        opt = MagicMock()
        loguru.opt.return_value = opt
        handler.emit(record)
        loguru.opt.assert_called_once()
        opt.log.assert_called_once()


def test_default_formatter_collapses_sqlalchemy_message() -> None:
    rec: dict = {"name": "sqlalchemy.engine.Engine", "message": "SELECT  \n\t1  \n  FROM t"}
    with patch("backend.common.log.settings") as s:
        s.LOG_FORMAT = "{message}\n"
        default_formatter(rec)
    assert rec["message"] == "SELECT 1 FROM t"


def test_default_formatter_appends_newline_when_missing() -> None:
    rec: dict = {"name": "app", "message": "x", "extra": {}}
    with patch("backend.common.log.settings") as s:
        s.LOG_FORMAT = "{message}"
        out = default_formatter(rec)
    assert out.endswith("\n")


def test_request_id_filter_truncates_trace() -> None:
    rec: dict = {}
    with patch("backend.common.log.get_request_trace_id", return_value="abcdefgh"):
        with patch("backend.common.log.settings") as s:
            s.TRACE_ID_LOG_LENGTH = 4
            request_id_filter(rec)
    assert rec["request_id"] == "abcd"
