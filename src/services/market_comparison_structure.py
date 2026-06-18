# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


CASE_KEYS = ("a", "b", "c")


def _cell(label: str, colspan: int = 1, rowspan: int = 1) -> Dict[str, Any]:
    return {"label": label, "colspan": colspan, "rowspan": rowspan}


TABLE_SPECS: List[Dict[str, Any]] = [
    {
        "key": "market_comp_basic_rows",
        "title": "表3-10 比较实例基本情况表",
        "columns": ["项目", "比较实例A", "比较实例B", "比较实例C"],
        "header_rows": [[_cell("项目"), _cell("比较实例A"), _cell("比较实例B"), _cell("比较实例C")]],
        "group_columns": [],
        "source_target": "library",
    },
    {
        "key": "market_comp_factor_condition_rows",
        "title": "表3-11 比较因素条件说明表",
        "columns": ["因素类别", "因素分项", "比较因素", "估价对象", "案例A", "案例B", "案例C"],
        "header_rows": [
            [
                _cell("待估宗地及比较实例", colspan=3),
                _cell("估价对象", rowspan=2),
                _cell("案例A", rowspan=2),
                _cell("案例B", rowspan=2),
                _cell("案例C", rowspan=2),
            ],
            [_cell("因素类别"), _cell("因素分项"), _cell("比较因素")],
        ],
        "group_columns": [0, 1],
        "source_target": "factors",
    },
    {
        "key": "market_comp_time_index_rows",
        "title": "表3-12 估价对象与比较案例交易期日指数表",
        "columns": ["项目", "估价对象", "实例A", "实例B", "实例C"],
        "header_rows": [[_cell("项目"), _cell("估价对象"), _cell("实例A"), _cell("实例B"), _cell("实例C")]],
        "group_columns": [],
        "source_target": "factors",
    },
    {
        "key": "market_comp_factor_index_rows",
        "title": "表3-13 估价对象及比较因素条件指数表",
        "columns": ["因素类别", "因素分项", "比较因素", "估价对象", "案例A", "案例B", "案例C"],
        "header_rows": [
            [
                _cell("待估宗地及比较实例/比较因素", colspan=3),
                _cell("估价对象"),
                _cell("案例A"),
                _cell("案例B"),
                _cell("案例C"),
            ]
        ],
        "group_columns": [0, 1],
        "source_target": "factors",
    },
    {
        "key": "market_comp_correction_rows",
        "title": "表3-14 估价对象比较因素修正系数表",
        "columns": ["因素类别", "因素分项", "比较因素", "案例A", "案例B", "案例C"],
        "header_rows": [
            [
                _cell("待估宗地及比较实例/比较因素", colspan=3),
                _cell("案例A"),
                _cell("案例B"),
                _cell("案例C"),
            ]
        ],
        "group_columns": [0, 1],
        "source_target": "factors",
    },
]


def _row_keys(column_count: int) -> List[str]:
    if column_count == 4:
        return ["label", *CASE_KEYS]
    if column_count == 5:
        return ["label", "subject", *CASE_KEYS]
    if column_count == 6:
        return ["group", "subgroup", "label", *CASE_KEYS]
    return ["group", "subgroup", "label", "subject", *CASE_KEYS]


def _display_rows(rows: Iterable[Dict[str, Any]], column_count: int) -> List[Dict[str, Any]]:
    keys = _row_keys(column_count)
    result: List[Dict[str, Any]] = []
    for row in rows or []:
        item = dict(row)
        for key in keys:
            if item.get(key) in (None, ""):
                item[key] = "待校核" if key not in {"group", "subgroup"} else ""
        result.append(item)
    return result


def build_market_comparison_table_sections(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    analysis = data.get("market_comp_analysis") or {}
    result: List[Dict[str, Any]] = []
    for spec in TABLE_SPECS:
        rows = analysis.get(spec["key"]) or data.get(spec["key"]) or []
        result.append(
            {
                **spec,
                "report_title": spec["title"],
                "rows": _display_rows(rows, len(spec["columns"])),
            }
        )
    return result


def table_row_values(table: Dict[str, Any], row: Dict[str, Any]) -> List[Any]:
    return [row.get(key) for key in _row_keys(len(table.get("columns") or []))]
