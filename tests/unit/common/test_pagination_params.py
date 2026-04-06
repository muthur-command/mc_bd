"""backend.common.pagination — 分页参数与 PageData 模型。"""

from __future__ import annotations

from backend.common.pagination import PageData, _CustomPageParams


def test_custom_page_params_to_raw_params() -> None:
    p = _CustomPageParams(page=3, size=15)
    raw = p.to_raw_params()
    assert raw.limit == 15
    assert raw.offset == 30


def test_page_data_model_structure() -> None:
    pd = PageData[dict](
        items=({"id": 1},),
        total=1,
        page=1,
        size=20,
        total_pages=1,
        links={  # type: ignore[arg-type]
            "first": "",
            "last": "",
            "self": "",
            "next": None,
            "prev": None,
        },
    )
    d = pd.model_dump()
    assert d["total"] == 1
    assert len(d["items"]) == 1
