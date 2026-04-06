"""backend.utils.pattern_validate"""

import pytest

from backend.utils import pattern_validate as pv


def test_is_phone_valid() -> None:
    assert pv.is_phone('13800138000')


def test_is_phone_invalid() -> None:
    assert pv.is_phone('123') is None


@pytest.mark.parametrize(
    ('url', 'ok'),
    [
        ('https://github.com/org/repo.git', True),
        ('http://host/path/repo', True),
        ('ftp://bad', False),
    ],
)
def test_is_git_url(url: str, ok: bool) -> None:
    m = pv.is_git_url(url)
    assert (m is not None) == ok


def test_is_has_number_and_letter() -> None:
    assert pv.is_has_number('a1')
    assert pv.is_has_letter('1b')
    assert pv.is_has_special_char('a!')
