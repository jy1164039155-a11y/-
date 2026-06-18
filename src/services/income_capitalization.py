# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List


D0 = Decimal("0")
D1 = Decimal("1")
WAN_QUANT = Decimal("0.0001")
MONEY_QUANT = Decimal("0.01")
PRICE_QUANT = Decimal("0.1")
FACTOR_QUANT = Decimal("0.0001")
INTEGER_QUANT = Decimal("1")
CASE_SLOTS = ("A", "B", "C")

BUILDING_PROFILE_REQUIRED_FIELDS = (
    ("building_form", "建筑物形态"),
    ("built_year", "建成年份"),
    ("floor_desc", "总层数"),
    ("owner_floor_desc", "权属楼层"),
    ("structure", "建筑结构"),
    ("exterior", "外墙情况"),
    ("entrance_door", "入户门"),
    ("windows", "窗户"),
    ("security_facilities", "防盗设施"),
    ("floor_finish", "地面情况"),
    ("ceiling_finish", "顶棚"),
    ("interior", "装修情况"),
    ("maintenance", "维护保养状况"),
    ("newness_desc", "房屋成新度描述"),
    ("economic_life_years", "经济耐用年限"),
    ("used_years", "已使用年限"),
    ("remaining_years", "剩余使用年限"),
    ("current_use_basis", "现状使用条件依据"),
    ("building_area_basis", "建筑面积依据"),
    ("land_area_basis", "土地面积依据"),
)

RENT_FACTOR_NARRATIVES = {
    "usage": "A、用途修正：估价对象与三个比较案例用途相同，因此不用做修正；",
    "transaction_time": "B、交易时间修正：估价对象与三个比较案例交易时间接近，因此不需要做时间修正；",
    "transaction_condition": "C、交易情况修正：估价对象与三个比较案例均是在正常情况下交易的，因此不做交易情况修正；",
    "commercial_prosperity": "a、商服繁华度：商服繁华度分为优、较优、一般、较劣、劣五个等级，以估价对象商服繁华度修正系数为100，每上升或下降一个级别，指数增加或减少2；",
    "bus_convenience": "b、公交便捷度：公交便捷度分为优、较优、一般、较劣、劣五个等级，以估价对象公交便捷度修正系数为100，每上升或下降一个级别，指数增加或减少2；",
    "road_accessibility": "c、道路通达度：道路通达度分为通畅、较通畅、一般通畅、较不通畅、不通畅五个等级，以估价对象道路通达度修正系数为100，每上升或下降一个级别，指数增加或减少2；",
    "infrastructure_guarantee": "d、水电等基础设施综合保证率：水电等基础设施综合保证率分为≥95%、[90，95]、≤90%三个等级，以估价对象为100，每上升或下降一个级别，指数增加或减少2；",
    "environment_quality": "e、环境质量：环境质量分为好、较好、一般、较差、差五个等级，以估价对象为100，每上升或下降一个级别，指数增加或减少2；",
    "public_facilities": "f、区域公共设施状况：区域公共设施状况分为齐全、较齐全、一般、较低、低五个等级，以估价对象为100，每上升或下降一个级别，指数增加或减少2；",
    "road_type": "a、所临道路类型：所临道路类型分为临主干道、临次干道、临支路、不临路等级别，以估价对象指数为100，每上升或下降一个级别，指数增加或减少2；",
    "ventilation_lighting": "b、通风采光：通风采光分为好、较好、一般、较差、差五个等级，以估价对象条件指数为100，每上升或下降一个级别，指数增加或减少1；",
    "newness": "c、房屋成新度：以估价对象成新度为100，每上升或下降一个级别，指数增加或减少4；",
    "building_structure": "d、建筑物结构：建筑物结构分为框架、钢混、砖混、砖木等四个等级，以估价对象为100，每上升或下降一个级别，指数增加或减少2；",
    "internal_layout": "e、建筑物内部格局：建筑物内部格局分为合理、较合理、不合理三个等级，以估价对象为100，每上升或下降一个级别，指数增加或减少1；",
    "decoration": "f、装修档次：装修档次分为毛坯、简单装修、中档装修、中高档装修、高档装修五个等级，以估价对象为100，每上升或下降一个级别，指数增加或减少2；",
    "parking": "g、停车情况：停车情况分为能满足停车需求、基本满足停车需求、不能满足停车需求三个等级，以估价对象条件指数为100，每上升或下降一个级别，指数增加或减少2；",
    "property_management": "h、物业情况：物业情况分为无物业管理、物业管理一般、物业管理较好三个等级，以估价对象为100，每上升或下降一个级别，指数增加或减少2。",
}


