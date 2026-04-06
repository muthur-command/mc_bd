"""backend.utils.dynamic_config — 内部布尔转换等小函数。"""

from backend.utils import dynamic_config as dc


def test_to_bool_only_true_string() -> None:
    assert dc._to_bool("true") is True
    assert dc._to_bool("false") is False
    assert dc._to_bool("") is False
