# -*- coding: utf-8 -*-
"""基准地价系数修正法 结构化测算服务。

镜像 cost_approximation.py 的产出结构：calculate_benchmark_correction(data) 返回包含
parameters / tables / results / generated_narratives / effective_narratives /
narrative_overrides / narrative_segment_sources / content_blocks / warnings / complete
的字典，供 valuation_process_builder._benchmark_corr_process() 渲染正文与热区。

核心公式（居住用地）：
    P住 = 级别基准地价 × (1+∑Ki) × Ky × Kv × Kt × Ks × Ka × Ke × Kto + Kf
其中：
    ∑Ki —— 区域因素修正系数之和（百分数）
    Ky  —— 年期修正系数 Kn=[1-1/(1+r)^m]/[1-1/(1+r)^n]
    Kv  —— 容积率修正系数（内插法）
    Kt  —— 期日修正系数 (1+月上涨率)^月数
    Ks/Ka/Ke/Kto —— 面积/形状/景观/朝向修正系数
    Kf  —— 开发程度修正额
"""
from __future__ import annotations

import math
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.services.cost_approximation import (
    _county_matches,
    _date,
    _decimal,
    _load_json_config_cached,
)
from src.services.tongdao_benchmark_source import build_tongdao_benchmark_config

D0 = Decimal("0")
D1 = Decimal("1")
FACTOR_QUANT = Decimal("0.0001")
PERCENT_QUANT = Decimal("0.0001")
PRICE_QUANT = Decimal("0.1")

BENCHMARK_CONFIG = Path("src") / "config" / "tongdao_benchmark_land_price.json"

# 住宅 → 居住用地 等用途别名归一
USAGE_ALIASES = {
    "住宅": "居住用地",
    "住宅用地": "居住用地",
    "居住": "居住用地",
    "居住用地": "居住用地",
    "商业": "商业服务业用地",
    "商服": "商业服务业用地",
    "商业用地": "商业服务业用地",
    "商业服务业用地": "商业服务业用地",
    "工业": "工矿用地",
    "工矿用地": "工矿用地",
    "仓储用地": "仓储用地",
    "公共管理与公共服务用地": "公共管理与公共服务用地",
    "交通运输用地": "交通运输用地",
    "公用设施用地": "公用设施用地",
    "绿地与开敞空间用地": "绿地与开敞空间用地",
    "特殊用地": "特殊用地",
    "其他": "其他用途",
    "其他用途": "其他用途",
}

STATUTORY_MAX_TERM_RULES = {
    "居住用地": Decimal("70"),
    "商业服务业用地": Decimal("40"),
    "工矿用地": Decimal("50"),
    "仓储用地": Decimal("50"),
    "公共管理与公共服务用地": Decimal("50"),
    "交通运输用地": Decimal("50"),
    "公用设施用地": Decimal("50"),
    "绿地与开敞空间用地": Decimal("50"),
    "特殊用地": Decimal("50"),
}

GRADE_ORDER = ["优", "较优", "一般", "较劣", "劣"]
LEVEL_ROMAN = {
    "一级": "Ⅰ级",
    "二级": "Ⅱ级",
    "三级": "Ⅲ级",
    "四级": "Ⅳ级",
    "五级": "Ⅴ级",
}
AREA_MODE_LABELS = {
    "whole": "整宗土地面积",
    "apportioned": "分摊土地使用权面积",
}
CONNOTATION_USAGE_KEYS = {
    "商业服务业用地": "商业服务业用地",
    "居住用地": "居住用地",
    "工矿用地": "工矿用地",
    "仓储用地": "仓储用地",
    "公共管理与公共服务用地": "公共管理与公共服务用地",
    "公用设施用地": "公用设施用地",
}

FORMULA_PROFILES = {
    "商业服务业用地:non_street": {
        "symbol": "P商",
        "frontage_mode": "non_street",
        "base_factor": "base",
        "factors": ["base", "ki", "ky", "kv", "kt", "ks", "ka", "ku", "kf"],
    },
    "商业服务业用地:street_route_price": {
        "symbol": "P商",
        "frontage_mode": "street_route_price",
        "base_factor": "route_price",
        "factors": ["route_price", "ky", "kv", "kt", "ks", "ka", "kc", "kk", "kd", "ku", "kf"],
    },
    "商业服务业用地:route_price_plus_non_street": {
        "symbol": "P商",
        "frontage_mode": "route_price_plus_non_street",
        "base_factor": "weighted",
        "factors": ["route_price", "base", "ki", "ky", "kv", "kt", "ks", "ka", "kc", "kk", "kd", "ku", "kf"],
    },
    "居住用地": {"symbol": "P住", "factors": ["base", "ki", "ky", "kv", "kt", "ks", "ka", "ke", "kto", "kf"]},
    "公共管理与公共服务用地": {"symbol": "P公共", "factors": ["base", "ki", "ky", "kv", "kt", "ks", "ka", "kf"]},
    "公用设施用地": {"symbol": "P公用", "factors": ["base", "ky", "kt", "ks", "ka", "kf"]},
    "仓储用地": {"symbol": "P仓", "factors": ["base", "ki", "ky", "kt", "ks", "ka", "kf"]},
    "工矿用地": {"symbol": "P工", "factors": ["base", "ki", "ky", "kt", "ks", "ka", "kf"]},
}


def _qfactor(value: Decimal) -> Decimal:
    return value.quantize(FACTOR_QUANT, rounding=ROUND_HALF_UP)


def _qpercent(value: Decimal) -> Decimal:
    return value.quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


def _qprice(value: Decimal) -> Decimal:
    return value.quantize(PRICE_QUANT, rounding=ROUND_HALF_UP)


def _factor_text(value: Decimal) -> str:
    return format(_qfactor(value), "f")


