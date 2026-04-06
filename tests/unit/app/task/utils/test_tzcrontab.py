"""tzcrontab_verify 行为。"""

from unittest.mock import patch

import pytest

from celery.schedules import ParseException

from backend.app.task.utils.tzcrontab import crontab_verify
from backend.common.exception import errors


def test_crontab_verify_accepts_five_fields() -> None:
    crontab_verify('* * * * *')


def test_crontab_verify_rejects_wrong_field_count() -> None:
    with pytest.raises(errors.RequestError) as ei:
        crontab_verify('* * *')
    assert '非法' in (ei.value.msg or '')


def test_crontab_verify_maps_parse_exception() -> None:
    with patch('backend.app.task.utils.tzcrontab.crontab', side_effect=ParseException()):
        with pytest.raises(errors.RequestError) as ei:
            crontab_verify('0 0 * * *')
        assert '非法' in (ei.value.msg or '')
