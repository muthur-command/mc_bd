"""backend.utils.dynamic_import — 缓存导入与模型解析。"""

import pytest

from backend.common.exception import errors
from backend.utils import dynamic_import as di


def test_import_module_cached_returns_same_object() -> None:
    di.import_module_cached.cache_clear()
    a = di.import_module_cached('json')
    b = di.import_module_cached('json')
    assert a is b


def test_dynamic_import_data_model_class() -> None:
    cls = di.dynamic_import_data_model('json.decoder.JSONDecoder')
    assert cls.__name__ == 'JSONDecoder'


def test_dynamic_import_data_model_invalid_raises_server_error() -> None:
    with pytest.raises(errors.ServerError) as ei:
        di.dynamic_import_data_model('json.decoder.NonexistentClassName')
    assert ei.value.msg == '数据模型列动态解析失败，请联系系统超级管理员'


def test_get_model_objects_missing_module() -> None:
    assert di.get_model_objects('backend.definitely_missing_model_module_xyz') is None


def test_get_model_objects_returns_classes_from_module() -> None:
    objs = di.get_model_objects('types')
    assert objs
    assert all(type(o) is type for o in objs)
