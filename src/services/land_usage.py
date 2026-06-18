# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LandUsageOption:
    key: str
    label: str
    report_value: str
    current_class: str
    price_class: str
    asset_category: str
    keywords: tuple[str, ...]


LAND_USAGE_OPTIONS: tuple[LandUsageOption, ...] = (
    LandUsageOption("residential", "居住用地", "居住用地", "居住用地", "居住用地", "residential", ("住宅", "居住", "公寓")),
    LandUsageOption("commercial", "商业服务业用地", "商业服务业用地", "商业服务业用地", "商业服务业用地", "commercial", ("商业", "商服", "商务", "零售", "餐饮", "旅馆", "娱乐", "金融")),
    LandUsageOption("industrial", "工矿用地", "工矿用地", "工矿用地", "工矿用地", "industrial", ("工业", "工矿", "厂房", "制造")),
    LandUsageOption("warehouse", "仓储用地", "仓储用地", "仓储用地", "仓储用地", "industrial", ("仓储", "物流", "仓库")),
    LandUsageOption("public", "公共管理与公共服务用地", "公共管理与公共服务用地", "公共管理与公共服务用地", "公共管理与公共服务用地", "public", ("公共", "机关", "教育", "医疗", "文化", "体育", "科研", "卫生")),
    LandUsageOption("transportation", "交通运输用地", "交通运输用地", "交通运输用地", "交通运输用地", "public", ("交通", "道路", "铁路", "港口", "机场")),
    LandUsageOption("utility", "公用设施用地", "公用设施用地", "公用设施用地", "公用设施用地", "public", ("公用", "供水", "排水", "供电", "燃气", "环卫")),
    LandUsageOption("green", "绿地与开敞空间用地", "绿地与开敞空间用地", "绿地与开敞空间用地", "绿地与开敞空间用地", "public", ("绿地", "公园", "广场", "开敞")),
    LandUsageOption("special", "特殊用地", "特殊用地", "特殊用地", "特殊用地", "other", ("特殊", "军事", "宗教", "殡葬")),
    LandUsageOption("other", "其他", "", "", "", "other", ()),
)

OTHER_LAND_USAGE_KEY = "other"

LAND_USAGE_OPTION_BY_KEY = {item.key: item for item in LAND_USAGE_OPTIONS}

LAND_USAGE_OFFICIAL_V3_CODE_BY_KEY = {
    "residential": "V3-07",
    "public": "V3-08",
    "commercial": "V3-09",
    "industrial": "V3-10",
    "warehouse": "V3-11",
    "transportation": "V3-12",
    "utility": "V3-13",
    "green": "V3-14",
    "special": "V3-15",
}

LAND_USAGE_EXACT_ALIASES = {
    "居住用地": "residential",
    "住宅用地": "residential",
    "城镇住宅用地": "residential",
    "农村宅基地": "residential",
    "城镇社区服务设施用地": "residential",
    "农村社区服务设施用地": "residential",
    "商业服务业用地": "commercial",
    "商服用地": "commercial",
    "公用设施营业网点用地": "commercial",
    "工矿用地": "industrial",
    "工矿仓储用地": "industrial",
    "工业用地": "industrial",
    "采矿用地": "industrial",
    "盐田": "industrial",
    "仓储用地": "warehouse",
    "物流仓储用地": "warehouse",
    "储备库用地": "warehouse",
    "公共管理与公共服务用地": "public",
    "新闻出版用地": "public",
    "科教用地": "public",
    "医卫慈善用地": "public",
    "文体娱乐用地": "public",
    "交通运输用地": "transportation",
    "公用设施用地": "utility",
    "公共设施用地": "utility",
    "绿地与开敞空间用地": "green",
    "公园与绿地": "green",
    "特殊用地": "special",
}

# Specific phrases must be checked before broad words such as "公共" or "设施".
LAND_USAGE_KEYWORD_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("commercial", ("公用设施营业网点", "商业", "商服", "商务", "零售", "批发市场", "餐饮", "旅馆", "金融")),
    ("warehouse", ("仓储", "物流", "储备库", "仓库")),
    ("industrial", ("工业", "工矿", "采矿", "盐田", "厂房", "制造")),
    ("residential", ("住宅", "居住", "住房", "保障房", "宅基地", "社区服务设施", "公寓")),
    ("transportation", ("交通", "道路", "铁路", "公路", "机场", "港口", "码头", "停车场", "场站", "管道运输")),
    ("utility", ("公用设施", "公共设施", "供水", "排水", "供电", "燃气", "供热", "通信", "邮政", "广播电视", "环卫", "消防", "水工设施")),
    ("green", ("绿地", "公园", "广场", "开敞空间")),
    ("public", ("公共管理", "机关团体", "教育", "科研", "医疗", "卫生", "社会福利", "文化", "体育", "新闻出版", "科教", "医卫慈善", "文体娱乐")),
    ("special", ("特殊", "军事", "使领馆", "宗教", "文物古迹", "监教", "殡葬", "风景名胜设施")),
)


def _text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("value", "")
    text = str(value or "").strip()
    if not text or text == "______" or text.startswith("【请填写"):
        return ""
    return text


def infer_land_usage_key(text: Any) -> str:
    usage = _text(text)
    if not usage:
        return ""
    if usage in LAND_USAGE_EXACT_ALIASES:
        return LAND_USAGE_EXACT_ALIASES[usage]
    for option in LAND_USAGE_OPTIONS:
        if option.label == usage or option.report_value == usage or option.price_class == usage or option.current_class == usage:
            return option.key
    for key, keywords in LAND_USAGE_KEYWORD_RULES:
        if any(keyword in usage for keyword in keywords):
            return key
    return OTHER_LAND_USAGE_KEY


def land_usage_first_level_label(key: str) -> str:
    option = LAND_USAGE_OPTION_BY_KEY.get(key)
    return option.label if option else "其他"


def official_land_usage_code(key: str) -> str:
    return LAND_USAGE_OFFICIAL_V3_CODE_BY_KEY.get(key, "")


def normalize_land_usage_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    raw_usage = _text(data.get("land_usage")) or _text(data.get("land_usage_short")) or _text(data.get("land_usage_full"))
    key = _text(data.get("land_usage_key"))
    if key not in LAND_USAGE_OPTION_BY_KEY and key != OTHER_LAND_USAGE_KEY:
        key = infer_land_usage_key(raw_usage)

    if key == OTHER_LAND_USAGE_KEY:
        other = _text(data.get("land_usage_other")) or raw_usage
        if not other:
            return data
        usage = other
        current_class = other
        price_class = other
        asset_category = "other"
    elif key in LAND_USAGE_OPTION_BY_KEY:
        option = LAND_USAGE_OPTION_BY_KEY[key]
        usage = option.price_class or option.report_value
        current_class = option.price_class or option.current_class
        price_class = option.price_class
        asset_category = option.asset_category
        other = ""
    else:
        return data

    data["land_usage_key"] = key
    if key == OTHER_LAND_USAGE_KEY:
        data["land_usage_other"] = other
    else:
        data["land_usage_other"] = ""
    data["land_usage"] = usage
    data["land_usage_short"] = usage
    data["land_usage_full"] = usage
    data["land_usage_current_class"] = current_class
    data["land_usage_price_class"] = price_class
    data["asset_use_category"] = asset_category
    if asset_category == "other":
        data["asset_use_category_other"] = data.get("land_usage_other") or usage
    else:
        data["asset_use_category_other"] = ""
    return data
