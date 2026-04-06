"""backend.common.response.response_code — 枚举码值。"""

from backend.common.response.response_code import CustomResponseCode


def test_custom_http_codes_numeric() -> None:
    assert CustomResponseCode.HTTP_200.code == 200
    assert CustomResponseCode.HTTP_400.code == 400
