"""版本常量与 PEP 440 形态。"""

from packaging.version import Version

from backend.const import MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION, __short_version__, __version__


def test_version_components_match_full_string() -> None:
    assert __version__ == f"{__short_version__}.{PATCH_VERSION}"
    assert __short_version__ == f"{MAJOR_VERSION}.{MINOR_VERSION}"


def test_version_is_valid_packaging_version() -> None:
    v = Version(__version__)
    assert v.release[0] == MAJOR_VERSION
    assert v.release[1] == MINOR_VERSION
