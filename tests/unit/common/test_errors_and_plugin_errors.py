"""common.exception.errors、plugin.errors。"""

from backend.common.exception.errors import CustomError, ForbiddenError, RequestError
from backend.common.response.response_code import CustomErrorCode, StandardResponseCode
from backend.plugin.errors import PluginConfigError, PluginInjectError, PluginInstallError


def test_custom_error_carries_code_and_msg() -> None:
    err = CustomError(error=CustomErrorCode.CAPTCHA_ERROR)
    assert err.code == CustomErrorCode.CAPTCHA_ERROR.code
    assert err.msg == CustomErrorCode.CAPTCHA_ERROR.msg


def test_request_error_defaults() -> None:
    err = RequestError()
    assert err.code == StandardResponseCode.HTTP_400


def test_forbidden_error_code() -> None:
    err = ForbiddenError(msg='no')
    assert err.code == StandardResponseCode.HTTP_403
    assert err.msg == 'no'


def test_plugin_errors_are_exception_subclasses() -> None:
    assert issubclass(PluginConfigError, Exception)
    assert issubclass(PluginInjectError, Exception)
    assert issubclass(PluginInstallError, Exception)
