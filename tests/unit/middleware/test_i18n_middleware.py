"""I18nMiddleware 与 get_current_language。"""

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from starlette.testclient import TestClient

from backend.core.conf import settings
from backend.middleware.i18n_middleware import I18nMiddleware, get_current_language


def test_get_current_language_empty_header_uses_default() -> None:
    req = MagicMock()
    req.headers.get = MagicMock(return_value="")
    assert get_current_language(req) == settings.I18N_DEFAULT_LANGUAGE


def test_get_current_language_zh_mapping() -> None:
    req = MagicMock()
    req.headers.get = MagicMock(return_value="zh-CN,zh;q=0.9")
    assert get_current_language(req) == "zh-CN"


def test_get_current_language_en_mapping() -> None:
    req = MagicMock()
    req.headers.get = MagicMock(return_value="en-US,en;q=0.8")
    assert get_current_language(req) == "en-US"


def test_get_current_language_unknown_falls_back_to_raw_lower() -> None:
    req = MagicMock()
    req.headers.get = MagicMock(return_value="fr-FR")
    assert get_current_language(req) == "fr-fr"


def test_i18n_middleware_sets_current_language() -> None:
    app = FastAPI()
    app.add_middleware(I18nMiddleware)

    @app.get("/x")
    async def _x() -> dict:
        return {"ok": True}

    with patch("backend.middleware.i18n_middleware.i18n") as mock_i18n:
        mock_i18n.current_language = "en-US"
        client = TestClient(app)
        client.get("/x", headers={"Accept-Language": "zh-CN"})
        assert mock_i18n.current_language == "zh-CN"