def _percent_text(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _percent4_text(value: Decimal) -> str:
    """∑Ki 合计固定保留 4 位小数（范例 2.4020），不裁剪尾随零。"""
    return format(_qpercent(value), "f")


def _trim(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _base_dir() -> str:
    return str(Path(__file__).resolve().parents[2])


def _normalize_usage(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text in USAGE_ALIASES:
        return USAGE_ALIASES[text]
    for alias, mapped in USAGE_ALIASES.items():
        if alias and alias in text:
            return mapped
    return text


def _statutory_max_term(config: Dict[str, Any], usage: str) -> Decimal:
    configured = _decimal((config.get("statutory_max_term") or {}).get(usage))
    if configured > D0:
        return configured
    return STATUTORY_MAX_TERM_RULES.get(_normalize_usage(usage), D0)


def _formula_profile(usage: str, frontage_mode: str = "") -> Dict[str, Any]:
    normalized = _normalize_usage(usage)
    if normalized == "商业服务业用地":
        mode = _normalize_frontage_mode(frontage_mode)
        return FORMULA_PROFILES[f"商业服务业用地:{mode}"]
    return FORMULA_PROFILES.get(normalized, {"symbol": "P", "factors": ["base", "ki", "ky", "kt", "ks", "ka", "kf"]})


def _normalize_frontage_mode(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"route_price_plus_non_street", "临街+不临街", "路线价+级别价", "拆分", "拆分加权"}:
        return "route_price_plus_non_street"
    if text in {"street_route_price", "临街", "路线价", "临街路线价"}:
        return "street_route_price"
    return "non_street"


def _normalize_frontage_relation(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"setback", "non_adjacent", "manual", "退距", "非紧邻", "不紧邻", "需人工填写", "人工临街深度"}:
        return "setback"
    return "adjacent"


def _is_split_frontage(context_or_profile: Dict[str, Any]) -> bool:
    profile = context_or_profile.get("formula_profile") or context_or_profile
    return str(profile.get("frontage_mode") or "") == "route_price_plus_non_street"


def _formula_has(context_or_profile: Dict[str, Any], key: str) -> bool:
    profile = context_or_profile.get("formula_profile") or context_or_profile
    return key in set(profile.get("factors") or [])


def _factor_symbol(key: str) -> str:
    return {
        "base": "级别基准地价",
        "route_price": "路线价",
        "ki": "（1+∑Ki）",
        "ky": "Ky",
        "kv": "Kv",
        "kt": "Kt",
        "ks": "Ks",
        "ka": "Ka",
        "ke": "Ke",
        "kto": "Kto",
        "ku": "Ku",
        "kc": "Kc",
        "kk": "Kk",
        "kd": "Kd",
        "kf": "Kf",
    }.get(key, key)


def _formula_text(context: Dict[str, Any], symbolic: bool = True) -> str:
    profile = context.get("formula_profile") or _formula_profile(context.get("usage") or "", context.get("frontage_mode") or "")
    usage = _normalize_usage(context.get("usage") or "")
    if usage == "商业服务业用地" and symbolic:
        route_formula = "P商=路线价×Ky×Kv×Kt×Ks×Ka×Kc×Kk×Kd×Ku＋Kf"
        non_street_formula = "P商=级别基准地价×（1+∑Ki）×Ky×Kv×Kt×Ks×Ka×Ku＋Kf"
        mode = str(profile.get("frontage_mode") or "")
        if mode == "route_price_plus_non_street":
            return f"1、商业服务业用地（临街）\n{route_formula}\n2、商业服务业用地（不临街）\n{non_street_formula}"
        if mode == "street_route_price":
            return f"1、商业服务业用地（临街）\n{route_formula}"
        return f"2、商业服务业用地（不临街）\n{non_street_formula}"
    if _is_split_frontage(profile):
        if symbolic:
            return "临街：P商=路线价×Ky×Kv×Kt×Ks×Ka×Kc×Kk×Kd×Ku＋Kf\n不临街：P商=级别基准地价×（1+∑Ki）×Ky×Kv×Kt×Ks×Ka×Ku＋Kf"
        return "P商=(P临×A临＋P不临×A不临)÷A商"
    labels = []
    for key in profile.get("factors") or []:
        if key == "kf":
            continue
        labels.append(_factor_symbol(key))
    expression = "×".join(labels)
    if "kf" in (profile.get("factors") or []):
        expression = f"{expression}＋Kf"
    return f"{profile.get('symbol') or 'P'}={expression}" if symbolic else expression


def _level_display(level: str, *, roman: bool = False) -> str:
    text = str(level or "").strip()
    return LEVEL_ROMAN.get(text, text) if roman else text


def _area_mode(data: Dict[str, Any], analysis: Dict[str, Any], usage: str) -> str:
    params = _analysis_parameters(analysis)
    raw = str(
        data.get("land_area_mode")
        or analysis.get("land_area_mode")
        or params.get("land_area_mode")
        or ""
    ).strip()
    if raw in {"apportioned", "分摊", "分摊土地使用权面积"}:
        return "apportioned"
    if raw in {"whole", "整宗", "整宗土地面积", "土地面积", "宗地面积"}:
        return "whole"
    if _normalize_usage(usage) == "居住用地" and (data.get("building_area") or data.get("room_detail_location")):
        return "apportioned"
    return "whole"


def _area_label(mode: str, *, sentence: bool = False) -> str:
    if mode == "apportioned":
        return "分摊土地使用权面积"
    return "宗地面积" if sentence else "整宗土地面积"


def _usage_for_connotation(usage: str, coverage_scope: str) -> str:
    normalized = _normalize_usage(usage)
    if coverage_scope == "乡镇" and normalized in {"工矿用地", "仓储用地"}:
        return "工矿、仓储用地"
    return CONNOTATION_USAGE_KEYS.get(normalized, normalized)


def _format_date_for_report(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("-", ".")


def _formula_value_text(context: Dict[str, Any]) -> str:
    profile = context.get("formula_profile") or _formula_profile(context.get("usage") or "", context.get("frontage_mode") or "")
    if _is_split_frontage(profile):
        route_price = _trim(context.get("route_component_price") or D0)
        non_street_price = _trim(context.get("non_street_component_price") or D0)
        frontage_area = _trim(context.get("frontage_area_m2") or D0)
        non_frontage_area = _trim(context.get("non_frontage_area_m2") or D0)
        commercial_area = _trim(context.get("commercial_area_m2") or D0)
        return f"({route_price}×{frontage_area}+{non_street_price}×{non_frontage_area})÷{commercial_area}"
    value_map = {
        "base": _trim(context["base_price"]),
        "route_price": _trim(context.get("route_price") or D0),
        "ki": f"（1+{_percent4_text(context['sum_ki'])}%）",
        "ky": _factor_text(context["ky"]),
        "kv": _factor_text(context["kv"]),
        "kt": _factor_text(context["kt"]),
        "ks": _trim(context["ks"]),
        "ka": _trim(context["ka"]),
        "ke": _trim(context["ke"]),
        "kto": _trim(context["kto"]),
        "ku": _factor_text(context.get("ku") or D1),
        "kc": _factor_text(context.get("kc") or D1),
        "kk": _factor_text(context.get("kk") or D1),
        "kd": _factor_text(context.get("kd") or D1),
    }
    values = [value_map[key] for key in profile.get("factors") or [] if key not in {"kf"} and key in value_map]
    expression = "×".join(values)
    if "kf" in (profile.get("factors") or []):
        expression = f"{expression}+{_trim(context['kf'])}"
    return expression


def _load_config(base_dir: str) -> Dict[str, Any]:
    fallback = _load_json_config_cached(Path(base_dir) / BENCHMARK_CONFIG)
    return build_tongdao_benchmark_config(base_dir, fallback)


def _config_applies(config: Dict[str, Any], county_name: str) -> bool:
    if not county_name:
        return False
    candidates = [config.get("county") or ""] + list(config.get("county_aliases") or [])
    return any(_county_matches(county_name, alias) for alias in candidates if alias)


def _analysis_parameters(analysis: Dict[str, Any]) -> Dict[str, Any]:
    params = analysis.get("parameters") or {}
    if isinstance(params, dict):
        return params
    if isinstance(params, list):
        return {
            str(item.get("key") or ""): item.get("value")
            for item in params
            if isinstance(item, dict) and item.get("key")
        }
    return {}


def _infer_township_grade(config: Dict[str, Any], analysis: Dict[str, Any], data: Dict[str, Any]) -> str:
    direct = str(
        analysis.get("township_grade")
        or data.get("township_grade")
        or data.get("benchmark_township_grade")
        or ""
    ).strip()
    if direct:
        return direct.replace("乡镇", "")
    candidates = " ".join(
        str(value or "")
        for value in [
            analysis.get("township_name"),
            data.get("township_name"),
            data.get("town_name"),
            data.get("land_location_short"),
            data.get("land_location_full"),
            data.get("location"),
        ]
    )
    for town, grade in (config.get("township_grade_aliases") or {}).items():
        if town and town in candidates:
            return str(grade or "").replace("乡镇", "")
    return ""


def _base_price_lookup(config: Dict[str, Any], coverage_scope: str, usage: str, level: str, township_grade: str) -> Decimal:
    if coverage_scope == "乡镇":
        return _decimal(
            (((config.get("township_base_land_price") or {}).get(township_grade) or {}).get(usage) or {}).get(level)
        )
    return _decimal(((config.get("base_land_price") or {}).get(usage) or {}).get(level))


def _route_segment_lookup(config: Dict[str, Any], segment_id: str) -> Dict[str, Any]:
    if not segment_id:
        return {}
    for row in config.get("route_price_segments") or []:
        if str(row.get("id") or row.get("code") or "").strip() == str(segment_id).strip():
            return row
    return {}


def _road_type_from_text(value: Any) -> str:
    text = str(value or "").replace(" ", "")
    if "主干道" in text:
        return "主干道"
    if "次干道" in text:
        return "次干道"
    if "支路" in text:
        return "支路"
    return text.strip()


def _bucket_value(bucket: str, value: Decimal) -> bool:
    text = str(bucket or "").replace(" ", "")
    if not text or value <= D0:
        return False
    if text.startswith("≤"):
        return value <= _decimal(text[1:])
    if text.startswith("<"):
        return value < _decimal(text[1:])
    if text.startswith("≥"):
        return value >= _decimal(text[1:])
    if text.startswith(">"):
        return value > _decimal(text[1:])
    if "-" in text:
        lo, hi = text.split("-", 1)
        return _decimal(lo) < value <= _decimal(hi) if text.startswith("(") else _decimal(lo) <= value <= _decimal(hi)
    return value == _decimal(text)


def _coefficient_by_bucket(table: Dict[str, Any], road_type: str, value: Decimal) -> Decimal:
    buckets = list(table.get("buckets") or [])
    rows = list(table.get("rows") or [])
    road = _road_type_from_text(road_type)
    row = next((item for item in rows if _road_type_from_text(item.get("road_type")) == road), {})
    coefficients = list(row.get("coefficients") or [])
    for index, bucket in enumerate(buckets):
        if index < len(coefficients) and coefficients[index] not in {"", "/"} and _bucket_value(bucket, value):
            return _decimal(coefficients[index])
    return D0


def _ku_options(table: Dict[str, Any]) -> List[Dict[str, str]]:
    grades = list(table.get("grades") or [])
    descriptions = list(table.get("descriptions") or [])
    coefficients = list(table.get("coefficients") or [])
    return [
        {
            "label": grade,
            "grade": grade,
            "description": descriptions[index] if index < len(descriptions) else "",
            "coefficient": coefficients[index] if index < len(coefficients) else "",
        }
        for index, grade in enumerate(grades)
    ]


def _ku_coefficient(table: Dict[str, Any], grade: str) -> Decimal:
    for option in _ku_options(table):
        if option.get("grade") == grade:
            return _decimal(option.get("coefficient"))
    return D0


def _corner_coefficient(table: Dict[str, Any], ratio: Decimal) -> Decimal:
    if ratio <= D0:
        return D0
    buckets = list(table.get("buckets") or [])
    coefficients = list(table.get("coefficients") or [])
    for index, bucket in enumerate(buckets):
        text = str(bucket or "").replace(" ", "")
        if not text:
            continue
        if text.startswith(">") and ratio > _decimal(text[1:].replace("/1", "")):
            return _decimal(coefficients[index]) if index < len(coefficients) else D0
        match = text.strip("()[]").split(",")
        if len(match) == 2:
            lo = _decimal(match[0].replace("/1", ""))
            hi = _decimal(match[1].replace("/1", ""))
            if lo < ratio <= hi:
                return _decimal(coefficients[index]) if index < len(coefficients) else D0
    return D0


def _base_plot_ratio_from_table(table: Dict[str, Any], level: str) -> str:
    levels = list(table.get("levels") or [])
    if level not in levels:
        return ""
    col = levels.index(level)
    best: tuple[Decimal, str] | None = None
    for row in table.get("rows") or []:
        values = row.get("values") or []
        if len(values) <= col:
            continue
        diff = abs(_decimal(values[col]) - D1)
        ratio = str(row.get("ratio") or "").strip()
        if not ratio:
            continue
        if best is None or diff < best[0]:
            best = (diff, ratio)
    return best[1] if best else ""


def _base_connotation_rows(config: Dict[str, Any], coverage_scope: str, usage: str, township_grade: str) -> List[Dict[str, Any]]:
    structured = ((config.get("base_price_connotation_tables") or {}).get("township" if coverage_scope == "乡镇" else "city") or {})
    if structured:
        usage_key = _usage_for_connotation(usage, coverage_scope)
        rows: List[Dict[str, Any]] = []
        for raw in structured.get("rows") or []:
            if coverage_scope == "乡镇" and township_grade and str(raw.get("等别") or "").replace("乡镇", "") != township_grade.replace("乡镇", ""):
                continue
            rows.append({
                "level": raw.get("级别", ""),
                "term": raw.get(f"{usage_key}_使用年期", ""),
                "plot_ratio": raw.get(f"{usage_key}_容积率", ""),
                "development": raw.get("开发程度", ""),
                "base_date": raw.get("估价期日", ""),
            })
        if rows:
            common_development = next((str(row.get("development") or "") for row in rows if row.get("development")), "")
            common_base_date = next((str(row.get("base_date") or "") for row in rows if row.get("base_date")), "")
            common_term = next((str(row.get("term") or "") for row in rows if row.get("term")), "")
            for row in rows:
                row["development"] = row.get("development") or common_development
                row["base_date"] = row.get("base_date") or common_base_date
                row["term"] = row.get("term") or common_term
            return rows

    raw = config.get("base_price_connotation") or {}
    base_rows = list(raw.get("rows") or [])
    levels = ["一级", "二级", "三级"] if coverage_scope == "乡镇" else list(raw.get("levels") or ["一级", "二级", "三级", "四级", "五级"])
    statutory = _statutory_max_term(config, usage)
    statutory_text = f"{_trim(statutory)}年" if statutory > D0 else ""
    can_use_residential_fallback = _normalize_usage(usage) == "居住用地" and coverage_scope == "城区"
    common_development = str(
        raw.get("development")
        or (base_rows[0].get("development") if base_rows else "")
        or "五通一平"
    ).strip()
    base_date = str(
        raw.get("base_date")
        or (base_rows[0].get("base_date") if base_rows else "")
        or ((config.get("policy_document") or {}).get("base_date") or "")
    ).strip()
    plot_table = _plot_ratio_config(config, coverage_scope, usage, township_grade)
    rows: List[Dict[str, Any]] = []
    for level in levels:
        existing = next((row for row in base_rows if str(row.get("level") or "").strip() == level), {})
        fallback_plot_ratio = str(existing.get("plot_ratio") or "").strip() if can_use_residential_fallback else ""
        fallback_term = str(existing.get("term") or "").strip() if can_use_residential_fallback else ""
        plot_ratio = _base_plot_ratio_from_table(plot_table, level) or fallback_plot_ratio
        rows.append({
            "level": level,
            "term": statutory_text or fallback_term,
            "plot_ratio": plot_ratio,
            "development": common_development,
            "base_date": base_date,
        })
    return rows


def _base_connotation_row(config: Dict[str, Any], coverage_scope: str, usage: str, township_grade: str, level: str) -> Dict[str, Any]:
    rows = _base_connotation_rows(config, coverage_scope, usage, township_grade)
    for row in rows:
        if str(row.get("level") or "").strip() == str(level or "").strip():
            return row
    return rows[0] if rows else {}


def _base_connotation_table_section(config: Dict[str, Any], coverage_scope: str, township_grade: str) -> Optional[Dict[str, Any]]:
    table = ((config.get("base_price_connotation_tables") or {}).get("township" if coverage_scope == "乡镇" else "city") or {})
    usage_keys = [
        "商业服务业用地",
        "居住用地",
        "工矿用地",
        "仓储用地",
        "公共管理与公共服务用地",
        "公用设施用地",
    ]
    title_scope = "乡镇" if coverage_scope == "乡镇" else "城区"
    if table:
        rows = list(table.get("rows") or [])
        if coverage_scope == "乡镇" and township_grade:
            rows = [
                row for row in rows
                if str(row.get("等别") or "").replace("乡镇", "") == township_grade.replace("乡镇", "")
            ] or rows
        return {
            "key": "benchmark_base_connotation_table",
            "title": "基准地价内涵",
            "report_title": f"表3-1 通道县{title_scope}基准地价内涵",
            "columns": list(table.get("columns") or []),
            "header_rows": list(table.get("header_rows") or []),
            "rows": rows,
            "source_target": "benchmark_corr_analysis",
        }

    raw = config.get("base_price_connotation") or {}
    if coverage_scope == "乡镇":
        levels = ["一级", "二级", "三级"]
    else:
        levels = list(raw.get("levels") or [])
        if not levels:
            for price_by_level in (config.get("base_land_price") or {}).values():
                levels = list(price_by_level.keys())
                break
        levels = levels or ["一级", "二级", "三级", "四级", "五级"]

    columns = ["级别", "土地权利"]
    for usage_key in usage_keys:
        columns.extend([f"{usage_key}_使用年期", f"{usage_key}_容积率"])
    columns.extend(["开发程度", "估价期日"])
    header_rows = [
        [
            {"label": "级别", "rowspan": 2, "colspan": 1},
            {"label": "土地权利", "rowspan": 2, "colspan": 1},
            *({"label": usage_key, "rowspan": 1, "colspan": 2} for usage_key in usage_keys),
            {"label": "开发程度", "rowspan": 2, "colspan": 1},
            {"label": "估价期日", "rowspan": 2, "colspan": 1},
        ],
        [
            *(
                cell
                for _usage_key in usage_keys
                for cell in (
                    {"label": "使用年期", "rowspan": 1, "colspan": 1},
                    {"label": "容积率", "rowspan": 1, "colspan": 1},
                )
            ),
        ],
    ]

    rows: List[Dict[str, Any]] = []
    for level in levels:
        row: Dict[str, Any] = {"级别": level, "土地权利": "出让土地使用权"}
        common_development = ""
        common_base_date = ""
        for usage_key in usage_keys:
            connotation = _base_connotation_row(config, coverage_scope, usage_key, township_grade, level)
            row[f"{usage_key}_使用年期"] = connotation.get("term") or ""
            row[f"{usage_key}_容积率"] = connotation.get("plot_ratio") or ""
            common_development = common_development or str(connotation.get("development") or "")
            common_base_date = common_base_date or str(connotation.get("base_date") or "")
        row["开发程度"] = common_development
        row["估价期日"] = common_base_date
        rows.append(row)

    note = (
        "注：1、本次土地用途根据《国土空间调查、规划、用途管制用地用海分类指南》进行分类，"
        "商业服务业用地对应上轮基准地价用途中的商服用地，居住用地对应住宅用地，"
        "工矿用地、仓储用地分别对应工矿仓储用地，公共管理与公共服务用地、公用设施用地按相应用途内涵确定。"
        "2、五通一平指红线外通路、通电、通讯、通上水、通下水，红线内场地平整。"
    )
    rows.append({"级别": note})
    return {
        "key": "benchmark_base_connotation_table",
        "title": "基准地价内涵",
        "report_title": f"表3-1 通道县{title_scope}基准地价内涵",
        "columns": columns,
        "header_rows": header_rows,
        "rows": rows,
        "source_target": "benchmark_corr_analysis",
        "group_columns": [1],
    }


def _same_development_degree(base: str, current: str) -> bool:
    def norm(value: str) -> str:
        text = str(value or "")
        if "七通" in text:
            return "七通一平"
        if "五通" in text:
            return "五通一平"
        if "三通" in text:
            return "三通一平"
        return text.strip()

    return bool(norm(base) and norm(base) == norm(current))


def _plot_ratio_config(config: Dict[str, Any], coverage_scope: str, usage: str, township_grade: str) -> Dict[str, Any]:
    tables = config.get("plot_ratio_table") or {}
    if coverage_scope == "乡镇":
        return (((tables.get("__township__") or {}).get(usage) or {}).get(township_grade) or {})
    return tables.get(usage) or {}


def _months_between(base_date, target_date) -> Decimal:
    """期日修正历时（月）：整月差 + 日差/30。范例 2025-04-01→2026-06-03 = 14.07 月。"""
    months = (target_date.year - base_date.year) * 12 + (target_date.month - base_date.month)
    day_fraction = Decimal(target_date.day - base_date.day) / Decimal("30")
    return Decimal(months) + day_fraction


def _interpolate_plot_ratio(table: Dict[str, Any], level: str, plot_ratio: Decimal) -> Optional[Decimal]:
    levels = list(table.get("levels") or [])
    if level not in levels:
        return None
    col = levels.index(level)
    rows = [
        (Decimal(str(row.get("ratio"))), Decimal(str((row.get("values") or [])[col])))
        for row in table.get("rows") or []
        if row.get("values") and len(row["values"]) > col
    ]
    if not rows:
        return None
    rows.sort(key=lambda item: item[0])
    if plot_ratio <= rows[0][0]:
        return rows[0][1]
    if plot_ratio >= rows[-1][0]:
        return rows[-1][1]
    for (lo_ratio, lo_val), (hi_ratio, hi_val) in zip(rows, rows[1:]):
        if lo_ratio <= plot_ratio <= hi_ratio:
            if hi_ratio == lo_ratio:
                return lo_val
            span = (plot_ratio - lo_ratio) / (hi_ratio - lo_ratio)
            return lo_val + span * (hi_val - lo_val)
    return rows[-1][1]


def _term_factor(rate: Decimal, m: Decimal, n: Decimal) -> Decimal:
    """年期修正 Kn=[1-1/(1+r)^m]/[1-1/(1+r)^n]。"""
    r = float(rate)
    mf = float(m)
    nf = float(n)
    numerator = 1 - 1 / ((1 + r) ** mf)
    denominator = 1 - 1 / ((1 + r) ** nf)
    if denominator == 0:
        return D1
    return Decimal(str(numerator / denominator))


def _date_factor(monthly_rate: Decimal, months: Decimal) -> Decimal:
    """期日修正 Kt=(1+月上涨率)^月数。"""
    rate = float(monthly_rate)
    return Decimal(str((1 + rate) ** float(months)))


def calculate_benchmark_correction(data: Dict[str, Any], base_dir: Optional[str] = None) -> Dict[str, Any]:
    base_dir = base_dir or _base_dir()
    config = _load_config(base_dir)
    county_name = str(data.get("county_name") or data.get("county") or "").strip()
    analysis = dict(data.get("benchmark_corr_analysis") or {})
    analysis_params = _analysis_parameters(analysis)

    warnings: List[Dict[str, str]] = []
    if not config:
        warnings.append({"level": "warning", "message": "未找到基准地价配置文件（tongdao_benchmark_land_price.json）。"})
        return _empty_result(warnings)
    if not _config_applies(config, county_name):
        return _unsupported_result(
            f"当前县市「{county_name or '待填写'}」暂无可用的基准地价系数修正法结构化配置；本阶段仅适配通道县，不按通道县数据试算。",
            config,
        )

    def pick(key: str, default: Any = "") -> Any:
        for source in (analysis, analysis_params, data):
            value = source.get(key)
            if value not in (None, ""):
                return value
        return default

    def pick_analysis(*keys: str) -> Any:
        for key in keys:
            for source in (analysis, analysis_params):
                value = source.get(key)
                if value not in (None, ""):
                    return value
        return ""

    def pick_data(*keys: str) -> Any:
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return value
        return ""

    coverage_scope = str(pick("coverage_scope") or "").strip() or ("乡镇" if pick("township_grade") or pick("township_name") else "城区")
    township_grade = _infer_township_grade(config, analysis, data)
    if coverage_scope == "乡镇" and not township_grade:
        warnings.append({"level": "warning", "message": "乡镇基准地价需先确定乡镇等别。", "target": "benchmark_corr_analysis.township_grade"})

    usage = _normalize_usage(
        pick_analysis("land_use_type", "land_usage", "land_usage_price_class", "land_usage_key")
        or pick_data("land_usage_price_class", "land_use_type", "land_usage", "land_usage_key")
    )
    level = str(pick_analysis("land_level") or pick_data("land_level") or "").strip()
    frontage_mode = _normalize_frontage_mode(pick_analysis("frontage_mode") or pick_data("frontage_mode"))
    plot_ratio = _decimal(
        pick_data("set_plot_ratio", "set_plot_ratio_display", "plot_ratio")
        or pick_analysis("plot_ratio", "set_plot_ratio", "set_plot_ratio_display")
    )
    land_use_term = _decimal(
        pick_data("land_use_term_years", "land_use_term", "set_term_years")
        or pick_analysis("land_use_term", "set_term_years", "land_use_term_years")
    )
    land_area = _decimal(pick_analysis("land_area") or pick_data("land_area"))
    area_mode = _area_mode(data, analysis, usage)
    area_label = _area_label(area_mode)
    area_sentence_label = _area_label(area_mode, sentence=True)

    valuation_date_text = pick_data("valuation_date") or pick_analysis("valuation_date")
    valuation_date = _date(valuation_date_text)
    base_date_text = (
        pick_analysis("base_date")
        or ((analysis_params.get("parameters") or {}) if isinstance(analysis_params.get("parameters"), dict) else {}).get("base_date")
        or (config.get("policy_document") or {}).get("base_date")
    )
    base_date = _date(base_date_text)
    missing: List[str] = []
    if not usage:
        missing.append("土地用途未匹配到通道县基准地价用途")
    if not level:
        missing.append("土地级别未选择")
    formula_profile = _formula_profile(usage, frontage_mode)

    # 级别基准地价 Po
    base_price = _base_price_lookup(config, coverage_scope, usage, level, township_grade)
    if base_price <= D0 and _formula_has(formula_profile, "base"):
        missing.append(f"未取得「{coverage_scope}{township_grade}{usage}{level}」级别基准地价")

    # 商业服务业用地临街路线价 Po
    route_segment_id = str(pick_analysis("route_segment_id") or pick_data("route_segment_id") or "").strip()
    route_segment = _route_segment_lookup(config, route_segment_id)
    route_price_input = pick_analysis("route_price", "route_price_override") or pick_data("route_price", "route_price_override")
    route_price_source_note = str(
        pick_analysis("route_price_source_note", "route_price_override_reason")
        or pick_data("route_price_source_note", "route_price_override_reason")
        or ""
    ).strip()
    route_price = _decimal(route_segment.get("route_price") or route_price_input)
    route_price_source = "route_table" if route_segment else ("manual" if route_price > D0 else "")
    if _formula_has(formula_profile, "route_price"):
        if route_price <= D0:
            missing.append("临街路线价Po未匹配或未填写")
        elif route_price_source == "manual" and not route_price_source_note:
            missing.append("人工填写路线价Po需补充来源说明")

    # Kv 容积率修正（内插）
    pr_config = _plot_ratio_config(config, coverage_scope, usage, township_grade)
    use_kv = _formula_has(formula_profile, "kv")
    kv_raw = _interpolate_plot_ratio(pr_config, level, plot_ratio) if (pr_config and plot_ratio > D0) else None
    kv = _qfactor(kv_raw) if (use_kv and kv_raw is not None) else D1
    if use_kv and not pr_config:
        missing.append(f"未取得「{coverage_scope}{township_grade}{usage}」容积率修正系数表")
    elif use_kv and plot_ratio <= D0:
        missing.append("容积率未填写，无法进行容积率修正")
    elif use_kv and kv_raw is None:
        missing.append(f"容积率{_trim(plot_ratio)}未匹配「{coverage_scope}{township_grade}{usage}」容积率修正系数表（级别或区间缺失）")

    # Ky 年期修正
    cap_rate = _decimal((config.get("cap_rate") or {}).get(usage)) / Decimal("100")
    statutory_term = _statutory_max_term(config, usage)
    if statutory_term <= D0:
        missing.append(f"未匹配「{usage or '待校核'}」法定最高出让年期")
    if land_use_term <= D0:
        missing.append("设定土地使用年期未填写，无法进行年期修正")
    if cap_rate <= D0 and land_use_term > D0 and statutory_term > D0 and land_use_term != statutory_term:
        missing.append(f"未取得「{usage}」土地还原率，无法进行年期修正")
    ky = _qfactor(_term_factor(cap_rate, land_use_term, statutory_term)) if cap_rate > D0 and land_use_term > D0 else D1

    # Kt 期日修正
    monthly_rate_raw = (
        pick_analysis("monthly_growth_rate")
        or (analysis_params.get("monthly_growth_rate") if isinstance(analysis_params, dict) else "")
        or (config.get("date_adjustment") or {}).get("monthly_growth_rate")
    )
    monthly_rate = _decimal(monthly_rate_raw) / Decimal("100")
    months_input = pick_analysis("months_elapsed")
    months = _decimal(months_input) if months_input not in (None, "") else (_months_between(base_date, valuation_date) if (base_date and valuation_date) else D0)
    if not valuation_date:
        missing.append("估价期日未填写，无法计算期日修正")
    kt = _qfactor(_date_factor(monthly_rate, months)) if months > D0 else D1

    # ∑Ki 区域因素修正
    if _formula_has(formula_profile, "ki"):
        region_rows, sum_ki, region_missing = _resolve_region_factors(config, usage, level, analysis, coverage_scope, township_grade)
        missing.extend(region_missing)
        sum_ki = _qpercent(sum_ki)
    else:
        region_rows, sum_ki = [], D0
    ki_multiplier = D1 + sum_ki / Decimal("100") if _formula_has(formula_profile, "ki") else D1

    # Ks 面积修正
    individual_factors = analysis.get("individual_factors") or {}
    ks_grade = str(
        pick_analysis("area_grade")
        or ((individual_factors.get("area") or {}).get("grade"))
        or ((individual_factors.get("area") or {}).get("level"))
        or pick_data("area_grade")
        or ""
    ).strip()
    area_table = (config.get("area_table") or {}).get(usage) or {}
    ks = _grade_coefficient(area_table, ks_grade)
    if not ks_grade:
        missing.append("宗地面积优劣度未确认")
    elif ks_grade not in (area_table.get("grades") or []):
        missing.append(f"宗地面积优劣度「{ks_grade}」未匹配到面积修正系数Ks")

    # Ka 形状修正
    ka_grade = str(
        pick_analysis("shape_grade")
        or ((individual_factors.get("shape") or {}).get("grade"))
        or ((individual_factors.get("shape") or {}).get("level"))
        or pick_data("shape_grade")
        or ""
    ).strip()
    shape_table = config.get("shape_table") or {}
    ka = _shape_coefficient(shape_table, usage, ka_grade)
    if not ka_grade:
        missing.append("宗地形状优劣度未确认")
    elif ka_grade not in (shape_table.get("grades") or []):
        missing.append(f"宗地形状优劣度「{ka_grade}」未匹配到形状修正系数Ka")

    # Ke 景观修正
    ke_grade = str(
        pick_analysis("landscape_grade")
        or ((individual_factors.get("landscape") or {}).get("grade"))
        or ((individual_factors.get("landscape") or {}).get("level"))
        or pick_data("landscape_grade")
        or ""
    ).strip()
    landscape_table = config.get("landscape_table") or {}
    ke = _landscape_coefficient(landscape_table, ke_grade) if _formula_has(formula_profile, "ke") else D1
    if _formula_has(formula_profile, "ke"):
        if not ke_grade:
            missing.append("景观环境优劣度未确认")
        elif ke_grade not in (landscape_table.get("grades") or []):
            missing.append(f"景观环境优劣度「{ke_grade}」未匹配到景观修正系数Ke")

    # Kto 朝向修正
    orientation = str(
        pick_analysis("orientation")
        or ((individual_factors.get("orientation") or {}).get("grade"))
        or ((individual_factors.get("orientation") or {}).get("level"))
        or pick_data("orientation")
        or ""
    ).strip()
    orientation_table = config.get("orientation_table") or {}
    kto = _orientation_coefficient(orientation_table, orientation) if _formula_has(formula_profile, "kto") else D1
    if _formula_has(formula_profile, "kto"):
        if not orientation:
            missing.append("建筑物朝向未确认")
        elif not _orientation_matched(orientation_table, orientation):
            missing.append(f"建筑物朝向「{orientation}」未匹配到朝向修正系数Kto")

    # 商业服务业用地专属修正：Ku、Kc、Kk、Kd
    ku_grade = str(
        pick_analysis("ku_grade", "surrounding_land_use_grade")
        or pick_data("ku_grade", "surrounding_land_use_grade")
        or ""
    ).strip()
    ku_table = config.get("surrounding_land_use_table") or {}
    ku = _ku_coefficient(ku_table, ku_grade) if _formula_has(formula_profile, "ku") else D1
    if _formula_has(formula_profile, "ku") and not ku_grade:
        missing.append("周边土地利用类型Ku未确认")
    elif _formula_has(formula_profile, "ku") and ku <= D0:
        missing.append("周边土地利用类型Ku未匹配到修正系数")

    route_road_grade = str(
        pick_analysis("route_road_grade", "road_grade", "planning_road_grade")
        or pick_data("route_road_grade", "road_grade", "planning_road_grade")
        or ""
    ).strip()
    route_road_type_source = (
        route_segment.get("road_type")
        if route_segment
        else (
            pick_analysis("route_road_type", "road_type")
            or pick_data("route_road_type", "road_type")
            or route_road_grade
        )
    )
    route_road_type = _road_type_from_text(route_road_type_source)
    route_road_type_source_name = "路线价段" if route_segment and route_segment.get("road_type") else ("规划道路等级匹配" if route_road_grade and route_road_type else ("人工填写" if route_road_type else ""))
    frontage_relation = _normalize_frontage_relation(pick_analysis("frontage_relation") or pick_data("frontage_relation"))
    frontage_width_m = _decimal(pick_analysis("frontage_width_m") or pick_data("frontage_width_m"))
    frontage_depth_input = _decimal(pick_analysis("frontage_depth_m") or pick_data("frontage_depth_m"))
    commercial_area_m2 = _decimal(pick_analysis("commercial_area_m2", "commercial_area") or pick_data("commercial_area_m2", "commercial_area")) or land_area
    standard_depth_raw = (
        route_segment.get("standard_depth")
        or pick_analysis("frontage_standard_depth_m", "standard_depth")
        or pick_data("frontage_standard_depth_m", "standard_depth")
        or {"主干道": "20", "次干道": "16", "支路": "12"}.get(route_road_type, "")
    )
    frontage_standard_depth_m = _decimal(standard_depth_raw)
    adjacent_derived_depth_m = (
        (commercial_area_m2 / frontage_width_m).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if commercial_area_m2 > D0 and frontage_width_m > D0
        else D0
    )
    frontage_depth_source = "manual" if frontage_relation == "setback" else "auto_by_area_width"
    frontage_depth_m = frontage_depth_input if frontage_relation == "setback" else adjacent_derived_depth_m
    frontage_area_m2 = D0
    non_frontage_area_m2 = D0
    if _is_split_frontage(formula_profile):
        if commercial_area_m2 <= D0:
            missing.append("商服总面积未填写，无法进行临街/不临街拆分")
        if frontage_standard_depth_m <= D0:
            missing.append("路线价段标准深度未匹配，无法计算临街商服用地面积")
        if frontage_width_m <= D0:
            missing.append("临街宽度未填写，无法计算临街商服用地面积")
        if frontage_relation == "setback" and frontage_depth_m <= D0:
            missing.append("非紧邻道路时需填写有效临街深度")
        if (
            frontage_relation == "setback"
            and frontage_depth_m > D0
            and frontage_standard_depth_m > D0
            and frontage_depth_m > frontage_standard_depth_m
        ):
            missing.append("非紧邻道路且有效临街深度大于标准深度，不宜采用路线价测算")
        split_depth_for_area = (
            frontage_depth_m
            if frontage_relation == "setback" and D0 < frontage_depth_m <= frontage_standard_depth_m
            else frontage_standard_depth_m
        )
        if commercial_area_m2 > D0 and split_depth_for_area > D0 and frontage_width_m > D0:
            frontage_area_m2 = (split_depth_for_area * frontage_width_m).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            non_frontage_area_m2 = (commercial_area_m2 - frontage_area_m2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if frontage_area_m2 <= D0:
                missing.append("临街商服用地面积未能计算")
            if non_frontage_area_m2 < D0:
                missing.append("临街商服用地面积大于商服总面积，请核对标准深度、临街宽度和商服总面积")
    kd = D1
    kk = D1
    kc = D1
    frontage_depth_table = config.get("frontage_depth_table") or {}
    frontage_width_table = config.get("frontage_width_table") or {}
    corner_table = config.get("corner_coefficient_table") or {}
    if _formula_has(formula_profile, "kd"):
        if not frontage_depth_table:
            missing.append("未取得通道县城区临街深度修正系数表，无法计算Kd")
        kd = _coefficient_by_bucket(frontage_depth_table, route_road_type, frontage_depth_m)
        if kd <= D0 and frontage_standard_depth_m > D0 and frontage_depth_m >= frontage_standard_depth_m:
            kd = D1
        if not route_road_type:
            missing.append("临街道路类型未确认，无法计算Kd")
        if frontage_width_m <= D0:
            missing.append("临街宽度未填写，无法计算临街深度及Kd")
        if frontage_relation == "setback" and frontage_depth_m <= D0:
            missing.append("非紧邻道路时需填写有效临街深度，无法计算Kd")
        if frontage_depth_m <= D0:
            missing.append("临街深度未填写，无法计算Kd")
        elif frontage_depth_table and kd <= D0:
            missing.append("临街深度Kd未匹配到修正系数")
        if (
            _normalize_frontage_mode(frontage_mode) == "street_route_price"
            and frontage_standard_depth_m > D0
            and frontage_depth_m > frontage_standard_depth_m
        ):
            if frontage_relation == "adjacent":
                missing.append("临街深度大于标准深度，不应按整宗路线价测算，请切换为临街+不临街拆分路径")
            else:
                missing.append("有效临街深度大于标准深度，不宜采用路线价测算")
    if _formula_has(formula_profile, "kk"):
        if not frontage_width_table:
            missing.append("未取得通道县城区临街宽度修正系数表，无法计算Kk")
        kk = _coefficient_by_bucket(frontage_width_table, route_road_type, frontage_width_m)
        if not route_road_type:
            missing.append("临街道路类型未确认，无法计算Kk")
        if frontage_width_m <= D0:
            missing.append("临街宽度未填写，无法计算Kk")
        elif frontage_width_table and kk <= D0:
            missing.append("临街宽度Kk未匹配到修正系数")
    is_corner_raw = pick_analysis("is_corner") if pick_analysis("is_corner") not in (None, "") else pick_data("is_corner")
    is_corner = str(is_corner_raw).strip().lower() in {"1", "true", "yes", "是", "街角", "y"}
    corner_route_price_a = _decimal(pick_analysis("corner_route_price_a") or pick_data("corner_route_price_a"))
    corner_route_price_b = _decimal(pick_analysis("corner_route_price_b") or pick_data("corner_route_price_b"))
    corner_main_route_price = D0
    corner_side_route_price = D0
    if corner_route_price_a > D0 and corner_route_price_b > D0:
        corner_main_route_price = max(corner_route_price_a, corner_route_price_b)
        corner_side_route_price = min(corner_route_price_a, corner_route_price_b)
        corner_price_ratio = _qfactor(corner_main_route_price / corner_side_route_price) if corner_side_route_price > D0 else D0
    else:
        corner_price_ratio = _decimal(pick_analysis("corner_price_ratio") or pick_data("corner_price_ratio"))
    corner_coefficient_input = _decimal(pick_analysis("corner_coefficient", "kc") or pick_data("corner_coefficient", "kc"))
    if _formula_has(formula_profile, "kc") and not corner_table:
        missing.append("未取得通道县城区街角地修正系数表，无法计算Kc")
    if _formula_has(formula_profile, "kc") and is_corner:
        if corner_price_ratio <= D0:
            missing.append("街角地相邻两条路线价未填写，无法计算正街/旁街比例及Kc")
        kc = corner_coefficient_input if corner_coefficient_input > D0 else _corner_coefficient(corner_table, corner_price_ratio)
        if kc <= D0:
            missing.append("街角地Kc未确认")

    # Kf 开发程度修正额：只有设定开发程度与基准内涵一致，或用户显式填写修正额时才可确认。
    connotation = _base_connotation_row(config, coverage_scope, usage, township_grade, level)
    base_development = str((connotation or {}).get("development") or "").strip()
    set_development = str(
        pick_data("land_development_set", "set_development", "land_development_actual")
        or pick_analysis("set_development", "land_development_set", "development_condition")
        or ""
    ).strip()
    kf_input = pick_analysis("development_adjustment", "kf") or pick_data("development_adjustment", "kf")
    development_note = str(pick_analysis("development_note") or pick_data("development_note") or "").strip()
    if kf_input not in (None, ""):
        kf = _decimal(kf_input)
    elif base_development and set_development and _same_development_degree(base_development, set_development):
        kf = D0
        development_note = (
            development_note
            or f"根据{(config.get('policy_document') or {}).get('name') or '通道县城镇基准地价更新技术报告'}，"
            f"估价对象对应级别基准地价内涵开发程度为{base_development}。本次评估待估宗地设定开发程度为{set_development}，"
            "二者一致，故不需进行宗地开发程度修正，即Kf=0。"
        )
    else:
        kf = D0
        missing.append("开发程度修正额未确认")
        development_note = (
            development_note
            or f"根据{(config.get('policy_document') or {}).get('name') or '通道县城镇基准地价更新技术报告'}表5.6.12，"
            "通道县土地开发费用测算范围包括道路、供水、排水、电力、电讯及场地平整等费用，合计约70-120元/平方米。"
            f"本次评估待估宗地设定开发程度为{set_development or '待校核'}，基准地价内涵开发程度为{base_development or '待校核'}，"
            "二者不一致时，应根据实际开发程度差额填写开发程度修正额Kf。"
        )

    support_status = "supported" if not missing else "incomplete"
    should_calculate_price = support_status == "supported"
    route_component_price = D0
    non_street_component_price = D0
    commercial_weighted_price = D0
    if _is_split_frontage(formula_profile):
        route_multiplier = ky * kv * kt * ks * ka * ku * kc * kk * kd
        non_street_multiplier = ki_multiplier * ky * kv * kt * ks * ka * ku
        route_component_price = _qprice(route_price * route_multiplier + kf) if should_calculate_price else D0
        non_street_component_price = _qprice(base_price * non_street_multiplier + kf) if should_calculate_price else D0
        commercial_weighted_price = (
            _qprice((route_component_price * frontage_area_m2 + non_street_component_price * non_frontage_area_m2) / commercial_area_m2)
            if should_calculate_price and commercial_area_m2 > D0
            else D0
        )
        final_price = commercial_weighted_price
    else:
        formula_base_price = route_price if _formula_has(formula_profile, "route_price") else base_price
        factor_multiplier = D1
        for factor_key, factor_value in [
            ("ki", ki_multiplier),
            ("ky", ky),
            ("kv", kv),
            ("kt", kt),
            ("ks", ks),
            ("ka", ka),
            ("ke", ke),
            ("kto", kto),
            ("ku", ku),
            ("kc", kc),
            ("kk", kk),
            ("kd", kd),
        ]:
            if _formula_has(formula_profile, factor_key):
                factor_multiplier *= factor_value
        final_price_raw = formula_base_price * factor_multiplier + kf
        final_price = _qprice(final_price_raw) if should_calculate_price else D0

    context = {
        "county_name": county_name,
        "coverage_scope": coverage_scope,
        "township_grade": township_grade,
        "usage": usage,
        "frontage_mode": frontage_mode,
        "level": level,
        "land_location_short": pick_data("land_location_short", "location_short"),
        "land_location_full": pick_data("land_location_full", "location", "land_location"),
        "plot_ratio": plot_ratio,
        "land_use_term": land_use_term,
        "land_area": land_area,
        "land_area_mode": area_mode,
        "land_area_label": area_label,
        "land_area_sentence_label": area_sentence_label,
        "valuation_date": valuation_date_text,
        "base_date": _format_date_for_report(base_date_text),
        "base_price": base_price,
        "route_price": route_price,
        "route_price_source": route_price_source,
        "route_price_source_note": route_price_source_note,
        "route_segment_id": route_segment_id,
        "route_segment": route_segment,
        "route_road_type": route_road_type,
        "route_road_grade": route_road_grade,
        "route_road_type_source": route_road_type_source_name,
        "kv": kv,
        "ky": ky,
        "kt": kt,
        "sum_ki": sum_ki,
        "ki_multiplier": ki_multiplier,
        "ks": ks,
        "ks_grade": ks_grade,
        "ka": ka,
        "ka_grade": ka_grade,
        "ke": ke,
        "ke_grade": ke_grade,
        "kto": kto,
        "orientation": orientation,
        "ku": ku,
        "ku_grade": ku_grade,
        "kd": kd,
        "kk": kk,
        "kc": kc,
        "commercial_area_m2": commercial_area_m2,
        "frontage_standard_depth_m": frontage_standard_depth_m,
        "frontage_area_m2": frontage_area_m2,
        "non_frontage_area_m2": non_frontage_area_m2,
        "frontage_average_depth_m": frontage_depth_m,
        "frontage_relation": frontage_relation,
        "frontage_depth_source": frontage_depth_source,
        "route_component_price": route_component_price,
        "non_street_component_price": non_street_component_price,
        "commercial_weighted_price": commercial_weighted_price,
        "frontage_depth_m": frontage_depth_m,
        "frontage_width_m": frontage_width_m,
        "is_corner": is_corner,
        "corner_route_price_a": corner_route_price_a,
        "corner_route_price_b": corner_route_price_b,
        "corner_main_route_price": corner_main_route_price,
        "corner_side_route_price": corner_side_route_price,
        "corner_price_ratio": corner_price_ratio,
        "kf": kf,
        "cap_rate": cap_rate,
        "statutory_term": statutory_term,
        "monthly_rate": monthly_rate,
        "months": months,
        "region_rows": region_rows,
        "final_price": final_price,
        "config": config,
        "development_note": development_note,
        "base_development": base_development,
        "set_development": set_development,
        "support_status": support_status,
        "support_missing_items": missing,
        "formula_profile": formula_profile,
    }

    result: Dict[str, Any] = {
        "parameters": _build_parameters(context),
        "parameter_rows": _build_parameter_rows(context),
        "tables": _build_tables(context),
        "results": [
            {
                "key": "benchmark_corr_price",
                "label": "基准地价系数修正法最终单价",
                "value": _trim(final_price) if should_calculate_price else "",
                "unit": "元/平方米",
                "formula": _formula_text(context, symbolic=False),
            }
        ],
        "result_values": {
            "benchmark_corr_price": _trim(final_price) if should_calculate_price else "",
            "formula_symbol": formula_profile.get("symbol") or "P",
            "route_component_price": _trim(route_component_price) if route_component_price > D0 else "",
            "non_street_component_price": _trim(non_street_component_price) if non_street_component_price > D0 else "",
            "commercial_weighted_price": _trim(commercial_weighted_price) if commercial_weighted_price > D0 else "",
        },
        "benchmark_corr_price": _trim(final_price) if should_calculate_price else "",
        "warnings": warnings + [
            {"level": "warning", "message": item, "target": _missing_target(item, region_rows)}
            for item in missing
        ],
        "complete": not missing and not warnings and final_price > D0,
        "coverage_scope": coverage_scope,
        "township_grade": township_grade,
        "support_status": support_status,
        "support_missing_items": missing,
        "policy_snapshot": config.get("policy_document") or {},
        "source_table_refs": config.get("source_table_refs") or {},
        "map_image_ids": analysis.get("map_image_ids") or [],
    }
    # 可编辑因素结构：前端优劣度选择即自动取系数（满足“优劣度→系数自动联动”要求）。
    result["region_factor_selections"] = region_rows
    result["regional_factors"] = region_rows
    result["individual_factors"] = _build_individual_factors(context)
    result["land_usage"] = usage
    result["land_use_type"] = usage
    result["land_level"] = level
    result["frontage_mode"] = frontage_mode
    result["route_segment_id"] = route_segment_id
    result["route_price"] = _trim(route_price) if route_price > D0 else ""
    result["route_price_source"] = route_price_source
    result["route_price_source_note"] = route_price_source_note
    result["route_road_type"] = route_road_type
    result["route_road_grade"] = route_road_grade
    result["route_road_type_source"] = route_road_type_source_name
    result["frontage_relation"] = frontage_relation
    result["frontage_depth_source"] = frontage_depth_source
    result["commercial_area_m2"] = _trim(commercial_area_m2) if commercial_area_m2 > D0 else ""
    result["frontage_standard_depth_m"] = _trim(frontage_standard_depth_m) if frontage_standard_depth_m > D0 else ""
    result["frontage_area_m2"] = _trim(frontage_area_m2) if frontage_area_m2 > D0 else ""
    result["non_frontage_area_m2"] = _trim(non_frontage_area_m2) if non_frontage_area_m2 > D0 else ""
    result["frontage_average_depth_m"] = _trim(frontage_depth_m) if frontage_depth_m > D0 else ""
    result["route_component_price"] = _trim(route_component_price) if route_component_price > D0 else ""
    result["non_street_component_price"] = _trim(non_street_component_price) if non_street_component_price > D0 else ""
    result["commercial_weighted_price"] = _trim(commercial_weighted_price) if commercial_weighted_price > D0 else ""
    result["frontage_depth_m"] = _trim(frontage_depth_m) if frontage_depth_m > D0 else ""
    result["frontage_width_m"] = _trim(frontage_width_m) if frontage_width_m > D0 else ""
    result["is_corner"] = is_corner
    result["corner_route_price_a"] = _trim(corner_route_price_a) if corner_route_price_a > D0 else ""
    result["corner_route_price_b"] = _trim(corner_route_price_b) if corner_route_price_b > D0 else ""
    result["corner_main_route_price"] = _trim(corner_main_route_price) if corner_main_route_price > D0 else ""
    result["corner_side_route_price"] = _trim(corner_side_route_price) if corner_side_route_price > D0 else ""
    result["corner_price_ratio"] = _trim(corner_price_ratio) if corner_price_ratio > D0 else ""
    result["ku_grade"] = ku_grade
    generated = _build_narratives(context)
    overrides = dict(analysis.get("narrative_overrides") or {})
    result["narrative_overrides"] = overrides
    result["generated_narratives"] = generated
    result["effective_narratives"] = {
        key: str(overrides.get(key) or value) for key, value in generated.items()
    }
    result["narrative_segment_sources"] = _build_segment_sources(context)
    result["content_blocks"] = _build_content_blocks(context)
    return result


def _empty_result(warnings: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "parameters": {},
        "parameter_rows": [],
        "tables": [],
        "results": [],
        "benchmark_corr_price": "",
        "warnings": warnings,
        "complete": False,
        "support_status": "incomplete",
        "support_missing_items": [item.get("message", "") for item in warnings],
        "narrative_overrides": {},
        "generated_narratives": {},
        "effective_narratives": {},
        "narrative_segment_sources": {},
        "content_blocks": [],
    }


def _unsupported_result(message: str, config: Dict[str, Any]) -> Dict[str, Any]:
    warning = {"level": "warning", "message": message, "target": "benchmark_corr_analysis"}
    result = _empty_result([warning])
    result["support_status"] = "unsupported"
    result["support_missing_items"] = [message]
    result["policy_snapshot"] = config.get("policy_document") or {}
    result["source_table_refs"] = config.get("source_table_refs") or {}
    result["tables"] = _base_reference_tables(config)
    return result


def _missing_target(message: str, region_rows: List[Dict[str, Any]]) -> str:
    """把基准法待校核项定位到第五部分内的具体控件。

    前端的 benchmarkFocusId 使用 benchmark_corr_analysis.<path>，这里返回同一口径，
    避免所有预警都只跳到方法根节点。
    """
    text = str(message or "")
    for index, row in enumerate(region_rows or []):
        sub_factor = str(row.get("sub_factor") or row.get("indicator") or "")
        if sub_factor and sub_factor in text:
            return f"benchmark_corr_analysis.regional_factors.{index}.coefficient"
    mapping = (
        ("乡镇", "benchmark_corr_analysis.township_grade"),
        ("土地用途", "benchmark_corr_analysis.land_use_type"),
        ("土地级别", "benchmark_corr_analysis.land_level"),
        ("临街路线价", "benchmark_corr_analysis.parameters.route_price"),
        ("路线价Po", "benchmark_corr_analysis.parameters.route_price"),
        ("路线价", "benchmark_corr_analysis.route_segment_id"),
        ("商服总面积", "benchmark_corr_analysis.parameters.commercial_area_m2"),
        ("临街商服用地面积", "benchmark_corr_analysis.parameters.frontage_area_m2"),
        ("标准深度", "benchmark_corr_analysis.parameters.frontage_standard_depth_m"),
        ("周边土地利用类型", "benchmark_corr_analysis.ku_grade"),
        ("Ku", "benchmark_corr_analysis.ku_grade"),
        ("道路等级", "benchmark_corr_analysis.parameters.route_road_grade"),
        ("道路类型", "benchmark_corr_analysis.parameters.route_road_type"),
        ("临街关系", "benchmark_corr_analysis.frontage_relation"),
        ("临街深度", "benchmark_corr_analysis.frontage_depth_m"),
        ("Kd", "benchmark_corr_analysis.frontage_depth_m"),
        ("临街宽度", "benchmark_corr_analysis.frontage_width_m"),
        ("Kk", "benchmark_corr_analysis.frontage_width_m"),
        ("街角", "benchmark_corr_analysis.corner_coefficient"),
        ("Kc", "benchmark_corr_analysis.corner_coefficient"),
        ("级别基准地价", "benchmark_corr_analysis.parameters.base_land_price"),
        ("容积率", "set_plot_ratio"),
        ("法定最高出让年期", "benchmark_corr_analysis.parameters.legal_term_years"),
        ("法定最高年期", "benchmark_corr_analysis.parameters.legal_term_years"),
        ("使用年期", "land_use_term"),
        ("设定使用年期", "land_use_term"),
        ("土地还原率", "benchmark_corr_analysis.parameters.cap_rate"),
        ("估价期日", "valuation_date"),
        ("宗地面积", "benchmark_corr_analysis.individual_factors.area.coefficient"),
        ("宗地形状", "benchmark_corr_analysis.individual_factors.shape.coefficient"),
        ("景观环境", "benchmark_corr_analysis.individual_factors.landscape.coefficient"),
        ("建筑物朝向", "benchmark_corr_analysis.individual_factors.orientation.coefficient"),
        ("开发程度修正额", "benchmark_corr_analysis.parameters.kf"),
        ("开发程度", "land_development_set"),
    )
    for token, target in mapping:
        if token in text:
            return target
    return "benchmark_corr_analysis"


def _resolve_region_factors(
    config: Dict[str, Any],
    usage: str,
    level: str,
    analysis: Dict[str, Any],
    coverage_scope: str,
    township_grade: str,
) -> tuple[List[Dict[str, Any]], Decimal, List[str]]:
    if coverage_scope == "乡镇":
        table = ((((config.get("township_region_factor_table") or {}).get(township_grade) or {}).get(usage) or {}).get(level) or [])
    else:
        table = ((config.get("region_factor_table") or {}).get(usage) or {}).get(level) or []
    table_by_sub = {row.get("sub_factor"): row for row in table}
    # The fifth-part UI edits regional_factors directly. Older payloads used
    # region_factor_selections, so keep it as a fallback only; otherwise stale
    # compatibility data can overwrite the user's latest dropdown choice.
    selections = analysis.get("regional_factors") or analysis.get("region_factor_selections") or []
    selection_by_sub = {
        item.get("sub_factor") or item.get("indicator") or item.get("key"): item
        for item in selections
    }

    rows: List[Dict[str, Any]] = []
    total = D0
    missing: List[str] = []
    if not table:
        return rows, total, [f"未取得「{coverage_scope}{township_grade}{usage}{level}」区域因素修正系数表"]
    for definition in table:
        sub = definition.get("sub_factor")
        selection = selection_by_sub.get(sub) or {}
        grade = str(selection.get("grade") or selection.get("level") or "").strip()
        grades = definition.get("grades") or {}
        criteria = definition.get("criteria") or {}
        coef = _decimal(grades.get(grade)) if grade in grades else D0
        if grade in grades:
            total += coef
        else:
            missing.append(f"区域因素「{sub}」优劣度未确认")
        # options：前端按优劣度选择即自动取对应修正率（满足“优劣度→系数自动联动”要求）。
        options = [
            {
                "label": g,
                "grade": g,
                "coefficient": _percent_text(_decimal(grades.get(g))),
                "criteria": str(criteria.get(g) or ""),
                "indicator_desc": str(criteria.get(g) or ""),
            }
            for g in GRADE_ORDER
            if g in grades
        ]
        rows.append({
            "factor": definition.get("factor") or "",
            "indicator": sub or "",
            "sub_factor": sub or "",
            "description": str(selection.get("description") or (criteria.get(grade) if grade else "") or ""),
            "level": grade,
            "grade": grade,
            "coefficient": _percent_text(coef) if grade in grades else "",
            "confirmed": bool(selection.get("confirmed")) if selection else False,
            "options": options,
        })
    return rows, total, missing


def _grade_coefficient(table: Dict[str, Any], grade: str) -> Decimal:
    grades = list(table.get("grades") or [])
    coefficients = list(table.get("coefficients") or [])
    if grade in grades:
        idx = grades.index(grade)
        if idx < len(coefficients):
            return _decimal(coefficients[idx])
    return D1


def _shape_coefficient(table: Dict[str, Any], usage: str, grade: str) -> Decimal:
    grades = list(table.get("grades") or [])
    coefficients = list((table.get("coefficients") or {}).get(usage) or [])
    if grade in grades and grades.index(grade) < len(coefficients):
        return _decimal(coefficients[grades.index(grade)])
    return D1


def _landscape_coefficient(table: Dict[str, Any], grade: str) -> Decimal:
    grades = list(table.get("grades") or [])
    coefficients = list(table.get("coefficients") or [])
    if grade in grades and grades.index(grade) < len(coefficients):
        return _decimal(coefficients[grades.index(grade)])
    return D1


def _orientation_coefficient(table: Dict[str, Any], orientation: str) -> Decimal:
    coefficients = table.get("coefficients") or {}
    if orientation in coefficients:
        return _decimal(coefficients[orientation])
    for key, value in coefficients.items():
        if orientation and orientation in str(key):
            return _decimal(value)
    return D1


def _orientation_matched(table: Dict[str, Any], orientation: str) -> bool:
    """朝向是否在朝向修正系数表中命中（精确或包含匹配），用于命中失败硬门禁。"""
    coefficients = table.get("coefficients") or {}
    if not orientation:
        return False
    if orientation in coefficients:
        return True
    return any(orientation in str(key) for key in coefficients)


def _grade_options(grades: List[str], coefficients: List[Any], descriptions: Optional[List[Any]] = None) -> List[Dict[str, str]]:
    options: List[Dict[str, str]] = []
    for i, grade in enumerate(grades):
        options.append({
            "label": grade,
            "grade": grade,
            "coefficient": str(coefficients[i]) if i < len(coefficients) else "",
            "description": str(descriptions[i]) if descriptions and i < len(descriptions) else "",
        })
    return options


def _build_individual_factors(context: Dict[str, Any]) -> Dict[str, Any]:
    config = context["config"]
    usage = context["usage"]
    area_cfg = (config.get("area_table") or {}).get(usage) or {}
    shape_cfg = config.get("shape_table") or {}
    landscape_cfg = config.get("landscape_table") or {}
    orientation_cfg = config.get("orientation_table") or {}
    shape_coefs = (shape_cfg.get("coefficients") or {}).get(usage) or []
    orientation_grades = orientation_cfg.get("grades") or []
    orientation_coefs = orientation_cfg.get("coefficients") or {}
    factors = {
        "area": {
            "grade": context["ks_grade"],
            "level": context["ks_grade"],
            "coefficient": _trim(context["ks"]),
            "options": _grade_options(area_cfg.get("grades") or [], area_cfg.get("coefficients") or [], area_cfg.get("thresholds") or []),
        },
        "shape": {
            "grade": context["ka_grade"],
            "level": context["ka_grade"],
            "coefficient": _trim(context["ka"]),
            "options": _grade_options(shape_cfg.get("grades") or [], shape_coefs, shape_cfg.get("descriptions") or []),
        },
        "landscape": {
            "grade": context["ke_grade"],
            "level": context["ke_grade"],
            "coefficient": _trim(context["ke"]),
            "options": _grade_options(landscape_cfg.get("grades") or [], landscape_cfg.get("ranges") or [], landscape_cfg.get("descriptions") or []),
        },
        "orientation": {
            "grade": context["orientation"],
            "level": context["orientation"],
            "coefficient": _trim(context["kto"]),
            "options": [{"label": g, "grade": g, "coefficient": str(orientation_coefs.get(g, "")), "description": ""} for g in orientation_grades],
        },
        "plot_ratio": {
            "value": _trim(context["plot_ratio"]) if context["plot_ratio"] > D0 else "",
            "coefficient": _factor_text(context["kv"]),
        },
        "term": {
            "set_term_years": _trim(context["land_use_term"]) if context["land_use_term"] > D0 else "",
            "legal_term_years": _trim(context["statutory_term"]) if context["statutory_term"] > D0 else "",
            "coefficient": _factor_text(context["ky"]),
        },
        "date": {"base_date": str(context["base_date"] or ""), "valuation_date": str(context["valuation_date"] or ""), "coefficient": _factor_text(context["kt"])},
        "development": {"kf": _trim(context["kf"])},
    }
    if _formula_has(context, "ku"):
        ku_table = context["config"].get("surrounding_land_use_table") or {}
        factors["surrounding_land_use"] = {
            "grade": context.get("ku_grade") or "",
            "level": context.get("ku_grade") or "",
            "coefficient": _factor_text(context.get("ku") or D1),
            "options": _ku_options(ku_table),
        }
    if _formula_has(context, "kd"):
        factors["frontage_depth"] = {
            "value": _trim(context.get("frontage_depth_m") or D0) if (context.get("frontage_depth_m") or D0) > D0 else "",
            "coefficient": _factor_text(context.get("kd") or D1),
        }
    if _formula_has(context, "kk"):
        factors["frontage_width"] = {
            "value": _trim(context.get("frontage_width_m") or D0) if (context.get("frontage_width_m") or D0) > D0 else "",
            "coefficient": _factor_text(context.get("kk") or D1),
        }
    if _formula_has(context, "kc"):
        factors["corner"] = {
            "is_corner": bool(context.get("is_corner")),
            "corner_price_ratio": _trim(context.get("corner_price_ratio") or D0) if (context.get("corner_price_ratio") or D0) > D0 else "",
            "coefficient": _factor_text(context.get("kc") or D1),
        }
    if not _formula_has(context, "ke"):
        factors.pop("landscape", None)
    if not _formula_has(context, "kto"):
        factors.pop("orientation", None)
    if not _formula_has(context, "kv"):
        factors.pop("plot_ratio", None)
    return factors


def _build_parameters(context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "coverage_scope": context["coverage_scope"],
        "township_grade": context["township_grade"],
        "land_use_type": context["usage"],
        "frontage_mode": context.get("frontage_mode") or "",
        "land_level": context["level"],
        "base_land_price": _trim(context["base_price"]),
        "base_price_source": (context["config"].get("policy_document") or {}).get("document_no", ""),
        "route_segment_id": context.get("route_segment_id") or "",
        "route_price": _trim(context.get("route_price") or D0) if (context.get("route_price") or D0) > D0 else "",
        "route_price_source": context.get("route_price_source") or "",
        "route_price_source_note": context.get("route_price_source_note") or "",
        "route_road_type": context.get("route_road_type") or "",
        "route_road_grade": context.get("route_road_grade") or "",
        "route_road_type_source": context.get("route_road_type_source") or "",
        "frontage_relation": context.get("frontage_relation") or "",
        "frontage_depth_source": context.get("frontage_depth_source") or "",
        "commercial_area_m2": _trim(context.get("commercial_area_m2") or D0) if (context.get("commercial_area_m2") or D0) > D0 else "",
        "frontage_standard_depth_m": _trim(context.get("frontage_standard_depth_m") or D0) if (context.get("frontage_standard_depth_m") or D0) > D0 else "",
        "frontage_area_m2": _trim(context.get("frontage_area_m2") or D0) if (context.get("frontage_area_m2") or D0) > D0 else "",
        "non_frontage_area_m2": _trim(context.get("non_frontage_area_m2") or D0) if (context.get("non_frontage_area_m2") or D0) > D0 else "",
        "frontage_average_depth_m": _trim(context.get("frontage_average_depth_m") or D0) if (context.get("frontage_average_depth_m") or D0) > D0 else "",
        "route_component_price": _trim(context.get("route_component_price") or D0) if (context.get("route_component_price") or D0) > D0 else "",
        "non_street_component_price": _trim(context.get("non_street_component_price") or D0) if (context.get("non_street_component_price") or D0) > D0 else "",
        "commercial_weighted_price": _trim(context.get("commercial_weighted_price") or D0) if (context.get("commercial_weighted_price") or D0) > D0 else "",
        "plot_ratio": _trim(context["plot_ratio"]) if context["plot_ratio"] > D0 else "",
        "kv": _factor_text(context["kv"]),
        "cap_rate": _percent_text(context["cap_rate"] * Decimal("100")) if context["cap_rate"] > D0 else "",
        "set_term_years": _trim(context["land_use_term"]) if context["land_use_term"] > D0 else "",
        "legal_term_years": _trim(context["statutory_term"]) if context["statutory_term"] > D0 else "",
        "land_area": _trim(context["land_area"]) if context["land_area"] > D0 else "",
        "land_area_mode": context.get("land_area_mode") or "",
        "land_area_label": context.get("land_area_label") or "",
        "ky": _factor_text(context["ky"]),
        "base_date": str(context["base_date"] or ""),
        "valuation_date": str(context["valuation_date"] or ""),
        "months_elapsed": _trim(context["months"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "monthly_growth_rate": _percent_text(context["monthly_rate"] * Decimal("100")),
        "kt": _factor_text(context["kt"]),
        "sum_ki": _percent4_text(context["sum_ki"]),
        "ks": _trim(context["ks"]),
        "ka": _trim(context["ka"]),
        "ke": _trim(context["ke"]),
        "kto": _trim(context["kto"]),
        "ku": _factor_text(context.get("ku") or D1),
        "ku_grade": context.get("ku_grade") or "",
        "kd": _factor_text(context.get("kd") or D1),
        "kk": _factor_text(context.get("kk") or D1),
        "kc": _factor_text(context.get("kc") or D1),
        "frontage_depth_m": _trim(context.get("frontage_depth_m") or D0) if (context.get("frontage_depth_m") or D0) > D0 else "",
        "frontage_width_m": _trim(context.get("frontage_width_m") or D0) if (context.get("frontage_width_m") or D0) > D0 else "",
        "is_corner": bool(context.get("is_corner")),
        "corner_route_price_a": _trim(context.get("corner_route_price_a") or D0) if (context.get("corner_route_price_a") or D0) > D0 else "",
        "corner_route_price_b": _trim(context.get("corner_route_price_b") or D0) if (context.get("corner_route_price_b") or D0) > D0 else "",
        "corner_main_route_price": _trim(context.get("corner_main_route_price") or D0) if (context.get("corner_main_route_price") or D0) > D0 else "",
        "corner_side_route_price": _trim(context.get("corner_side_route_price") or D0) if (context.get("corner_side_route_price") or D0) > D0 else "",
        "corner_price_ratio": _trim(context.get("corner_price_ratio") or D0) if (context.get("corner_price_ratio") or D0) > D0 else "",
        "kf": _trim(context["kf"]),
        "base_development": context.get("base_development") or "",
        "set_development": context.get("set_development") or "",
        "formula_text": _formula_text(context),
    }


def _build_parameter_rows(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = [
        {"key": "base_land_price", "label": "级别基准地价", "value": _trim(context["base_price"]), "unit": "元/平方米", "source": "policy", "confirmed": True},
        {"key": "route_price", "label": "路线价Po", "value": _trim(context.get("route_price") or D0), "unit": "元/平方米", "source": context.get("route_price_source") or "", "confirmed": bool(context.get("route_price"))},
        {"key": "commercial_area_m2", "label": "商服总面积", "value": _trim(context.get("commercial_area_m2") or D0), "unit": "平方米", "source": "derived", "confirmed": (context.get("commercial_area_m2") or D0) > D0},
        {"key": "frontage_area_m2", "label": "临街商服面积", "value": _trim(context.get("frontage_area_m2") or D0), "unit": "平方米", "source": "derived", "confirmed": (context.get("frontage_area_m2") or D0) > D0},
        {"key": "non_frontage_area_m2", "label": "其他商服面积", "value": _trim(context.get("non_frontage_area_m2") or D0), "unit": "平方米", "source": "derived", "confirmed": (context.get("non_frontage_area_m2") or D0) >= D0},
        {"key": "route_component_price", "label": "临街商服分项单价", "value": _trim(context.get("route_component_price") or D0), "unit": "元/平方米", "source": "derived", "confirmed": (context.get("route_component_price") or D0) > D0},
        {"key": "non_street_component_price", "label": "不临街商服分项单价", "value": _trim(context.get("non_street_component_price") or D0), "unit": "元/平方米", "source": "derived", "confirmed": (context.get("non_street_component_price") or D0) > D0},
        {"key": "plot_ratio", "label": "设定容积率", "value": _trim(context["plot_ratio"]), "unit": "", "source": "manual", "confirmed": True},
        {"key": "kv", "label": "容积率修正系数Kv", "value": _factor_text(context["kv"]), "unit": "", "source": "derived", "confirmed": True},
        {"key": "ky", "label": "年期修正系数Ky", "value": _factor_text(context["ky"]), "unit": "", "source": "derived", "confirmed": True},
        {"key": "kt", "label": "期日修正系数Kt", "value": _factor_text(context["kt"]), "unit": "", "source": "derived", "confirmed": True},
        {"key": "sum_ki", "label": "区域因素修正系数∑Ki", "value": _percent4_text(context["sum_ki"]) + "%", "unit": "", "source": "derived", "confirmed": True},
        {"key": "ks", "label": "面积修正系数Ks", "value": _trim(context["ks"]), "unit": "", "source": "policy", "confirmed": True},
        {"key": "ka", "label": "形状修正系数Ka", "value": _trim(context["ka"]), "unit": "", "source": "policy", "confirmed": True},
        {"key": "ke", "label": "景观修正系数Ke", "value": _trim(context["ke"]), "unit": "", "source": "policy", "confirmed": True},
        {"key": "kto", "label": "朝向修正系数Kto", "value": _trim(context["kto"]), "unit": "", "source": "policy", "confirmed": True},
        {"key": "ku", "label": "周边土地利用类型修正系数Ku", "value": _factor_text(context.get("ku") or D1), "unit": "", "source": "policy", "confirmed": bool(context.get("ku_grade"))},
        {"key": "corner_route_price_a", "label": "街角相邻路线价一", "value": _trim(context.get("corner_route_price_a") or D0), "unit": "元/平方米", "source": "manual", "confirmed": (context.get("corner_route_price_a") or D0) > D0},
        {"key": "corner_route_price_b", "label": "街角相邻路线价二", "value": _trim(context.get("corner_route_price_b") or D0), "unit": "元/平方米", "source": "manual", "confirmed": (context.get("corner_route_price_b") or D0) > D0},
        {"key": "corner_main_route_price", "label": "正街路线价", "value": _trim(context.get("corner_main_route_price") or D0), "unit": "元/平方米", "source": "derived", "confirmed": (context.get("corner_main_route_price") or D0) > D0},
        {"key": "corner_side_route_price", "label": "旁街路线价", "value": _trim(context.get("corner_side_route_price") or D0), "unit": "元/平方米", "source": "derived", "confirmed": (context.get("corner_side_route_price") or D0) > D0},
        {"key": "corner_price_ratio", "label": "正街/旁街地价比例", "value": _trim(context.get("corner_price_ratio") or D0), "unit": "", "source": "derived", "confirmed": (context.get("corner_price_ratio") or D0) > D0},
        {"key": "kc", "label": "街角地修正系数Kc", "value": _factor_text(context.get("kc") or D1), "unit": "", "source": "policy", "confirmed": not bool(context.get("is_corner")) or (context.get("kc") or D0) > D0},
        {"key": "kk", "label": "临街宽度修正系数Kk", "value": _factor_text(context.get("kk") or D1), "unit": "", "source": "policy", "confirmed": (context.get("frontage_width_m") or D0) > D0},
        {"key": "kd", "label": "临街深度修正系数Kd", "value": _factor_text(context.get("kd") or D1), "unit": "", "source": "policy", "confirmed": (context.get("frontage_depth_m") or D0) > D0},
        {"key": "kf", "label": "开发程度修正额Kf", "value": _trim(context["kf"]), "unit": "元/平方米", "source": "policy", "confirmed": True},
    ]
    key_to_factor = {
        "base_land_price": "base",
        "route_price": "route_price",
        "commercial_area_m2": "route_price",
        "frontage_area_m2": "route_price",
        "non_frontage_area_m2": "route_price",
        "route_component_price": "route_price",
        "non_street_component_price": "base",
        "kv": "kv",
        "sum_ki": "ki",
        "ke": "ke",
        "kto": "kto",
        "ku": "ku",
        "corner_route_price_a": "kc",
        "corner_route_price_b": "kc",
        "corner_main_route_price": "kc",
        "corner_side_route_price": "kc",
        "corner_price_ratio": "kc",
        "kc": "kc",
        "kk": "kk",
        "kd": "kd",
    }
    if not _is_split_frontage(context):
        rows = [row for row in rows if row["key"] not in {"commercial_area_m2", "frontage_area_m2", "non_frontage_area_m2", "route_component_price", "non_street_component_price"}]
    return [row for row in rows if key_to_factor.get(row["key"]) is None or _formula_has(context, key_to_factor[row["key"]])]


def _cap_rate_table_section(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    config = context["config"]
    usage = context["usage"]
    if usage in {"商业服务业用地", "居住用地"}:
        table = config.get("cap_rate_table") or {}
        title = "表3-4 通道县商业服务业、居住用地土地还原率表"
    else:
        table = config.get("cap_rate_other_table") or {}
        title = "表3-4 通道县工矿、仓储、公用设施和公共管理与公共服务用地还原率表"
    if not table:
        return None
    return {
        "key": "benchmark_cap_rate_table",
        "title": "土地还原率",
        "report_title": title,
        "columns": list(table.get("columns") or []),
        "rows": list(table.get("rows") or []),
        "source_target": "benchmark_corr_ky",
    }


def _region_scope_title(context: Dict[str, Any]) -> str:
    scope = str(context.get("coverage_scope") or "")
    township_grade = str(context.get("township_grade") or "")
    level = _level_display(str(context.get("level") or ""), roman=True)
    usage = str(context.get("usage") or "")
    return f"{scope}{township_grade}{level}{usage}".replace("乡镇乡镇", "乡镇")


def _region_indicator_table_section(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rows = list(context.get("region_rows") or [])
    if not rows:
        return None
    return {
        "key": "benchmark_region_indicator_table",
        "title": "区域因素修正系数指标说明表",
        "report_title": f"表3-6 通道县{_region_scope_title(context)}宗地地价区域因素修正系数指标说明表",
        "columns": ["因素", "因子"] + GRADE_ORDER,
        "rows": [
            {
                "因素": row.get("factor") or "",
                "因子": row.get("sub_factor") or row.get("indicator") or "",
                **{
                    grade: str(((next((opt for opt in row.get("options") or [] if opt.get("grade") == grade), {}) or {}).get("criteria")) or "")
                    for grade in GRADE_ORDER
                },
            }
            for row in rows
        ],
        "source_target": "benchmark_corr_ki",
    }


def _area_table_section(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    source = config.get("area_table") or {}
    if not source:
        return None
    columns = ["用地类型", "项目"] + GRADE_ORDER
    rows: List[Dict[str, Any]] = [
        {
            "cells": [
                {"label": "指标说明", "colspan": 2},
                {"label": "面积适中，有利于宗地利用"},
                {"label": "面积较适中，较有利于宗地利用"},
                {"label": "面积一般，对宗地利用基本无影响"},
                {"label": "面积偏小或偏大，对宗地利用有一定影响"},
                {"label": "面积过小或过大，对宗地利用影响明显"},
            ]
        }
    ]
    for usage, table in source.items():
        grades = list(table.get("grades") or GRADE_ORDER)
        thresholds = list(table.get("thresholds") or [])
        coefficients = list(table.get("coefficients") or [])
        threshold_map = {grade: thresholds[i] if i < len(thresholds) else "" for i, grade in enumerate(grades)}
        coefficient_map = {grade: coefficients[i] if i < len(coefficients) else "" for i, grade in enumerate(grades)}
        rows.append({
            "cells": [
                {"label": usage, "rowspan": 2},
                {"label": "指标范围"},
                *[{"label": threshold_map.get(grade, "")} for grade in GRADE_ORDER],
            ]
        })
        rows.append({
            "cells": [
                {"hidden": True},
                {"label": "修正系数"},
                *[{"label": coefficient_map.get(grade, "")} for grade in GRADE_ORDER],
            ]
        })
    return {
        "key": "benchmark_area_table",
        "title": "宗地面积修正系数表",
        "report_title": "表3-8 宗地面积修正系数表",
        "columns": columns,
        "rows": rows,
        "source_target": "benchmark_corr_ks",
    }


def _shape_table_section(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    table = config.get("shape_table") or {}
    if not table:
        return None
    descriptions = list(table.get("descriptions") or [])
    rows: List[Dict[str, Any]] = [
        {"指标标准": "指标说明", **{grade: descriptions[i] if i < len(descriptions) else "" for i, grade in enumerate(table.get("grades") or GRADE_ORDER)}}
    ]
    for usage, coefficients in (table.get("coefficients") or {}).items():
        rows.append({"指标标准": usage, **{grade: coefficients[i] if i < len(coefficients) else "" for i, grade in enumerate(table.get("grades") or GRADE_ORDER)}})
    return {
        "key": "benchmark_shape_table",
        "title": "宗地形状修正系数表",
        "report_title": "表3-9 宗地形状修正系数表",
        "columns": ["指标标准"] + list(table.get("grades") or GRADE_ORDER),
        "rows": rows,
        "source_target": "benchmark_corr_ka",
    }


def _route_price_table_section(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rows = list(context["config"].get("route_price_segments") or [])
    if not rows:
        return None
    return {
        "key": "benchmark_route_price_table",
        "title": "商业服务业用地路线价",
        "report_title": "表3-6 通道县城区商业服务业用地路线价",
        "columns": ["编号", "道路名称", "路线起点", "路线终点", "所属级别", "道路类型", "标准深度", "路线价"],
        "rows": [
            {
                "编号": row.get("code") or row.get("id") or "",
                "道路名称": row.get("road_name") or "",
                "路线起点": row.get("route_start") or "",
                "路线终点": row.get("route_end") or "",
                "所属级别": row.get("level") or "",
                "道路类型": row.get("road_type") or "",
                "标准深度": row.get("standard_depth") or "",
                "路线价": row.get("route_price") or "",
            }
            for row in rows
        ],
        "source_target": "benchmark_corr_route_price",
    }


def _frontage_depth_table_section(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    table = config.get("frontage_depth_table") or {}
    if not table:
        return None
    buckets = list(table.get("buckets") or [])
    return {
        "key": "benchmark_frontage_depth_table",
        "title": "临街深度修正系数表",
        "report_title": "表3-7 通道县城区宗地地价临街深度修正系数表",
        "columns": ["深度系数类型"] + buckets,
        "rows": [
            {"深度系数类型": row.get("road_type") or "", **{bucket: (row.get("coefficients") or [])[i] if i < len(row.get("coefficients") or []) else "" for i, bucket in enumerate(buckets)}}
            for row in table.get("rows") or []
        ],
        "source_target": "benchmark_corr_kd",
    }


def _frontage_width_table_section(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    table = config.get("frontage_width_table") or {}
    if not table:
        return None
    buckets = list(table.get("buckets") or [])
    return {
        "key": "benchmark_frontage_width_table",
        "title": "临街宽度修正系数表",
        "report_title": "表3-8 通道县城区临街宽度修正系数表",
        "columns": ["宗地临街宽度"] + buckets,
        "rows": [
            {"宗地临街宽度": row.get("road_type") or "", **{bucket: (row.get("coefficients") or [])[i] if i < len(row.get("coefficients") or []) else "" for i, bucket in enumerate(buckets)}}
            for row in table.get("rows") or []
        ],
        "source_target": "benchmark_corr_kk",
    }


def _corner_table_section(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    table = config.get("corner_coefficient_table") or {}
    if not table:
        return None
    buckets = list(table.get("buckets") or [])
    coefficients = list(table.get("coefficients") or [])
    return {
        "key": "benchmark_corner_table",
        "title": "街角地修正系数表",
        "report_title": "表3-9 通道县商业服务业用地街角地修正系数表",
        "columns": ["正街地价/旁街地价"] + buckets,
        "rows": [
            {"正街地价/旁街地价": "修正系数", **{bucket: coefficients[i] if i < len(coefficients) else "" for i, bucket in enumerate(buckets)}}
        ],
        "source_target": "benchmark_corr_kc",
    }


def _surrounding_land_use_table_section(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    table = config.get("surrounding_land_use_table") or {}
    if not table:
        return None
    grades = list(table.get("grades") or [])
    descriptions = list(table.get("descriptions") or [])
    coefficients = list(table.get("coefficients") or [])
    return {
        "key": "benchmark_surrounding_land_use_table",
        "title": "宗地周边土地利用类型修正系数表",
        "report_title": "表3-10 宗地周边土地利用类型修正系数表",
        "columns": ["指标标准"] + grades,
        "rows": [
            {"指标标准": "指标说明", **{grade: descriptions[i] if i < len(descriptions) else "" for i, grade in enumerate(grades)}},
            {"指标标准": "修正系数", **{grade: coefficients[i] if i < len(coefficients) else "" for i, grade in enumerate(grades)}},
        ],
        "source_target": "benchmark_corr_ku",
    }


def _build_tables(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    config = context["config"]
    usage = context["usage"]
    level = context["level"]
    coverage_scope = context["coverage_scope"]
    township_grade = context["township_grade"]
    tables: List[Dict[str, Any]] = []

    # 表3-1 基准地价内涵（正式多用途横向表头）
    connotation_section = _base_connotation_table_section(config, coverage_scope, township_grade)
    if connotation_section:
        tables.append(connotation_section)

    base_table = config.get("base_land_price") or {}
    levels = ["一级", "二级", "三级", "四级", "五级"]
    tables.append({
        "key": "benchmark_base_price_table",
        "title": "级别基准地价",
        "report_title": "表3-2 通道县城区级别基准地价（元/平方米）",
        "columns": ["用地类型"] + levels,
        "levels": levels,
        "use_types": list(base_table.keys()),
        "rows": [
            {
                "用地类型": use,
                "use_type": use,
                "values": [base_table.get(use, {}).get(lv, "") for lv in levels],
                **{lv: base_table.get(use, {}).get(lv, "") for lv in levels},
            }
            for use in base_table
        ],
        "source_target": "benchmark_corr_analysis",
    })
    township_base = config.get("township_base_land_price") or {}
    if township_base:
        township_rows: List[Dict[str, Any]] = []
        for grade, use_map in township_base.items():
            for current_usage, values in use_map.items():
                township_rows.append({
                    "乡镇等别": grade,
                    "用地类型": current_usage,
                    "一级": values.get("一级", ""),
                    "二级": values.get("二级", ""),
                    "三级": values.get("三级", ""),
                })
        tables.append({
            "key": "benchmark_township_base_price_table",
            "title": "乡镇级别基准地价",
            "report_title": "表3-2 通道县乡镇级别基准地价（元/平方米）",
            "columns": ["乡镇等别", "用地类型", "一级", "二级", "三级"],
            "levels": ["一级", "二级", "三级"],
            "use_types": sorted({current_usage for use_map in township_base.values() for current_usage in use_map}),
            "township_grades": list(township_base.keys()),
            "rows": township_rows,
            "source_target": "benchmark_corr_analysis",
        })

    # 表3-3 容积率修正系数表（当前用途）
    pr_table = _plot_ratio_config(config, coverage_scope, usage, township_grade)
    if pr_table:
        pr_levels = list(pr_table.get("levels") or [])
        tables.append({
            "key": "benchmark_plot_ratio_table",
            "title": "容积率修正系数表",
            "report_title": f"表3-3 通道县{coverage_scope}{township_grade}{usage}容积率修正系数表",
            "columns": ["容积率"] + pr_levels,
            "rows": [
                {"容积率": row.get("label"), **{pr_levels[i]: (row.get("values") or [])[i] for i in range(len(pr_levels)) if i < len(row.get("values") or [])}}
                for row in pr_table.get("rows") or []
            ],
            "source_target": "benchmark_corr_kv",
        })

    # 表3-4 还原率（商业/居住一套；工矿、仓储、公服、公用设施另一套）
    cap_section = _cap_rate_table_section(context)
    if cap_section:
        tables.append(cap_section)

    # 表3-5 期日修正测算表
    tables.append({
        "key": "benchmark_date_adjustment_table",
        "title": "期日修正测算表",
        "report_title": f"表3-5 估价对象{usage}期日修正测算表",
        "columns": ["项目", "内容"],
        "rows": [
            {"项目": "土地用途", "内容": usage},
            {"项目": "基准地价的基准日", "内容": str(context["base_date"] or "")},
            {"项目": "估价期日", "内容": str(context["valuation_date"] or "")},
            {"项目": "估价期日修正的上涨时间(月)", "内容": _trim(context["months"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))},
            {"项目": "月上涨率", "内容": _percent_text(context["monthly_rate"] * Decimal("100")) + "%"},
            {"项目": "估价对象期日修正系数", "内容": _factor_text(context["kt"])},
        ],
        "source_target": "benchmark_corr_kt",
    })

    # 表3-6 指标说明表 + 表3-7 区域因素修正系数表（选取结果）
    if _formula_has(context, "ki"):
        indicator_section = _region_indicator_table_section(context)
        if indicator_section:
            tables.append(indicator_section)
        tables.append({
            "key": "benchmark_region_factor_table",
            "title": "宗地地价区位因素修正系数表",
            "report_title": f"表3-7 通道县{_region_scope_title(context)}宗地地价区域因素修正系数表",
            "columns": ["因素", "因子", "因素说明", "优劣度", "修正系数（%）"],
            "rows": [
                {
                    "因素": row["factor"],
                    "因子": row["sub_factor"],
                    "因素说明": row["description"],
                    "优劣度": row.get("grade") or row.get("level") or "待确认",
                    "修正系数（%）": row["coefficient"],
                }
                for row in context["region_rows"]
            ] + [
                {"因素": "合计", "因子": "/", "因素说明": "/", "优劣度": "/", "修正系数（%）": _percent4_text(context["sum_ki"])}
            ],
            "source_target": "benchmark_corr_ki",
        })

    if _formula_has(context, "route_price"):
        for section in (
            _route_price_table_section(context),
            _frontage_depth_table_section(config),
            _frontage_width_table_section(config),
            _corner_table_section(config),
        ):
            if section:
                tables.append(section)
    surrounding_section = _surrounding_land_use_table_section(config) if _formula_has(context, "ku") else None
    if surrounding_section:
        tables.append(surrounding_section)

    # 表3-8 面积 / 表3-9 形状 / 表3-10 景观 / 表3-11 朝向
    area_section = _area_table_section(config)
    if area_section:
        tables.append(area_section)
    shape_section = _shape_table_section(config)
    if shape_section:
        tables.append(shape_section)
    landscape_table = config.get("landscape_table") or {}
    if _formula_has(context, "ke") and landscape_table:
        tables.append({
            "key": "benchmark_landscape_table",
            "title": "景观状况修正系数表",
            "report_title": "表3-10 居住用地宗地景观状况修正系数表",
            "columns": ["优劣度", "指标说明", "修正系数"],
            "rows": [
                {"优劣度": g, "指标说明": (landscape_table.get("descriptions") or [])[i] if i < len(landscape_table.get("descriptions") or []) else "", "修正系数": (landscape_table.get("ranges") or [])[i] if i < len(landscape_table.get("ranges") or []) else ""}
                for i, g in enumerate(landscape_table.get("grades") or [])
            ],
            "source_target": "benchmark_corr_ke",
        })
    orientation_table = config.get("orientation_table") or {}
    if _formula_has(context, "kto") and orientation_table:
        grades = orientation_table.get("grades") or []
        coefs = orientation_table.get("coefficients") or {}
        tables.append({
            "key": "benchmark_orientation_table",
            "title": "建筑物朝向修正系数表",
            "report_title": "表3-11 建筑物朝向修正系数表",
            "columns": ["朝向", "修正系数"],
            "rows": [{"朝向": g, "修正系数": coefs.get(g, "")} for g in grades],
            "source_target": "benchmark_corr_kto",
        })

    return tables


def _base_reference_tables(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    return _build_tables({
        "config": config,
        "usage": "居住用地",
        "level": "二级",
        "coverage_scope": "城区",
        "township_grade": "",
        "base_date": (config.get("policy_document") or {}).get("base_date"),
        "valuation_date": "",
        "months": D0,
        "monthly_rate": D0,
        "kt": D1,
        "region_rows": [],
        "sum_ki": D0,
        "ks": D1,
        "ka": D1,
        "ke": D1,
        "kto": D1,
        "plot_ratio": D0,
        "kv": D1,
        "formula_profile": _formula_profile("居住用地"),
    })


def _build_content_blocks(context: Dict[str, Any]) -> List[Dict[str, str]]:
    base_price_table_key = (
        "benchmark_township_base_price_table"
        if context.get("coverage_scope") == "乡镇"
        else "benchmark_base_price_table"
    )
    blocks = [
        {"type": "narrative", "key": "benchmark_corr_method_intro"},
        {"type": "narrative", "key": "benchmark_corr_base_price"},
        {"type": "table", "key": "benchmark_base_connotation_table"},
        {"type": "table", "key": base_price_table_key},
        {"type": "narrative", "key": "benchmark_corr_formula"},
        {"type": "narrative", "key": "benchmark_corr_po"},
    ]
    if _formula_has(context, "kv"):
        blocks.extend([
            {"type": "narrative", "key": "benchmark_corr_kv"},
            {"type": "table", "key": "benchmark_plot_ratio_table"},
        ])
    blocks.extend([
        {"type": "narrative", "key": "benchmark_corr_ky"},
        {"type": "table", "key": "benchmark_cap_rate_table"},
        {"type": "narrative", "key": "benchmark_corr_kt"},
        {"type": "table", "key": "benchmark_date_adjustment_table"},
    ])
    if _formula_has(context, "ki"):
        blocks.extend([
            {"type": "narrative", "key": "benchmark_corr_ki"},
            {"type": "table", "key": "benchmark_region_indicator_table"},
            {"type": "table", "key": "benchmark_region_factor_table"},
        ])
    if _formula_has(context, "route_price"):
        blocks.extend([
            {"type": "table", "key": "benchmark_route_price_table"},
            {"type": "narrative", "key": "benchmark_corr_frontage_special_intro"},
            {"type": "narrative", "key": "benchmark_corr_kc"},
            {"type": "table", "key": "benchmark_corner_table"},
            {"type": "narrative", "key": "benchmark_corr_kd"},
            {"type": "table", "key": "benchmark_frontage_depth_table"},
            {"type": "narrative", "key": "benchmark_corr_kk"},
            {"type": "table", "key": "benchmark_frontage_width_table"},
        ])
    blocks.extend([
        {"type": "narrative", "key": "benchmark_corr_ks"},
        {"type": "table", "key": "benchmark_area_table"},
        {"type": "narrative", "key": "benchmark_corr_ka"},
        {"type": "table", "key": "benchmark_shape_table"},
    ])
    if _formula_has(context, "ku"):
        blocks.extend([
            {"type": "narrative", "key": "benchmark_corr_ku"},
            {"type": "table", "key": "benchmark_surrounding_land_use_table"},
        ])
    if _formula_has(context, "ke"):
        blocks.extend([
            {"type": "narrative", "key": "benchmark_corr_ke"},
            {"type": "table", "key": "benchmark_landscape_table"},
        ])
    if _formula_has(context, "kto"):
        blocks.extend([
            {"type": "narrative", "key": "benchmark_corr_kto"},
            {"type": "table", "key": "benchmark_orientation_table"},
        ])
    blocks.extend([
        {"type": "narrative", "key": "benchmark_corr_kf"},
        {"type": "narrative", "key": "benchmark_corr_solve"},
        {"type": "result", "key": "benchmark_corr_price"},
    ])
    return blocks


def _build_narratives(context: Dict[str, Any]) -> Dict[str, str]:
    usage = context["usage"]
    level = context["level"]
    coverage_scope = context["coverage_scope"]
    township_grade = context["township_grade"]
    formula_profile = context.get("formula_profile") or _formula_profile(usage)
    formula_symbol = formula_profile.get("symbol") or "P"
    doc = (context["config"].get("policy_document") or {})
    report = doc.get("technical_report") or "《通道侗族自治县城镇基准地价更新技术报告》（2025年11月）"
    base_price = _trim(context["base_price"])
    kv = _factor_text(context["kv"])
    ky = _factor_text(context["ky"])
    kt = _factor_text(context["kt"])
    sum_ki = _percent4_text(context["sum_ki"])
    ks = _trim(context["ks"])
    ka = _trim(context["ka"])
    ke = _trim(context["ke"])
    kto = _trim(context["kto"])
    ku = _factor_text(context.get("ku") or D1)
    kd = _factor_text(context.get("kd") or D1)
    kk = _factor_text(context.get("kk") or D1)
    kc = _factor_text(context.get("kc") or D1)
    route_price = _trim(context.get("route_price") or D0) if (context.get("route_price") or D0) > D0 else ""
    frontage_depth = _trim(context.get("frontage_depth_m") or D0) if (context.get("frontage_depth_m") or D0) > D0 else ""
    frontage_width = _trim(context.get("frontage_width_m") or D0) if (context.get("frontage_width_m") or D0) > D0 else ""
    frontage_standard_depth = _trim(context.get("frontage_standard_depth_m") or D0) if (context.get("frontage_standard_depth_m") or D0) > D0 else ""
    commercial_area = _trim(context.get("commercial_area_m2") or D0) if (context.get("commercial_area_m2") or D0) > D0 else ""
    frontage_area = _trim(context.get("frontage_area_m2") or D0) if (context.get("frontage_area_m2") or D0) > D0 else ""
    non_frontage_area = _trim(context.get("non_frontage_area_m2") or D0) if (context.get("non_frontage_area_m2") or D0) > D0 else ""
    route_component_price = _trim(context.get("route_component_price") or D0) if (context.get("route_component_price") or D0) > D0 else ""
    non_street_component_price = _trim(context.get("non_street_component_price") or D0) if (context.get("non_street_component_price") or D0) > D0 else ""
    frontage_standard_depth = _trim(context.get("frontage_standard_depth_m") or D0) if (context.get("frontage_standard_depth_m") or D0) > D0 else ""
    commercial_area = _trim(context.get("commercial_area_m2") or D0) if (context.get("commercial_area_m2") or D0) > D0 else ""
    frontage_area = _trim(context.get("frontage_area_m2") or D0) if (context.get("frontage_area_m2") or D0) > D0 else ""
    non_frontage_area = _trim(context.get("non_frontage_area_m2") or D0) if (context.get("non_frontage_area_m2") or D0) > D0 else ""
    route_component_price = _trim(context.get("route_component_price") or D0) if (context.get("route_component_price") or D0) > D0 else ""
    non_street_component_price = _trim(context.get("non_street_component_price") or D0) if (context.get("non_street_component_price") or D0) > D0 else ""
    corner_route_price_a = _trim(context.get("corner_route_price_a") or D0) if (context.get("corner_route_price_a") or D0) > D0 else ""
    corner_route_price_b = _trim(context.get("corner_route_price_b") or D0) if (context.get("corner_route_price_b") or D0) > D0 else ""
    corner_main_route_price = _trim(context.get("corner_main_route_price") or D0) if (context.get("corner_main_route_price") or D0) > D0 else ""
    corner_side_route_price = _trim(context.get("corner_side_route_price") or D0) if (context.get("corner_side_route_price") or D0) > D0 else ""
    corner_ratio = _trim(context.get("corner_price_ratio") or D0) if (context.get("corner_price_ratio") or D0) > D0 else ""
    kf = _trim(context["kf"])
    ku = _factor_text(context.get("ku") or D1)
    kd = _factor_text(context.get("kd") or D1)
    kk = _factor_text(context.get("kk") or D1)
    kc = _factor_text(context.get("kc") or D1)
    route_price = _trim(context.get("route_price") or D0)
    final_price = _trim(context["final_price"])
    plot_ratio = _trim(context["plot_ratio"]) if context["plot_ratio"] > D0 else ""
    term = _trim(context["land_use_term"]) if context["land_use_term"] > D0 else ""
    statutory = _trim(context["statutory_term"]) if context["statutory_term"] > D0 else ""
    cap_rate_pct = _percent_text(context["cap_rate"] * Decimal("100")) if context["cap_rate"] > D0 else ""
    months = _trim(context["months"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    monthly_pct = _percent_text(context["monthly_rate"] * Decimal("100"))

    level_roman = _level_display(level, roman=True)
    location_text = str(context.get("land_location_full") or context.get("land_location_short") or context.get("location") or "").strip()
    base_date_display = str(context.get("base_date") or "")
    valuation_date_display = str(context.get("valuation_date") or "")
    area_value = _trim(context["land_area"]) if context["land_area"] > D0 else "待校核"
    area_label = str(context.get("land_area_sentence_label") or "宗地面积")
    usage_sentence = "住宅" if usage == "居住用地" else (usage or "待校核")
    usage_market_label = "住宅用地" if usage == "居住用地" else (usage or "待校核")

    factor_explanations = {
        "base": "P1b——估价对象所处级别的基准地价",
        "route_price": "Po——估价对象所临路线价",
        "ki": "∑Ki——区域因素修正值之和",
        "ky": "Ky——年期修正系数",
        "kv": "Kv——容积率修正系数",
        "kt": "Kt——估价期日修正系数",
        "ks": "Ks——宗地面积修正系数",
        "ka": "Ka——宗地形状修正系数",
        "ke": "Ke——景观环境修正系数",
        "kto": "Kto——建筑物朝向修正系数",
        "ku": "Ku——周边土地利用类型修正系数",
        "kc": "Kc——街角地修正系数",
        "kk": "Kk——临街宽度修正系数",
        "kd": "Kd——临街深度修正系数",
        "kf": "Kf——开发程度修正额",
    }
    formula_explain = "\n".join(
        [f"{formula_symbol}——估价对象设定开发程度条件下宗地地价"]
        + [factor_explanations[key] for key in formula_profile.get("factors") or [] if key in factor_explanations]
    )
    if context["statutory_term"] > D0 and context["land_use_term"] == context["statutory_term"]:
        ky_text = (
            f"通道县出让基准地价设定的土地使用年期为各用途土地法定出让最高使用年期，为{usage}{statutory}年；"
            f"此次评估设定宗地的出让土地使用权土地使用年期为{usage}{term}年，与出让基准地价设定用途的内涵使用年期一致，故此次评估不需进行使用年期修正。\n"
            f"年期修正系数计算公式如下：\n"
            f"Ky=[1-1/(1+r)^m]/[1-1/(1+r)^n]\n"
            f"式中：\n"
            f"r——土地还原率；\n"
            f"m——估价对象设定土地使用年期；\n"
            f"n——基准地价内涵土地使用年期。\n"
            f"根据{report}，{usage}土地还原率为{cap_rate_pct or '待校核'}%。\n"
            f"则：Ky=1.0000。"
        )
    else:
        ky_text = (
            f"通道县出让基准地价设定的土地使用年期为各用途土地法定出让最高使用年期，为{usage}{statutory or '待校核'}年；"
            f"此次评估设定宗地的出让土地使用权土地使用年期为{usage}{term or '待校核'}年，与出让基准地价设定用途的内涵使用年期不一致，故此次评估需要进行使用年期修正。\n"
            f"年期修正系数计算公式如下：\n"
            f"Ky=[1-1/(1+r)^m]/[1-1/(1+r)^n]\n"
            f"式中：\n"
            f"r——土地还原率；\n"
            f"m——估价对象设定土地使用年期；\n"
            f"n——基准地价内涵土地使用年期。\n"
            f"根据{report}，{usage}土地还原率为{cap_rate_pct or '待校核'}%。\n"
            f"则：Ky=[1-1/(1+{cap_rate_pct or '待校核'}%)^{term or '待校核'}]/[1-1/(1+{cap_rate_pct or '待校核'}%)^{statutory or '待校核'}]={ky}。"
        )
    if context.get("support_status") != "supported":
        missing_text = "；".join(str(item) for item in context.get("support_missing_items") or [])
        solve_text = f"{missing_text or '修正参数尚待校核'}，待补齐后生成完整求价过程。"
    elif _is_split_frontage(context):
        solve_text = (
            f"①临街商服用地P商={route_price}×{ky}×{kv}×{kt}×{ks}×{ka}×{kc}×{kk}×{kd}×{ku}+{kf}={route_component_price}（元/平方米）\n"
            f"②不临街商服用地P商={base_price}×（1+{sum_ki}%）×{ky}×{kv}×{kt}×{ks}×{ka}×{ku}+{kf}={non_street_component_price}（元/平方米）\n"
            f"商业用地综合单价=（{route_component_price}×{frontage_area}+{non_street_component_price}×{non_frontage_area}）/{commercial_area}={final_price}（元/平方米）"
        )
    else:
        solve_prefix = ""
        if _normalize_usage(usage) == "商业服务业用地":
            solve_prefix = "临街商业服务业用地" if _formula_has(context, "route_price") else "不临街商业服务业用地"
        solve_formula = _formula_text(context).splitlines()[-1]
        solve_text = (
            f"{solve_prefix}{solve_formula}={_formula_value_text(context)}\n"
            f"={final_price}元/平方米。"
        )
    route_segment = context.get("route_segment") or {}
    route_name = str(route_segment.get("road_name") or "").strip()
    route_start = str(route_segment.get("route_start") or "").strip()
    route_end = str(route_segment.get("route_end") or "").strip()
    route_road_type = str(context.get("route_road_type") or route_segment.get("road_type") or "").strip()
    standard_depth = str(route_segment.get("standard_depth") or "").strip()
    if not standard_depth:
        standard_depth = {"主干道": "20", "次干道": "16", "支路": "12"}.get(route_road_type, "")
    frontage_relation_label = "与道路有退距" if context.get("frontage_relation") == "setback" else "紧邻道路"
    road_type_source_text = str(context.get("route_road_type_source") or "").strip()
    route_desc = (
        f"{route_name or '待校核'}（{route_start or '待校核'}至{route_end or '待校核'}）"
        if route_segment
        else "人工填写路线价"
    )
    source_note = str(context.get("route_price_source_note") or "").strip()
    frontage_depth_text = frontage_depth or "待校核"
    frontage_width_text = frontage_width or "待校核"
    if frontage_depth and standard_depth:
        depth_cmp = "大于" if _decimal(frontage_depth) > _decimal(standard_depth) else "等于" if _decimal(frontage_depth) == _decimal(standard_depth) else "小于"
        depth_conclusion = (
            f"临街深度{depth_cmp}{route_road_type or '该道路'}标准深度{standard_depth}米，"
            f"{'故不需进行临街深度修正' if _decimal(frontage_depth) >= _decimal(standard_depth) else '故需进行临街深度修正'}"
        )
    else:
        depth_conclusion = "临街深度及标准深度尚待校核"
    if _is_split_frontage(context):
        po_text = (
            f"本次评估设定估价对象土地用途为{usage or '待校核'}，估价对象位于{location_text or '待校核'}。"
            f"根据{report}、通道县城区商业服务业用地路线价表及估价对象临街条件，"
            f"临街部分位于{route_desc}路线价段内，该路线价为{route_price or '待校核'}元/平方米，即Po={route_price or '待校核'}元/平方米；"
            f"其他不临街部分位于通道县{coverage_scope}{township_grade}{level_roman or level or '待校核'}{usage or '待校核'}，"
            f"级别基准地价P1b={base_price or '待校核'}元/平方米。"
            + (f"本次路线价由人工采用，来源说明为：{source_note}。" if context.get("route_price_source") == "manual" and source_note else "")
        )
    elif _formula_has(context, "route_price"):
        po_text = (
            f"本次评估设定估价对象土地用途为{usage or '待校核'}，估价对象位于{location_text or '待校核'}，"
            f"估价对象按临街商业服务业用地路线价路径测算。根据{report}、通道县城区商业服务业用地路线价表及估价对象临街条件，"
            f"估价对象位于{route_desc}路线价段内，该路线价为{route_price or '待校核'}元/平方米，即Po={route_price or '待校核'}元/平方米。"
            + (f"本次路线价由人工采用，来源说明为：{source_note}。" if context.get("route_price_source") == "manual" and source_note else "")
        )
    else:
        po_text = (
            f"本次评估设定估价对象土地用途为{usage or '待校核'}，估价对象位于{location_text or '待校核'}，"
            f"根据{report}和通道县城镇基准地价成果图件，估价对象位于通道县{coverage_scope}{township_grade}{level_roman or level or '待校核'}{usage or '待校核'}，"
            f"其级别基准地价Po={base_price or '待校核'}元/平方米。"
        )

    return {
        "benchmark_corr_method_intro": (
              "基准地价系数修正法是利用城镇基准地价和基准地价修正系数表等评估成果，按照替代原则，"
              "对估价对象的区域条件和个别条件等与其所处区域的平均条件相比较，并对照修正系数表选取相应的修正系数"
              "对基准地价进行修正，进而求取估价对象在估价基准日价格的方法。\n"
              "根据《城镇土地估价规程》（GB/T18508-2014），运用基准地价系数修正法评估宗地价格一般分以下几个步骤进行：\n"
              "（1）具体说明本次评估所采用的基准地价的制定情况、内涵及其测算公式；\n"
              "（2）根据估价对象的具体位置及当地城区土地级别图，确定估价对象所在土地级别和基准地价；\n"
              "（3）根据估价对象具体用途、规划限制条件等，确定其容积率修正系数；\n"
              "（4）根据估价对象具体土地使用年期，确定其年期修正系数；\n"
              "（5）根据估价对象估价期日和基准地价基准日，确定期日修正系数；\n"
              "（6）根据估价对象的实际情况以及基准地价修正体系，确定区域及个别因素修正值；\n"
              "（7）根据估价对象实际开发程度和基准地价内涵开发程度，确定开发程度修正；\n"
              "（8）根据基准地价内涵规定的公式，计算基准地价系数修正法测算结果。"
        ),
        "benchmark_corr_base_price": (
              "根据估价对象区域因素及个别因素，按照《城镇土地估价规程》要求，结合通道县基准地价的执行情况。"
              f"通道县基准地价的依据是{report}。\n"
              f"出让土地使用权基准地价的内涵为：在估价基准日{base_date_display}，各土地级别或均质区域内，"
              "现状平均土地开发程度和平均容积率下，同一用途的完整土地使用权的平均价格。\n"
              "地类按商业服务业、居住、公共管理与公共服务、工矿、仓储、公用设施用地区分，各类用地的使用年期均为法定最高使用年限。"
              f"通道县{coverage_scope}基准地价及其内涵具体情况见下表："
        ),
        "benchmark_corr_po": po_text,
        "benchmark_corr_formula": (
              f"根据估价对象实际情况，本次评估采用基准地价系数修正法评估{usage or '待校核'}土地价格的基本计算公式为：\n"
              + f"{_formula_text(context)}\n"
              f"式中：\n{formula_explain}。"
        ),
        "benchmark_corr_kv": (
            f"容积率的变化会影响地价的变化。在进行{usage_sentence}宗地评估时，当实际容积率与平均容积率不同时，必须进行修正。"
            f"本次评估设定容积率为{plot_ratio or '待校核'}。根据{report}，"
            f"查《通道县{coverage_scope}{township_grade}{usage}容积率修正系数表》，采用内插法得估价对象容积率修正值为：Kv={kv}。"
        ),
        "benchmark_corr_ky": ky_text,
        "benchmark_corr_kt": (
            f"根据{report}，通道县城镇基准地价基准日为{base_date_display}，本次评估估价期日为{valuation_date_display or '待校核'}，"
            f"历时{months}个月，需进行估价期日修正。通道县目前尚未建立地价动态监测体系，"
            f"经查询通道县土地成交信息及估价对象所在区域土地市场情况，同类型城镇{usage_market_label}在此期间的地价月平均上涨率约为{monthly_pct}%，"
            f"本次评估结合宗地所在区域地价上涨幅度，确定估价对象估价期日修正系数Kt={kt}。具体测算见下表：\n"
            f"Kt=(1+{monthly_pct}%)^{months}={kt}。"
        ),
        "benchmark_corr_ki": (
            f"根据{report}中《通道县{_region_scope_title(context)}宗地地价区域因素修正系数指标说明表》及《通道县{_region_scope_title(context)}宗地地价区域因素修正系数表》，"
            f"结合估价对象区域因素条件，确定各区域因素修正系数，并求得区域因素修正系数之和∑Ki={sum_ki}%。"
        ),
        "benchmark_corr_route_price": (
            f"商服用地临街宗地价格受所临道路路线价影响较大。路线价为基准地价的线状表达方式，"
            f"主要反映商业服务业用地临街标准宗地一定深度上的地价水平。\n"
            f"根据估价对象临街状况及{report}中的通道县城区商业服务业用地路线价表，"
            f"本次评估采用{route_desc if _formula_has(context, 'route_price') else '待校核'}路线价段进行测算，"
            f"路线价Po={route_price or '待校核'}元/平方米。"
            + (f"\n该路线价来源说明为：{source_note}。" if _formula_has(context, "route_price") and context.get("route_price_source") == "manual" and source_note else "")
        ),
        "benchmark_corr_frontage_special_intro": (
            (
                f"商服用地临街宗地特别因素主要包括修正面积分配、街角地、临街深度、临街宽度等因素。"
                f"本次评估根据估价对象临街状况及路线价修正体系，对上述因素分别进行分析。"
                f"根据最有效利用原则，本次评估商服用地面积按街角地、主干道、次干道、临路线价高的路段顺序优先进行分配。"
                f"估价对象{frontage_relation_label}，商服总面积为{commercial_area or area_value}平方米，已知{route_road_type or '待校核'}标准深度为{frontage_standard_depth or '待校核'}米，"
                f"临街宽度为{frontage_width_text}米，{'有效临街深度为' + frontage_depth_text + '米，' if context.get('frontage_relation') == 'setback' else ''}则：\n"
                f"①临街商服用地面积=标准临街深度×临街宽度={frontage_standard_depth or '待校核'}×{frontage_width_text}={frontage_area or '待校核'}（平方米）\n"
                f"②其他商服用地面积=商服总面积-临街商服用地面积={commercial_area or '待校核'}-{frontage_area or '待校核'}={non_frontage_area or '待校核'}（平方米）"
            )
            if _is_split_frontage(context)
            else (
                f"商服用地临街宗地特别因素主要包括修正面积分配、街角地、临街深度、临街宽度等因素。"
                f"本次评估估价对象全宗按临街路线价路径测算，不再另行拆分临街与不临街面积。"
                f"估价对象{area_label}为{area_value}平方米，所临路线价道路类型为{route_road_type or '待校核'}，"
                f"临街深度为{frontage_depth_text}米，临街宽度为{frontage_width_text}米。"
            )
        ),
        "benchmark_corr_kd": (
            f"在同一路线价区段，各宗土地虽然临接同一街道，但因其深度、宽度、形状、面积、位置等不同，"
            f"单位面积地价会有一定差别，其中对土地价格影响较大的是宗地临街深度。"
            f"路线价估价法认为，距道路越近，受道路通达、人流集聚和商业展示影响越明显，地价相对越高；"
            f"当宗地实际临街深度与路线价设定标准深度不一致时，应进行临街深度修正。\n"
            f"本次评估宗地所临路线价道路类型为{route_road_type or '待校核'}"
            f"{f'（由{road_type_source_text}确定）' if road_type_source_text else ''}，"
            f"标准深度为{standard_depth or '待校核'}米，估价对象临街深度为{frontage_depth_text}米，{depth_conclusion}。"
            f"根据{report}中《通道县城区宗地地价临街深度修正系数表》，确定估价对象临街深度修正系数Kd={kd}。"
        ),
        "benchmark_corr_kk": (
            f"临街宽度会影响商业服务业用地的展示面、可达性和实际利用价值。"
            f"本次评估估价对象临街宽度为{frontage_width_text}米，"
            f"根据{report}中《通道县城区临街宽度修正系数表》，确定估价对象临街宽度修正系数Kk={kk}。"
        ),
        "benchmark_corr_kc": (
            f"街角地是指同时临两条相互交叉路段的宗地，街角条件是影响商业服务业用地价格的重要微观因素之一。"
            f"街角地交通便利，人流、车流集聚程度通常较高，单位面积商业服务业用地收益能力相对较强。\n"
            f"在具体操作过程中，须注意以下几点：一是街角地修正范围为纵横里地线与临街线之间的区域；"
            f"二是街角地第一宗地以路线价较高的街道为正街、路线价较低的街道为旁街，其余宗地以直接紧邻街道为正街；"
            f"三是街角地地价计算公式为：Pml=Pz×Kc。\n"
            f"本次评估估价对象{'为街角地' if context.get('is_corner') else '非街角地'}。"
            + (
                f"相邻两条路线价分别为{corner_route_price_a or '待校核'}元/平方米、{corner_route_price_b or '待校核'}元/平方米，"
                f"系统以较高者{corner_main_route_price or '待校核'}元/平方米为正街地价，较低者{corner_side_route_price or '待校核'}元/平方米为旁街地价，"
                f"正街地价与旁街地价比例为{corner_ratio or '待校核'}，需进行街角地修正。"
                if context.get("is_corner")
                else "估价对象不属于街角地，故不需进行街角地修正。"
            )
            + f"根据{report}中《通道县商业服务业用地街角地修正系数表》，确定街角地修正系数Kc={kc}。"
        ),
        "benchmark_corr_ks": (
            f"土地面积对土地的利用有一定影响，过大或者过小均对土地的最佳利用产生不良影响。估价对象{area_label}为{area_value}平方米。"
            f"根据{report}，查《宗地面积修正系数表》，得估价对象宗地面积修正系数Ks={ks}。"
        ),
        "benchmark_corr_ka": (
            f"宗地形状对土地利用效率有一定影响。根据估价对象宗地形状条件，结合{report}中《宗地形状修正系数表》，"
            f"确定估价对象宗地形状优劣度为{context['ka_grade'] or '待校核'}，宗地形状修正系数Ka={ka}。"
        ),
        "benchmark_corr_ku": (
            f"商业服务业用地价值还受周边土地利用类型及商业集聚状况影响。"
            f"本次评估估价对象周边土地利用类型优劣度为{context.get('ku_grade') or '待校核'}，"
            f"根据{report}中《宗地周边土地利用类型修正系数表》，确定周边土地利用类型修正系数Ku={ku}。"
        ),
        "benchmark_corr_ke": (
            f"住宅用地受景观环境的影响越来越大。根据{report}中《居住用地宗地景观状况修正系数表》，"
            f"可得待估宗地景观环境修正系数Ke={ke}。"
        ),
        "benchmark_corr_kto": (
            f"通过现场勘查，所评估宗地地上住宅建筑物朝向为{context['orientation'] or '南'}，"
            f"根据{report}中《建筑物朝向修正系数表》，可得待估宗地建筑物朝向修正系数Kto={kto}。"
        ),
        "benchmark_corr_kf": (
            str(context.get("development_note") or "")
            or "本次评估待估宗地设定开发程度与基准地价内涵开发程度一致，故不需进行宗地开发程度修正，即 Kf=0。"
        ),
        "benchmark_corr_solve": (
            solve_text
        ),
    }


def _build_segment_sources(context: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """导出热区源。

    约定（与 CH-3 前端 benchmarkFocusId 对齐）：
    - 方法内部派生参数 field 使用 benchmark_corr_analysis.parameters.<key> 前缀；
    - 第二部分事实字段（set_plot_ratio / land_use_term / valuation_date / land_development_set）保持裸键，
      以命中前端 focus_item_* 主表单控件。
    """
    p = "benchmark_corr_analysis.parameters."
    base_price = _trim(context["base_price"])
    kv = _factor_text(context["kv"])
    ky = _factor_text(context["ky"])
    kt = _factor_text(context["kt"])
    sum_ki = _percent4_text(context["sum_ki"])
    ks = _trim(context["ks"])
    ka = _trim(context["ka"])
    ke = _trim(context["ke"])
    kto = _trim(context["kto"])
    ku = _factor_text(context.get("ku") or D1)
    kd = _factor_text(context.get("kd") or D1)
    kk = _factor_text(context.get("kk") or D1)
    kc = _factor_text(context.get("kc") or D1)
    route_price = _trim(context.get("route_price") or D0) if (context.get("route_price") or D0) > D0 else ""
    frontage_depth = _trim(context.get("frontage_depth_m") or D0) if (context.get("frontage_depth_m") or D0) > D0 else ""
    frontage_width = _trim(context.get("frontage_width_m") or D0) if (context.get("frontage_width_m") or D0) > D0 else ""
    frontage_standard_depth = _trim(context.get("frontage_standard_depth_m") or D0) if (context.get("frontage_standard_depth_m") or D0) > D0 else ""
    commercial_area = _trim(context.get("commercial_area_m2") or D0) if (context.get("commercial_area_m2") or D0) > D0 else ""
    frontage_area = _trim(context.get("frontage_area_m2") or D0) if (context.get("frontage_area_m2") or D0) > D0 else ""
    non_frontage_area = _trim(context.get("non_frontage_area_m2") or D0) if (context.get("non_frontage_area_m2") or D0) > D0 else ""
    route_component_price = _trim(context.get("route_component_price") or D0) if (context.get("route_component_price") or D0) > D0 else ""
    non_street_component_price = _trim(context.get("non_street_component_price") or D0) if (context.get("non_street_component_price") or D0) > D0 else ""
    corner_route_price_a = _trim(context.get("corner_route_price_a") or D0) if (context.get("corner_route_price_a") or D0) > D0 else ""
    corner_route_price_b = _trim(context.get("corner_route_price_b") or D0) if (context.get("corner_route_price_b") or D0) > D0 else ""
    corner_main_route_price = _trim(context.get("corner_main_route_price") or D0) if (context.get("corner_main_route_price") or D0) > D0 else ""
    corner_side_route_price = _trim(context.get("corner_side_route_price") or D0) if (context.get("corner_side_route_price") or D0) > D0 else ""
    corner_ratio = _trim(context.get("corner_price_ratio") or D0) if (context.get("corner_price_ratio") or D0) > D0 else ""
    valuation_date = str(context["valuation_date"] or "")
    plot_ratio = _trim(context["plot_ratio"]) if context["plot_ratio"] > D0 else ""
    land_use_term = _trim(context["land_use_term"]) if context["land_use_term"] > D0 else ""
    set_development = str(context.get("set_development") or "")
    base_development = str(context.get("base_development") or "")
    statutory_term = _trim(context["statutory_term"]) if context["statutory_term"] > D0 else ""
    cap_rate_pct = _percent_text(context["cap_rate"] * Decimal("100")) if context["cap_rate"] > D0 else ""
    months = _trim(context["months"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    monthly_pct = _percent_text(context["monthly_rate"] * Decimal("100"))
    usage = str(context.get("usage") or "")
    level = str(context.get("level") or "")
    land_area = _trim(context["land_area"]) if context["land_area"] > D0 else ""
    area_label = str(context.get("land_area_sentence_label") or "")
    solve_sources = []
    if _formula_has(context, "route_price"):
        solve_sources.append({"field": p + "route_price", "text": route_price, "kind": "value"})
    else:
        solve_sources.append({"field": p + "base_land_price", "text": base_price, "kind": "value"})
    if _formula_has(context, "ki"):
        solve_sources.append({"field": p + "sum_ki", "text": f"{sum_ki}%", "kind": "value"})
    for key, text in [
        ("ky", ky),
        ("kv", kv),
        ("kt", kt),
        ("ks", ks),
        ("ka", ka),
        ("ke", ke),
        ("kto", kto),
        ("ku", ku),
        ("kc", kc),
        ("kk", kk),
        ("kd", kd),
        ("kf", _trim(context["kf"])),
    ]:
        if _formula_has(context, key):
            solve_sources.append({"field": p + key, "text": text, "kind": "value"})
    if context.get("support_status") == "supported":
        solve_sources.append({"field": "benchmark_corr_price", "text": _trim(context["final_price"]), "kind": "value"})
    if _is_split_frontage(context):
        solve_sources.extend([
            {"field": p + "route_component_price", "text": route_component_price, "kind": "value"},
            {"field": p + "non_street_component_price", "text": non_street_component_price, "kind": "value"},
            {"field": p + "frontage_area_m2", "text": frontage_area, "kind": "value"},
            {"field": p + "non_frontage_area_m2", "text": non_frontage_area, "kind": "value"},
        ])

    sources: Dict[str, List[Dict[str, str]]] = {
        "benchmark_corr_base_price": [
            {"field": p + "base_date", "text": str(context.get("base_date") or ""), "kind": "value"},
        ],
        "benchmark_corr_po": [
            {"field": "benchmark_corr_analysis.land_use_type", "text": usage, "kind": "value"},
            {"field": "land_location_full", "text": str(context.get("land_location_full") or context.get("land_location_short") or ""), "kind": "value"},
            {"field": "benchmark_corr_analysis.land_level", "text": level, "kind": "value"},
            {"field": p + "base_land_price", "text": base_price, "kind": "value"},
            {"field": "benchmark_corr_analysis.route_segment_id", "text": str((context.get("route_segment") or {}).get("road_name") or ""), "kind": "value"},
            {"field": p + "route_price", "text": route_price, "kind": "value"},
        ],
        "benchmark_corr_formula": [],
        "benchmark_corr_kv": [
            {"field": "set_plot_ratio", "text": plot_ratio, "kind": "value"},
            {"field": p + "kv", "text": kv, "kind": "value"},
        ],
        "benchmark_corr_ky": [
            {"field": "land_use_term", "text": land_use_term, "kind": "value"},
            {"field": p + "legal_term_years", "text": statutory_term, "kind": "value"},
            {"field": p + "cap_rate", "text": f"{cap_rate_pct}%", "kind": "value"},
            {"field": p + "ky", "text": ky, "kind": "value"},
        ],
        "benchmark_corr_kt": [
            {"field": p + "months_elapsed", "text": months, "kind": "value"},
            {"field": p + "monthly_growth_rate", "text": f"{monthly_pct}%", "kind": "value"},
            {"field": p + "kt", "text": kt, "kind": "value"},
        ],
        "benchmark_corr_ki": [
            {"field": p + "sum_ki", "text": f"{sum_ki}%", "kind": "value"},
        ],
        "benchmark_corr_route_price": [
            {"field": "benchmark_corr_analysis.route_segment_id", "text": str((context.get("route_segment") or {}).get("road_name") or ""), "kind": "value"},
            {"field": p + "route_price", "text": route_price, "kind": "value"},
            {"field": p + "route_price_source_note", "text": str(context.get("route_price_source_note") or ""), "kind": "value"},
        ],
        "benchmark_corr_frontage_special_intro": [
            {"field": p + "commercial_area_m2", "text": commercial_area or land_area, "kind": "value"},
            {"field": p + "frontage_standard_depth_m", "text": frontage_standard_depth, "kind": "value"},
            {"field": p + "frontage_area_m2", "text": frontage_area, "kind": "value"},
            {"field": p + "non_frontage_area_m2", "text": non_frontage_area, "kind": "value"},
            {"field": "benchmark_corr_analysis.frontage_relation", "text": str(context.get("frontage_relation") or ""), "kind": "value"},
            {"field": "benchmark_corr_analysis.frontage_depth_m", "text": frontage_depth, "kind": "value"},
            {"field": "benchmark_corr_analysis.frontage_width_m", "text": frontage_width, "kind": "value"},
            {"field": p + "route_road_type", "text": str(context.get("route_road_type") or ""), "kind": "value"},
            {"field": p + "route_road_grade", "text": str(context.get("route_road_grade") or ""), "kind": "value"},
        ],
        "benchmark_corr_kd": [
            {"field": "benchmark_corr_analysis.frontage_depth_m", "text": frontage_depth, "kind": "value"},
            {"field": p + "route_road_type", "text": str(context.get("route_road_type") or ""), "kind": "value"},
            {"field": p + "route_road_grade", "text": str(context.get("route_road_grade") or ""), "kind": "value"},
            {"field": p + "kd", "text": kd, "kind": "value"},
        ],
        "benchmark_corr_kk": [
            {"field": "benchmark_corr_analysis.frontage_width_m", "text": frontage_width, "kind": "value"},
            {"field": p + "kk", "text": kk, "kind": "value"},
        ],
        "benchmark_corr_kc": [
            {"field": "benchmark_corr_analysis.corner_route_price_a", "text": corner_route_price_a, "kind": "value"},
            {"field": "benchmark_corr_analysis.corner_route_price_b", "text": corner_route_price_b, "kind": "value"},
            {"field": p + "corner_main_route_price", "text": corner_main_route_price, "kind": "value"},
            {"field": p + "corner_side_route_price", "text": corner_side_route_price, "kind": "value"},
            {"field": p + "corner_price_ratio", "text": corner_ratio, "kind": "value"},
            {"field": p + "kc", "text": kc, "kind": "value"},
        ],
        "benchmark_corr_ks": [
            {"field": "land_area_mode", "text": area_label, "kind": "value"},
            {"field": "land_area", "text": land_area, "kind": "value"},
            {"field": p + "ks", "text": ks, "kind": "value"},
        ],
        "benchmark_corr_ka": [
            {"field": p + "ka", "text": ka, "kind": "value"},
        ],
        "benchmark_corr_ku": [
            {"field": "benchmark_corr_analysis.ku_grade", "text": str(context.get("ku_grade") or ""), "kind": "value"},
            {"field": p + "ku", "text": ku, "kind": "value"},
        ],
        "benchmark_corr_ke": [
            {"field": p + "ke", "text": ke, "kind": "value"},
        ],
        "benchmark_corr_kto": [
            {"field": p + "kto", "text": kto, "kind": "value"},
        ],
        "benchmark_corr_solve": solve_sources,
        "benchmark_corr_kf": [
            {"field": p + "base_development", "text": base_development, "kind": "value"},
            {"field": "land_development_set", "text": set_development, "kind": "value"},
            {"field": p + "kf", "text": _trim(context["kf"]), "kind": "value"},
        ],
    }
    for key, factor in [
        ("benchmark_corr_kv", "kv"),
        ("benchmark_corr_ki", "ki"),
        ("benchmark_corr_ke", "ke"),
        ("benchmark_corr_kto", "kto"),
        ("benchmark_corr_route_price", "route_price"),
        ("benchmark_corr_frontage_special_intro", "route_price"),
        ("benchmark_corr_kd", "kd"),
        ("benchmark_corr_kk", "kk"),
        ("benchmark_corr_kc", "kc"),
        ("benchmark_corr_ku", "ku"),
    ]:
        if not _formula_has(context, factor):
            sources[key] = []
    if valuation_date:
        sources["benchmark_corr_kt"].insert(0, {"field": "valuation_date", "text": valuation_date, "kind": "value"})
    return {
        key: [item for item in items if str(item.get("text") or "").strip()]
        for key, items in sources.items()
    }
