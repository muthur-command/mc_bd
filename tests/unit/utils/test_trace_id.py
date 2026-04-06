"""backend.utils.trace_id — get_request_trace_id。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from backend.utils.trace_id import get_request_trace_id


def test_trace_id_default_when_context_missing() -> None:
    fake = SimpleNamespace()
    fake.exists = lambda: False  # type: ignore[attr-defined]

    with patch('backend.utils.trace_id.settings') as s:
        s.TRACE_ID_LOG_DEFAULT_VALUE = 'no-trace'
        with patch('backend.utils.trace_id.ctx', fake):
            assert get_request_trace_id() == 'no-trace'


def test_trace_id_from_context_when_present() -> None:
    fake = SimpleNamespace()
    fake.exists = lambda: True  # type: ignore[attr-defined]
    fake.get = lambda k, d: 'req-abc'  # type: ignore[attr-defined, misc]

    with patch('backend.utils.trace_id.settings') as s:
        s.TRACE_ID_REQUEST_HEADER_KEY = 'X-Request-ID'
        s.TRACE_ID_LOG_DEFAULT_VALUE = 'fallback-id'
        with patch('backend.utils.trace_id.ctx', fake):
            assert get_request_trace_id() == 'req-abc'
