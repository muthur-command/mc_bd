"""common.enums：MenuType 等基类方法。"""

from backend.common.enums import MenuType


def test_menu_type_members() -> None:
    assert 'directory' in MenuType.get_member_keys()
    assert 0 in MenuType.get_member_values()
    d = MenuType.get_member_dict()
    assert d['menu'] == 1
