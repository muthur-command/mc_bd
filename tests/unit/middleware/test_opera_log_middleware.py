"""OperaLogMiddleware：非 API 短路、脱敏与截断静态方法。"""

from unittest.mock import patch

from fastapi import FastAPI
from starlette.testclient import TestClient

from backend.core.conf import settings
from backend.middleware.opera_log_middleware import OperaLogMiddleware


def test_opera_log_middleware_skips_non_v1_paths() -> None:
    app = FastAPI()
    app.add_middleware(OperaLogMiddleware)

    @app.get("/health")
    async def _h() -> dict:
        return {"ok": True}

    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_desensitization_redacts_configured_keys() -> None:
    with patch.object(settings, "OPERA_LOG_REDACT_KEYS", ["password", "token"]):
        raw = {"password": "secret", "token": "t", "name": "u"}
        out = OperaLogMiddleware.desensitization(raw)
        assert out["password"] == "[REDACTED]"
        assert out["token"] == "[REDACTED]"
        assert out["name"] == "u"


def test_truncate_small_payload_unchanged() -> None:
    args = {"a": 1, "b": "hello"}
    assert OperaLogMiddleware.truncate(args) == args