RENT_FACTOR_DEFS = (
    ("usage", "交易因素", "用途", "住宅", "同为住宅用途时不作修正。", "2"),
    ("transaction_time", "交易因素", "交易时间", "估价期日", "交易时间与估价期日接近时不作修正。", "2"),
    ("transaction_condition", "交易因素", "交易情况", "正常交易", "正常交易不作修正。", "2"),
    ("commercial_prosperity", "区域因素", "商服繁华度", "较优", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("bus_convenience", "区域因素", "公交便捷度", "较优", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("road_accessibility", "区域因素", "道路通达度", "较通畅", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("infrastructure_guarantee", "区域因素", "水电等基础设施综合保证率", "≥95%", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("environment_quality", "区域因素", "环境质量", "好", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("public_facilities", "区域因素", "区域公共设施状况", "齐全", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("road_type", "个别因素", "所临道路类型", "临主干道", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("ventilation_lighting", "个别因素", "通风采光", "好", "以估价对象为100，每相差一个等级修正1个指数点。", "1"),
    ("newness", "个别因素", "房屋成新度", "七成新", "以估价对象为100，每相差一个等级修正4个指数点。", "4"),
    ("building_structure", "个别因素", "建筑物结构", "砖混", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("internal_layout", "个别因素", "建筑物内部格局", "合理", "以估价对象为100，每相差一个等级修正1个指数点。", "1"),
    ("decoration", "个别因素", "装修档次", "简单装修", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("parking", "个别因素", "停车情况", "基本满足停车需求", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
    ("property_management", "个别因素", "物业情况", "无物业管理", "以估价对象为100，每相差一个等级修正2个指数点。", "2"),
)

RENT_FACTOR_SCALES: Dict[str, Dict[str, Any]] = {
    "usage": {"scale_type": "equality", "values": [], "step": "0"},
    "transaction_time": {"scale_type": "equality_month", "values": [], "step": "0"},
    "transaction_condition": {"scale_type": "equality", "values": ["正常交易", "非正常交易"], "step": "0"},
    "commercial_prosperity": {"scale_type": "ordered", "values": ["优", "较优", "一般", "较劣", "劣"], "step": "2"},
    "bus_convenience": {"scale_type": "ordered", "values": ["优", "较优", "一般", "较劣", "劣"], "step": "2"},
    "road_accessibility": {"scale_type": "ordered", "values": ["通畅", "较通畅", "一般通畅", "较不通畅", "不通畅"], "step": "2"},
    "infrastructure_guarantee": {"scale_type": "ordered", "values": ["≥95%", "90%-<95%", "<90%"], "step": "2"},
    "environment_quality": {"scale_type": "ordered", "values": ["好", "较好", "一般", "较差", "差"], "step": "2"},
    "public_facilities": {"scale_type": "ordered", "values": ["齐全", "较齐全", "一般", "较低", "低"], "step": "2"},
    "road_type": {"scale_type": "ordered", "values": ["临主干道", "临次干道", "临支路", "不临路"], "step": "1"},
    "ventilation_lighting": {"scale_type": "ordered", "values": ["好", "较好", "一般", "较差", "差"], "step": "1"},
    "newness": {
        "scale_type": "ordered",
        "values": ["十成新", "九成新", "八成新", "七成新", "六成新", "五成新", "四成新", "三成新", "二成新", "一成新"],
        "step": "4",
    },
    "building_structure": {"scale_type": "ordered", "values": ["框架", "钢混", "砖混", "砖木"], "step": "2"},
    "internal_layout": {"scale_type": "ordered", "values": ["合理", "较合理", "不合理"], "step": "1"},
    "decoration": {"scale_type": "ordered", "values": ["高档", "中高档", "中档", "简单装修", "毛坯"], "step": "2"},
    "parking": {"scale_type": "ordered", "values": ["能满足停车需求", "基本满足停车需求", "不能满足停车需求"], "step": "2"},
    "property_management": {"scale_type": "ordered", "values": ["物业管理较好", "物业管理一般", "无物业管理"], "step": "2"},
}

RENT_FACTOR_VALUE_ALIASES = {
    "95%": "≥95%",
    "大于等于95%": "≥95%",
    "砖混结构": "砖混",
    "钢混结构": "钢混",
    "框架结构": "框架",
    "砖木结构": "砖木",
    "基本满足停车": "基本满足停车需求",
    "能满足停车": "能满足停车需求",
    "不能满足停车": "不能满足停车需求",
    "无": "无物业管理",
}
GENERIC_RENT_FACTOR_LEVELS = ["优", "较优", "一般", "较劣", "劣"]

RENT_USAGE_OPTIONS = (
    ("residential", "住宅"),
    ("commercial", "商业"),
    ("office", "办公"),
    ("industrial", "工业"),
    ("warehouse", "仓储"),
    ("other", "其他"),
)

RESIDENTIAL_CONSTRUCTION_COST_SOURCE = "《湖南省建筑物建设成本参考标准研究成果》（湘房协〔2023〕3号，价值时点2023年1月1日）"

RESIDENTIAL_CONSTRUCTION_COST_STANDARDS = {
    "steel_concrete_1": {"structure": "钢混结构", "grade": "一等", "min": "2300", "max": "2500"},
    "steel_concrete_2": {"structure": "钢混结构", "grade": "二等", "min": "1900", "max": "2100"},
    "steel_concrete_3": {"structure": "钢混结构", "grade": "三等", "min": "1700", "max": "1900"},
    "steel_concrete_4": {"structure": "钢混结构", "grade": "四等", "min": "1500", "max": "1700"},
    "brick_concrete_1": {"structure": "砖混结构", "grade": "一等", "min": "1300", "max": "1400"},
    "brick_concrete_2": {"structure": "砖混结构", "grade": "二等", "min": "1200", "max": "1300"},
    "brick_wood": {"structure": "砖木结构", "grade": "/", "min": "900", "max": "1000"},
    "simple": {"structure": "简易结构", "grade": "/", "min": "350", "max": "500"},
}

RENT_FACTOR_PREFIXES = {
    "usage": "A、用途修正",
    "transaction_time": "B、交易时间修正",
    "transaction_condition": "C、交易情况修正",
    "commercial_prosperity": "a、商服繁华度",
    "bus_convenience": "b、公交便捷度",
    "road_accessibility": "c、道路通达度",
    "infrastructure_guarantee": "d、水电等基础设施综合保证率",
    "environment_quality": "e、环境质量",
    "public_facilities": "f、区域公共设施状况",
    "road_type": "a、所临道路类型",
    "ventilation_lighting": "b、通风采光",
    "newness": "c、房屋成新度",
    "building_structure": "d、建筑物结构",
    "internal_layout": "e、建筑物内部格局",
    "decoration": "f、装修档次",
    "parking": "g、停车情况",
    "property_management": "h、物业情况",
}


def _decimal(value: Any, default: Decimal = D0) -> Decimal:
    if value in (None, ""):
        return default
    text = str(value).strip().replace(",", "").replace("%", "").replace("‰", "")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return default


def _percent_decimal(value: Any) -> Decimal:
    return _decimal(value) / Decimal("100")


def _permille_decimal(value: Any) -> Decimal:
    return _decimal(value) / Decimal("1000")


def _fmt(value: Decimal, quant: Decimal) -> str:
    return format(value.quantize(quant, rounding=ROUND_HALF_UP), "f")


def _wan(value: Decimal) -> str:
    return _fmt(value, WAN_QUANT)


def _money(value: Decimal) -> str:
    return _fmt(value, MONEY_QUANT)


def _price(value: Decimal) -> str:
    return _fmt(value, PRICE_QUANT)


def _factor(value: Decimal) -> str:
    return _fmt(value, FACTOR_QUANT)


def _integer(value: Decimal) -> str:
    return _fmt(value, INTEGER_QUANT)


def _strip_display_suffix(value: Any, suffix: str) -> str:
    text = str(value or "").strip()
    if text and not text.startswith("【") and text.endswith(suffix):
        return text[: -len(suffix)].strip()
    return text


def _strip_display_prefix(value: Any, prefix: str) -> str:
    text = str(value or "").strip()
    if text and not text.startswith("【") and text.startswith(prefix):
        return text[len(prefix) :].strip()
    return text


def _book_title_display(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.startswith("【"):
        return text
    if text.startswith("《") and text.endswith("》"):
        return text
    return f"《{text}》"


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "是", "已确认"}


def _first_number(value: Any, default: Decimal = D0) -> Decimal:
    match = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return _decimal(match.group(0), default) if match else default


def _parse_date(value: Any) -> date | None:
    numbers = [int(item) for item in re.findall(r"\d+", str(value or ""))[:3]]
    if len(numbers) != 3:
        return None
    try:
        return date(numbers[0], numbers[1], numbers[2])
    except ValueError:
        return None


def _normalize_usage_key(value: Any, fallback: str = "residential") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    valid_keys = {key for key, _ in RENT_USAGE_OPTIONS}
    if text in valid_keys:
        return text
    if any(item in text for item in ("住宅", "居住", "公寓")):
        return "residential"
    if any(item in text for item in ("商业", "商服", "商铺", "门面", "零售")):
        return "commercial"
    if any(item in text for item in ("办公", "写字楼")):
        return "office"
    if any(item in text for item in ("工业", "厂房", "工矿")):
        return "industrial"
    if any(item in text for item in ("仓储", "仓库", "物流")):
        return "warehouse"
    return "other"


def _usage_label(usage_key: Any, other: Any = "", fallback: Any = "") -> str:
    key = str(usage_key or "").strip()
    if key == "other":
        return str(other or fallback or "").strip()
    labels = dict(RENT_USAGE_OPTIONS)
    return labels.get(key) or str(fallback or "").strip()


def _normalize_cost_structure_key(value: Any, fallback_text: Any = "") -> str:
    text = str(value or fallback_text or "").strip()
    if text in {"steel_concrete", "brick_concrete", "brick_wood", "simple"}:
        return text
    if text in {"steel_concrete_1", "steel_concrete_2", "steel_concrete_3", "steel_concrete_4"}:
        return "steel_concrete"
    if text in {"brick_concrete_1", "brick_concrete_2"}:
        return "brick_concrete"
    if "简易" in text:
        return "simple"
    if "砖木" in text:
        return "brick_wood"
    if any(item in text for item in ("钢混", "钢筋混凝土", "框架", "混凝土")):
        return "steel_concrete"
    return "brick_concrete"


def _normalize_cost_grade_key(structure_key: str, value: Any = "", floor_desc: Any = "") -> str:
    text = str(value or "").strip()
    if text in {"1", "一", "一等"}:
        return "1"
    if text in {"2", "二", "二等"}:
        return "2"
    if text in {"3", "三", "三等"}:
        return "3"
    if text in {"4", "四", "四等"}:
        return "4"
    if structure_key == "steel_concrete":
        floors = _first_number(floor_desc)
        if floors >= Decimal("34"):
            return "1"
        if floors >= Decimal("18"):
            return "2"
        if floors >= Decimal("8"):
            return "3"
        return "4"
    if structure_key == "brick_concrete":
        if "二" in text:
            return "2"
        return "1"
    return ""


def _residential_cost_standard_key(structure_key: str, grade_key: str = "") -> str:
    if structure_key == "steel_concrete":
        return f"steel_concrete_{grade_key or '4'}"
    if structure_key == "brick_concrete":
        return f"brick_concrete_{grade_key or '1'}"
    if structure_key == "brick_wood":
        return "brick_wood"
    if structure_key == "simple":
        return "simple"
    return "brick_concrete_1"


def residential_cost_standard_options() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for key, item in RESIDENTIAL_CONSTRUCTION_COST_STANDARDS.items():
        rows.append(
            {
                "key": key,
                "structure": item["structure"],
                "grade": item["grade"],
                "min": item["min"],
                "max": item["max"],
                "range_label": f"{item['min']}-{item['max']}",
                "source_doc": RESIDENTIAL_CONSTRUCTION_COST_SOURCE,
            }
        )
    return rows


def _rental_property_label(instances: Iterable[Dict[str, Any]], data: Dict[str, Any]) -> str:
    source = ""
    for item in instances:
        source = str(item.get("usage") or "").strip()
        if source:
            break
    if not source:
        source = str(data.get("land_usage") or "住宅").strip()
    source = source.replace("用地", "").replace("用途", "").strip() or "住宅"
    if source.endswith("用房") or source.endswith("物业"):
        return source
    if source in {"住宅", "居住"}:
        return "住宅用房"
    return f"{source}用房"


def _elapsed_years(start: Any, end: Any) -> Decimal:
    start_date = _parse_date(start)
    end_date = _parse_date(end)
    if not start_date or not end_date or end_date < start_date:
        return D0
    return Decimal(end_date.toordinal() - start_date.toordinal()) / Decimal("365")


def _normalize_factor_value(key: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if key == "usage":
        usage_key = _normalize_usage_key(text, fallback="other")
        return _usage_label(usage_key, text if usage_key == "other" else "", text)
    if key == "transaction_time":
        parsed = _parse_date(text)
        if parsed:
            return f"{parsed.year:04d}.{parsed.month:02d}"
        numbers = re.findall(r"\d+", text)
        if len(numbers) >= 2:
            return f"{int(numbers[0]):04d}.{int(numbers[1]):02d}"
        return text
    if key == "transaction_condition":
        if text in {"正常", "正常交易", "正常市场交易"}:
            return "正常交易"
        if any(item in text for item in ("非正常", "异常", "关联交易", "特殊交易")):
            return "非正常交易"
    normalized = RENT_FACTOR_VALUE_ALIASES.get(text, text)
    values = RENT_FACTOR_SCALES.get(key, {}).get("values") or []
    if normalized in values:
        return normalized
    if normalized in GENERIC_RENT_FACTOR_LEVELS and values:
        generic_index = GENERIC_RENT_FACTOR_LEVELS.index(normalized)
        target_index = int(
            (
                Decimal(generic_index)
                * Decimal(len(values) - 1)
                / Decimal(len(GENERIC_RENT_FACTOR_LEVELS) - 1)
            ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        return values[target_index]
    contained_values = [candidate for candidate in values if candidate in normalized or normalized in candidate]
    if contained_values:
        return max(contained_values, key=len)
    return normalized


def _factor_levels(key: str, subject_value: Any = "") -> List[Dict[str, Any]]:
    scale = RENT_FACTOR_SCALES.get(key) or {}
    values = scale.get("values") or []
    step = _decimal(scale.get("step"), D0)
    subject = _normalize_factor_value(key, subject_value)
    subject_score = None
    if subject in values:
        subject_score = len(values) - values.index(subject)
    levels: List[Dict[str, Any]] = []
    for index, value in enumerate(values):
        quality_score = len(values) - index
        relative_index = ""
        if subject_score is not None:
            relative_index = _money(Decimal("100") + Decimal(quality_score - subject_score) * step)
        levels.append(
            {
                "label": value,
                "value": value,
                "quality_score": quality_score,
                "index": relative_index,
                "description": f"条件为{value}",
            }
        )
    return levels


def _factor_case_index(key: str, subject_value: Any, case_value: Any) -> str:
    scale = RENT_FACTOR_SCALES.get(key) or {}
    subject = _normalize_factor_value(key, subject_value)
    case = _normalize_factor_value(key, case_value)
    if not subject or not case:
        return ""
    if scale.get("scale_type") in {"equality", "equality_month"}:
        return "100.00" if subject == case else ""
    values = scale.get("values") or []
    if subject not in values or case not in values:
        return ""
    subject_score = len(values) - values.index(subject)
    case_score = len(values) - values.index(case)
    return _money(Decimal("100") + Decimal(case_score - subject_score) * _decimal(scale.get("step"), D0))


def _default_rent_instances(data: Dict[str, Any], existing: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing_by_slot = {
        str(item.get("slot") or CASE_SLOTS[index] if index < len(CASE_SLOTS) else "").upper(): dict(item)
        for index, item in enumerate(existing or [])
    }
    result: List[Dict[str, Any]] = []
    for slot in CASE_SLOTS:
        item = existing_by_slot.get(slot, {})
        usage_key = str(item.get("usage_key") or "").strip() or _normalize_usage_key(
            item.get("usage") or data.get("land_usage")
        )
        usage_other = str(item.get("usage_other") or "").strip()
        usage = _usage_label(usage_key, usage_other, item.get("usage") or data.get("land_usage") or "住宅")
        result.append(
            {
                "slot": slot,
                "name": item.get("name") or "",
                "location": item.get("location") or "",
                "monthly_rent": str(item.get("monthly_rent") or ""),
                "transaction_date": item.get("transaction_date") or data.get("valuation_date") or "",
                "usage_key": usage_key,
                "usage_other": usage_other,
                "usage": usage,
                "description": item.get("description") or "",
                "photo_data": item.get("photo_data") or "",
                "photo_name": item.get("photo_name") or "",
                "location_image_data": item.get("location_image_data") or "",
                "location_image_name": item.get("location_image_name") or "",
                "confirmed": bool(item.get("confirmed", False)),
            }
        )
    return result


def _default_rent_factors(
    data: Dict[str, Any],
    existing: Iterable[Dict[str, Any]],
    instances: Iterable[Dict[str, Any]],
    profile: Dict[str, Any],
) -> List[Dict[str, Any]]:
    existing_by_key = {str(item.get("key") or ""): dict(item) for item in existing or []}
    instance_by_slot = {str(item.get("slot") or "").upper(): dict(item) for item in instances or []}
    result: List[Dict[str, Any]] = []
    for key, group, label, default_subject, help_text, step in RENT_FACTOR_DEFS:
        existing_item = existing_by_key.get(key, {})
        subject_value = existing_item.get("subject_value") or default_subject
        if key == "usage":
            subject_value = existing_item.get("subject_value") or profile.get("actual_use") or data.get("land_usage") or default_subject
        elif key == "transaction_time":
            subject_value = existing_item.get("subject_value") or data.get("valuation_date") or default_subject
        elif key == "transaction_condition":
            subject_value = existing_item.get("subject_value") or "正常交易"
        elif key == "newness":
            subject_value = existing_item.get("subject_value") or profile.get("newness_desc") or default_subject
        elif key == "building_structure":
            subject_value = existing_item.get("subject_value") or profile.get("structure") or default_subject
        elif key == "decoration":
            subject_value = existing_item.get("subject_value") or profile.get("interior") or default_subject
        subject_value = _normalize_factor_value(key, subject_value)
        scale = RENT_FACTOR_SCALES.get(key) or {}
        scale_values = scale.get("values") or []
        if scale.get("scale_type") == "ordered" and subject_value not in scale_values:
            subject_value = _normalize_factor_value(key, default_subject)
        if scale.get("scale_type") == "ordered" and subject_value not in scale_values and scale_values:
            subject_value = scale_values[len(scale_values) // 2]
        cases = {}
        existing_cases = existing_item.get("cases") or {}
        for slot in CASE_SLOTS:
            case = dict(existing_cases.get(slot) or {})
            instance = instance_by_slot.get(slot, {})
            auto_value = ""
            auto_source = ""
            if key == "usage":
                auto_value = instance.get("usage") or ""
                auto_source = "rent_instance"
            elif key == "transaction_time":
                auto_value = instance.get("transaction_date") or ""
                auto_source = "rent_instance"
            elif key == "transaction_condition":
                auto_value = "正常交易"
                auto_source = "system_default"
            auto_value = _normalize_factor_value(key, auto_value)
            source = str(case.get("source") or "").strip()
            current_value = _normalize_factor_value(key, case.get("value"))
            current_index = str(case.get("index") or "").strip()
            preliminary_value = current_value or auto_value
            inferred_existing_index = _factor_case_index(key, subject_value, preliminary_value)
            manual_override = source == "manual_override" or (
                source == "manual"
                and (
                    (current_value and auto_value and current_value != auto_value)
                    or (current_index and inferred_existing_index and _decimal(current_index) != _decimal(inferred_existing_index))
                )
            ) or (
                current_index
                and _decimal(current_index) != Decimal("100")
                and (not inferred_existing_index or _decimal(current_index) != _decimal(inferred_existing_index))
            )
            value = current_value if manual_override or not auto_value else auto_value
            if not value:
                value = current_value
            inferred_index = _factor_case_index(key, subject_value, value)
            if manual_override and current_index:
                factor_index = current_index
            elif inferred_index:
                factor_index = inferred_index
            else:
                factor_index = current_index if source in {"manual", "manual_override"} else ""
            cases[slot] = {
                "value": value,
                "level_label": _normalize_factor_value(key, case.get("level_label") or value),
                "index": factor_index,
                "source": "manual_override" if manual_override else (auto_source if auto_value else (source or "manual")),
                "override_reason": case.get("override_reason") or "",
                "confirmed": bool(case.get("confirmed", False)),
            }
        result.append(
            {
                "key": key,
                "group": group,
                "label": label,
                "subject_value": subject_value,
                "subject_level_label": _normalize_factor_value(key, existing_item.get("subject_level_label") or subject_value),
                "subject_index": "100",
                "help_text": existing_item.get("help_text") or help_text,
                "scale_type": scale.get("scale_type") or "ordered",
                "step": str(scale.get("step") or step or "0"),
                "levels": _factor_levels(key, subject_value),
                "required": bool(existing_item.get("required", True)),
                "review_status": existing_item.get("review_status") or "pending",
                "cases": cases,
            }
        )
    return result


def _building_profile(data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    profile = dict(analysis.get("building_profile") or {})
    valuation_year = _parse_date(data.get("valuation_date"))
    built_year = str(profile.get("built_year") or "").strip()
    used_years = profile.get("used_years")
    if not built_year and used_years not in (None, "") and valuation_year:
        try:
            built_year = str(valuation_year.year - int(_first_number(str(used_years))))
        except Exception:
            pass
    if not built_year:
        built_year = ""
    used_years = profile.get("used_years")
    if used_years in (None, "") and built_year and valuation_year:
        try:
            used_years = max(valuation_year.year - int(_first_number(built_year)), 0)
        except Exception:
            pass
    economic_life = str(profile.get("economic_life_years") or "50")
    used_years = str(used_years if used_years not in (None, "") else "")
    remaining_years = profile.get("remaining_years")
    if remaining_years in (None, "") and used_years:
        remaining_years = _decimal(economic_life) - _decimal(used_years)
    building_area = str(profile.get("building_area") or data.get("building_area") or "")
    land_area = str(profile.get("land_area") or data.get("land_area") or "")
    plot_ratio = str(
        data.get("set_plot_ratio_display")
        or data.get("set_plot_ratio")
        or profile.get("set_plot_ratio")
        or profile.get("plot_ratio")
        or ""
    )
    condition_type = str(data.get("valuation_condition_type") or "").strip()
    default_use_condition = "规划利用条件" if condition_type == "规划" else "现状使用条件" if condition_type == "现状" else condition_type
    location_candidates = [
        ("room_detail_location", data.get("room_detail_location")),
        ("land_location_full", data.get("land_location_full")),
        ("building_location", profile.get("building_location")),
        ("land_location", data.get("land_location")),
    ]
    location_source_ref = "building_location"
    building_location = ""
    for ref, value in location_candidates:
        text = str(value or "").strip()
        if text and text not in {"待校核", "【待校核】", "______"} and len(text) > 1:
            location_source_ref = ref
            building_location = text
            break
    if location_source_ref == "building_location":
        location_source_ref = "income_cap_analysis.building_profile.building_location"
    return {
        "building_location": building_location,
        "building_location_source_ref": location_source_ref,
        "building_form": profile.get("building_form") or "",
        "built_year": built_year,
        "floor_desc": profile.get("floor_desc") or "",
        "owner_floor_desc": profile.get("owner_floor_desc") or "",
        "structure": profile.get("structure") or "砖混结构",
        "exterior": profile.get("exterior") or "",
        "entrance_door": profile.get("entrance_door") or "",
        "windows": profile.get("windows") or "",
        "security_facilities": profile.get("security_facilities") or "",
        "floor_finish": profile.get("floor_finish") or "",
        "ceiling_finish": profile.get("ceiling_finish") or "",
        "interior": profile.get("interior") or "简单装修",
        "maintenance": profile.get("maintenance") or "维护保养状况一般",
        "newness_rate": str(profile.get("newness_rate") or "70"),
        "newness_desc": profile.get("newness_desc") or "",
        "economic_life_years": economic_life,
        "used_years": used_years,
        "remaining_years": str(remaining_years if remaining_years not in (None, "") else ""),
        "building_area": building_area,
        "land_area": land_area,
        "actual_use": profile.get("actual_use") or data.get("land_usage") or "",
        "current_use_condition": default_use_condition or profile.get("current_use_condition") or "",
        "current_use_condition_manual": False,
        "current_use_basis": profile.get("current_use_basis") or "《评估委托书》",
        "building_area_basis": profile.get("building_area_basis") or "《不动产测绘报告书》",
        "land_area_basis": profile.get("land_area_basis") or "《宗地图》",
        "plot_ratio": plot_ratio,
        "set_plot_ratio": plot_ratio,
    }


def _income_parameters(analysis: Dict[str, Any]) -> Dict[str, str]:
    params = dict(analysis.get("income_parameters") or {})
    return {
        "vacancy_rate_range": str(params.get("vacancy_rate_range") or ""),
        "vacancy_rate": str(params.get("vacancy_rate") or ""),
        "rentable_area_ratio": str(params.get("rentable_area_ratio") or ""),
    }


def _expense_parameters(data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, str]:
    params = dict(analysis.get("expense_parameters") or {})
    profile = dict(analysis.get("building_profile") or {})
    valuation_date = str(data.get("valuation_date") or "")
    structure_key = _normalize_cost_structure_key(params.get("replacement_cost_structure_key"), profile.get("structure"))
    grade_key = _normalize_cost_grade_key(structure_key, params.get("replacement_cost_grade_key"), profile.get("floor_desc"))
    standard_key = str(params.get("replacement_cost_standard_key") or "").strip()
    if standard_key in RESIDENTIAL_CONSTRUCTION_COST_STANDARDS:
        standard = RESIDENTIAL_CONSTRUCTION_COST_STANDARDS[standard_key]
        structure_key = _normalize_cost_structure_key(standard.get("structure"))
        grade_key = _normalize_cost_grade_key(structure_key, standard.get("grade"))
    else:
        standard_key = _residential_cost_standard_key(structure_key, grade_key)
        standard = RESIDENTIAL_CONSTRUCTION_COST_STANDARDS.get(
            standard_key,
            RESIDENTIAL_CONSTRUCTION_COST_STANDARDS["brick_concrete_1"],
        )
    range_min = str(params.get("replacement_cost_range_min") or standard["min"])
    range_max = str(params.get("replacement_cost_range_max") or standard["max"])
    adopted = str(params.get("replacement_base_unit_cost") or range_max)
    adopted_source = str(params.get("replacement_cost_adopted_source") or "").strip()
    if not adopted_source:
        adopted_source = "range_max_default" if adopted == range_max else "manual_override"
    return {
        "management_rate": str(params.get("management_rate") or "2"),
        "repair_rate": str(params.get("repair_rate") or "2"),
        "replacement_cost_standard_key": standard_key,
        "replacement_cost_structure_key": structure_key,
        "replacement_cost_grade_key": grade_key,
        "replacement_cost_structure_label": str(standard.get("structure") or ""),
        "replacement_cost_grade_label": str(standard.get("grade") or ""),
        "replacement_cost_range_min": range_min,
        "replacement_cost_range_max": range_max,
        "replacement_cost_range_label": f"{range_min}-{range_max}",
        "replacement_cost_default_unit_cost": range_max,
        "replacement_cost_source_doc": str(params.get("replacement_cost_source_doc") or RESIDENTIAL_CONSTRUCTION_COST_SOURCE),
        "replacement_cost_adopted_source": adopted_source,
        "replacement_cost_override_reason": str(params.get("replacement_cost_override_reason") or ""),
        "replacement_base_unit_cost": adopted,
        "regional_adjustment_coefficient": str(params.get("regional_adjustment_coefficient") or "0.90"),
        "cost_growth_rate": str(params.get("cost_growth_rate") or "2"),
        "cost_base_date": str(params.get("cost_base_date") or "2023-01-01"),
        "valuation_date": str(params.get("valuation_date") or valuation_date),
        "residual_rate": str(params.get("residual_rate") or "2"),
        "insurance_rate_permille": str(params.get("insurance_rate_permille") or "2"),
        "property_tax_rate": str(params.get("property_tax_rate") or "4"),
        "property_tax_reduction_rate": str(params.get("property_tax_reduction_rate") or "50"),
        "vat_exempt": bool(params.get("vat_exempt", True)),
    }


def _cap_rate_parameters(data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, str]:
    params = dict(analysis.get("cap_rate_parameters") or {})
    return {
        "land_usage": str(params.get("land_usage") or data.get("land_usage") or "住宅用地"),
        "income_land_cap_rate": str(params.get("income_land_cap_rate") or "6.5"),
        "income_building_cap_rate": str(params.get("income_building_cap_rate") or "8.5"),
        "use_term_years": str(params.get("use_term_years") or _first_number(data.get("land_use_term"), Decimal("70")) or "70"),
        "source_note": str(params.get("source_note") or "土地纯收益与价格比率法、投资收益法测算确定"),
        "confirmed": bool(params.get("confirmed", False)),
    }


def _case_factor_coefficient(factors: Iterable[Dict[str, Any]], slot: str) -> Decimal:
    coefficient = D1
    for factor in factors:
        if not factor.get("required", True):
            continue
        subject_index = _decimal(factor.get("subject_index"), Decimal("100"))
        case = (factor.get("cases") or {}).get(slot) or {}
        case_index = _decimal(case.get("index"), Decimal("100"))
        if subject_index <= D0 or case_index <= D0:
            continue
        coefficient *= subject_index / case_index
    return coefficient


def _factor_case_coefficient(factor: Dict[str, Any], slot: str) -> str:
    subject_index = _decimal(factor.get("subject_index"), Decimal("100"))
    case = (factor.get("cases") or {}).get(slot) or {}
    case_index = _decimal(case.get("index"), Decimal("100"))
    if subject_index <= D0 or case_index <= D0:
        return "待校核"
    return _factor(subject_index / case_index)


def _rent_calculations(instances: List[Dict[str, Any]], factors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for item in instances:
        slot = str(item.get("slot") or "").upper()
        rent = _decimal(item.get("monthly_rent"))
        coefficient = _case_factor_coefficient(factors, slot)
        corrected = rent * coefficient
        rows.append(
            {
                "slot": slot,
                "monthly_rent": _money(rent) if rent else "",
                "correction_coefficient": _factor(coefficient),
                "corrected_monthly_rent": _money(corrected) if rent else "",
            }
        )
    return rows


def _factor_cell_refs(factor: Dict[str, Any], *, mode: str) -> List[str]:
    key = str(factor.get("key") or "")
    if mode in {"condition", "index"}:
        field_name = "value" if mode == "condition" else "index"
        return [
            "",
            f"income_cap_analysis.rent_factor_items.{key}.subject_value",
            *[
                f"income_cap_analysis.rent_factor_items.{key}.cases.{slot}.{field_name}"
                for slot in CASE_SLOTS
            ],
        ]
    return [
        "",
        *[
            f"income_cap_analysis.rent_factor_items.{key}.cases.{slot}.index"
            for slot in CASE_SLOTS
        ],
    ]


def _factor_rows(
    factors: List[Dict[str, Any]],
    instances: List[Dict[str, Any]],
    *,
    mode: str,
    subject_location: str = "",
    subject_location_ref: str = "income_cap_analysis.building_profile.building_location",
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    instance_by_slot = {item.get("slot"): item for item in instances}
    if mode in {"condition", "index"}:
        rows.extend(
            [
                {
                    "cells": [
                        "位置",
                        subject_location or "待校核",
                        *[(instance_by_slot.get(slot) or {}).get("location") or "待校核" for slot in CASE_SLOTS],
                    ],
                    "cell_refs": [
                        "",
                        subject_location_ref,
                        *[f"income_cap_analysis.rent_instances.{slot}.location" for slot in CASE_SLOTS],
                    ],
                },
                {
                    "cells": [
                        "住宅租金(元/m2·月)",
                        "待估",
                        *[
                            (instance_by_slot.get(slot) or {}).get("monthly_rent") or "待校核"
                            for slot in CASE_SLOTS
                        ],
                    ],
                    "cell_refs": [
                        "",
                        "",
                        *[f"income_cap_analysis.rent_instances.{slot}.monthly_rent" for slot in CASE_SLOTS],
                    ],
                },
            ]
        )
    for factor in factors:
        cases = factor.get("cases") or {}
        if mode == "condition":
            values = [
                factor.get("label"),
                factor.get("subject_value") or "待校核",
                *[(cases.get(slot) or {}).get("value") or "待校核" for slot in CASE_SLOTS],
            ]
        elif mode == "index":
            values = [
                factor.get("label"),
                factor.get("subject_index") or "100",
                *[(cases.get(slot) or {}).get("index") or "待校核" for slot in CASE_SLOTS],
            ]
        else:
            values = [
                factor.get("label"),
                *[
                    f"{factor.get('subject_index') or '100'}/{(cases.get(slot) or {}).get('index') or '待校核'}"
                    if _decimal((cases.get(slot) or {}).get("index"), Decimal("100")) > D0
                    else "待校核"
                    for slot in CASE_SLOTS
                ],
            ]
        rows.append({"cells": [str(value or "") for value in values], "cell_refs": _factor_cell_refs(factor, mode=mode)})
    return rows


def _table_sections(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    instances = analysis.get("rent_instances") or []
    factors = analysis.get("rent_factor_items") or []
    calculations = {item.get("slot"): item for item in analysis.get("rent_calculations") or []}
    profile = analysis.get("building_profile") or {}
    subject_location = profile.get("building_location") or "待校核"
    subject_location_ref = profile.get("building_location_source_ref") or "income_cap_analysis.building_profile.building_location"
    correction_rows = [
        {
            "cells": [
                "位置",
                *[(next((item for item in instances if item.get("slot") == slot), {}) or {}).get("location") or "待校核" for slot in CASE_SLOTS],
            ],
            "cell_refs": [
                "",
                *[f"income_cap_analysis.rent_instances.{slot}.location" for slot in CASE_SLOTS],
            ],
        },
        {
            "cells": [
                "住宅租金(元/m2·月)",
                *[(calculations.get(slot) or {}).get("monthly_rent") or "待校核" for slot in CASE_SLOTS],
            ],
            "cell_refs": [
                "",
                *[f"income_cap_analysis.rent_instances.{slot}.monthly_rent" for slot in CASE_SLOTS],
            ],
        },
    ]
    correction_rows.extend(_factor_rows(factors, instances, mode="correction"))
    correction_rows.extend(
        [
            {
                "cells": [
                    "比准租金(元/m2·月)",
                    *[(calculations.get(slot) or {}).get("corrected_monthly_rent") or "待校核" for slot in CASE_SLOTS],
                ],
                "cell_refs": [
                    "",
                    *[f"income_cap_analysis.rent_calculations.{slot}.corrected_monthly_rent" for slot in CASE_SLOTS],
                ],
            },
            {
                "cells": [
                    "算术平均值(元/m2·月)",
                    *[str((analysis.get("income_results") or {}).get("average_monthly_rent") or "待校核") for _ in CASE_SLOTS],
                ],
                "cell_refs": [
                    "",
                    *["income_cap_analysis.income_results.average_monthly_rent" for _ in CASE_SLOTS],
                ],
            },
        ]
    )
    return [
        {
            "key": "income_rent_evidence_rows",
            "title": "租金比较实例照片及位置表",
            "report_title": "租金比较实例照片及位置表",
            "columns": ["实例照片", "实例位置"],
            "header_rows": [[{"label": "实例照片"}, {"label": "实例位置"}]],
            "group_columns": [],
            "rows": [{"cells": [f"实例{item.get('slot')}照片", f"实例{item.get('slot')}位置"]} for item in instances],
            "source_target": "income_instances",
        },
        {
            "key": "income_rent_condition_rows",
            "title": "表3-13 比较因素条件说明表",
            "report_title": "表3-13 比较因素条件说明表",
            "columns": ["比较因素", "估价对象", "案例A", "案例B", "案例C"],
            "header_rows": [[
                {"label": "估价对象及比较实例/比较因素"},
                {"label": "估价对象"},
                {"label": "案例A"},
                {"label": "案例B"},
                {"label": "案例C"},
            ]],
            "group_columns": [],
            "rows": _factor_rows(
                factors,
                instances,
                mode="condition",
                subject_location=subject_location,
                subject_location_ref=subject_location_ref,
            ),
            "source_target": "income_factors",
        },
        {
            "key": "income_rent_index_rows",
            "title": "表3-14 比较因素条件指数表",
            "report_title": "表3-14 比较因素条件指数表",
            "columns": ["比较因素", "估价对象", "案例A", "案例B", "案例C"],
            "header_rows": [[
                {"label": "估价对象及比较实例/比较因素"},
                {"label": "估价对象"},
                {"label": "案例A"},
                {"label": "案例B"},
                {"label": "案例C"},
            ]],
            "group_columns": [],
            "rows": _factor_rows(
                factors,
                instances,
                mode="index",
                subject_location=subject_location,
                subject_location_ref=subject_location_ref,
            ),
            "source_target": "income_factors",
        },
        {
            "key": "income_rent_correction_rows",
            "title": "表3-15 比较因素条件修正系数表",
            "report_title": "表3-15 比较因素条件修正系数表",
            "columns": ["比较因素", "案例A", "案例B", "案例C"],
            "header_rows": [[
                {"label": "估价对象及比较实例/比较因素"},
                {"label": "案例A"},
                {"label": "案例B"},
                {"label": "案例C"},
            ]],
            "group_columns": [],
            "rows": correction_rows,
            "source_target": "income_factors",
        },
        {
            "key": "income_cap_rate_rows",
            "title": "表3-16 道县土地和房屋还原利率表(%)",
            "report_title": "表3-16 道县土地和房屋还原利率表(%)",
            "columns": [
                "土地用途",
                (analysis.get("cap_rate_parameters") or {}).get("land_usage") or "待校核",
            ],
            "header_rows": [[
                {"label": "土地用途"},
                {"label": (analysis.get("cap_rate_parameters") or {}).get("land_usage") or "待校核"},
            ]],
            "group_columns": [],
            "rows": [
                {
                    "cells": [
                        "土地还原利率",
                        f"{(analysis.get('cap_rate_parameters') or {}).get('income_land_cap_rate') or '待校核'}%",
                    ],
                    "cell_refs": [
                        "",
                        "income_cap_analysis.cap_rate_parameters.income_land_cap_rate",
                    ],
                },
                {
                    "cells": [
                        "房屋还原利率",
                        f"{(analysis.get('cap_rate_parameters') or {}).get('income_building_cap_rate') or '待校核'}%",
                    ],
                    "cell_refs": [
                        "",
                        "income_cap_analysis.cap_rate_parameters.income_building_cap_rate",
                    ],
                },
            ],
            "source_target": "income_parameters",
        },
    ]


def _intro_text(data: Dict[str, Any]) -> str:
    return str(data.get("income_cap_method_intro") or "").strip() or (
        "收益还原法是在估算估价对象在未来每年预期纯收益（正常年纯收益）的基础上，以一定的土地还原率，"
        "将评估对象在未来每年的纯收益折算为估价期日收益总和的一种方法。\n"
        "法定有限年期的土地使用权价格计算公式为：\n"
        "P＝A/r×[1－1/（1＋r）^n]\n"
        "式中：\n"
        "P——土地价格；\n"
        "A——土地年纯收益；\n"
        "r——土地还原利率；\n"
        "n——使用土地的年期或有土地收益的年期。\n"
        "具体测算思路是：\n"
        "A、房地年总收益＝房地年租金＝月租金×12×收益总面积×出租率×有效使用面积比率。\n"
        "B、房地出租年总费用＝维修费+管理费+保险费+税金。\n"
        "C、房地年纯收益＝房地年总收益-房地出租年总费用。\n"
        "D、房屋年纯收益＝房屋现值×房屋还原率。\n"
        "房屋现值＝重置价-折旧总额＝重置成本-年折旧费×已使用年限。\n"
        "E、土地年纯收益＝房地年纯收益-房屋年纯收益。\n"
        "F、总地价＝土地年纯收益÷r×[1-1/（1+r）^n]。\n"
        "G、单位面积地价＝总地价÷总用地面积。"
    )


def _factor_adjustment_narrative(factor: Dict[str, Any]) -> str:
    key = str(factor.get("key") or "")
    label = str(factor.get("label") or "比较因素")
    prefix = RENT_FACTOR_PREFIXES.get(key) or f"{label}修正"
    subject_index_text = str(factor.get("subject_index") or "100").strip()
    subject_index = _decimal(subject_index_text, Decimal("100"))
    cases = factor.get("cases") or {}
    case_indexes = {
        slot: _decimal((cases.get(slot) or {}).get("index"), D0)
        for slot in CASE_SLOTS
    }
    if subject_index <= D0 or any(value <= D0 for value in case_indexes.values()):
        return f"{prefix}：{label}指数尚未完整校核，待估价师补充后确定是否修正；"
    coefficients = {
        slot: subject_index / case_indexes[slot]
        for slot in CASE_SLOTS
    }
    same_indexes = all(case_indexes[slot] == subject_index for slot in CASE_SLOTS)
    if same_indexes:
        return f"{prefix}：估价对象与三个比较案例{label}相同或相当，条件指数均为{subject_index_text}，因此无需修正；"
    case_index_text = "，".join(
        f"案例{slot}为{str((cases.get(slot) or {}).get('index') or '待校核')}"
        for slot in CASE_SLOTS
    )
    coefficient_text = "，".join(
        f"案例{slot}修正系数为{subject_index_text}/{str((cases.get(slot) or {}).get('index') or '待校核')}={_factor(coefficients[slot])}"
        for slot in CASE_SLOTS
    )
    basis = str(factor.get("help_text") or "").strip()
    if key == "transaction_condition":
        reasons = [
            str((cases.get(slot) or {}).get("override_reason") or "").strip()
            for slot in CASE_SLOTS
            if _normalize_factor_value(key, (cases.get(slot) or {}).get("value")) == "非正常交易"
        ]
        reasons = list(dict.fromkeys(item for item in reasons if item))
        if reasons:
            basis = f"非正常交易调整依据：{'；'.join(reasons)}。"
    if any(word in basis for word in ("不作修正", "不用做修正", "无需修正", "不需要做")):
        basis = ""
    basis_text = f"{basis} " if basis else ""
    return f"{prefix}：{basis_text}以估价对象条件指数{subject_index_text}为基准，{case_index_text}，{coefficient_text}；"


def _build_narratives(data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, str]:
    profile = analysis.get("building_profile") or {}
    income_params = analysis.get("income_parameters") or {}
    expense_params = analysis.get("expense_parameters") or {}
    cap = analysis.get("cap_rate_parameters") or {}
    results = analysis.get("income_results") or {}
    instances = analysis.get("rent_instances") or []
    calculations = analysis.get("rent_calculations") or []
    factors = analysis.get("rent_factor_items") or []
    valuation_date = str(data.get("valuation_date") or "【待校核】")
    land_usage = str(data.get("land_usage") or cap.get("land_usage") or "设定土地用途")
    rental_label = _rental_property_label(instances, data)

    factor_by_key = {str(item.get("key") or ""): item for item in factors}

    INCOME_FACTOR_LABELS = {
        "usage": "用途",
        "transaction_time": "交易时间",
        "transaction_condition": "交易情况",
        "commercial_prosperity": "商服繁华度",
        "bus_convenience": "公交便捷度",
        "road_accessibility": "道路通达度",
        "infrastructure_guarantee": "水电等基础设施综合保证率",
        "environment_quality": "环境质量",
        "public_facilities": "公共设施",
        "road_type": "所临道路类型",
        "ventilation_lighting": "通风采光",
        "newness": "房屋成新度",
        "building_structure": "建筑物结构",
        "internal_layout": "建筑物内部格局",
        "decoration": "装修档次",
        "parking": "停车情况",
        "property_management": "物业情况",
    }

    def case_factor_value(key: str, slot: str) -> str:
        value = ((factor_by_key.get(key) or {}).get("cases") or {}).get(slot) or {}
        val_str = str(value.get("value") or "").strip()
        if not val_str:
            label = INCOME_FACTOR_LABELS.get(key) or "因素"
            return f"【请填写案例{slot}{label}】"
        return val_str

    instance_lines = []
    for item in instances:
        slot = str(item.get("slot") or "")
        if item.get("description"):
            instance_lines.append(str(item.get("description")))
            continue
        instance_lines.append(
            f"实例{slot}：{item.get('name') or f'【请填写实例{slot}名称】'}，位于{item.get('location') or f'【请填写实例{slot}位置】'}，"
            f"商服繁华度{case_factor_value('commercial_prosperity', slot)}，"
            f"水电等基础设施综合保证率{case_factor_value('infrastructure_guarantee', slot)}，"
            f"区域内公交便捷度{case_factor_value('bus_convenience', slot)}，"
            f"道路通达度{case_factor_value('road_accessibility', slot)}，"
            f"环境质量{case_factor_value('environment_quality', slot)}，"
            f"公共设施{case_factor_value('public_facilities', slot)}，"
            f"{case_factor_value('road_type', slot)}，{case_factor_value('building_structure', slot)}，"
            f"建筑物内部结构{case_factor_value('internal_layout', slot)}，"
            f"房屋{case_factor_value('newness', slot)}，通风采光条件{case_factor_value('ventilation_lighting', slot)}，"
            f"{case_factor_value('decoration', slot)}，{case_factor_value('parking', slot)}，"
            f"{case_factor_value('property_management', slot)}，于{item.get('transaction_date') or f'【请填写实例{slot}交易时间】'}"
            f"住宅平均租金为{item.get('monthly_rent') or f'【请填写实例{slot}月租金】'}元/平方米·月。"
        )
    rent_calc_text = "、".join(
        f"案例{item.get('slot')}比准租金{item.get('corrected_monthly_rent') or ('【请填写实例' + str(item.get('slot')) + '月租金】')}元/平方米·月"
        for item in calculations
    )

    building_location_val = profile.get('building_location') or data.get('land_location') or '【请填写估价对象坐落】'
    building_form_val = profile.get('building_form') or '【请填写独栋建筑物】'
    built_year_val = profile.get('built_year') or '【请填写建成年份】'
    floor_desc_val = profile.get('floor_desc') or '【请填写房屋总层数】'
    owner_floor_desc_val = profile.get('owner_floor_desc') or '【请填写业主房屋所在层数】'
    structure_val = profile.get('structure') or '【请选择房屋结构】'
    entrance_door_val = profile.get('entrance_door') or '【请填写房屋入户门】'
    windows_val = profile.get('windows') or '【请填写窗户情况】'
    security_facilities_val = profile.get('security_facilities') or '【请填写防盗设施】'
    exterior_val = profile.get('exterior') or '【请填写外墙装饰】'
    floor_finish_val = profile.get('floor_finish') or '【请填写地面装修】'
    ceiling_finish_val = profile.get('ceiling_finish') or '【请填写顶棚装修】'
    interior_val = profile.get('interior') or '【请填写墙面装修】'
    maintenance_val = profile.get('maintenance') or '【请填写维护保养状况】'
    newness_desc_val = profile.get('newness_desc') or '【请填写成新度】'
    economic_life_years_val = profile.get('economic_life_years') or '【请填写房屋耐用年限】'
    used_years_val = profile.get('used_years') or '【请填写房屋已使用年限】'
    remaining_years_val = profile.get('remaining_years') or '【请填写房屋尚可使用年限】'
    
    building_area_basis_val = profile.get('building_area_basis') or '【请填写建筑面积依据】'
    building_area_val = profile.get('building_area') or '【请填写建筑面积】'
    land_area_basis_val = profile.get('land_area_basis') or '【请填写土地面积依据】'
    land_area_val = profile.get('land_area') or '【请填写土地分摊面积】'
    
    current_use_basis_val = profile.get('current_use_basis') or '【请填写现状使用依据】'
    current_use_condition_val = profile.get('current_use_condition') or '【请填写现状使用条件】'
    plot_ratio_val = profile.get('plot_ratio') or '【请填写现状土地容积率】'
    set_plot_ratio_val = profile.get('set_plot_ratio') or '【请填写设定土地容积率】'
    floor_desc_display = _strip_display_suffix(floor_desc_val, "层")
    owner_floor_desc_display = _strip_display_suffix(owner_floor_desc_val, "层")
    entrance_door_display = _strip_display_suffix(entrance_door_val, "入户门")
    windows_display = _strip_display_suffix(windows_val, "窗户")
    security_facilities_display = _strip_display_suffix(security_facilities_val, "防盗网")
    maintenance_display = _strip_display_prefix(maintenance_val, "维护保养状况")
    building_area_basis_display = _book_title_display(building_area_basis_val)
    land_area_basis_display = _book_title_display(land_area_basis_val)
    current_use_basis_display = _book_title_display(current_use_basis_val)

    building_description = (
        f"根据受托估价人员现场勘察，估价对象位于{building_location_val}，"
        f"所在宗地上有{building_form_val}，总层数为{floor_desc_display}层，"
        f"业主房屋所在层数为{owner_floor_desc_display}层，建成年份为{built_year_val}年，"
        f"建筑物为{structure_val}，{entrance_door_display}入户门，{windows_display}窗户，"
        f"{security_facilities_display}防盗网，外墙{exterior_val}，屋内{floor_finish_val}，"
        f"顶棚{ceiling_finish_val}，{interior_val}，维护保养状况{maintenance_display}，"
        f"约{newness_desc_val}，房屋整体经济耐用年限为{economic_life_years_val}年，"
        f"已使用{used_years_val}年，剩余使用年限为{remaining_years_val}年。"
        f"根据委托方提供的估价对象{building_area_basis_display}、{land_area_basis_display}，"
        f"估价对象建筑面积为{building_area_val}平方米，分摊土地使用权面积{land_area_val}平方米。"
        f"根据{current_use_basis_display}委托方拟按估价对象{current_use_condition_val}进行出让，"
        f"则估价对象现状容积率为{plot_ratio_val}。根据估价目的，本次评估设定土地容积率为{set_plot_ratio_val}。"
    )

    gross_intro_lines = [
        "收益还原法评估过程：",
        "1、确定房地年总收益",
        building_description,
        "①月租金的确定",
        (
            "调查估价对象所处区域与估价对象条件相当的用于出租的住宅物业租金水平，确定估价对象房地产出租的总收益。"
            "经估价人员调查与估价对象在同一供需圈内的类似物业情况，选取了三个具有普遍性的物业的租金水平作为比较实例："
        ),
        *instance_lines,
    ]
    factor_intro_lines = [
        "②编制租金案例比较因素表",
        "结合影响房屋租金的主要因素，以估价对象因素为100进行租金修正，估价对象与实例比较因素情况详见下表。",
    ]
    factor_basis_lines = ["租金的比较因素修正说明："]
    previous_group = ""
    group_titles = {"区域因素": "D、区域因素修正", "个别因素": "E、个别因素修正"}
    for factor in factors:
        group = str(factor.get("group") or "")
        if group in group_titles and group != previous_group:
            factor_basis_lines.append(group_titles[group])
        factor_basis_lines.append(_factor_adjustment_narrative(factor))
        previous_group = group
    factor_basis_lines.append("得到估价对象比较因素条件指数表和比较因素条件修正系数表。")
    rent_solve_lines = [
        f"通过市场比较，3个比较实例的比准租金接近，故采取3个比较实例的比准租金结果的算术平均值作为估价对象的租金。{rent_calc_text}。",
        (
            f"{rental_label}月租金＝（"
            f"{'+'.join(item.get('corrected_monthly_rent') or ('【请填写实例' + str(item.get('slot')) + '月租金】') for item in calculations)}"
            f"）/3＝{results.get('average_monthly_rent') or '【计算求取住宅用房月租金】'}（元/平方米·月）。"
        ),
    ]
    annual_gross_lines = [
        "③房地年总收益的确定",
        (
            f"估价人员通过对周边出租行情进行调查，区域内出租案例较多，根据市场调查区域商住房地产平均空置率为"
            f"{income_params.get('vacancy_rate_range') or '【请填写空置率区间】'}，"
            f"本次评估取平均空置率{income_params.get('vacancy_rate') or '【请填写空置率】'}%。"
            f"估价对象地上建筑物可出租房屋比例为{income_params.get('rentable_area_ratio') or '【请填写有效出租面积比】'}%。"
        ),
        (
            f"房地年总收益＝{rental_label}月租金×12×（1-空置率）×{rental_label}出租率"
            f"＝{results.get('average_monthly_rent') or '【计算求取住宅用房月租金】'}×12×（1-{income_params.get('vacancy_rate') or '【请填写空置率】'}%）×"
            f"{profile.get('building_area') or '【请填写建筑面积】'}×{income_params.get('rentable_area_ratio') or '【请填写有效出租面积比】'}%÷10000"
            f"＝{results.get('annual_gross_income') or '【计算求取房地年总收益】'}（万元）。"
        ),
    ]
    gross_lines = gross_intro_lines + factor_intro_lines + factor_basis_lines + rent_solve_lines + annual_gross_lines
    county_name = data.get("county_name") or data.get("county") or "道县"
    cost_grade = str(expense_params.get("replacement_cost_grade_label") or "")
    cost_grade_text = "" if cost_grade in {"", "/"} else cost_grade
    cost_structure_text = str(expense_params.get("replacement_cost_structure_label") or profile.get("structure") or "住宅砖混")
    cost_standard_name = f"住宅类{cost_structure_text}{cost_grade_text}"
    cost_range = expense_params.get("replacement_cost_range_label") or (
        f"{expense_params.get('replacement_cost_range_min')}-{expense_params.get('replacement_cost_range_max')}"
    )
    adopted_cost = expense_params.get("replacement_base_unit_cost") or "【待校核】"
    adopted_source_text = (
        "因系统项目库中默认取值"
        if expense_params.get("replacement_cost_adopted_source") == "range_max_default"
        else "因受托估价人员现场踏勘调查并核实后本次评估确定"
    )
    regional_coefficient = expense_params.get("regional_adjustment_coefficient") or "1.0"
    regional_coefficient_value = _decimal(regional_coefficient, D1)
    
    adopted_cost_dec = _decimal(adopted_cost)
    regional_coef_dec = _decimal(regional_coefficient)
    unit_cost_base_dec = adopted_cost_dec * regional_coef_dec
    unit_cost_base_str = _integer(unit_cost_base_dec)

    if regional_coefficient_value == D1:
        coefficient_sentence = f"取{cost_structure_text}住宅用房重置价格为{adopted_cost}元/平方米。"
        coefficient_formula = f"{adopted_cost}"
    else:
        coefficient_sentence = (
            f"根据该文件中的“利用系数表”，估价对象位于{county_name}，应进行利用系数修正，修正系数为{regional_coefficient}，"
            f"取二等砖混结构住宅用房重置价格为{adopted_cost}元/平方米，则{county_name}类似混合结构住宅楼建筑物重置价为"
            f"{adopted_cost}×{regional_coefficient}={unit_cost_base_str}元/平方米。"
        )
        coefficient_formula = f"{adopted_cost}×{regional_coefficient}"

    replacement_basis = (
        f"根据《{expense_params.get('replacement_cost_source_doc') or RESIDENTIAL_CONSTRUCTION_COST_SOURCE}》（编号：湘房协〔2023〕3号，2023年2月14日）"
        f"中的“各类建筑物建设成本参考标准”，{cost_standard_name}建设成本价格在{cost_range}元/平方米；"
        f"{coefficient_sentence}"
    )

    elapsed_years_val = _decimal(expense_params.get("cost_elapsed_years"))
    growth_rate_val = expense_params.get("cost_growth_rate") or "2"
    cost_base_date_val = expense_params.get("cost_base_date") or "2023-01-01"
    valuation_date_val = expense_params.get("valuation_date") or data.get("valuation_date") or "【待校核】"

    growth_lines_text = []
    if elapsed_years_val > D0:
        growth_lines_text.append(
            f"考虑近几年价格上涨水平，取砖混结构重置价格年增长率为{growth_rate_val}%。《{expense_params.get('replacement_cost_source_doc') or RESIDENTIAL_CONSTRUCTION_COST_SOURCE}》"
            f"（编号：湘房协〔2023〕3号，2023年2月14日）建筑物建设成本对应的价值时点为{cost_base_date_val}，"
            f"而本次评估的估价期日是{valuation_date_val}，相距{expense_params.get('cost_elapsed_years') or '0'}年。"
        )
        growth_formula_text = (
            f"可确定估价对象估价期日的房屋重置价格单价为"
            f"{unit_cost_base_str}×(1+{growth_rate_val}%)^{expense_params.get('cost_elapsed_years') or '0'}="
            f"{results.get('replacement_unit_cost') or '【待计算】'}元/平方米。"
        )
        growth_lines_text.append(growth_formula_text)
    else:
        # 经历年数为0，直接等于修正基准单价
        growth_lines_text.append(
            f"相距时间为0年，无需进行价格指数修正，估价对象重置单价即为{results.get('replacement_unit_cost') or '【待计算】'}元/平方米。"
        )

    expense_lines = [
        "2、确定房地年总费用",
        "房地年总费用是指估价对象在正常经营活动中每年所必须支出的必要费用。",
        (
            f"（1）经营管理费：指对出租房屋进行的必要管理所需的费用。按年租金的2%～5%计，本次评估中根据估价对象"
            f"地上建筑物管理难易程度确定为{expense_params.get('management_rate') or '2'}%，则："
        ),
        f"经营管理费＝房地年总收益×{expense_params.get('management_rate') or '2'}%",
        f"＝{results.get('annual_gross_income') or '【获取总收益】'}×{expense_params.get('management_rate') or '2'}%",
        f"＝{results.get('management_fee') or '【获取管理费】'}（万元）",
        (
            f"（2）经营维修费：指为保障房屋正常使用每年需支付的修缮费。根据估价对象房屋的实际使用情况，"
            f"按建筑物重置价格的{expense_params.get('repair_rate') or '2'}%计算。"
        ),
        replacement_basis,
    ]
    expense_lines.extend(growth_lines_text)
    expense_lines.extend([
        "房屋重置价格＝重置单价×总建筑面积",
        f"＝{results.get('replacement_unit_cost') or '【待计算】'}×{profile.get('building_area') or '【获取面积】'}＝{results.get('building_replacement_price') or '【获取重置总价】'}（万元）",
        "则：经营维修费＝房屋重置价格×设备修缮率",
        f"＝{results.get('building_replacement_price') or '【获取重置总价】'}×{expense_params.get('repair_rate') or '2'}%",
        f"＝{results.get('repair_fee') or '【获取修缮费】'}（万元）",
        (
            f"（3）房屋年保险费：指房产所有人为使自己的房产避免意外损失而向保险公司支付的费用。按房屋现值"
            f"乘以保险费率{expense_params.get('insurance_rate_permille') or '2'}‰计算，则："
        ),
        "①计算房屋年折旧费：房屋年折旧费指房屋在使用过程中因损耗而在租金中补偿的那部分价值。",
        (
            f"估价对象建筑为{profile.get('structure') or '砖混结构'}，耐用年限为{profile.get('economic_life_years') or '50'}年，"
            f"残值率{expense_params.get('residual_rate') or '2'}%，估价对象地上房屋建成于{profile.get('built_year') or '【待校核】'}年，"
            f"已使用年限约为{profile.get('used_years') or '【待校核】'}年，剩余使用年限{profile.get('remaining_years') or '【待校核】'}年，"
            f"此次评估设定出让土地使用权年限为{cap.get('use_term_years') or '70'}年，大于房屋剩余使用年限，"
            f"根据孰短原则，折旧年限＝房屋已使用年限+房屋剩余使用年限。则年折旧费计算公式为："
        ),
        "年折旧费＝房屋重置价×（1-残值率）÷（房屋已使用年限+房屋剩余使用年限）",
        (
            f"＝{results.get('building_replacement_price') or '【获取重置价】'}×（1-{expense_params.get('residual_rate') or '2'}%）"
            f"÷（{profile.get('used_years') or '【待校核】'}+{profile.get('remaining_years') or '【待校核】'}）"
        ),
        f"＝{results.get('annual_depreciation') or '【获取折旧费】'}（万元）",
        "②计算房屋现值",
        "房屋现值＝房屋重置价格-折旧总额",
        f"＝{results.get('building_replacement_price') or '【获取重置价】'}-年折旧费×已使用年限",
        (
            f"＝{results.get('building_replacement_price') or '【获取重置价】'}-{results.get('annual_depreciation') or '【获取折旧费】'}"
            f"×{profile.get('used_years') or '【待校核】'}"
        ),
        f"＝{results.get('building_current_value') or '【获取房屋现值】'}（万元）",
        "③计算房屋年保险费",
        f"房屋年保险费＝房屋现值×{expense_params.get('insurance_rate_permille') or '2'}‰",
        f"＝{results.get('building_current_value') or '【获取房屋现值】'}×{expense_params.get('insurance_rate_permille') or '2'}‰",
        f"＝{results.get('insurance_fee') or '【获取保险费】'}（万元）",
        "（4）税费：包括房产税、城市维护建设税及教育费附加等。",
        (
            "根据《中华人民共和国房产税暂行条例》、《财政部 国家税务总局关于营改增后契税 房产税 土地增值税 个人所得税 计税依据问题的通知》"
            "（财税〔2016〕36号）、《国家税务总局关于营改增后契税 房产税 土地增值税 个人所得税 计税依据问题的公告》（国家税务总局公告2016年第23号），"
            "个人出租住房减按4%征收房产税，增值税免征，"
            "故本次评估中房产税税率取4%，增值税取0%。"
        ),
        "故本次评估中增值税、个人所得税、印花税、城市维护建设税、教育费附加、地方教育附加均为0%。",
        (
            f"房产税＝房地年总收益×4%"
        ),
        (
            f"＝{results.get('annual_gross_income') or '【获取总收益】'}×4%"
        ),
        f"＝{results.get('tax_fee') or '【获取税费】'}（万元）",
        "房地年总费用＝经营管理费+经营维修费+房屋年保险费+税费",
        (
            f"＝{results.get('management_fee') or '【获取管理费】'}+{results.get('repair_fee') or '【获取修缮费】'}+"
            f"{results.get('insurance_fee') or '【获取保险费】'}+{results.get('tax_fee') or '【获取税费】'}"
        ),
        f"＝{results.get('total_expense') or '【获取总费用】'}（万元）"
    ])
    return {
        "income_cap_method_intro": _intro_text(data),
        "income_cap_gross_income_narrative": "\n".join(gross_lines),
        "income_cap_gross_income_intro": "\n".join(gross_intro_lines),
        "income_cap_rent_factor_intro": "\n".join(factor_intro_lines),
        "income_cap_rent_factor_basis": "\n".join(factor_basis_lines),
        "income_cap_rent_solve_narrative": "\n".join(rent_solve_lines),
        "income_cap_annual_gross_narrative": "\n".join(annual_gross_lines),
        "income_cap_expense_narrative": "\n".join(expense_lines),
        "income_cap_real_estate_net_narrative": (
            "3、房地年纯收益\n"
            "房地年纯收益＝房地年总收益-房地年总费用\n"
            f"＝{results.get('annual_gross_income') or '【计算求取房地年总收益】'}-{results.get('total_expense') or '【计算求取房地年总费用】'}\n"
            f"＝{results.get('real_estate_net_income') or '【计算求取房地年纯收益】'}（万元）"
        ),
        "income_cap_building_income_narrative": (
            "4、房屋年纯收益\n"
            "根据前文，采用土地纯收益与价格比率法、投资收益法测算确定土地和房屋的还原率，详见下表：\n"
            "则，房屋年纯收益＝房屋现值×房屋还原利率\n"
            f"＝{results.get('building_current_value') or '【计算求取房屋现值】'}×{cap.get('income_building_cap_rate') or '【请填写房屋还原率】'}%\n"
            f"＝{results.get('building_net_income') or '【计算求取房屋年纯收益】'}（万元）"
        ),
        "income_cap_building_income_intro": (
            "4、房屋年纯收益\n"
            "根据前文，采用土地纯收益与价格比率法、投资收益法测算确定土地和房屋的还原率，详见下表："
        ),
        "income_cap_building_income_solve": (
            "则，房屋年纯收益＝房屋现值×房屋还原利率\n"
            f"＝{results.get('building_current_value') or '【计算求取房屋现值】'}×{cap.get('income_building_cap_rate') or '【请填写房屋还原率】'}%\n"
            f"＝{results.get('building_net_income') or '【计算求取房屋年纯收益】'}（万元）"
        ),
        "income_cap_land_income_narrative": (
            "5、土地年纯收益\n"
            "土地年纯收益＝房地年纯收益-房屋年纯收益\n"
            f"＝{results.get('real_estate_net_income') or '【计算求取房地年纯收益】'}-{results.get('building_net_income') or '【计算求取房屋年纯收益】'}\n"
            f"＝{results.get('land_net_income') or '【计算求取土地年纯收益】'}（万元）"
        ),
        "income_cap_total_price_narrative": (
            "6、计算待估宗地总地价\n"
            "总地价＝土地年纯收益÷r×[1-1/（1＋r）^n]\n"
            f"其中：r——土地还原率{cap.get('income_land_cap_rate') or '【请填写土地还原率】'}%。\n"
            f"n——待估宗地土地使用年期{cap.get('use_term_years') or '【请填写使用年限】'}年。\n"
            f"＝{results.get('land_net_income') or '【计算求取土地年纯收益】'}÷{cap.get('income_land_cap_rate') or '【请填写土地还原率】'}%×"
            f"[1-1/（1+{cap.get('income_land_cap_rate') or '【请填写土地还原率】'}%）^{cap.get('use_term_years') or '【请填写使用年限】'}]"
            f"\n＝{results.get('total_land_price') or '【计算求取总地价】'}（万元）"
        ),
        "income_cap_unit_price_narrative": (
            "7、计算宗地单位面积地价\n"
            "单位面积地价＝总地价÷总用地面积\n"
            f"＝{results.get('total_land_price') or '【计算求取总地价】'}×10000÷{profile.get('land_area') or '【待校核】'}\n"
            f"＝{results.get('unit_land_price') or '【计算求取单位面积地价】'}（元/平方米）\n"
            f"收益还原法测算地价的结果为：估价对象于估价期日{valuation_date}，在设定土地用途，设定土地使用年限，"
            f"设定土地开发程度，现状利用条件下的国有土地出让使用权价格为{land_usage}{results.get('unit_land_price') or '【计算求取单位面积地价】'}元/平方米。"
        ),
    }


def _income_narrative_segment_sources(data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    profile = analysis.get("building_profile") or {}
    income_params = analysis.get("income_parameters") or {}
    expense_params = analysis.get("expense_parameters") or {}
    cap = analysis.get("cap_rate_parameters") or {}
    results = analysis.get("income_results") or {}
    floor_desc_display = _strip_display_suffix(profile.get("floor_desc"), "层")
    owner_floor_desc_display = _strip_display_suffix(profile.get("owner_floor_desc"), "层")
    entrance_door_display = _strip_display_suffix(profile.get("entrance_door"), "入户门")
    windows_display = _strip_display_suffix(profile.get("windows"), "窗户")
    security_facilities_display = _strip_display_suffix(profile.get("security_facilities"), "防盗网")
    maintenance_display = _strip_display_prefix(profile.get("maintenance"), "维护保养状况")
    building_area_basis_display = _book_title_display(profile.get("building_area_basis"))
    land_area_basis_display = _book_title_display(profile.get("land_area_basis"))
    current_use_basis_display = _book_title_display(profile.get("current_use_basis"))

    def pct(value: Any) -> str:
        text = str(value or "").strip()
        return f"{text}%" if text else ""

    def permille(value: Any) -> str:
        text = str(value or "").strip()
        return f"{text}‰" if text else ""

    def year(value: Any) -> str:
        text = str(value or "").strip()
        return f"{text}年" if text else ""

    def item(text: Any, field: str, prefix: str = "", suffix: str = "", priority: int = 0) -> Dict[str, str]:
        return {
            "text": str(text or "").strip(),
            "field": field,
            "prefix": prefix,
            "suffix": suffix,
            "priority": str(priority),
        }

    return {
        "income_cap_gross_income_intro": [
            item(profile.get("building_location"), profile.get("building_location_source_ref") or "income_cap_analysis.building_profile.building_location", "估价对象位于", "，"),
            item(profile.get("building_form"), "income_cap_analysis.building_profile.building_form", "所在宗地上有", "，"),
            item(floor_desc_display, "income_cap_analysis.building_profile.floor_desc", "总层数为", "层"),
            item(owner_floor_desc_display, "income_cap_analysis.building_profile.owner_floor_desc", "业主房屋所在层数为", "层"),
            item(profile.get("built_year"), "income_cap_analysis.building_profile.built_year", "建成年份为", "年"),
            item(profile.get("structure"), "income_cap_analysis.building_profile.structure", "建筑物为", "，"),
            item(entrance_door_display, "income_cap_analysis.building_profile.entrance_door", "，", "入户门"),
            item(windows_display, "income_cap_analysis.building_profile.windows", "入户门，", "窗户"),
            item(security_facilities_display, "income_cap_analysis.building_profile.security_facilities", "窗户，", "防盗网"),
            item(profile.get("exterior"), "income_cap_analysis.building_profile.exterior", "外墙", "，屋内"),
            item(profile.get("floor_finish"), "income_cap_analysis.building_profile.floor_finish", "屋内", "，"),
            item(profile.get("ceiling_finish"), "income_cap_analysis.building_profile.ceiling_finish", "顶棚", "，"),
            item(profile.get("interior"), "income_cap_analysis.building_profile.interior", "，", "，维护保养状况"),
            item(maintenance_display, "income_cap_analysis.building_profile.maintenance", "维护保养状况", "，"),
            item(profile.get("newness_desc"), "income_cap_analysis.building_profile.newness_desc", "约", "，"),
            item(profile.get("economic_life_years"), "income_cap_analysis.building_profile.economic_life_years", "经济耐用年限为", "年"),
            item(profile.get("used_years"), "income_cap_analysis.building_profile.used_years", "已使用", "年"),
            item(profile.get("remaining_years"), "income_cap_analysis.building_profile.remaining_years", "剩余使用年限为", "年"),
            item(building_area_basis_display, "income_cap_analysis.building_profile.building_area_basis", "提供的估价对象", "、"),
            item(land_area_basis_display, "income_cap_analysis.building_profile.land_area_basis", "、", "，"),
            item(profile.get("building_area"), "income_cap_analysis.building_profile.building_area", "估价对象建筑面积为", "平方米"),
            item(profile.get("land_area"), "income_cap_analysis.building_profile.land_area", "分摊土地使用权面积", "平方米"),
            item(current_use_basis_display, "income_cap_analysis.building_profile.current_use_basis", "根据", "委托方"),
            item(profile.get("current_use_condition"), "valuation_condition_type", "拟按估价对象", "进行出让"),
            item(profile.get("plot_ratio"), "set_plot_ratio", "现状容积率为", "。"),
            item(profile.get("set_plot_ratio"), "set_plot_ratio", "设定土地容积率为", "。"),
        ],
        "income_cap_annual_gross_narrative": [
            item(income_params.get("vacancy_rate_range"), "income_cap_analysis.income_parameters.vacancy_rate_range", "平均空置率为"),
            item(pct(income_params.get("vacancy_rate")), "income_cap_analysis.income_parameters.vacancy_rate", "平均空置率"),
            item(pct(income_params.get("vacancy_rate")), "income_cap_analysis.income_parameters.vacancy_rate", "（1-"),
            item(pct(income_params.get("rentable_area_ratio")), "income_cap_analysis.income_parameters.rentable_area_ratio", "可出租房屋比例为"),
            item(pct(income_params.get("rentable_area_ratio")), "income_cap_analysis.income_parameters.rentable_area_ratio", "×", "÷10000"),
            item(profile.get("building_area"), "income_cap_analysis.building_profile.building_area", "）×", "×", priority=10),
            item(results.get("annual_gross_income"), "income_cap_analysis.income_results.annual_gross_income", "＝", "（万元）"),
        ],
        "income_cap_expense_narrative": [
            item(pct(expense_params.get("management_rate")), "income_cap_analysis.expense_parameters.management_rate", "确定为"),
            item(pct(expense_params.get("management_rate")), "income_cap_analysis.expense_parameters.management_rate", "房地年总收益×"),
            item(pct(expense_params.get("repair_rate")), "income_cap_analysis.expense_parameters.repair_rate", "重置价格的"),
            item(pct(expense_params.get("repair_rate")), "income_cap_analysis.expense_parameters.repair_rate", "房屋重置价格×"),
            item(expense_params.get("replacement_cost_range_label"), "income_cap_analysis.expense_parameters.replacement_cost_range_max", "参考范围为", "元/平方米"),
            item(expense_params.get("replacement_base_unit_cost"), "income_cap_analysis.expense_parameters.replacement_base_unit_cost", "本次采用"),
            item(expense_params.get("replacement_base_unit_cost"), "income_cap_analysis.expense_parameters.replacement_base_unit_cost", "默认取区间上限"),
            item(expense_params.get("replacement_base_unit_cost"), "income_cap_analysis.expense_parameters.replacement_base_unit_cost", "校核后本次采用"),
            item(expense_params.get("regional_adjustment_coefficient"), "income_cap_analysis.expense_parameters.regional_adjustment_coefficient", "取利用系数"),
            item(pct(expense_params.get("cost_growth_rate")), "income_cap_analysis.expense_parameters.cost_growth_rate", "年增长率为"),
            item(pct(expense_params.get("cost_growth_rate")), "income_cap_analysis.expense_parameters.cost_growth_rate", "(1+"),
            item(expense_params.get("cost_base_date"), "income_cap_analysis.expense_parameters.cost_base_date", "价值时点为"),
            item(expense_params.get("valuation_date"), "valuation_date", "估价期日是"),
            item(profile.get("building_area"), "income_cap_analysis.building_profile.building_area", "×", "÷10000"),
            item(pct(expense_params.get("insurance_rate_permille")).replace("%", "‰"), "income_cap_analysis.expense_parameters.insurance_rate_permille", "保险费率"),
            item(permille(expense_params.get("insurance_rate_permille")), "income_cap_analysis.expense_parameters.insurance_rate_permille", "×"),
            item(year(profile.get("economic_life_years")), "income_cap_analysis.building_profile.economic_life_years", "耐用年限为"),
            item(pct(expense_params.get("residual_rate")), "income_cap_analysis.expense_parameters.residual_rate", "残值率"),
            item(pct(expense_params.get("residual_rate")), "income_cap_analysis.expense_parameters.residual_rate", "（1-"),
            item(year(profile.get("used_years")), "income_cap_analysis.building_profile.used_years", "已使用年限约为"),
            item(year(profile.get("remaining_years")), "income_cap_analysis.building_profile.remaining_years", "剩余使用年限"),
            item(profile.get("used_years"), "income_cap_analysis.building_profile.used_years", "年折旧费×"),
            item(pct(expense_params.get("property_tax_rate")), "income_cap_analysis.expense_parameters.property_tax_rate", "按"),
            item(pct(expense_params.get("property_tax_reduction_rate")), "income_cap_analysis.expense_parameters.property_tax_reduction_rate", "本次按"),
        ],
        "income_cap_total_price_narrative": [
            item(pct(cap.get("income_land_cap_rate")), "income_cap_analysis.cap_rate_parameters.income_land_cap_rate", "土地还原率"),
            item(year(cap.get("use_term_years")), "income_cap_analysis.cap_rate_parameters.use_term_years", "土地使用年期"),
            item(results.get("total_land_price"), "income_cap_analysis.income_results.total_land_price", "＝", "（万元）"),
        ],
        "income_cap_unit_price_narrative": [
            item(results.get("total_land_price"), "income_cap_analysis.income_results.total_land_price", "＝"),
            item(profile.get("land_area"), "income_cap_analysis.building_profile.land_area", "÷"),
            item(results.get("unit_land_price"), "income_cap_analysis.income_results.unit_land_price", "＝", "（元/平方米）"),
            item(str(data.get("valuation_date") or ""), "valuation_date", "估价期日"),
        ],
    }


def calculate_income_capitalization(data: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(data.get("income_cap_analysis") or {})
    result["rent_instances"] = _default_rent_instances(data, result.get("rent_instances") or [])
    result["building_profile"] = _building_profile(data, result)
    result["rent_factor_items"] = _default_rent_factors(
        data,
        result.get("rent_factor_items") or [],
        result["rent_instances"],
        result["building_profile"],
    )
    result["income_parameters"] = _income_parameters(result)
    result["expense_parameters"] = _expense_parameters(data, result)
    result["cap_rate_parameters"] = _cap_rate_parameters(data, result)

    profile = result["building_profile"]
    income_params = result["income_parameters"]
    expense_params = result["expense_parameters"]
    cap = result["cap_rate_parameters"]

    result["rent_calculations"] = _rent_calculations(result["rent_instances"], result["rent_factor_items"])
    corrected_rents = [
        _decimal(item.get("corrected_monthly_rent"))
        for item in result["rent_calculations"]
        if _decimal(item.get("corrected_monthly_rent")) > D0
    ]
    average_rent = sum(corrected_rents, D0) / Decimal(len(corrected_rents)) if corrected_rents else D0
    average_rent = average_rent.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    building_area = _decimal(profile.get("building_area"))
    land_area = _decimal(profile.get("land_area"))
    vacancy_rate = _percent_decimal(income_params.get("vacancy_rate"))
    rentable_ratio = _percent_decimal(income_params.get("rentable_area_ratio"))
    annual_gross = Decimal(_wan(average_rent * Decimal("12") * (D1 - vacancy_rate) * building_area * rentable_ratio / Decimal("10000")))

    base_unit = _decimal(expense_params.get("replacement_base_unit_cost"))
    region_coeff = _decimal(expense_params.get("regional_adjustment_coefficient"), D1)
    growth_rate = _percent_decimal(expense_params.get("cost_growth_rate"))
    elapsed = _elapsed_years(expense_params.get("cost_base_date"), expense_params.get("valuation_date"))
    result["expense_parameters"]["cost_elapsed_years"] = _money(elapsed)
    replacement_unit = (base_unit * region_coeff * ((D1 + growth_rate) ** elapsed)).quantize(INTEGER_QUANT, rounding=ROUND_HALF_UP)
    replacement_price = Decimal(_wan(replacement_unit * building_area / Decimal("10000")))
    management_fee = Decimal(_wan(annual_gross * _percent_decimal(expense_params.get("management_rate"))))
    repair_fee = Decimal(_wan(replacement_price * _percent_decimal(expense_params.get("repair_rate"))))
    life_years = _decimal(profile.get("economic_life_years"))
    residual_rate = _percent_decimal(expense_params.get("residual_rate"))
    annual_depreciation = Decimal(_wan(replacement_price * (D1 - residual_rate) / life_years)) if life_years > D0 else D0
    building_current_value = Decimal(_wan(replacement_price - annual_depreciation * _decimal(profile.get("used_years"))))
    insurance_fee = Decimal(_wan(building_current_value * _permille_decimal(expense_params.get("insurance_rate_permille"))))
    tax_fee = Decimal(
        _wan(
            annual_gross
            * _percent_decimal(expense_params.get("property_tax_rate"))
            * _percent_decimal(expense_params.get("property_tax_reduction_rate"))
        )
    )
    total_expense = Decimal(_wan(management_fee + repair_fee + insurance_fee + tax_fee))
    real_estate_net = Decimal(_wan(annual_gross - total_expense))
    building_net = Decimal(_wan(building_current_value * _percent_decimal(cap.get("income_building_cap_rate"))))
    land_net = Decimal(_wan(real_estate_net - building_net))
    land_rate = _percent_decimal(cap.get("income_land_cap_rate"))
    term = _decimal(cap.get("use_term_years"))
    term_factor = D1 - (D1 / ((D1 + land_rate) ** term)) if land_rate > D0 and term > D0 else D1
    total_land_price = Decimal(_wan(land_net / land_rate * term_factor)) if land_rate > D0 else D0
    unit_land_price = _price(total_land_price * Decimal("10000") / land_area) if land_area > D0 else ""

    result["income_results"] = {
        "average_monthly_rent": _money(average_rent) if average_rent else "",
        "annual_gross_income": _wan(annual_gross),
        "replacement_unit_cost": _integer(replacement_unit),
        "building_replacement_price": _wan(replacement_price),
        "management_fee": _wan(management_fee),
        "repair_fee": _wan(repair_fee),
        "annual_depreciation": _wan(annual_depreciation),
        "building_current_value": _wan(building_current_value),
        "insurance_fee": _wan(insurance_fee),
        "tax_fee": _wan(tax_fee),
        "total_expense": _wan(total_expense),
        "real_estate_net_income": _wan(real_estate_net),
        "building_net_income": _wan(building_net),
        "land_net_income": _wan(land_net),
        "term_factor": _factor(term_factor),
        "total_land_price": _wan(total_land_price),
        "unit_land_price": unit_land_price,
    }
    if unit_land_price:
        result["income_cap_price"] = unit_land_price
    result["narrative_segment_sources"] = _income_narrative_segment_sources(data, result)

    warnings: List[Dict[str, str]] = []
    if len([item for item in result["rent_instances"] if _decimal(item.get("monthly_rent")) > D0]) < 3:
        warnings.append({"level": "warning", "message": "收益还原法尚未录入三宗有效租金实例。", "target": "income_instances"})
    if any(not _bool(item.get("confirmed")) for item in result["rent_instances"]):
        warnings.append({"level": "warning", "message": "租金实例 A/B/C 尚未全部确认。", "target": "income_instances"})
    missing_images = [
        item.get("slot")
        for item in result["rent_instances"]
        if not item.get("photo_data") or not item.get("location_image_data")
    ]
    if missing_images:
        warnings.append({"level": "warning", "message": "租金实例照片或位置图尚未全部上传。", "target": "income_instances"})
    for factor in result["rent_factor_items"]:
        for slot in CASE_SLOTS:
            case = (factor.get("cases") or {}).get(slot) or {}
            if factor.get("required", True) and (not _bool(case.get("confirmed")) or _decimal(case.get("index")) <= D0):
                warnings.append(
                    {
                        "level": "warning",
                        "message": f"收益还原法“{factor.get('label')}”因素尚未完成 A/B/C 校核。",
                        "target": "income_factors",
                        "factor_key": factor.get("key") or "",
                    }
                )
                break
            if (
                factor.get("key") == "transaction_condition"
                and _normalize_factor_value("transaction_condition", case.get("value")) == "非正常交易"
                and not str(case.get("override_reason") or "").strip()
            ):
                warnings.append(
                    {
                        "level": "warning",
                        "message": f"收益还原法案例{slot}为非正常交易，尚未填写人工调整依据。",
                        "target": "income_factors",
                        "factor_key": "transaction_condition",
                    }
                )
                break
    if not _bool(cap.get("confirmed")):
        warnings.append({"level": "warning", "message": "土地和房屋还原率尚未确认。", "target": "income_parameters"})
    missing_building_fields = [
        label for key, label in BUILDING_PROFILE_REQUIRED_FIELDS if not str(profile.get(key) or "").strip()
    ]
    if missing_building_fields:
        warnings.append(
            {
                "level": "warning",
                "message": f"地上建筑物情况尚缺：{'、'.join(missing_building_fields)}。",
                "target": "income_instances",
            }
        )
    for key, label in (("building_area", "建筑面积"), ("land_area", "土地面积")):
        if _decimal(profile.get(key)) <= D0:
            warnings.append({"level": "warning", "message": f"收益还原法缺少{label}。", "target": "income_parameters"})
    if not str(income_params.get("vacancy_rate_range") or "").strip():
        warnings.append({"level": "warning", "message": "收益还原法缺少区域平均空置率区间。", "target": "income_parameters"})
    if _decimal(income_params.get("vacancy_rate")) <= D0:
        warnings.append({"level": "warning", "message": "收益还原法缺少本次采用空置率。", "target": "income_parameters"})
    if _decimal(income_params.get("rentable_area_ratio")) <= D0:
        warnings.append({"level": "warning", "message": "收益还原法缺少有效出租面积比率。", "target": "income_parameters"})
    adopted_cost = _decimal(expense_params.get("replacement_base_unit_cost"))
    range_min = _decimal(expense_params.get("replacement_cost_range_min"))
    range_max = _decimal(expense_params.get("replacement_cost_range_max"))
    if range_min > D0 and range_max > D0 and (adopted_cost < range_min or adopted_cost > range_max):
        if not str(expense_params.get("replacement_cost_override_reason") or "").strip():
            warnings.append(
                {
                    "level": "warning",
                    "message": "建筑物建设成本采用值超出附件参考范围，请填写取值说明。",
                    "target": "income_parameters",
                }
            )
    result["warnings"] = warnings
    result["complete"] = not warnings

    generated = _build_narratives(data, result)
    overrides = result.get("narrative_overrides") or {}
    result["generated_narratives"] = generated
    result["effective_narratives"] = {key: str(overrides.get(key) or value) for key, value in generated.items()}
    result["tables"] = _table_sections(result)
    result["results"] = [
        {
            "key": "income_cap_price",
            "label": "收益还原法最终单价",
            "value": result.get("income_cap_price") or "",
            "unit": "元/平方米",
            "formula": "土地年纯收益÷土地还原率×年期收益系数÷土地面积",
        }
    ]
    return result
