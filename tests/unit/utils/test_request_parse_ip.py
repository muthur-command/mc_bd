"""utils.request_parse：get_request_ip。"""

from unittest.mock import MagicMock

from backend.utils.request_parse import get_request_ip


def test_get_request_ip_prefers_x_real_ip() -> None:
    req = MagicMock()
    req.headers.get = lambda k, d=None: {'X-Real-IP': '10.0.0.1'}.get(k, d)
    assert get_request_ip(req) == '10.0.0.1'


def test_get_request_ip_x_forwarded_for_first() -> None:
    req = MagicMock()
    req.headers.get = lambda k, d=None: {'X-Forwarded-For': '192.168.1.2, 10.0.0.1'}.get(k, d)
    assert get_request_ip(req) == '192.168.1.2'


def test_get_request_ip_testclient_host() -> None:
    req = MagicMock()
    req.headers.get = MagicMock(return_value=None)
    req.client.host = 'testclient'
    assert get_request_ip(req) == '127.0.0.1'
