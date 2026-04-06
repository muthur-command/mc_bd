"""database.db：create_database_url 行为。"""

from backend.common.enums import DataBaseType
from backend.core.conf import settings
from backend.database.db import create_database_url


def test_create_database_url_unittest_suffix() -> None:
    base = settings.DATABASE_SCHEMA
    url = create_database_url(unittest=True)
    assert url.database == f'{base}_test'


def test_create_database_url_without_database_name() -> None:
    url = create_database_url(with_database=False)
    if DataBaseType.mysql == settings.DATABASE_TYPE:
        assert url.database is None
    else:
        assert url.database == 'postgres'
