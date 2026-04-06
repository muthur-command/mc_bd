"""backend.utils.build_tree（不依赖 ORM 行序列化）。"""

import pytest

from backend.common.enums import BuildTreeType
from backend.utils.build_tree import recursive_to_tree, traversal_to_tree


def test_traversal_to_tree_parent_child() -> None:
    nodes = [
        {'id': 1, 'parent_id': None, 'name': 'root'},
        {'id': 2, 'parent_id': 1, 'name': 'child'},
    ]
    tree = traversal_to_tree(nodes)
    assert len(tree) == 1
    assert tree[0]['id'] == 1
    assert 'children' in tree[0]
    assert tree[0]['children'][0]['id'] == 2


def test_recursive_to_tree_matches_flat_roots() -> None:
    nodes = [
        {'id': 1, 'parent_id': None},
        {'id': 2, 'parent_id': 1},
    ]
    t1 = traversal_to_tree(nodes)
    t2 = recursive_to_tree(nodes, parent_id=None)
    assert len(t1) == len(t2) == 1


def test_get_tree_data_traversal_requires_orm_rows() -> None:
    """get_tree_data 经 select_list_serialize，需 SQLAlchemy 模型行；此处仅文档化行为。"""
    from backend.utils.build_tree import get_tree_data

    with pytest.raises(AttributeError):
        get_tree_data([{'id': 1}], build_type=BuildTreeType.traversal)  # type: ignore[list-item]
