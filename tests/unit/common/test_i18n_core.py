"""backend.common.i18n — 翻译键解析（使用不调用 `load_locales` 的子类实例）。"""

from __future__ import annotations

from backend.common.i18n import I18n


class _FixedLangI18n(I18n):
    """测试专用：固定 `current_language`，避免依赖 starlette_context。"""

    def __init__(self, lang: str, locales: dict) -> None:
        self._test_lang = lang
        self.locales = locales

    @property
    def current_language(self) -> str:  # type: ignore[override]
        return self._test_lang

    @current_language.setter
    def current_language(self, language: str) -> None:  # type: ignore[override]
        self._test_lang = language


def test_t_nested_key() -> None:
    i = _FixedLangI18n(
        'en',
        {'en': {'response': {'success': 'OK'}}},
    )
    assert i.t('response.success') == 'OK'


def test_t_format_kwargs() -> None:
    i = _FixedLangI18n('en', {'en': {'greet': 'Hi {name}'}})
    assert i.t('greet', name='Ada') == 'Hi Ada'


def test_t_returns_default_when_resolved_empty_string() -> None:
    i = _FixedLangI18n('en', {'en': {'empty': ''}})
    assert i.t('empty', default='fallback') == 'fallback'
