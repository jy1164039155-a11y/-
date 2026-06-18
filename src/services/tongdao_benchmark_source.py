# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import warnings
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from zipfile import ZipFile
import xml.etree.ElementTree as ET


SOURCE_DOCX = Path("01_Source") / "03_attachment" / "通道县城镇基准地价更新技术报告打印.docx"
W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
LEVELS_5 = ["一级", "二级", "三级", "四级", "五级"]
GRADES = ["优", "较优", "一般", "较劣", "劣"]
USAGE_ALIASES = {
    "商业服务业用地": ["商业服务业用地"],
    "居住用地": ["居住用地", "住宅用地", "居住"],
    "工矿用地": ["工矿用地", "工矿、仓储用地", "工矿仓储用地"],
    "仓储用地": ["仓储用地", "工矿、仓储用地", "工矿仓储用地"],
    "公共管理与公共服务用地": ["公共管理与公共服务用地"],
    "公用设施用地": ["公用设施用地"],
}
ROMAN_LEVELS = {
    "Ⅰ": "一级",
    "I": "一级",
    "Ⅱ": "二级",
    "II": "二级",
    "Ⅲ": "三级",
    "III": "三级",
    "Ⅳ": "四级",
    "IV": "四级",
    "Ⅴ": "五级",
    "V": "五级",
    "一": "一级",
    "二": "二级",
    "三": "三级",
    "四": "四级",
    "五": "五级",
}
TOWNSHIP_GRADES = ("一等乡镇", "二等乡镇", "三等乡镇")


def build_tongdao_benchmark_config(base_dir: str, fallback: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Merge hand-curated safe metadata with tables extracted from the converted technical report.

    The converted report has a usable Word table layer, but many table titles live in
    preceding paragraphs.  We bind values by formal table title/table number rather than by
    loose keyword search, so process tables in chapter 3 cannot be mistaken for final
    correction tables in chapter 5/appendix.
    """

    config = deepcopy(fallback or {})
    docx_path = Path(base_dir) / SOURCE_DOCX
    if not docx_path.exists():
        config.setdefault("source_status", "missing")
        return config
    extracted = _extract_cached(str(docx_path), docx_path.stat().st_mtime_ns)
    merged = deepcopy(config)
    extracted = deepcopy(extracted)
    extracted_cap_rate = extracted.pop("cap_rate", {}) or {}
    if extracted_cap_rate:
        merged.setdefault("cap_rate", {}).update(extracted_cap_rate)
    for key, value in extracted.items():
        if value not in ({}, [], None, ""):
            merged[key] = value
    merged.pop("default_object", None)
    merged["source_status"] = "structured"
    merged["source_docx"] = str(SOURCE_DOCX)
    return merged


@lru_cache(maxsize=4)
def _extract_cached(docx_path: str, _mtime_ns: int) -> Dict[str, Any]:
    elements = _document_elements(Path(docx_path))
    return {
        "base_price_connotation_tables": _extract_base_connotation_tables(elements),
        "base_land_price": _extract_city_base_prices(elements),
        "township_base_land_price": _extract_township_base_prices(elements),
        "plot_ratio_table": _extract_plot_ratio_tables(elements),
        "route_price_segments": _extract_route_price_segments(elements),
        "frontage_depth_table": _extract_frontage_depth_table(elements),
        "frontage_width_table": _extract_frontage_width_table(elements),
        "road_grade_match_table": _extract_road_grade_match_table(elements),
        "corner_coefficient_table": _extract_corner_coefficient_table(elements),
        "surrounding_land_use_table": _extract_surrounding_land_use_table(elements),
        **_extract_cap_rate_tables(elements),
        "region_factor_table": _extract_region_factor_tables(elements, scope="city"),
        "township_region_factor_table": _extract_region_factor_tables(elements, scope="township"),
        "source_table_refs": _extract_source_refs(elements),
        "township_grade_aliases": _extract_township_grade_aliases(elements),
    }


def _document_elements(docx_path: Path) -> List[Dict[str, Any]]:
    with ZipFile(docx_path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    body = root.find("w:body", W_NS)
    elements: List[Dict[str, Any]] = []
    table_index = -1
    previous_paragraphs: List[str] = []
    for child in list(body or []):
        tag = child.tag.split("}")[-1]
        if tag == "p":
            text = _text_of(child)
            if text:
                previous_paragraphs.append(text)
                previous_paragraphs = previous_paragraphs[-10:]
            elements.append({"type": "p", "text": text})
        elif tag == "tbl":
            table_index += 1
            rows = _table_rows(child)
            title = _nearest_table_title(previous_paragraphs)
            elements.append({
                "type": "table",
                "index": table_index,
                "title": title,
                "previous": list(previous_paragraphs),
                "rows": rows,
            })
    return elements


def _text_of(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.findall(".//w:t", W_NS)).strip()


def _table_rows(table: ET.Element) -> List[List[str]]:
    rows: List[List[str]] = []
    for tr in table.findall("./w:tr", W_NS):
        values = [_text_of(tc) for tc in tr.findall("./w:tc", W_NS)]
        if any(value.strip() for value in values):
            rows.append(values)
    return rows


def _nearest_table_title(previous: Iterable[str]) -> str:
    for text in reversed(list(previous)):
        if text.strip().startswith("表"):
            return _clean_text(text)
    return ""


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).replace(" .", ".")


def _extract_base_connotation_tables(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract formal benchmark land-price connotation tables.

    The final report needs the original multi-purpose header structure rather than a
    current-use-only simplified table.  The converted technical report exposes both
    chapter tables and appendix duplicates; chapter tables are preferred.
    """

    result: Dict[str, Any] = {}
    for item in elements:
        if item.get("type") != "table":
            continue
        title = str(item.get("title") or "")
        rows = item.get("rows") or []
        joined = "".join("".join(row) for row in rows[:3])
        normalized_joined = re.sub(r"\s+", "", joined)
        if "基准地价内涵" not in title or "商业服务业用地" not in normalized_joined or "居住用地" not in normalized_joined:
            continue
        if "2025" not in joined or "出让土地使用权" not in normalized_joined:
            continue
        if "城区" in title and "city" not in result:
            result["city"] = _parse_base_connotation_table(rows, title, township=False)
        elif "乡镇" in title and "township" not in result:
            result["township"] = _parse_base_connotation_table(rows, title, township=True)
    return {key: value for key, value in result.items() if value}


def _parse_base_connotation_table(rows: List[List[str]], title: str, *, township: bool) -> Dict[str, Any]:
    if not rows:
        return {}
    usages = [
        "商业服务业用地",
        "居住用地",
        "工矿用地" if not township else "工矿、仓储用地",
        "仓储用地" if not township else "",
        "公共管理与公共服务用地",
        "公用设施用地",
    ]
    usages = [usage for usage in usages if usage]
    columns: List[str] = []
    header_rows: List[List[Dict[str, Any]]] = []
    if township:
        columns.extend(["等别", "级别", "土地权利"])
        first_header = [
            {"label": "等别", "rowspan": 2},
            {"label": "级别", "rowspan": 2},
            {"label": "土地权利", "rowspan": 2},
        ]
    else:
        columns.extend(["级别", "土地权利"])
        first_header = [
            {"label": "级别", "rowspan": 2},
            {"label": "土地权利", "rowspan": 2},
        ]
    second_header: List[Dict[str, Any]] = []
    for usage in usages:
        first_header.append({"label": usage, "colspan": 2})
        second_header.extend([{"label": "使用年期"}, {"label": "容积率"}])
        columns.extend([f"{usage}_使用年期", f"{usage}_容积率"])
    first_header.extend([{"label": "开发程度", "rowspan": 2}, {"label": "估价期日", "rowspan": 2}])
    columns.extend(["开发程度", "估价期日"])
    header_rows = [first_header, second_header]

    parsed_rows: List[Dict[str, Any]] = []
    row_source = rows[2:] if len(rows) > 2 and any("使用年期" in cell for cell in rows[1]) else rows[1:]
    active_grade = ""
    for raw in row_source:
        row = [_clean_text(cell) for cell in raw]
        if not any(row):
            continue
        if township:
            row = row + [""] * (3 + len(usages) * 2 + 2 - len(row))
            if "等" in row[0]:
                active_grade = row[0].replace("乡镇", "")
            current: Dict[str, Any] = {"等别": active_grade, "级别": _clean_connotation_value(row[1]), "土地权利": _clean_connotation_value(row[2])}
            offset = 3
        else:
            row = row + [""] * (2 + len(usages) * 2 + 2 - len(row))
            current = {"级别": _clean_connotation_value(row[0]), "土地权利": _clean_connotation_value(row[1])}
            offset = 2
        if not current.get("级别"):
            continue
        for usage in usages:
            current[f"{usage}_使用年期"] = _clean_connotation_value(row[offset])
            current[f"{usage}_容积率"] = _clean_connotation_value(row[offset + 1])
            offset += 2
        current["开发程度"] = _clean_connotation_value(row[offset])
        current["估价期日"] = _clean_connotation_value(row[offset + 1])
        parsed_rows.append(current)
    return {
        "source_title": title,
        "columns": columns,
        "header_rows": header_rows,
        "rows": parsed_rows,
        "usages": usages,
        "scope": "乡镇" if township else "城区",
    }


def _clean_connotation_value(value: Any) -> str:
    return _clean_text(value).replace(" ", "")


OTHER_CAP_RATE_USAGES = ("工矿用地", "仓储用地", "公共管理与公共服务用地", "公用设施用地")


def _extract_cap_rate_tables(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    other_table_seen = False
    for item in elements:
        if item.get("type") != "table":
            continue
        title = str(item.get("title") or "")
        rows = item.get("rows") or []
        joined = "".join("".join(row) for row in rows)
        if "工矿" in title and "公共管理与公共服务" in title and "还原率表" in title:
            other_table_seen = True
            table = _parse_other_cap_rate_table(rows, title)
            cap_rates = _cap_rates_from_other_table(table) if table else {}
            if table:
                result["cap_rate_other_table"] = table
            if cap_rates:
                # 解析值优先：与报告原值保持一致，覆盖内置默认还原率。
                result.setdefault("cap_rate", {}).update(cap_rates)
            missing = [usage for usage in OTHER_CAP_RATE_USAGES if usage not in cap_rates]
            if missing:
                warnings.warn(
                    "通道县技术报告其他用地还原率表解析失败，缺失 "
                    f"{'、'.join(missing)}，对应还原率将回退到内置默认值，"
                    f"请核对报告原值是否变动（表标题：{title or '无'}）。",
                    stacklevel=2,
                )
        elif "土地还原率表" in title and "商业服务业" in joined and "居住" in joined and "cap_rate_table" not in result:
            table = _parse_commercial_residential_cap_rate_table(rows, title)
            if table:
                result["cap_rate_table"] = table
                result.setdefault("cap_rate", {}).update(_cap_rates_from_commercial_residential_table(table))
    if not other_table_seen:
        warnings.warn(
            "通道县技术报告中未找到工矿/仓储/公共管理/公用设施用地还原率表，"
            "四类土地还原率将回退到内置默认值，请核对报告原值是否变动。",
            stacklevel=2,
        )
    return result


def _cap_rates_from_other_table(table: Dict[str, Any]) -> Dict[str, str]:
    rows = list(table.get("rows") or [])
    land_rate_row = next(
        (
            row
            for row in rows
            if any("土地还原率" in str(value or "") for value in row.values())
        ),
        {},
    )
    if not land_rate_row:
        return {}
    result: Dict[str, str] = {}
    for column, value in land_rate_row.items():
        text = _clean_number(value).replace("%", "")
        if not text:
            continue
        if "工矿" in column:
            result["工矿用地"] = text
        if "仓储" in column:
            result["仓储用地"] = text
        if "公共管理与公共服务" in column:
            result["公共管理与公共服务用地"] = text
        if "公用设施" in column:
            result["公用设施用地"] = text
    return result


def _cap_rates_from_commercial_residential_table(table: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for row in table.get("rows") or []:
        usage = _normalize_usage(row.get("用地类型") or row.get("土地(房屋)类型") or "")
        if not usage:
            continue
        rate = ""
        for key, value in row.items():
            if "还原率" in key:
                rate = _clean_number(value).replace("%", "")
        if rate:
            result[usage] = rate
    return result


def _parse_other_cap_rate_table(rows: List[List[str]], title: str) -> Dict[str, Any]:
    if len(rows) < 2:
        return {}
    columns = [_clean_text(cell) for cell in rows[0] if _clean_text(cell)]
    parsed_rows: List[Dict[str, Any]] = []
    for row in rows[1:]:
        values = [_clean_text(cell) for cell in row]
        if not any(values):
            continue
        values += [""] * (len(columns) - len(values))
        parsed_rows.append({columns[i]: values[i] for i in range(len(columns))})
    return {"source_title": title, "columns": columns, "rows": parsed_rows}


def _parse_commercial_residential_cap_rate_table(rows: List[List[str]], title: str) -> Dict[str, Any]:
    if len(rows) < 2:
        return {}
    header = [_clean_text(cell) for cell in rows[0] if _clean_text(cell)]
    # The source has detail/process tables as well.  Keep only final summary-like rows.
    if "用地类型" not in "".join(header) or "还原率" not in "".join(header):
        return {}
    parsed_rows: List[Dict[str, Any]] = []
    for row in rows[1:]:
        values = [_clean_text(cell) for cell in row]
        if not any("用地" in value for value in values[:1]):
            continue
        values += [""] * (len(header) - len(values))
        parsed_rows.append({header[i]: values[i] for i in range(len(header))})
    if not parsed_rows:
        return {}
    return {"source_title": title, "columns": header, "rows": parsed_rows}


def _extract_city_base_prices(elements: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    for item in elements:
        if item.get("type") != "table":
            continue
        title = str(item.get("title") or "")
        if "通道县城区级别基准地价" not in title:
            continue
        rows = item.get("rows") or []
        if not rows or "用地类型" not in "".join(rows[0]):
            continue
        result: Dict[str, Dict[str, str]] = {}
        for row in rows[1:]:
            if len(row) < 6:
                continue
            usage = _normalize_usage(row[0])
            if usage:
                result[usage] = {level: _clean_number(row[i + 1]) for i, level in enumerate(LEVELS_5)}
        if result:
            return result
    return {}


def _extract_township_base_prices(elements: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, str]]]:
    result: Dict[str, Dict[str, Dict[str, str]]] = {}
    active_grade = ""
    for item in elements:
        if item.get("type") != "table" or "通道县乡镇级别基准地价" not in str(item.get("title") or ""):
            continue
        for row in item.get("rows") or []:
            if not row or "用地类型" in row:
                continue
            row = row + [""] * (6 - len(row))
            grade, _towns, usage_raw, lv1, lv2, lv3 = row[:6]
            if "等" in grade:
                active_grade = _clean_text(grade).replace(" ", "")
            usage = _normalize_usage(usage_raw)
            if not active_grade or not usage:
                continue
            values = {"一级": _clean_number(lv1), "二级": _clean_number(lv2), "三级": _clean_number(lv3)}
            if values["三级"] in {"/", ""}:
                values.pop("三级", None)
            result.setdefault(active_grade, {})[usage] = values
    return result


def _extract_plot_ratio_tables(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    township_result: Dict[str, Any] = {}
    for item in elements:
        if item.get("type") != "table":
            continue
        title = str(item.get("title") or "")
        if "容积率修正系数表" not in title:
            continue
        rows = item.get("rows") or []
        if len(rows) < 3:
            continue
        if "城区" in title:
            usage = _normalize_usage(title)
            if usage:
                _merge_city_plot_ratio(result, usage, rows, title)
        elif "乡镇" in title:
            usage = _normalize_usage(title)
            if usage:
                _merge_township_plot_ratio(township_result, usage, rows, title)
    if township_result:
        result["__township__"] = township_result
    return result


def _merge_city_plot_ratio(target: Dict[str, Any], usage: str, rows: List[List[str]], title: str) -> None:
    parsed = _parse_city_plot_ratio(rows, title)
    if not parsed:
        return
    parsed_levels = list(parsed.get("levels") or [])
    existing = target.setdefault(
        usage,
        {"levels": [], "rows": [], "source_title": title},
    )
    levels = existing.setdefault("levels", [])
    for level in parsed_levels:
        if level and level not in levels:
            levels.append(level)
            for existing_row in existing.get("rows") or []:
                existing_row.setdefault("values", []).append("")
    by_ratio = {str(row.get("ratio")): row for row in existing.get("rows") or []}
    for row in parsed.get("rows") or []:
        ratio = str(row.get("ratio") or "")
        if not ratio:
            continue
        target_row = by_ratio.get(ratio)
        if not target_row:
            target_row = {"ratio": row.get("ratio"), "label": row.get("label"), "values": [""] * len(levels)}
            existing.setdefault("rows", []).append(target_row)
            by_ratio[ratio] = target_row
        while len(target_row.setdefault("values", [])) < len(levels):
            target_row["values"].append("")
        for level, value in zip(parsed_levels, row.get("values") or []):
            if level in levels:
                target_row["values"][levels.index(level)] = value
    existing["rows"] = sorted(
        existing.get("rows") or [],
        key=lambda row: _safe_decimal(row.get("ratio")),
    )
    existing["source_title"] = title


def _parse_city_plot_ratio(rows: List[List[str]], title: str) -> Dict[str, Any]:
    header = rows[0]
    levels = [cell for cell in header[1:] if cell]
    table_rows: List[Dict[str, Any]] = []
    for row in rows[1:]:
        if len(row) < 2:
            continue
        label = _clean_text(row[0]).replace(" ", "")
        values = [_clean_number(value) for value in row[1:1 + len(levels)]]
        if label and any(values):
            table_rows.append({"ratio": _ratio_to_number(label), "label": label, "values": values})
    return {"levels": levels, "rows": table_rows, "source_title": title}


def _safe_decimal(value: Any) -> float:
    match = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return float(match.group(0)) if match else 0.0


def _extract_route_price_segments(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows_out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in elements:
        if item.get("type") != "table":
            continue
        title = str(item.get("title") or "")
        if "商业服务业用地路线价" not in title:
            continue
        rows = item.get("rows") or []
        if not rows or "道路名称" not in "".join(rows[0]):
            continue
        for row in rows[1:]:
            row = row + [""] * 8
            code, road_name, start, end, level, road_type, standard_depth, route_price = [_clean_text(cell) for cell in row[:8]]
            if not code or code == "编号":
                continue
            key = f"{code}|{road_name}|{start}|{end}"
            if key in seen:
                continue
            seen.add(key)
            rows_out.append({
                "id": code,
                "code": code,
                "road_name": road_name,
                "route_start": start,
                "route_end": end,
                "level": _level_from_text(level) or level,
                "road_type": road_type,
                "standard_depth": _clean_number(standard_depth),
                "route_price": _clean_number(route_price),
                "source_title": title,
            })
    return rows_out


def _extract_frontage_depth_table(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    for item in elements:
        title = str(item.get("title") or "")
        if "表5.6.7" not in title or "临街深度" not in title:
            continue
        rows = item.get("rows") or []
        if len(rows) < 2:
            continue
        buckets = [_clean_text(cell).replace(" ", "") for cell in rows[0][1:]]
        parsed_rows: List[Dict[str, Any]] = []
        for row in rows[1:]:
            if len(row) < 2:
                continue
            road_type = _clean_text(row[0]).replace(" ", "")
            coefficients = [_clean_number(value) for value in row[1:1 + len(buckets)]]
            if road_type:
                parsed_rows.append({"road_type": road_type, "coefficients": coefficients})
        return {
            "source_title": title,
            "source_symbol": "Kd",
            "buckets": buckets,
            "rows": parsed_rows,
        }
    return {}


def _extract_frontage_width_table(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    for item in elements:
        title = str(item.get("title") or "")
        if "表5.6.8" not in title or "临街宽度" not in title:
            continue
        rows = item.get("rows") or []
        if len(rows) < 2:
            continue
        buckets = [_clean_text(cell).replace(" ", "") for cell in rows[0][1:]]
        parsed_rows: List[Dict[str, Any]] = []
        for row in rows[1:]:
            if len(row) < 2:
                continue
            road_type = _normalize_road_type(row[0])
            coefficients = [_clean_number(value) for value in row[1:1 + len(buckets)]]
            if road_type:
                parsed_rows.append({"road_type": road_type, "coefficients": coefficients})
        return {
            "source_title": title,
            "source_symbol": "Kw",
            "formula_symbol": "Kk",
            "buckets": buckets,
            "rows": parsed_rows,
        }
    return {}


def _extract_road_grade_match_table(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """规划道路通达度功能分值表用于给路线价修正表匹配道路等级。

    转换件中该表标题/单元格偶尔被拆碎，运行配置保留稳定映射：
    主干道、次干道、支路三类用于 Kd/Kk 表查系数；具体“生活型/交通型/混合型”
    仍作为来源说明保留，方便估价师校核。
    """
    source_title = "规划道路通达度功能分值表"
    for item in elements:
        title = str(item.get("title") or "")
        rows = item.get("rows") or []
        text = title + "".join("".join(row) for row in rows[:4])
        if "规划道路通达度" in text and ("道路等级" in text or "主干道" in text):
            source_title = title or source_title
            break
    rows = [
        {"grade": "混合型主干道", "road_type": "主干道"},
        {"grade": "生活型主干道", "road_type": "主干道"},
        {"grade": "交通型主干道", "road_type": "主干道"},
        {"grade": "生活型次干道", "road_type": "次干道"},
        {"grade": "交通型次干道", "road_type": "次干道"},
        {"grade": "支路", "road_type": "支路"},
    ]
    return {"source_title": source_title, "rows": rows}


def _extract_corner_coefficient_table(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    for item in elements:
        title = str(item.get("title") or "")
        normalized_title = title.replace(" ", "")
        if "表5.6.9" not in normalized_title or "街角" not in normalized_title:
            continue
        rows = item.get("rows") or []
        if len(rows) < 2:
            continue
        buckets = [_clean_text(cell).replace(" ", "") for cell in rows[0][1:]]
        coefficients = [_clean_number(value) for value in rows[1][1:1 + len(buckets)]]
        return {
            "source_title": title,
            "source_symbol": "Kc",
            "buckets": buckets,
            "coefficients": coefficients,
        }
    return {}


def _extract_surrounding_land_use_table(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    for item in elements:
        title = str(item.get("title") or "")
        if "表5.6.13" not in title or "周边土地利用类型" not in title:
            continue
        rows = item.get("rows") or []
        if len(rows) < 3:
            continue
        grades = [_clean_text(cell) for cell in rows[0][1:]]
        descriptions = [_clean_text(cell) for cell in rows[1][1:1 + len(grades)]]
        coefficients = [_clean_number(cell) for cell in rows[2][1:1 + len(grades)]]
        return {
            "source_title": title,
            "source_symbol": "Ku",
            "grades": grades,
            "descriptions": descriptions,
            "coefficients": coefficients,
        }
    return {}


def _normalize_road_type(value: Any) -> str:
    text = _clean_text(value).replace(" ", "")
    if "主干道" in text:
        return "主干道"
    if "次干道" in text:
        return "次干道"
    if "支路" in text:
        return "支路"
    return text


def _merge_township_plot_ratio(target: Dict[str, Any], usage: str, rows: List[List[str]], title: str) -> None:
    if len(rows) < 2:
        return
    groups = _township_column_groups(rows[0], rows[1])
    if not groups:
        return
    usage_bucket = target.setdefault(usage, {})
    for grade, columns in groups.items():
        bucket = usage_bucket.setdefault(grade, {"levels": [level for level, _ in columns], "rows": [], "source_title": title})
        for row in rows[2:]:
            if not row:
                continue
            label = _clean_text(row[0]).replace(" ", "")
            if not label:
                continue
            values = []
            for _level, column_index in columns:
                values.append(_clean_number(row[column_index]) if column_index < len(row) else "")
            if any(values):
                bucket["rows"].append({"ratio": _ratio_to_number(label), "label": label, "values": values})


def _township_column_groups(row0: List[str], row1: List[str]) -> Dict[str, List[Tuple[str, int]]]:
    groups: Dict[str, List[Tuple[str, int]]] = {}
    active_grade = ""
    for index, header in enumerate(row0):
        text = _clean_text(header).replace(" ", "")
        if "一等乡镇" in text:
            active_grade = "一等"
        elif "二等乡镇" in text:
            active_grade = "二等"
        elif "三等乡镇" in text:
            active_grade = "三等"
        level = _level_from_text(row1[index] if index < len(row1) else "")
        if active_grade and level:
            groups.setdefault(active_grade, []).append((level, index))
    return groups


def _extract_region_factor_tables(elements: List[Dict[str, Any]], *, scope: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    pending: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    pending_titles: Dict[Tuple[str, str, str], str] = {}
    for item in elements:
        if item.get("type") != "table":
            continue
        title = str(item.get("title") or "")
        if "宗地地价区域因素修正系数" not in title:
            continue
        info = _parse_region_title(title)
        if not info:
            continue
        is_township = info["scope"] == "乡镇"
        if (scope == "city" and is_township) or (scope == "township" and not is_township):
            continue
        key = (info.get("township_grade") or "", info["usage"], info["level"])
        if "指标说明" in title:
            if key in pending:
                _attach_criteria(pending[key], item.get("rows") or [])
                _store_region_table(result, info, pending.pop(key), pending_titles.pop(key, title))
            continue
        rows = _parse_region_coefficient_rows(item.get("rows") or [])
        if not rows:
            continue
        pending[key] = rows
        pending_titles[key] = title
    for key, rows in list(pending.items()):
        township_grade, usage, level = key
        _store_region_table(result, {"scope": "乡镇" if township_grade else "城区", "township_grade": township_grade, "usage": usage, "level": level}, rows, pending_titles.get(key, ""))
    return result


def _parse_region_title(title: str) -> Dict[str, str] | None:
    if "指标说明" not in title and "修正系数表" not in title:
        return None
    title = _clean_text(title).replace(" ", "")
    prefix = re.sub(r"^表5\.[45]\.\d+", "", title)
    prefix = prefix.replace("宗地地价区域因素修正系数指标说明表", "").replace("宗地地价区域因素修正系数表", "")
    township_grade = ""
    scope = "城区"
    for grade in TOWNSHIP_GRADES:
        if prefix.startswith(grade):
            township_grade = grade.replace("乡镇", "")
            scope = "乡镇"
            prefix = prefix[len(grade):]
            break
    if prefix.startswith("城区"):
        prefix = prefix[2:]
    level = _level_from_text(prefix)
    if not level:
        return None
    usage_part = re.sub(r"^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|I|II|III|IV|V|一|二|三|四|五)级", "", prefix)
    usage = _normalize_usage(usage_part)
    if not usage:
        return None
    return {"scope": scope, "township_grade": township_grade, "usage": usage, "level": level}


def _parse_region_coefficient_rows(rows: List[List[str]]) -> List[Dict[str, Any]]:
    parsed: List[Dict[str, Any]] = []
    active_factor = ""
    for row in rows[1:]:
        row = row + [""] * 7
        factor = _clean_text(row[0]) or active_factor
        sub_factor = _clean_text(row[1])
        if not sub_factor:
            continue
        active_factor = factor
        grades = {grade: _clean_number(row[index + 2]) for index, grade in enumerate(GRADES)}
        parsed.append({"factor": factor, "sub_factor": sub_factor, "grades": grades, "criteria": {}})
    return parsed


def _attach_criteria(rows: List[Dict[str, Any]], criteria_rows: List[List[str]]) -> None:
    by_sub = {_normalize_factor_name(row["sub_factor"]): row for row in rows}
    for raw in criteria_rows[1:]:
        raw = raw + [""] * 6
        sub = _normalize_factor_name(raw[0])
        target = by_sub.get(sub)
        if target is None:
            target = _fuzzy_factor_row(by_sub, sub)
        if target is None:
            continue
        target["criteria"] = {grade: _clean_text(raw[index + 1]) for index, grade in enumerate(GRADES)}


def _fuzzy_factor_row(rows_by_sub: Dict[str, Dict[str, Any]], sub: str) -> Dict[str, Any] | None:
    for key, row in rows_by_sub.items():
        if key and sub and (key in sub or sub in key):
            return row
    return None


def _store_region_table(result: Dict[str, Any], info: Dict[str, str], rows: List[Dict[str, Any]], title: str) -> None:
    usage = info["usage"]
    usages = [usage]
    if usage == "工矿用地" and ("工矿、仓储" in title or "工矿仓储" in title):
        usages.append("仓储用地")
    level = info["level"]
    for row in rows:
        row.setdefault("source_title", title)
    for current_usage in usages:
        copied_rows = deepcopy(rows)
        if info.get("scope") == "乡镇":
            result.setdefault(info.get("township_grade") or "", {}).setdefault(current_usage, {})[level] = copied_rows
        else:
            result.setdefault(current_usage, {})[level] = copied_rows


def _extract_source_refs(elements: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    refs: Dict[str, Dict[str, Any]] = {}
    for item in elements:
        title = str(item.get("title") or "")
        if not title.startswith("表"):
            continue
        refs[title] = {"table_index": item.get("index"), "title": title}
    return refs


def _extract_township_grade_aliases(elements: List[Dict[str, Any]]) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for item in elements:
        if item.get("type") != "table" or "通道县乡镇级别基准地价" not in str(item.get("title") or ""):
            continue
        active_grade = ""
        active_towns = ""
        for row in item.get("rows") or []:
            if not row or "用地类型" in row:
                continue
            row = row + [""] * 3
            if "等" in row[0]:
                active_grade = _clean_text(row[0]).replace(" ", "")
            if row[1].strip():
                active_towns = _clean_text(row[1]).replace(" ", "")
            if active_grade and active_towns:
                for town in re.split(r"[、,，\s]+", active_towns):
                    if town:
                        aliases[town] = active_grade
    # The converted table sometimes merges several names without separators.
    aliases.update({
        "县溪镇": "一等",
        "播阳镇": "二等",
        "牙屯堡镇": "二等",
        "万佛山镇": "二等",
        "菁芜洲镇": "二等",
        "坪坦乡": "二等",
        "陇城镇": "二等",
        "溪口镇": "二等",
        "大高坪苗族乡": "三等",
        "大高坪乡": "三等",
        "独坡镇": "三等",
    })
    return aliases


def _normalize_usage(value: Any) -> str:
    text = _clean_text(value).replace(" ", "")
    if not text:
        return ""
    for usage, aliases in USAGE_ALIASES.items():
        if any(alias in text for alias in aliases):
            return usage
    return ""


def _normalize_factor_name(value: Any) -> str:
    return re.sub(r"[\s（）()%()]", "", str(value or ""))


def _level_from_text(value: Any) -> str:
    text = _clean_text(value).replace(" ", "")
    match = re.search(r"(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|III|II|IV|V|I|一|二|三|四|五)级", text)
    if match:
        return ROMAN_LEVELS.get(match.group(1), "")
    if text in {"一级", "二级", "三级", "四级", "五级"}:
        return text
    return ""


def _clean_number(value: Any) -> str:
    text = _clean_text(value).replace(" ", "")
    return text.replace("，", ",")


def _ratio_to_number(label: str) -> str:
    text = label.replace("≤", "").replace("≥", "").replace("≧", "").replace("＞", "").replace(">", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return match.group(0) if match else label
