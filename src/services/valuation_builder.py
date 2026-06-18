# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from collections import Counter
from typing import Any, Dict, List

from src.services.ownership_builder import (
    asset_use_label,
    compile_desc_segments,
    infer_asset_use_category,
)
from src.services.land_usage import normalize_land_usage_fields


METHODS = [
    {
        "flag": "use_cost_approx",
        "name": "成本逼近法",
        "price_key": "cost_approx_price",
        "fit": {
            "residential": "可结合土地取得、开发成本及相关税费利润等资料，对估价对象在设定条件下的土地价格进行测算。",
            "industrial": "工矿用地成本构成、土地开发投入和基础设施配套成本通常具备可分析性，适合采用成本逼近法进行测算。",
            "commercial": "在可合理取得土地取得成本、开发成本及相关税费利润资料时，成本逼近法可作为商业服务业用地价格测算的校核方法。",
            "public": "公共管理与公共服务用地受公益属性和规划限制影响较大，成本逼近法可用于反映土地取得及开发投入水平。",
            "other": "在相关成本构成资料可合理确认时，成本逼近法可作为估价对象价格测算的方法之一。",
        },
    },
    {
        "flag": "use_market_comp",
        "name": "市场比较法",
        "price_key": "market_comp_price",
        "fit": {
            "residential": "当地居住用地及类似房地产交易资料具备可比基础，可通过可比实例修正测算估价对象价格。",
            "industrial": "当地工矿用地成交或供应案例可用于比较分析，可结合区位、用途、开发程度等因素修正确定价格。",
            "commercial": "商业服务业用地价格受临街条件、客流、商业可达性及市场交易活跃度影响明显，存在可比实例时适宜采用市场比较法。",
            "public": "若可取得类似公共服务设施或同类用途用地案例，可通过用途限制和区位条件修正进行比较测算。",
            "other": "在能够取得类似用途或相近条件交易案例时，可采用市场比较法进行比较测算。",
        },
    },
    {
        "flag": "use_income_cap",
        "name": "收益还原法",
        "price_key": "income_cap_price",
        "fit": {
            "residential": "若估价对象可形成稳定租金或居住收益资料，可通过收益资本化路径测算其土地收益价值。",
            "industrial": "若工矿用地相关物业租金、经营收益或生产配套收益可合理量化，可采用收益还原法进行测算。",
            "commercial": "商业服务业用地通常与经营收益、租金水平及客流条件关联紧密，收益资料可取得时适宜采用收益还原法。",
            "public": "公共管理与公共服务用地收益属性较弱，只有在可识别稳定收益或替代收益资料时才适合采用收益还原法。",
            "other": "在估价对象能够形成稳定收益且收益参数可合理确定时，可采用收益还原法。",
        },
    },
    {
        "flag": "use_benchmark_corr",
        "name": "基准地价系数修正法",
        "price_key": "benchmark_corr_price",
        "fit": {
            "residential": "估价对象处于城镇基准地价覆盖范围内，且用途、级别和修正因素可对应时，适宜采用基准地价系数修正法。",
            "industrial": "估价对象位于基准地价覆盖区域内，工矿用地级别和修正体系明确时，可采用基准地价系数修正法。",
            "commercial": "商业服务业用地如处于基准地价覆盖区域，且商业级别、临街深度等修正因素可确定，可采用基准地价系数修正法。",
            "public": "公共管理与公共服务用地如有对应基准地价体系和用途修正规则，可采用基准地价系数修正法。",
            "other": "若当地基准地价体系包含估价对象用途并可进行因素修正，可采用基准地价系数修正法。",
        },
    },
    {
        "flag": "use_residual",
        "name": "剩余法",
        "price_key": "residual_price",
        "fit": {
            "residential": "居住用地开发价值、建设成本、税费、利润等参数能够合理估算时，剩余法可反映开发利用条件下的土地价值。",
            "industrial": "工矿用地项目若可确定建成后价值、建设成本和开发利润，剩余法可作为特定开发情形下的测算方法。",
            "commercial": "商业服务业项目开发价值与经营预期关联较强，在售价、租金、成本和利润参数可确定时适合采用剩余法。",
            "public": "公共管理与公共服务用地开发收益属性通常较弱，剩余法仅在具备明确开发价值和成本参数时适用。",
            "other": "在可合理估算开发完成价值、建设成本及相关税费利润时，可采用剩余法。",
        },
    },
]

VALUATION_TEXT_KEYS = [
    "valuation_method_reasons",
    "valuation_method_applicability",
    "final_price_determination",
    "valuation_result_statement",
    "infrastructure_detail",
    "formula_display_text",
    "cost_approx_land_class_intro",
    "cost_approx_process_intro",
    "cost_approx_method_intro",
    "market_comp_method_intro",
    "market_comp_step1_instances",
    "market_comp_step4_solve",
    "income_cap_method_intro",
    "benchmark_corr_method_intro",
    "residual_method_intro",
]

METHOD_NAME_FIELDS = {
    "成本逼近法": "use_cost_approx",
    "市场比较法": "use_market_comp",
    "收益还原法": "use_income_cap",
    "基准地价系数修正法": "use_benchmark_corr",
    "剩余法": "use_residual",
}

COST_APPROX_INTRO = """成本逼近法是以开发土地所耗费的各项费用之和为主要依据，再加上一定的利润、利息、应缴纳的税金和土地增值收益来确定土地价格的估价方法。成本逼近法的基本计算公式如下：
V＝Ea＋Ed＋T＋R1＋R2＋R3＝VE＋R3
式中：
V——估价价格
Ea——土地取得费
Ed——土地开发费
T——税费
R1——利息
R2——利润
R3——土地增值
VE——土地成本价"""

MARKET_COMP_INTRO = """市场比较法是根据替代原理，将估价对象与在较近时期内已发生交易的类似土地交易实例进行对照比较，并依据后者已知的价格，参照该土地的交易情况、估价期日、区域以及个别因素等差别修正得出估价对象在估价期日的地价。市场比较法计算公式如下：
P＝PB×A×B×C×D×E×F
式中：
P——估价对象价格
PB——交易案例价格
A——交易情况修正系数（估价对象交易情况指数/比较实例交易情况指数）
B——交易方式修正系数（估价对象交易方式指数/比较实例交易方式指数）
C——估价期日修正系数（估价对象估价期日地价指数/比较实例交易日期地价指数）
D——区域因素修正系数（估价对象区域因素条件指数/比较实例区域因素条件指数）
E——个别因素修正系数（估价对象个别因素条件指数/比较实例个别因素条件指数）
F——年期修正系数（估价对象年期修正指数/比较实例年期修正指数）"""

INCOME_CAP_INTRO = """收益还原法是在估算估价对象在未来每年预期纯收益（正常年纯收益）的基础上，以一定的土地还原率，将评估对象在未来每年的纯收益折算为估价期日收益总和的一种方法。
法定有限年期的土地使用权价格计算公式为：
P＝A/r×[1－1/（1＋r）^n]
式中：
P——土地价格
A——土地年纯收益
r——土地还原利率
n——使用土地的年期或有土地收益的年期
具体测算思路是：
A、房地年总收益＝房地年租金＝月租金×12×收益总面积×出租率×有效使用面积比率
B、房地出租年总费用＝维修费+管理费+保险费+税金
C、房地年纯收益＝房地年总收益-房地出租年总费用
D、房屋年纯收益＝房屋现值×房屋还原率
E、土地年纯收益＝房地年纯收益-房屋年纯收益
F、总地价＝土地年纯收益÷r×[1-1/（1+r）^n]
G、单位面积地价＝总地价÷总用地面积"""

BENCHMARK_CORR_INTRO = """基准地价系数修正法是利用城镇基准地价和基准地价修正系数表等评估成果，按照替代原则，将被估宗地的区域条件和个别条件等与其所处区域的平均条件相比较，并对照修正系数表选取相应的修正系数对基准地价进行修正，进而求取宗地价格的一种估价方法。基准地价系数修正法计算公式如下：
P＝P1b×（1＋∑K）×Ky×Kd×Kr
式中：
P——宗地价格
P1b——估价对象所处级别的基准地价
∑K——影响地价的区域及个别因素修正系数之和
Ky——使用年期修正系数
Kd——期日修正系数
Kr——容积率修正系数"""

RESIDUAL_INTRO = """剩余法是在估算开发完成后不动产正常交易价格的基础上，扣除建筑物建造费用和与建筑物建造、买卖有关的专业费、利息、利润、税收等费用后，以价格余额来估算土地价格的方法。剩余法的基本计算公式如下：
V＝A－（B＋C＋D＋E＋F）
式中：
V——土地价格
A——开发完成后不动产的总价值
B——整个项目的开发成本（建筑安装工程费等）
C——专业费用（前期设计、策划费等）
D——投资利息
E——开发利润
F——租售税费及其他税收"""

PROMPT_FIELD_MAP = {
    "【请填写政府批复文件】": "acquisition_approval_doc_name",
    "【请填写批复文号】": "acquisition_approval_doc_no",
    "【请填写批复日期】": "acquisition_approval_doc_date",
    "【请填写被征地类】": "acquisition_land_class",
    "【请填写所属市级】": "local_city",
    "【请填写评估所属县市简称】": "county_name",
    "#县市简称#": "county_name",
    "【请填写规划条件批准机关】": "planning_approval_authority",
    "【请填写设定容积率上限】": "plot_ratio",
    "【请填写设定容积率】": "plot_ratio",
    "【请填写容积率】": "plot_ratio",
    "【请填写土地面积】": "land_area",
    "【请填写估价期日】": "valuation_date",
    "【请填写土地用途】": "land_usage",
    "【请填写设定用途】": "land_usage",
    "【请填写土地使用年期】": "land_use_term",
    "【请填写土地开发程度】": "land_development_set",
    "【请填写土地单价】": "final_unit_price",
    "【请填写土地总价】": "final_total_price",
    "【请填写土地总价大写】": "final_total_price_upper",
    "【请填写成本逼近法单价】": "cost_approx_price",
    "【请填写市场比较法单价】": "market_comp_price",
    "【请填写收益还原法单价】": "income_cap_price",
    "【请填写基准地价系数修正法单价】": "benchmark_corr_price",
    "【请填写剩余法单价】": "residual_price",
    "【请填写基准地价批准文号】": "base_price_doc_no",
    "【请填写基准地价发布文号】": "base_price_doc_no",
    "【请填写基准地价文件名称】": "base_price_doc_name",
    "【请填写基准地价颁布实施日期】": "base_price_publish_date",
    "【请填写基准地价估价基准日】": "base_price_base_date",
    "【请填写基准地价批准机关】": "base_price_doc_authority",
    "【请填写基准地价发布机关】": "base_price_doc_authority",
    "【请填写土地评估计算过程依据】": "valuation_basis_docs_list",
}

PROMPT_PREHEAL_MAP = {
    "county_name": "【请填写评估所属县市简称】",
    "planning_approval_authority": "【请填写规划条件批准机关】",
}

BASE_PRICE_PROMPTS = {
    "base_price_doc_no": "【请填写基准地价批准文号】",
    "base_price_doc_name": "【请填写基准地价文件名称】",
    "base_price_publish_date": "【请填写基准地价颁布实施日期】",
    "base_price_base_date": "【请填写基准地价估价基准日】",
    "base_price_doc_authority": "【请填写基准地价批准机关】",
}

METHOD_PRICE_PROMPTS = {
    "cost_approx_price": "【请填写成本逼近法单价】",
    "market_comp_price": "【请填写市场比较法单价】",
    "income_cap_price": "【请填写收益还原法单价】",
    "benchmark_corr_price": "【请填写基准地价系数修正法单价】",
    "residual_price": "【请填写剩余法单价】",
}


def _field_value(data: Dict[str, Any], key: str, default: Any = "") -> Any:
    value = data.get(key, default)
    if isinstance(value, dict):
        value = value.get("value", default)
    return default if value is None else value


def _text(data: Dict[str, Any], key: str, default: str = "") -> str:
    value = _field_value(data, key, default)
    text = str(value).strip()
    if not text or text == "______" or text.startswith("【请填写"):
        return default
    return text


def _is_blank_or_prompt(value: Any) -> bool:
    text = str(value or "").strip()
    return not text or text == "______" or text.startswith("【请填写")


def _preheal_prompt_fields(data: Dict[str, Any]) -> None:
    for key, prompt in PROMPT_PREHEAL_MAP.items():
        if _is_blank_or_prompt(_field_value(data, key, "")):
            data[key] = prompt


def _sync_legacy_land_usage_fields(data: Dict[str, Any]) -> None:
    normalize_land_usage_fields(data)


def _sync_acquisition_fields(data: Dict[str, Any]) -> None:
    """将旧版征地批复字段回填到正式字段，征收地类不得从土地用途派生。"""
    legacy_map = {
        "acquisition_land_class": "original_land_owner_desc",
        "acquisition_approval_doc_name": "gov_approval_name",
        "acquisition_approval_doc_no": "gov_approval_no",
        "acquisition_approval_doc_date": "gov_approval_date",
    }
    for target, legacy in legacy_map.items():
        if _is_blank_or_prompt(_field_value(data, target, "")):
            legacy_value = _text(data, legacy)
            if legacy_value:
                data[target] = legacy_value


def _local_city(data: Dict[str, Any]) -> str:
    explicit = _text(data, "local_city")
    if explicit:
        return explicit

    county = _text(data, "county_name") or _text(data, "local_county")
    if "通道" in county:
        return "怀化市"
    if "道县" in county:
        return "永州市"
    return "【请填写所属市级】"


def _approval_doc_reference(data: Dict[str, Any]) -> str:
    name = _text(data, "acquisition_approval_doc_name")
    if not name:
        return ""
    details = [
        value
        for value in (
            _text(data, "acquisition_approval_doc_no"),
            _text(data, "acquisition_approval_doc_date"),
        )
        if value
    ]
    parsed_name = _parse_doc_name(name)
    return f"{parsed_name}（{'，'.join(details)}）" if details else parsed_name


def _cost_approx_land_class_intro(data: Dict[str, Any]) -> str:
    location = _text(data, "land_location_full") or _text(data, "land_location", "【请填写估价对象坐落】")
    land_class = _text(data, "acquisition_land_class", "【请填写被征地类】")
    approval_doc = _approval_doc_reference(data)
    if approval_doc:
        return (
            f"估价对象位于{location}，根据{approval_doc}，评估宗地征收地类为{land_class}，"
            f"此次采用成本逼近法评估待估宗地地价时，估价期日被征用的土地为{land_class}。"
        )
    return (
        f"估价对象位于{location}，根据对估价对象周边区域用地调查，评估宗地以{land_class}为主，"
        f"此次采用成本逼近法评估待估宗地地价时，考虑估价期日被征用的土地为{land_class}。"
    )


def _derive_plot_ratio_display(data: Dict[str, Any]) -> None:
    # 1. 规划容积率派生
    plot_mode = str(_field_value(data, "plot_ratio_mode", "range") or "range").strip()
    plot_ratio = str(_field_value(data, "plot_ratio", "") or "").strip()
    plot_ratio_min = str(_field_value(data, "plot_ratio_min", "") or "").strip()
    if plot_mode not in ("range", "fixed"):
        plot_mode = "range" if plot_ratio_min else "fixed"
    data["plot_ratio_mode"] = plot_mode
    data["plot_ratio_display"] = f"{plot_ratio_min}-{plot_ratio}" if plot_mode == "range" and plot_ratio_min else plot_ratio

    # 2. 设定容积率派生与自愈兜底
    set_mode = str(_field_value(data, "set_plot_ratio_mode", "fixed") or "fixed").strip()
    set_ratio = str(_field_value(data, "set_plot_ratio", "") or "").strip()
    set_ratio_min = str(_field_value(data, "set_plot_ratio_min", "") or "").strip()
    
    if set_mode not in ("range", "fixed"):
        set_mode = "range" if set_ratio_min else "fixed"
    data["set_plot_ratio_mode"] = set_mode

    # 如果整个设定容积率没有手动填写上限/固定值（即空字符串或占位符），
    # 并且如果是 fixed 模式下，我们会自动兜底取规划容积率的相应设定
    if set_mode == "fixed":
        if not set_ratio or set_ratio == "______" or "【请填写" in set_ratio:
            data["set_plot_ratio"] = _field_value(data, "plot_ratio")
            set_ratio = str(_field_value(data, "plot_ratio", "") or "").strip()

    # 3. 拼接设定容积率的展示拼接字段
    if set_mode == "range" and set_ratio_min:
        data["set_plot_ratio_display"] = f"{set_ratio_min}-{set_ratio}"
    else:
        data["set_plot_ratio_display"] = set_ratio


def _force_default_text_options(data: Dict[str, Any]) -> None:
    data["show_price_in_text"] = True
    data["explain_unselected_methods"] = True


def _bool(data: Dict[str, Any], key: str, default: bool = False) -> bool:
    value = _field_value(data, key, default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes", "y", "是", "开启")


def _benchmark_corr_block_reason(data: Dict[str, Any]) -> str:
    county = _text(data, "county_name") or _text(data, "county") or _text(data, "local_county")
    if county and "通道" not in county:
        return f"当前基准地价系数修正法结构化测算仅适配通道县，{county}暂不按通道县基准地价口径试算。"
    if _bool(data, "base_price_is_expired") or str(data.get("base_price_expiry_status") or "").strip() == "expired":
        doc_no = _text(data, "base_price_doc_no") or _text(data, "base_land_price_doc_no") or BASE_PRICE_PROMPTS["base_price_doc_no"]
        doc_name = _text(data, "base_price_doc_name") or _text(data, "base_land_price_doc_name") or BASE_PRICE_PROMPTS["base_price_doc_name"]
        pub_date = _text(data, "base_price_publish_date") or _text(data, "base_land_price_pub_date") or BASE_PRICE_PROMPTS["base_price_publish_date"]
        base_date = _text(data, "base_price_base_date") or _text(data, "base_land_price_value_date") or BASE_PRICE_PROMPTS["base_price_base_date"]
        authority = _text(data, "base_price_doc_authority") or _text(data, "base_land_price_doc_authority") or BASE_PRICE_PROMPTS["base_price_doc_authority"]
        v_date = _text(data, "valuation_date") or "【请填写估价期日】"
        rule_doc_name = _text(data, "base_price_rule_doc_name", "《关于进一步做好湖南省公示地价体系建设和管理有关工作的通知》")
        rule_doc_no = _text(data, "base_price_rule_doc_no", "湘自资办发[2022]23号")
        update_cycle = _text(data, "base_price_update_cycle_years_text", "三")
        threshold_text = _text(data, "base_price_disable_threshold_years_text", "六")
        county_text = county or _text(data, "local_county") or "当地"
        return (
            f"{county_text}城镇基准地价的颁布实施时间为{pub_date}，城区基准地价估价基准日为{base_date}，"
            f"批准文号为{doc_no}，文件名称为{doc_name}，批准机关为{authority}，本次估价期日为{v_date}，"
            f"距估价期日超过{threshold_text}年，根据{rule_doc_name}（{rule_doc_no}）："
            f"“城镇基准地价每{update_cycle}年应全面更新一次，超过{threshold_text}年未全面更新的，"
            f"不得作为确定出让最低价标准的依据，不得作为宗地评估基准地价系数修正法的依据。”"
            f"因此不选择公示地价系数修正法。"
        )
    analysis = data.get("benchmark_corr_analysis") or {}
    support_status = str(analysis.get("support_status") or "").strip()
    missing = analysis.get("support_missing_items") or []
    if support_status in {"unsupported", "incomplete"} and missing:
        return "基准地价系数修正法尚有关键配置或修正因素待补齐：" + "；".join(str(item) for item in missing[:5])
    return ""


def _number(data: Dict[str, Any], key: str, default: int | None = None) -> int | None:
    val = _field_value(data, key, None)
    if val is None or str(val).strip() == "" or str(val).strip() == "______":
        return default
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


def _first_text(data: Dict[str, Any], keys: List[str], default: str = "") -> str:
    for key in keys:
        text = _text(data, key)
        if text:
            return text
    return default


def _first_bool(data: Dict[str, Any], keys: List[str], default: bool = False) -> bool:
    for key in keys:
        value = _field_value(data, key, None)
        if value is None or str(value).strip() == "":
            continue
        return _bool(data, key)
    return default


def _chinese_number(num: int) -> str:
    digits = "零一二三四五六七八九"
    if num < 0:
        return digits[0]
    if num < 10:
        return digits[num]
    if num < 20:
        return "十" if num == 10 else "十" + digits[num % 10]
    if num < 100:
        tens, ones = divmod(num, 10)
        return digits[tens] + "十" + (digits[ones] if ones else "")
    return str(num)


def _year_threshold_number(value: Any, default: int = 6) -> int:
    text = str(value or "").strip().replace("年", "")
    match = re.search(r"\d+", text)
    if match:
        return int(match.group(0))
    zh_map = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if text in zh_map:
        return zh_map[text]
    if text.startswith("十"):
        return 10 + zh_map.get(text[1:2], 0)
    if "十" in text:
        head, tail = text.split("十", 1)
        return zh_map.get(head, 0) * 10 + zh_map.get(tail[:1], 0)
    return default


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text or text == "______":
        return None
    match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", text)
    if not match:
        match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if not match:
        return None
    try:
        year, month, day = map(int, match.groups())
        return date(year, month, day)
    except ValueError:
        return None


def _year_from_text(value: Any) -> int | None:
    match = re.search(r"(\d{4})", str(value or ""))
    return int(match.group(1)) if match else None


def _calculate_expired_years(val_date: Any, base_date: Any) -> tuple[int, str]:
    val_dt = _parse_date(val_date)
    base_dt = _parse_date(base_date)
    if val_dt and base_dt:
        years = val_dt.year - base_dt.year
        if (val_dt.month, val_dt.day) < (base_dt.month, base_dt.day):
            years -= 1
        years = max(years, 0)
        return years, _chinese_number(years)

    val_year = _year_from_text(val_date)
    base_year = _year_from_text(base_date)
    if val_year is not None and base_year is not None:
        years = max(val_year - base_year, 0)
        return years, _chinese_number(years)

    return 0, ""


def _normalize_base_price_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    local_county = _text(data, "county_name") or _text(data, "local_county", "当地")
    local_gov = _text(data, "local_gov") or f"{local_county}人民政府"

    field_map = {
        "base_price_doc_no": ["base_price_doc_no", "base_land_price_doc_no"],
        "base_price_doc_name": ["base_price_doc_name", "base_land_price_doc_name"],
        "base_price_publish_date": [
            "base_price_publish_date",
            "base_land_price_publish_date",
            "base_land_price_pub_date",
        ],
        "base_price_base_date": [
            "base_price_base_date",
            "base_land_price_date",
            "base_land_price_value_date",
        ],
        "base_price_doc_authority": [
            "base_price_doc_authority",
            "base_land_price_doc_authority",
            "base_land_price_authority",
        ],
    }

    placeholders = {
        "base_price_doc_no": "",
        "base_price_doc_name": "",
        "base_price_publish_date": "",
        "base_price_base_date": "",
        "base_price_doc_authority": "",
    }

    for target, keys in field_map.items():
        value = _first_text(data, keys, placeholders[target])
        data[target] = value

    data["base_price_rule_doc_name"] = _first_text(
        data,
        ["base_price_rule_doc_name", "base_land_price_rule_doc_name"],
        "《关于进一步做好湖南省公示地价体系建设和管理有关工作的通知》",
    )
    data["base_price_rule_doc_no"] = _first_text(
        data,
        ["base_price_rule_doc_no", "base_land_price_rule_doc_no"],
        "湘自资办发[2022]23号",
    )
    data["base_price_update_cycle_years_text"] = _first_text(
        data,
        ["base_price_update_cycle_years_text", "base_land_price_expire_limit"],
        "三",
    )
    data["base_price_disable_threshold_years_text"] = _first_text(
        data,
        ["base_price_disable_threshold_years_text"],
        "六",
    )

    comparison_date = data.get("base_price_base_date") or data.get("base_price_publish_date")
    elapsed_years, elapsed_text = _calculate_expired_years(_text(data, "valuation_date"), comparison_date)
    can_judge_expiry = bool(_parse_date(_text(data, "valuation_date")) and _parse_date(comparison_date))
    threshold = _year_threshold_number(data["base_price_disable_threshold_years_text"], 6)
    is_expired = bool(can_judge_expiry and elapsed_years > threshold)
    data["base_price_is_expired"] = is_expired
    data["is_base_price_expired"] = is_expired
    data["base_price_expiry_status"] = "expired" if is_expired else "valid" if can_judge_expiry else "unknown"
    data["base_price_elapsed_years_number"] = elapsed_years
    data["base_price_elapsed_years_text"] = elapsed_text
    data["expired_years_text"] = elapsed_text

    # Backward-compatible aliases for old templates/scripts.
    data["base_land_price_doc_no"] = data["base_price_doc_no"]
    data["base_land_price_doc_name"] = data["base_price_doc_name"]
    data["base_land_price_publish_date"] = data["base_price_publish_date"]
    data["base_land_price_date"] = data["base_price_base_date"]
    data["base_land_price_doc_authority"] = data["base_price_doc_authority"]
    data["base_land_price_pub_date"] = data["base_price_publish_date"]
    data["base_land_price_value_date"] = data["base_price_base_date"]

    return data


def _base_price_elapsed_clause(data: Dict[str, Any]) -> str:
    threshold_text = _text(data, "base_price_disable_threshold_years_text", "六")
    status = str(data.get("base_price_expiry_status") or "").strip()
    if status == "expired":
        return f"距估价期日超过{threshold_text}年"
    if status == "valid":
        return f"距估价期日未超过{threshold_text}年"
    return "基准地价时效需补充日期后判断"


def _base_price_policy_warnings(data: Dict[str, Any]) -> List[str]:
    if not _bool(data, "base_price_is_expired"):
        return []
    warnings = []
    for key, label in [
        ("base_price_doc_no", "基准地价批准文号"),
        ("base_price_doc_name", "基准地价文件名称"),
        ("base_price_publish_date", "基准地价颁布实施日期"),
        ("base_price_base_date", "基准地价估价基准日"),
    ]:
        if str(data.get(key) or "").startswith("【请填写"):
            warnings.append(f"{label}尚未填写，基准地价过期说明可能不完整。")
    return warnings


def _decimal(value: Any) -> Decimal | None:
    text = str(value or "").strip()
    if not text or text == "______":
        return None
    text = re.sub(r"[^\d.\-]", "", text)
    if not text or text in ("-", ".", "-."):
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _fmt_decimal(value: Decimal | None, places: str = "0.1") -> str:
    if value is None:
        return ""
    quant = Decimal(places)
    rounded = value.quantize(quant, rounding=ROUND_HALF_UP)
    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _join_names(names: List[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return "、".join(names[:-1]) + "和" + names[-1]


def _selected_methods(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    selected = []
    for item in METHODS:
        if not _bool(data, item["flag"]):
            continue
        price_key = item["price_key"]
        price_value = _text(data, price_key)
        if not price_value and _is_blank_or_prompt(_field_value(data, price_key, "")):
            price_value = METHOD_PRICE_PROMPTS.get(price_key, "")
            if price_value:
                data[price_key] = price_value
        selected.append(
            {
                **item,
                "price_value": price_value,
                "price_decimal": _decimal(price_value),
            }
        )
    return selected


def _weight_logic(data: Dict[str, Any]) -> str:
    logic = _text(data, "weight_logic_type", "weighted_average")
    if logic in ("simple_average", "weighted_average"):
        return "weighted_average"
    if logic in ("median", "mode", "single_dominance"):
        return logic
    return "weighted_average"


def _method_weight_percentages(data: Dict[str, Any]) -> Dict[str, Decimal]:
    raw = data.get("method_weight_percentages") or {}
    if isinstance(raw, dict) and "value" in raw and isinstance(raw.get("value"), dict):
        raw = raw.get("value") or {}
    if not isinstance(raw, dict):
        return {}
    weights: Dict[str, Decimal] = {}
    for key, value in raw.items():
        decimal_value = _decimal(value)
        if decimal_value is not None:
            weights[str(key)] = decimal_value
    return weights


def _weights_for_methods(data: Dict[str, Any], methods: List[Dict[str, Any]]) -> Dict[str, Decimal]:
    if not methods:
        return {}

    logic = _weight_logic(data)
    dominant = _text(data, "dominant_method_name")
    names = [item["name"] for item in methods]

    if logic == "single_dominance" and dominant in names:
        return {item["name"]: Decimal("100") if item["name"] == dominant else Decimal("0") for item in methods}

    custom_weights = _method_weight_percentages(data)
    if logic == "weighted_average" and custom_weights:
        weights = {item["name"]: custom_weights.get(item["flag"], Decimal("0")) for item in methods}
        total = sum(weights.values())
        if total == Decimal("100"):
            return weights

    equal = (Decimal("100") / Decimal(len(methods))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    weights = {item["name"]: equal for item in methods}
    diff = Decimal("100") - sum(weights.values())
    weights[methods[-1]["name"]] += diff
    return weights


def _formula_text(methods: List[Dict[str, Any]], weights: Dict[str, Decimal], logic: str = "weighted_average") -> str:
    if not methods:
        return ""
    names = _join_names([item["name"] for item in methods])
    if logic == "median":
        return f"{names}测算结果的中位数"
    if logic == "mode":
        return f"{names}测算结果的众数"
    if logic == "single_dominance":
        dominant = next((item["name"] for item in methods if weights.get(item["name"], Decimal("0")) == Decimal("100")), "")
        return dominant or names
    return "+".join(f"{item['name']}×{_fmt_decimal(weights.get(item['name']), '0.01')}%" for item in methods)


def _median_price(methods: List[Dict[str, Any]]) -> Decimal | None:
    prices = sorted(item["price_decimal"] for item in methods if item["price_decimal"] is not None)
    if not prices:
        return None
    mid = len(prices) // 2
    if len(prices) % 2:
        return prices[mid]
    return (prices[mid - 1] + prices[mid]) / Decimal("2")


def _mode_price(methods: List[Dict[str, Any]], data: Dict[str, Any] | None = None) -> Decimal | None:
    prices = [item["price_decimal"] for item in methods if item["price_decimal"] is not None]
    if not prices:
        return None
    normalized = [price.normalize() for price in prices]
    counts = Counter(normalized)
    highest = max(counts.values())
    modes = [value for value, count in counts.items() if count == highest]
    if highest <= 1 or len(modes) != 1:
        if data is not None:
            data["requires_manual_final_price"] = True
        return None
    return modes[0]


def _final_unit_price(
    methods: List[Dict[str, Any]],
    weights: Dict[str, Decimal],
    logic: str = "weighted_average",
    data: Dict[str, Any] | None = None,
) -> Decimal | None:
    if not methods:
        return None
    if logic == "median":
        return _median_price(methods)
    if logic == "mode":
        return _mode_price(methods, data)
    total = Decimal("0")
    has_price = False
    for item in methods:
        price = item["price_decimal"]
        if price is None:
            continue
        total += price * weights.get(item["name"], Decimal("0")) / Decimal("100")
        has_price = True
    return total if has_price else None


def _weight_warnings(data: Dict[str, Any], formula: str, methods: List[Dict[str, Any]]) -> List[str]:
    warnings = []
    if not methods:
        warnings.append("尚未选择估价方法，无法生成正式确价测算段落。")

    for item in methods:
        if item["price_decimal"] is None:
            warnings.append(f"{item['name']}已勾选，但未填写有效单价。")

    logic = _weight_logic(data)
    if logic == "weighted_average":
        custom_weights = _method_weight_percentages(data)
        if custom_weights:
            active_total = sum(custom_weights.get(item["flag"], Decimal("0")) for item in methods)
            if active_total != Decimal("100"):
                warnings.append(f"加权算术平均的权重合计为{_fmt_decimal(active_total, '0.01')}%，请调整为100%。")
    if logic == "mode" and _mode_price(methods, data) is None:
        warnings.append("众数确价未形成唯一众数，请手填最终单价或切换为加权算术平均/中位数。")

    weights = [Decimal(match) for match in re.findall(r"(\d+(?:\.\d+)?)\s*%", formula or "")]
    if weights and sum(weights) != Decimal("100"):
        warnings.append(f"确价公式中的权重合计为{_fmt_decimal(sum(weights), '0.01')}%，请复核是否应为100%。")
    return warnings


def _use_detail(category: str, label: str, custom: str) -> str:
    if category == "residential":
        return f"{label}重点关注居住配套、道路通达、供水、供电、排水、通讯及场地平整等条件"
    if category == "industrial":
        return f"{label}重点关注交通运输、供电容量、给排水、生产配套、通讯及场地平整等条件"
    if category == "commercial":
        return f"{label}重点关注临街条件、商业可达性、客流基础、公共服务配套及市政管网条件"
    if category == "public":
        return f"{label}重点关注公共服务设施、市政配套、交通可达性、公益属性及规划限制条件"
    return f"{custom or label}应结合具体用途、规划条件、市政配套和现场利用状况综合判断"


def _method_applicability(data: Dict[str, Any], methods: List[Dict[str, Any]], category: str, label: str) -> str:
    if not methods:
        return ""
    desc = f"本次评估结合{label}的用途条件、权利状况、开发程度、资料完备性及当地土地市场状况，对已选估价方法进行适用性分析。"
    parts = [desc]
    for item in methods:
        parts.append(f"【{item['name']}】{item['fit'].get(category) or item['fit']['other']}")

    if _bool(data, "base_price_is_expired") and any(item["name"] == "基准地价系数修正法" for item in methods):
        parts.append(f"本次已关注基准地价成果{_base_price_elapsed_clause(data)}的时效问题，并在修正及结果确定环节进行复核。")

    purpose = _text(data, "transfer_purpose") or _text(data, "valuation_purpose")
    right_type = _text(data, "right_type")
    if purpose or right_type:
        tail = []
        if purpose:
            tail.append(f"估价目的为{purpose}")
        if right_type:
            tail.append(f"设定土地权利类型为{right_type}")
        parts.append(f"本评估在{ '、'.join(tail) }的前提下进行，选用方法与本次估价目的及设定条件相匹配。")
    else:
        parts.append(f"上述方法与{label}的设定用途及估价对象实际资料条件相匹配。")
    return "".join(parts)


# ==============================================================================
# 核心重构 1：新增通用外部 YAML 话术缓存及动态渲染 (一法一议，降级兜底)
# ==============================================================================
_TEXT_LIB_CACHE = None

def _get_text_lib() -> dict:
    global _TEXT_LIB_CACHE
    if _TEXT_LIB_CACHE is not None:
        return _TEXT_LIB_CACHE
    import os
    import yaml
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    text_library_path = os.path.join(BASE_DIR, "text_library.yaml")
    try:
        with open(text_library_path, 'r', encoding='utf-8') as f:
            _TEXT_LIB_CACHE = yaml.safe_load(f)
    except Exception:
        _TEXT_LIB_CACHE = {}
    if not _TEXT_LIB_CACHE:
        _TEXT_LIB_CACHE = {}
    return _TEXT_LIB_CACHE


def _parse_doc_name(raw: str) -> str:
    raw = raw.strip()
    if not raw or raw == "______":
        return ""
    m = re.match(r'^(.*?)([\(（].*?[\)）])?$', raw)
    if m:
        main_part = m.group(1).strip()
        bracket_part = m.group(2) or ""
        
        if main_part.startswith("《") and main_part.endswith("》"):
            pass
        else:
            main_part = main_part.strip("《》")
            main_part = f"《{main_part}》"
        return main_part + bracket_part
    return f"《{raw.strip('《》')}》"


def _split_doc_items(raw: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    book_depth = 0
    bracket_depth = 0
    separators = set("、,，;；\n")

    for ch in raw:
        if ch == "《":
            book_depth += 1
        elif ch == "》" and book_depth:
            book_depth -= 1
        elif ch in "（(":
            bracket_depth += 1
        elif ch in "）)" and bracket_depth:
            bracket_depth -= 1

        if ch in separators and book_depth == 0 and bracket_depth == 0:
            item = "".join(buf).strip()
            if item:
                parts.append(item)
            buf = []
            continue
        buf.append(ch)

    item = "".join(buf).strip()
    if item:
        parts.append(item)
    return parts


def _parse_basis_docs(raw: str) -> list[str]:
    raw = str(raw or "").strip()
    if raw == "______" or raw.startswith("【请填写"):
        raw = ""
    if not raw:
        return []
    parts = _split_doc_items(raw)
    
    seen = set()
    result = []
    for p in parts:
        parsed = _parse_doc_name(p)
        if parsed and parsed not in seen:
            seen.add(parsed)
            result.append(parsed)
    return result


def _get_adopt_reason(flag: str, category: str, label: str, data: dict) -> str:
    # V13.0: 优先从外部文本素材库加载，支持动态 Jinja2 渲染！
    text_lib = _get_text_lib()
    yaml_reason = text_lib.get("valuation_method_adopt_reasons", {}).get(flag, {}).get(category)
    if yaml_reason:
        from jinja2 import Template as JinjaTemplate
        try:
            return JinjaTemplate(yaml_reason).render(data).strip()
        except Exception:
            pass

    # 兜底保障（若 YAML 中未配置或加载失败，原样无缝降级）
    land_usage_short = _text(data, "land_usage_price_class") or _text(data, "land_usage_short", "设定用途")
    local_county = _text(data, "county_name") or _text(data, "local_county", "当地")
    
    reasons = {
        "use_cost_approx": {
            "residential": f"成本逼近法是以开发土地所耗费的各项客观费用之和为主要依据，再加上一定的利润、利息、应缴纳的税金和土地增值收益来确定土地价格的方法。考虑到估价对象所在区域有土地征收案例，政府公布了征地有关文件与补偿标准，可测算土地取得成本，且红线内外开发及成片前期投入数据充实，故选择成本逼近法作为土地评估方法之一。",
            "industrial": f"成本逼近法是以开发土地所耗费的各项客观费用之和为主要依据，再加上一定的利润、利息、应缴纳的税金和土地增值收益来确定土地价格的方法，尤其对新开发土地，可采用成本逼近法进行评估。考虑到估价对象所在区域有类似征地案例，能够通过征地案例的调查分析，对各项土地取得成本进行量化得出土地价格。根据{local_county}自然资源和规划局土地利用科提出的意见，本次评估采用成本逼近法作为评估方法之一。",
            "commercial": f"成本逼近法是以开发土地所耗费的各项客观费用之和为主要依据，再加上一定的利润、利息、应缴纳的税金和土地增值收益来确定土地价格的方法。对于商业服务业用地，在可合理取得区域成片开发投入和相关土地规费时，可以通过成本逼近法计算宗地重置成本，作为评估的合理核校路径，故采用成本逼近法作为评估方法之一。",
            "public": f"成本逼近法是以开发土地所耗费的各项客观费用之和为主要依据，再加上一定的利润、利息、应缴纳的税金和土地增值收益来确定土地价格的方法。公共管理与公共服务用地具有公益属性，利用现状或规划受限，成本逼近法能够客观反映土地取得及前期各项大市政配套设施的实际重置投入，故采用成本逼近法作为方法之一。",
            "other": f"成本逼近法是以开发土地所耗费的各项客观费用之和为主要依据，再加上一定的利润、利息、应缴纳的税金和土地增值收益来确定土地价格的方法。在各项土地取得及前期配套费客观充实的情况下，能够科学核算物理重置成本，故采用成本逼近法进行评估。"
        },
        "use_market_comp": {
            "residential": f"估价对象位于{local_county}城区，土地规划用途为居住用地，宗地所在区域周边居住用地及住宅市场活跃度高，有充足的同类型土地市场成交案例，可以选择到与估价对象相类似的近期已经发生交易的纯土地市场交易案例，通过对比较案例期日、用途、年期、交易方式、区域因素、个别因素等修正，得出估价对象的比准土地价格，适宜选用市场比较法进行评估。",
            "industrial": f"估价对象位于{local_county}集聚区，土地规划用途为工矿用地，宗地所在区域周边有同类型土地市场成交案例，可以选择到与估价对象相类似的近期已经发生交易的纯土地市场交易案例，通过对比较案例考虑期日、用途、年期、交易方式、区域因素、个别因素等影响因素的修正，得出估价对象的土地价格，适宜选用市场比较法进行评估。",
            "commercial": f"估价对象规划用途为商业服务业用地，若周边同类商业服务业用地交易或流转案例具有可采性，市场比较法能够通过区域和个别因素修正测算地价，故可选用市场比较法进行评估。",
            "public": f"在估价对象所处区域能够收集到同类公共服务设施或公用土地交易实例时，市场比较法能够基于替代原理，通过横向修正真实反映该用途地块在公开市场上的公允价值，故采用市场比较法进行评估。",
            "other": f"在同一供求圈或相近区域内能够收集到符合要求的三宗及以上类似产权交易案例时，采用市场比较法进行修正，能最直接灵敏地反映产权市场的价值实态，故选用该方法。"
        },
        "use_income_cap": {
            "residential": f"由于估价对象地上房屋建筑物有潜在收益，所在区域内同类型用房租赁情况较多，不动产总收益较易确定，且未来收益与风险资本化还原率能够客观量化，故可采用收益还原法作为评估方法之一。",
            "industrial": f"若估价对象周边工业厂房、配套设施的公开出租实例较多，或能通过工业资产的出租收益或通过对工业企业标准厂房生产运营总收益进行科学剥离，合理核算出土地纯收益。通过合理折现，能真实反映土地在工业运营周期内的资产收益潜能，故选用收益还原法作为评估方法之一。",
            "commercial": f"估价对象设定用途为商业服务业用地，如地上房屋建筑物具有经营或租金收益，且同类型商业用房租赁、经营资料具有可采性，可通过收益资本化路径反映其收益价格，故可选用收益还原法作为评估方法之一。",
            "public": f"针对实行市场化收费、能独立核算纯收益的公共服务设施（如营利性医院、私立学校、收费停车场、文体场馆等），其持续稳定的运营收入及相关开发成本能合理量化，可采用收益还原法测算反映其在特定营利许可条件下的资产还原潜力，故采用收益还原法作为方法之一。",
            "other": f"在估价对象存在稳定、可持续的纯收益流，且相关还原率和收益年期参数能够客观且科学核算的前提下，选用收益还原法最能反映资产资本化的核心本质，故选用该方法。"
        },
        "use_benchmark_corr": {
            "residential": f"评估宗地属于{local_county}城区居住用地范围，根据现行有效的城镇基准地价，估价对象位于基准地价覆盖范围内，有科学的居住用地修正体系可以采用，能够保证地价评估符合当地政府宏观地价政策，维护地价的稳定性，故采用公示地价系数修正法（基准地价系数修正法）作为评估方法之一。",
            "industrial": f"评估宗地属于{local_county}城区工矿用地范围，有对应土地级别的工矿用地基准地价标准和修正系数表。该方法有利于从宏观及法定地价等级上把握工矿用地的平均地价水平，故采用基准地价系数修正法作为评估方法之一。",
            "commercial": f"评估宗地处于{local_county}商业基准地价覆盖范围内，商业服务业用地级别与临街因素修正体系完备，能够合理体现商业区位价值等级和政策指导地价水平，具有很好的政策连贯性，故选用基准地价系数修正法作为方法之一。",
            "public": f"评估宗地处于当地城镇基准地价覆盖范围内，公共管理与公共服务用地级别划分明确，且有现行有效的基准地价修正系数规则，有利于贯彻法定价格政策，故采用基准地价系数修正法进行评估。",
            "other": f"估价对象处于基准地价覆盖区内，且规划用途具有对应级别和修正规则，能有效利用政府法定公示成果进行因素修正以反映指导价格水平，故选用该方法。"
        },
        "use_residual": {
            "residential": f"由于估价对象地上房屋建筑物及配套设施可以进行开发或再开发，其规划利用条件和开发设计指标明确。通过对开发完成后的房地产总价值的客观预测，并科学扣除追加的工程建设成本、利税及合理开发利润，能够以残余要素估价原理，科学测算出土地要素的剩余开发价值，故选用剩余法进行评估。",
            "industrial": f"估价对象虽然为工业待开发项目，但若其建成后的厂房与配套销售价格或预期价值可以通过市场比较法合理确定，并且追加的建设成本和开发利税资料清晰，亦可选用剩余法科学核算潜在地价，故选用该方法之一。",
            "commercial": f"估价对象为商业服务业待开发地块，规划设计指标明确，且商业追加开发的预期售价、租金水平、建设成本和合理利润能够合理预测时，可通过剥离后期追加成本测算土地剩余价格，故选用剩余法进行评估。",
            "public": f"在估价对象存在明确的代建开发协议、公共开发利用规划，且建成后的重置总价值与追加建造成本、利税参数能够客观确定的前提下，可通过剩余法作为开发辅助核算，故选用该方法进行评估。",
            "other": f"在估价对象规划条件明确，且开发完成后不动产整体交易价值与后期追加的工程开发及各项利税成本能够合理量化且预测的前提下，选用剩余法较能反映资产潜在的开发残余价值，故选用该方法进行评估。"
        }
    }
    sub_dict = reasons.get(flag, {})
    return sub_dict.get(category, sub_dict.get("other", ""))


def _get_exclude_reason(flag: str, category: str, label: str, data: dict) -> str:
    # V13.0: 优先从外部文本素材库加载，支持动态 Jinja2 条件与逻辑渲染！
    # 基准地价超期属于高风险政策判断，必须使用后端动态年限与缺项自愈逻辑，避免 YAML 里的
    # 简单占位表达重新写出未核定日期、文号或下划线。
    if flag != "use_benchmark_corr":
        text_lib = _get_text_lib()
        yaml_reason = text_lib.get("valuation_method_exclude_reasons", {}).get(flag)
        if yaml_reason:
            from jinja2 import Template as JinjaTemplate
            try:
                return JinjaTemplate(yaml_reason).render(data).strip()
            except Exception:
                pass

    # 兜底保障（若 YAML 中未配置或加载失败，原样无缝降级）
    land_usage_short = _text(data, "land_usage_price_class") or _text(data, "land_usage_short", "设定用途")
    count_val = _number(data, "comparable_case_count") or "______"
    
    if flag == "use_market_comp":
        return (
            f"不选择市场比较法：根据地产市场调查，估价对象所处区域同一供需圈内近期类似的国有土地出让及转让成交案例极少（可比案例仅有{count_val}个，少于3个），"
            f"且交易目的和宏观条件与设定用途差异显著，无法收集到足够数量且具备高度可比性的案例，难以建立可靠的价格比较基础，故不选用市场比较法。"
        )

    if flag == "use_income_cap":
        return (
            f"不选择收益还原法：估价对象土地纯收益及资本化还原率等关键参数受租赁市场、经营收益剥离和长期收益预期影响较大，"
            f"本次已选用更能直接反映估价对象设定条件和市场价格水平的方法进行测算，故不选用收益还原法。"
        )

    if flag == "use_cost_approx":
        return (
            f"不选择成本逼近法：估价对象设定用途为{land_usage_short}，其价格受区位交通、市场供求、规划利用条件等因素影响较大，"
            f"单纯从土地取得及开发成本角度难以充分反映估价期日的客观合理市场价值，故本次评估不选用成本逼近法。"
        )

    if flag == "use_residual":
        return (
            f"不选择剩余法（增值收益扣减法）：剩余法适用于投资开发潜力显著且可合理预测开发完成价值、后续开发成本及利润的宗地评估。"
            f"本次估价对象的价格测算已采用更适合其资料条件和市场表现的方法，故不选用剩余法进行评估。"
        )

    if flag == "use_benchmark_corr":
        block_reason = _benchmark_corr_block_reason(data)
        if block_reason:
            return f"不选择公示地价修正法（基准地价系数修正法）：{block_reason}"
        status = str(data.get("base_price_expiry_status") or "").strip()
        if status == "expired":
            doc_no = _text(data, "base_price_doc_no") or _text(data, "base_land_price_doc_no")
            doc_name = _text(data, "base_price_doc_name") or _text(data, "base_land_price_doc_name")
            pub_date = _text(data, "base_price_publish_date") or _text(data, "base_land_price_pub_date")
            base_date = _text(data, "base_price_base_date") or _text(data, "base_land_price_value_date")
            authority = _text(data, "base_price_doc_authority") or _text(data, "base_land_price_doc_authority")
            
            county = _text(data, "county_name") or _text(data, "local_county") or "当地"
            v_date = _text(data, "valuation_date")
            v_date_str = v_date or "【请填写估价期日】"
            rule_doc_name = _text(data, "base_price_rule_doc_name", "《关于进一步做好湖南省公示地价体系建设和管理有关工作的通知》")
            rule_doc_no = _text(data, "base_price_rule_doc_no", "湘自资办发[2022]23号")
            update_cycle = _text(data, "base_price_update_cycle_years_text", "三")
            threshold_text = _text(data, "base_price_disable_threshold_years_text", "六")
            threshold_num = _year_threshold_number(threshold_text, 6)
            
            is_missing_all = all(_is_blank_or_prompt(value) for value in (doc_no, doc_name, pub_date, base_date, authority))
            
            if is_missing_all:
                return (
                    f"不选择公示地价修正法（基准地价系数修正法）：{county}城镇基准地价资料尚待补充，"
                    f"其颁布实施时间为{BASE_PRICE_PROMPTS['base_price_publish_date']}，城区基准地价估价基准日为{BASE_PRICE_PROMPTS['base_price_base_date']}，"
                    f"批准文号为{BASE_PRICE_PROMPTS['base_price_doc_no']}，文件名称为{BASE_PRICE_PROMPTS['base_price_doc_name']}，"
                    f"批准机关为{BASE_PRICE_PROMPTS['base_price_doc_authority']}，本次估价期日为{v_date_str}，"
                    f"需补充基准地价文件及估价基准日后判断是否超过{threshold_text}年。"
                    f"在基准地价成果资料尚不完整、无法形成可靠修正依据的情况下，本次不选择公示地价系数修正法。"
                )
                
            time_part = (
                f"距估价期日超过{threshold_text}年，根据{rule_doc_name}（{rule_doc_no}）："
                f"“城镇基准地价每{update_cycle}年应全面更新一次，超过{threshold_text}年未全面更新的，"
                f"不得作为确定出让最低价标准的依据，不得作为宗地评估基准地价系数修正法的依据。”"
                f"因此不选择公示地价系数修正法。"
            )
                
            doc_no_str = doc_no or BASE_PRICE_PROMPTS["base_price_doc_no"]
            doc_name_str = doc_name or BASE_PRICE_PROMPTS["base_price_doc_name"]
            pub_date_str = pub_date or BASE_PRICE_PROMPTS["base_price_publish_date"]
            base_date_str = base_date or BASE_PRICE_PROMPTS["base_price_base_date"]
            authority_str = authority or BASE_PRICE_PROMPTS["base_price_doc_authority"]
            
            return (
                f"不选择公示地价修正法（基准地价系数修正法）：{county}城镇基准地价的颁布实施时间为{pub_date_str}，"
                f"城区基准地价估价基准日为{base_date_str}，批准文号为{doc_no_str}，文件名称为{doc_name_str}，"
                f"批准机关为{authority_str}，本次估价期日为{v_date_str}，{time_part}"
            )
        elif status == "unknown":
            county = _text(data, "county_name") or _text(data, "local_county") or "当地"
            v_date = _text(data, "valuation_date") or "【请填写估价期日】"
            threshold_text = _text(data, "base_price_disable_threshold_years_text", "六")
            return (
                f"不选择公示地价修正法（基准地价系数修正法）：{county}城镇基准地价资料尚待补充，"
                f"其颁布实施时间为{BASE_PRICE_PROMPTS['base_price_publish_date']}，城区基准地价估价基准日为{BASE_PRICE_PROMPTS['base_price_base_date']}，"
                f"批准文号为{BASE_PRICE_PROMPTS['base_price_doc_no']}，文件名称为{BASE_PRICE_PROMPTS['base_price_doc_name']}，"
                f"批准机关为{BASE_PRICE_PROMPTS['base_price_doc_authority']}，本次估价期日为{v_date}，"
                f"需补充基准地价文件及估价基准日后判断是否超过{threshold_text}年。"
                f"在基准地价成果资料尚不完整、无法形成可靠修正依据的情况下，本次不选择公示地价系数修正法。"
            )
        else:
            return (
                f"不选择公示地价修正法：虽然估价对象处于基准地价覆盖范围内，但由于其特定微观规划利用条件、地块形状与个性化利用约束已大幅超出基准地价"
                f"修正因素说明体系的常规覆盖范围；或由于区域近期发生了剧烈的微观市场化价格异动，利用宏观指导地价修正易产生均值化偏差。为了防范政策地价与个别"
                f"属性失真，本次已选用了针对性更强的微观方法，故不选择公示地价系数修正法。"
            )

    return ""


# ==============================================================================
# 核心重构 3：全用途通用条目式“选用/不选/确价”大一统拼装大引擎 (完全对齐三份合并报告原件水准)
# ==============================================================================
def _get_combination_rationales_legacy_unused(data: Dict[str, Any], methods: List[Dict[str, Any]], category: str, label: str) -> Dict[str, str]:
    if not methods:
        return {"adopt_part": "", "exclude_part": "", "reasons": "", "determination": ""}

    active_flags = {item["flag"] for item in methods}
    active_names = [item["name"] for item in methods]
    
    # ==============================================================================
    # 1. 估价方法选用理由（分条条目化，采用中式高雅序号 ①② 还原，对齐原件）
    # ==============================================================================
    adopt_parts = []
    adopt_parts.append("（1）采用方法及选用理由：")
    for idx, item in enumerate(methods, 1):
        flag = item["flag"]
        name = item["name"]
        adopt_wording = _get_adopt_reason(flag, category, label, data)
        prefix = "①" if idx == 1 else "②" if idx == 2 else "③" if idx == 3 else "④" if idx == 4 else "⑤"
        adopt_parts.append(f"{prefix}{name}\\n{adopt_wording}")
        
    adopt_parts.append(f"综上所述，经对上述估价方法适用性、资料完备性及项目特点进行分析，本次评估采用{_join_names(active_names)}作为估价方法。")
    adopt_part = "\\n".join(adopt_parts)
    
    # ==============================================================================
    # 2. 不采用方法及排除说明（智能按需拼装，时效过期硬排除）
    # ==============================================================================
    exclude_parts = []
    if _bool(data, "explain_unselected_methods") and len(active_flags) >= 1:
        unselected_items = [
            ("use_market_comp", "市场比较法"),
            ("use_income_cap", "收益还原法"),
            ("use_cost_approx", "成本逼近法"),
            ("use_residual", "剩余法（增值收益扣减法）"),
            ("use_benchmark_corr", "公示地价修正法")
        ]
        
        idx_ex = 1
        for flag, ch_name in unselected_items:
            if flag not in active_flags:
                exclude_wording = _get_exclude_reason(flag, category, label, data)
                prefix = "①" if idx_ex == 1 else "②" if idx_ex == 2 else "③" if idx_ex == 3 else "④" if idx_ex == 4 else "⑤"
                
                if "不选择公示地价修正法" in exclude_wording:
                    clean_wording = exclude_wording.replace("不选择公示地价修正法（基准地价系数修正法）：", "")
                    exclude_parts.append(f"{prefix}不选择公示地价修正法\\n{clean_wording}")
                else:
                    clean_wording = exclude_wording.replace(f"不选择{ch_name}：", "").replace(f"不选择{ch_name}（增值收益扣减法）：", "")
                    exclude_parts.append(f"{prefix}不选择{ch_name}\\n{clean_wording}")
                idx_ex += 1
    exclude_part = "\\n".join(exclude_parts) if exclude_parts else ""

    # ==============================================================================
    # 3. 地价的确定及加权说明（对齐废除生硬编号及引入句，实现科学原理与单价高保真缝合，100% 对齐原件）
    # ==============================================================================
    det_parts = []
    
    method_def_wordings = {
        "use_cost_approx": (
            "成本逼近法是以开发土地所耗费的各项客观费用之和为主要依据，再加上一定的利润、利息、"
            "应缴纳的税金和土地增值收益来确定土地价格的方法，尤其对新开发土地，可采用成本逼近法进行评估。"
            "考虑到估价对象所在区域有类似征地案例，能够通过征地案例的调查分析，对各项土地取得成本进行量化得出土地价格。"
        ),
        "use_market_comp": (
            "市场比较法是根据替代原理，将待估宗地与具有替代性的，且在估价期日近期市场上交易的类似地产进行比较，"
            "对类似地产成交价格作适当修正，以此得到待估宗地比准价格的一种方法。由于该方法选择的比较案例是市场搜集的"
            "比较客观的真实交易，修正体系是根据估价师多年实践经验编制而成，其测算结果能够真实的反映估价对象的客观合理市场价格。"
        ),
        "use_income_cap": (
            "收益还原法是在估算估价对象在未来每年预期纯收益（正常年纯收益）的基础上，以一定的土地还原率，"
            "将评估对象在未来每年的纯收益折算为估价期日收益总和的一种方法。因此该方法的测算结果能够比较真实的反映待估宗地的客观合理的市场价格。"
        ),
        "use_benchmark_corr": (
            "基准地价系数修正法（公示地价修正法）是利用城镇基准地价和基准地价因素修正系数表等评估成果，"
            "按照替代原则，将估价对象的区位条件以及期日、年期、容积率、开发程度等条件与其所在级别及区域的平均条件进行比较，"
            "对照修正系数表选取相应的修正系数对基准地价进行修正，从而求取估价对象在估价期日地价的方法。该方法具有宏观调控与均值控制的公信力。"
        ),
        "use_residual": (
            "剩余法（增值收益扣减法）是在估算开发完成后不动产正常交易价格的基础上，扣除建筑物建造费用和与建筑物建造、"
            "买卖有关的专业费、利息、利润、税收等费用后，以价格余额来估算土地价格的方法。该方法能够科学预测土地潜在的开发要素价值。"
        )
    }
    
    show_price = _bool(data, "show_price_in_text")
    for item in methods:
        flag = item["flag"]
        name = item["name"]
        price_val = item["price_value"] or "______"
        definition = method_def_wordings.get(flag, "")
        if show_price:
            det_parts.append(f"{definition}{name}测算的测算结果为{price_val}元/平方米。")
        else:
            det_parts.append(f"{definition}")
        
    formula_display = data.get("formula_display_text") or "______"
    logic = data.get("weight_logic_type") or "simple_average"
    dominant = data.get("dominant_method_name") or "______"
    
    if logic == "simple_average":
        det_parts.append(
            f"通过对当地土地市场和土地价格的分析和各方法的可靠性综合分析，根据项目特点，"
            f"综合考虑宗地所在区域的地价水平，确定以{_join_names(active_names)}评估结果的简单算术平均值[{formula_display}]作为最终结果。"
        )
    elif logic == "single_dominance":
        det_parts.append(
            f"通过对当地土地市场和土地价格的分析以及各方法可靠性的综合分析，根据项目特点，"
            f"综合考虑宗地所在区域的地价水平，确定以{dominant}的评估结果作为最终结果." # 这里的标点也一并采用原版
        )
    else:
        rationale = data.get("weight_rationale_text") or "各评估方法的参数来源可靠，测算过程符合估价规程规范"
        det_parts.append(
            f"综合分析，两种方法评估的结果内涵一致，考虑到{rationale}，根据项目特点，"
            f"综合考虑估价对象所在区域的地价水平，确定以{_join_names(active_names)}测算结果的加权平均值（取整）作为最终结果较为合理。"
        )
        
    determination = "\\n".join(det_parts)
    determination = determination.replace("[", "（").replace("]", "）")
    
    reasons = adopt_part + ("\\n\\n（2）未采用方法说明及客观排除理由如下：\\n" + exclude_part if exclude_part else "")
    
    return {
        "adopt_part": adopt_part,
        "exclude_part": exclude_part,
        "reasons": reasons,
        "determination": determination
    }


# 核心重构 3：新增 _get_method_warnings 证据依据预警校验发生器 (双轨解耦，仅用于前端界面展示)
def _get_method_warnings(data: Dict[str, Any]) -> List[Dict[str, str]]:
    _normalize_base_price_fields(data)
    warnings = []

    def explicit_false(key: str) -> bool:
        value = _field_value(data, key, None)
        return value is not None and str(value).strip() != "" and not _bool(data, key)

    if _bool(data, "use_market_comp"):
        count = _number(data, "comparable_case_count")
        if count is not None and count < 3:
            warnings.append({
                "method": "市场比较法",
                "level": "warning",
                "message": "已选择市场比较法，但可比案例数量少于3个，请确认案例来源、可比性或补充方法适用说明。"
            })

    if _bool(data, "use_income_cap") and explicit_false("has_stable_income_data"):
        warnings.append({
            "method": "收益还原法",
            "level": "warning",
            "message": "已选择收益还原法，但尚未确认稳定收益、租金或还原率资料，请核对收益参数来源。"
        })

    if _bool(data, "use_residual") and explicit_false("development_value_measurable"):
        warnings.append({
            "method": "剩余法",
            "level": "warning",
            "message": "已选择剩余法，因开发完成价值或追加开发成本尚未明确，请补充开发测算依据。"
        })

    if _bool(data, "use_cost_approx") and explicit_false("cost_data_reliable"):
        warnings.append({
            "method": "成本逼近法",
            "level": "warning",
            "message": "已选择成本逼近法，因土地取得或开发成本资料可靠性尚未确认，请核对成本依据。"
        })

    if _bool(data, "use_benchmark_corr") and _bool(data, "base_price_is_expired"):
        warnings.append({
            "method": "基准地价系数修正法",
            "level": "danger",
            "message": "已选择基准地价系数修正法，因基准地价可能超过有效更新期限，请核对政策文件并由估价师确认。"
        })
    elif _bool(data, "use_benchmark_corr"):
        block_reason = _benchmark_corr_block_reason(data)
        if block_reason:
            warnings.append({
                "method": "基准地价系数修正法",
                "level": "warning",
                "message": block_reason,
            })

    return warnings


# 核心重构 4：全用途通用条目式“选用/不选/确价”大一统拼装大引擎 (完全对齐三份合并报告原件水准)
def _get_combination_rationales(data: Dict[str, Any], methods: List[Dict[str, Any]], category: str, label: str) -> Dict[str, str]:
    if not methods:
        return {"adopt_part": "", "exclude_part": "", "reasons": "", "determination": ""}

    benchmark_block_reason = _benchmark_corr_block_reason(data)
    if benchmark_block_reason and len(methods) > 1:
        methods = [item for item in methods if item.get("flag") != "use_benchmark_corr"]

    active_flags = {item["flag"] for item in methods}
    active_names = [item["name"] for item in methods]
    
    # ==============================================================================
    # 1. 估价方法选用理由（分条条目化，采用中式高雅序号 ①② 还原，对齐原件）
    # ==============================================================================
    adopt_parts = []
    adopt_parts.append("（1）采用方法及选用理由：")
    for idx, item in enumerate(methods, 1):
        flag = item["flag"]
        name = item["name"]
        adopt_wording = _get_adopt_reason(flag, category, label, data)
        # 用带圈圈的数字如 ①② 标志独立条目标题，百分之百兼容 Word 渲染
        prefix = "①" if idx == 1 else "②" if idx == 2 else "③" if idx == 3 else "④" if idx == 4 else "⑤"
        adopt_parts.append(f"{prefix}{name}\n{adopt_wording}")
        
    adopt_parts.append(f"综上所述，经对上述估价方法适用性、资料完备性及项目特点进行分析，本次评估采用{_join_names(active_names)}作为估价方法。")
    adopt_part = "\n".join(adopt_parts)
    
    # ==============================================================================
    # 2. 不采用方法及排除说明（智能按需拼装，时效过期硬排除）
    # ==============================================================================
    exclude_parts = []
    if _bool(data, "explain_unselected_methods") and len(active_flags) >= 1:
        unselected_items = [
            ("use_market_comp", "市场比较法"),
            ("use_income_cap", "收益还原法"),
            ("use_cost_approx", "成本逼近法"),
            ("use_residual", "剩余法（增值收益扣减法）"),
            ("use_benchmark_corr", "公示地价修正法")
        ]
        
        idx_ex = 1
        for flag, ch_name in unselected_items:
            if flag not in active_flags:
                exclude_wording = _get_exclude_reason(flag, category, label, data)
                prefix = "①" if idx_ex == 1 else "②" if idx_ex == 2 else "③" if idx_ex == 3 else "④" if idx_ex == 4 else "⑤"
                
                # 如果是时效过期硬排除
                if "不选择公示地价修正法" in exclude_wording:
                    clean_wording = exclude_wording.replace("不选择公示地价修正法（基准地价系数修正法）：", "")
                    exclude_parts.append(f"{prefix}不选择公示地价修正法\n{clean_wording}")
                else:
                    clean_wording = exclude_wording.replace(f"不选择{ch_name}：", "").replace(f"不选择{ch_name}（增值收益扣减法）：", "")
                    exclude_parts.append(f"{prefix}不选择{ch_name}\n{clean_wording}")
                idx_ex += 1
    exclude_part = "\n".join(exclude_parts) if exclude_parts else ""

    # ==============================================================================
    # 3. 地价的确定及加权说明（对齐紫金新材料与皮革家属楼原稿，包含各方法测算说明与公式加权）
    # ==============================================================================
    det_parts = []
    det_parts.append(f"根据以上评估过程，本次评估采用了{_join_names(active_names)}进行测算。各估价方法测算情况如下：")
    
    method_def_wordings = {
        "use_cost_approx": (
            "成本逼近法是以开发土地所耗费的各项客观费用之和为主要依据，再加上一定的利润、利息、"
            "应缴纳的税金和土地增值收益来确定土地价格的方法。尤其对新开发土地，可采用成本逼近法进行评估。"
            "考虑到估价对象所在区域有类似征地案例，能够通过征地案例的调查分析，对各项土地取得成本进行量化得出土地价格。"
        ),
        "use_market_comp": (
            "市场比较法是根据替代原理，将待估宗地与具有替代性的，且在估价期日近期市场上交易的类似地产进行比较，"
            "对类似地产成交价格作适当修正，以此得到待估宗地比准价格的一种方法。由于该方法选择的比较案例是市场搜集的"
            "比较客观的真实交易，修正体系是根据估价师多年实践经验编制而成，其测算结果能够真实的反映估价对象的客观合理市场价格。"
        ),
        "use_income_cap": (
            "收益还原法是在估算估价对象在未来每年预期纯收益（正常年纯收益）的基础上，以一定的土地还原率，"
            "将评估对象在未来每年的纯收益折算为估价期日收益总和的一种方法。因此该方法的测算结果能够比较真实的反映待估宗地的客观合理的市场价格。"
        ),
        "use_benchmark_corr": (
            "基准地价系数修正法（公示地价修正法）是利用城镇基准地价和基准地价因素修正系数表等评估成果，"
            "按照替代原则，将估价对象的区位条件以及期日、年期、容积率、开发程度等条件与其所在级别及区域的平均条件进行比较，"
            "对照修正系数表选取相应的修正系数对基准地价进行修正，从而求取估价对象在估价期日地价的方法。该方法具有宏观调控与均值控制的公信力。"
        ),
        "use_residual": (
            "剩余法（增值收益扣减法）是在估算开发完成后不动产正常交易价格的基础上，扣除建筑物建造费用和与建筑物建造、"
            "买卖有关的专业费、利息、利润、税收等费用后，以价格余额来估算土地价格的方法。该方法能够科学预测土地潜在的开发要素价值。"
        )
    }
    
    show_price = _bool(data, "show_price_in_text")
    for item in methods:
        flag = item["flag"]
        name = item["name"]
        price_val = item["price_value"] or "______"
        definition = method_def_wordings.get(flag, "")
        if show_price:
            det_parts.append(f"{definition}{name}测算的测算结果为{price_val}元/平方米。")
        else:
            det_parts.append(definition)
        
    formula_display = data.get("formula_display_text") or "______"
    logic = _weight_logic(data)
    dominant = data.get("dominant_method_name") or "______"
    
    if logic == "weighted_average":
        det_parts.append(
            f"综上所述，对当地土地市场和土地价格的分析和各方法可靠性的综合分析，根据项目特点，"
            f"综合考虑宗地所在区域的地价水平，确定以{_join_names(active_names)}评估结果的加权算术平均值[{formula_display}]作为本次评估的最终结果。"
        )
    elif logic == "single_dominance":
        det_parts.append(
            f"综上所述，通过对当地土地市场和土地价格的分析以及各方法可靠性的综合分析，根据项目特点，"
            f"综合考虑宗地所在区域的地价水平，确定以{dominant}的评估结果作为本次评估的最终结果。"
        )
    elif logic == "median":
        det_parts.append(
            f"综上所述，通过对当地土地市场和土地价格的分析和各方法可靠性的综合分析，根据项目特点，"
            f"综合考虑宗地所在区域的地价水平，确定以{_join_names(active_names)}评估结果的中位数作为本次评估的最终结果。"
        )
    elif logic == "mode":
        det_parts.append(
            f"综上所述，通过对当地土地市场和土地价格的分析和各方法可靠性的综合分析，根据项目特点，"
            f"综合考虑宗地所在区域的地价水平，确定以{_join_names(active_names)}评估结果的众数作为本次评估的最终结果。"
        )
    else:
        rationale = data.get("weight_rationale_text") or "各评估方法的参数来源可靠，测算过程符合估价规程规范"
        det_parts.append(
            f"综合分析，两种方法评估的结果内涵一致，考虑到{rationale}，根据项目特点，"
            f"综合考虑估价对象所在区域的地价水平，确定以{_join_names(active_names)}测算结果的加权平均值（取整）作为最终结果较为合理。"
        )
        
    determination = "\n".join(det_parts)
    determination = determination.replace("[", "（").replace("]", "）")
    
    reasons = adopt_part + ("\n\n（2）未采用方法说明及客观排除理由如下：\n" + exclude_part if exclude_part else "")
    
    return {
        "adopt_part": adopt_part,
        "exclude_part": exclude_part,
        "reasons": reasons,
        "determination": determination
    }


def _infrastructure_detail(data: Dict[str, Any], category: str, label: str) -> str:
    scheme = {}
    try:
        import os
        import yaml

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with open(os.path.join(base_dir, "text_library.yaml"), "r", encoding="utf-8") as f:
            scheme = (yaml.safe_load(f) or {}).get("infrastructure_detail_scheme", {}) or {}
    except Exception:
        scheme = {}

    fallback_scheme = {
        "five_通_residential": "基础设施条件：估价对象土地实际开发程度为宗地红线外“五通”（即通路、通电、供水、排水、通讯），红线内场地平整无建筑物，详见下表。",
        "five_通_industrial": "基础设施条件：估价对象土地实际开发程度为宗地红线外“五通”（即通路、通电、通讯、供水、排水），红线内场地平整无建筑物，详见下表。",
        "five_通_commercial": "基础设施条件：估价对象土地实际开发程度为宗地红线外“五通”（即通路、通电、供水、排水、通讯），红线内开发状态以委托方提供资料及现场勘查结果为准，详见下表。",
        "five_通_public": "基础设施条件：估价对象土地实际开发程度为宗地红线外“五通”（即通路、通电、供水、排水、通讯），红线内场地达到现状公用设施建设及社会公益属性要求，详见下表。",
        "three_通": "基础设施条件：估价对象土地实际开发程度为宗地红线外“三通”（即通路、通电、给水），红线内场地平整。",
    }
    merged_scheme = {**fallback_scheme, **scheme}

    infra_type = _text(data, "infrastructure_type")
    scheme_text = str(merged_scheme.get(infra_type) or "").strip()
    if scheme_text:
        if label and label not in scheme_text:
            return f"设定土地用途为{label}。{scheme_text}"
        return scheme_text

    development = _text(data, "land_development_set") or _text(data, "land_development_actual") or "【请填写土地开发程度】"
    if "七通" in development:
        detail = "七通（即通路、通电、供水、排水、通讯、通气、通热）"
    elif "三通" in development:
        detail = "三通（即通路、通电、供水）"
    elif "五通" in development:
        detail = "五通（即通路、通电、供水、排水、通讯）"
    else:
        detail = development

    public_note = "，红线内开发状态结合公共服务设施建设及公益属性要求确定" if category == "public" else ""
    return f"基础设施条件：估价对象设定土地用途为{label}，土地实际开发程度为{development}，其中宗地红线外为{detail}{public_note}，详见下表。"


def _formula_and_determination(
    data: Dict[str, Any],
    methods: List[Dict[str, Any]],
    weights: Dict[str, Decimal],
    formula: str,
    warnings: List[str],
) -> tuple[str, str]:
    if not methods:
        return "", ""

    names = _join_names([item["name"] for item in methods])
    logic = _weight_logic(data)
    unit_price = _final_unit_price(methods, weights, logic, data)
    show_price = _bool(data, "show_price_in_text")
    price_parts = []
    for item in methods:
        if item["price_decimal"] is not None:
            price_parts.append(f"{item['name']}单价为{_fmt_decimal(item['price_decimal'])}元/平方米")
    price_sentence = f"其中，{'，'.join(price_parts)}。" if show_price and price_parts else ""

    area = _decimal(_text(data, "land_area"))
    total_text = ""
    if unit_price is not None and area is not None:
        total = unit_price * area / Decimal("10000")
        total_text = f"按土地面积{_fmt_decimal(area, '0.01')}平方米测算，对应土地总价约为{_fmt_decimal(total, '0.01')}万元。"

    formula_lines = [f"本次评估确价公式设定为：{formula}。"]
    if unit_price is not None:
        formula_lines.append(f"按上述公式测算，综合地面地价约为{_fmt_decimal(unit_price)}元/平方米。")
    if total_text:
        formula_lines.append(total_text)

    rationale = _text(data, "weight_rationale_text")
    if not rationale:
        if logic == "single_dominance":
            dominant = _text(data, "dominant_method_name", methods[0]["name"])
            rationale = f"结合估价对象资料条件和方法适用性，本次以{dominant}测算结果作为主要依据。"
        elif logic == "median":
            rationale = f"本次对{names}测算结果进行综合分析，采用中位数确定最终结果。"
        elif logic == "mode":
            rationale = f"本次对{names}测算结果进行综合分析，采用唯一众数确定最终结果。"
        else:
            rationale = f"本次对{names}测算结果进行综合分析，各方法资料基础和适用程度相对均衡，采用简单算术平均值（{formula}）确定最终结果。"

    rationale = rationale.replace("[", "（").replace("]", "）")

    determination_lines = []
    determination_lines.append(f"根据以上评估过程，本次综合采用{names}的测算结果，按“{formula}”确定最终地面地价。")
    
    parts_middle = []
    if price_sentence:
        parts_middle.append(price_sentence)
    parts_middle.append(rationale)
    if unit_price is not None:
        parts_middle.append(f"综合地面地价约为{_fmt_decimal(unit_price)}元/平方米。")
    if total_text:
        parts_middle.append(total_text)
        
    if parts_middle:
        determination_lines.append("".join(parts_middle))
        
    if warnings:
        determination_lines.append(f"复核提示：{'；'.join(warnings)}")

    return "".join(formula_lines), "\n".join(determination_lines)


def _four_digit_upper(num: int) -> str:
    digits = "零壹贰叁肆伍陆柒捌玖"
    units = ["仟", "佰", "拾", ""]
    values = [num // 1000, (num // 100) % 10, (num // 10) % 10, num % 10]
    parts: List[str] = []
    pending_zero = False
    for digit, unit in zip(values, units):
        if digit == 0:
            if parts:
                pending_zero = True
            continue
        if pending_zero:
            parts.append("零")
            pending_zero = False
        parts.append(f"{digits[digit]}{unit}")
    return "".join(parts)


def _rmb_upper_from_yuan(amount_yuan: Decimal | None) -> str:
    if amount_yuan is None:
        return "【请填写土地总价大写】"
    yuan = int(amount_yuan.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if yuan == 0:
        return "零元整"

    group_units = ["", "万", "亿", "兆"]
    groups: List[int] = []
    while yuan:
        groups.append(yuan % 10000)
        yuan //= 10000

    parts: List[str] = []
    zero_pending = False
    for reverse_idx, group in enumerate(reversed(groups)):
        group_idx = len(groups) - 1 - reverse_idx
        if group == 0:
            if parts:
                zero_pending = True
            continue
        if parts and (zero_pending or group < 1000):
            parts.append("零")
        parts.append(f"{_four_digit_upper(group)}{group_units[group_idx]}")
        zero_pending = False
    return "".join(parts) + "元整"


def _valuation_result_statement(
    data: Dict[str, Any],
    methods: List[Dict[str, Any]],
    weights: Dict[str, Decimal],
) -> str:
    client = _text(data, "client_name", "委托方")
    location = _text(data, "land_location_full") or _text(data, "land_location", "估价对象所在地")
    parcel_count = _text(data, "parcel_count", "一宗")
    land_area_text = _text(data, "land_area", "【请填写土地面积】")
    valuation_date = _text(data, "valuation_date", "【请填写估价期日】")
    land_usage = _text(data, "land_usage_price_class") or _text(data, "land_usage_short") or _text(data, "land_usage", "【请填写土地用途】")
    land_use_term = _text(data, "land_use_term", "【请填写土地使用年期】")
    plot_ratio = _text(data, "plot_ratio_display") or _text(data, "plot_ratio", "【请填写容积率】")
    set_ratio_raw = _text(data, "set_plot_ratio_display") or _text(data, "set_plot_ratio")
    set_plot_ratio_val = set_ratio_raw if set_ratio_raw else plot_ratio
    if not set_plot_ratio_val or set_plot_ratio_val == "______" or "【请填写" in set_plot_ratio_val:
        set_plot_ratio_val = plot_ratio
    development = _text(data, "land_development_set") or _text(data, "land_development_actual", "【请填写土地开发程度】")
    condition = _text(data, "valuation_condition_type", "设定")
    right_type = _text(data, "right_type", "")
    right_phrase = f"{right_type}土地使用权" if right_type else "土地使用权"

    unit_price = _decimal(data.get("final_unit_price"))
    if unit_price is None:
        unit_price = _final_unit_price(methods, weights, _weight_logic(data), data)
    unit_price_rounded = unit_price.quantize(Decimal("1"), rounding=ROUND_HALF_UP) if unit_price is not None else None
    unit_price_text = _fmt_decimal(unit_price_rounded, "1") if unit_price_rounded is not None else "【请填写土地单价】"

    area_decimal = _decimal(land_area_text)
    total_wan = _decimal(data.get("final_total_price"))
    if total_wan is None and unit_price_rounded is not None and area_decimal is not None:
        total_wan = (unit_price_rounded * area_decimal / Decimal("10000")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_wan_text = _fmt_decimal(total_wan, "0.01") if total_wan is not None else "【请填写土地总价】"

    total_yuan = (total_wan * Decimal("10000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) if total_wan is not None else None
    total_upper = _text(data, "final_total_price_upper")
    if not total_upper:
        total_upper = _rmb_upper_from_yuan(total_yuan)

    if unit_price_text and not _text(data, "final_unit_price"):
        data["final_unit_price"] = unit_price_text
    if total_wan_text and not _text(data, "final_total_price"):
        data["final_total_price"] = total_wan_text
    if total_upper and not _text(data, "final_total_price_upper"):
        data["final_total_price_upper"] = total_upper

    lines = [
        (
            f"{client}委托评估的，位于{location}的{parcel_count}国有土地，土地面积{land_area_text}平方米，"
            f"于估价期日{valuation_date}，在评估设定土地用途为{land_usage}，设定土地使用年期为{land_use_term}，"
            f"设定容积率为{set_plot_ratio_val}，设定土地开发程度为{development}，{condition}利用条件下的{right_phrase}价格如下（币种：人民币）："
        ),
        f"宗地数量：共{parcel_count}",
        f"估价对象土地总面积：{land_area_text}平方米",
        f"估价对象土地单价：{unit_price_text}元/平方米",
        f"估价对象土地总价：{total_wan_text}万元",
        f"大写：人民币{total_upper}；",
        "详见《土地估价结果一览表》。",
    ]
    return "\n".join(lines)


def _should_assign(data: Dict[str, Any], key: str, overwrite: bool) -> bool:
    if overwrite:
        return True
    current = _field_value(data, key, "")
    text = str(current or "").strip()
    return not text or text == "______" or "______" in text or "【请填写" in text


def _assign_generated(data: Dict[str, Any], key: str, value: str, overwrite: bool) -> None:
    if value and _should_assign(data, key, overwrite):
        data[key] = value


def _compile_for_key(data: Dict[str, Any], key: str) -> None:
    text = str(_field_value(data, key, "") or "")
    excluded = set(VALUATION_TEXT_KEYS)
    excluded.update(f"{item}_segments" for item in VALUATION_TEXT_KEYS)
    excluded.add("valuation_warnings")
    segment_data = {item_key: item_value for item_key, item_value in data.items() if item_key not in excluded}
    segments = compile_desc_segments(text, segment_data)
    for prompt, field_name in PROMPT_FIELD_MAP.items():
        segments = _mark_literal_segments(segments, prompt, field_name, override_existing=True)
    for method_name, field_name in METHOD_NAME_FIELDS.items():
        segments = _mark_literal_segments(segments, method_name, field_name)
    data[f"{key}_segments"] = segments


def _mark_literal_segments(
    segments: List[Dict[str, Any]],
    literal: str,
    field_name: str,
    *,
    override_existing: bool = False,
) -> List[Dict[str, Any]]:
    if not literal:
        return segments
    candidates = [literal]
    if literal.endswith("用地") and len(literal) > 2:
        candidates.append(literal[:-2])  # 剥去“用地” ➔ “住宅”
    elif literal.endswith("用途") and len(literal) > 2:
        candidates.append(literal[:-2])
        
    marked: List[Dict[str, Any]] = []
    for seg in segments:
        if ("field" in seg or "fields" in seg) and not override_existing:
            marked.append(seg)
            continue
        seg_text = seg.get("text", "")
        
        matched = False
        for cand in candidates:
            if cand and cand in seg_text:
                parts = seg_text.split(cand)
                for idx, part in enumerate(parts):
                    if part:
                        marked.append({"text": part})
                    if idx < len(parts) - 1:
                        marked.append({"text": cand, "field": field_name})
                matched = True
                break
        if not matched:
            marked.append(seg)
    return marked


def _render_yaml_template(template: str, data: Dict[str, Any], formula_text: str = "") -> str:
    if not template:
        return ""
    _normalize_base_price_fields(data)
    local_county = _text(data, "county_name") or _text(data, "local_county", "当地")
    local_gov = _text(data, "local_gov") or f"{local_county}人民政府"
    land_location = _text(data, "land_location", "估价对象坐落位置")
    valuation_date = _text(data, "valuation_date", "2026年04月23日")
    land_usage_short = _text(data, "land_usage_price_class") or _text(data, "land_usage_short", "设定土地用途")
    limit = _text(data, "base_price_update_cycle_years_text", "三")
    local_city = _local_city(data)
    
    text = template
    
    # 智能全变量正规防弹替换：自适应将所有的 {{ 变量名 }} 替换为实际业务数据，打通核心单价的高精注入与热区标记
    def repl(match):
        var_name = match.group(1).strip()
        local_vars = {
            "land_location": land_location,
            "local_county": local_county,
            "local_gov": local_gov,
            "local_city": local_city,
            "valuation_date": valuation_date,
            "land_usage_short": land_usage_short,
            "limit": limit,
            "formula": formula_text,
            "formula_display_text": formula_text,
            "base_price_doc_no": _text(data, "base_price_doc_no"),
            "base_price_doc_name": _text(data, "base_price_doc_name"),
            "base_price_publish_date": _text(data, "base_price_publish_date"),
            "base_price_base_date": _text(data, "base_price_base_date"),
            "base_price_doc_authority": _text(data, "base_price_doc_authority"),
            "base_price_rule_doc_name": _text(data, "base_price_rule_doc_name"),
            "base_price_rule_doc_no": _text(data, "base_price_rule_doc_no"),
            "base_price_update_cycle_years_text": _text(data, "base_price_update_cycle_years_text"),
            "base_price_disable_threshold_years_text": _text(data, "base_price_disable_threshold_years_text"),
            "base_price_elapsed_years_text": _text(data, "base_price_elapsed_years_text"),
            "base_price_elapsed_clause": _base_price_elapsed_clause(data),
            "expired_years_text": _text(data, "expired_years_text"),
            "valuation_basis_docs_rendered": _text(data, "valuation_basis_docs_rendered"),
        }
        if var_name in local_vars:
            return local_vars[var_name]
        return str(data.get(var_name) if data.get(var_name) is not None else match.group(0))
        
    text = re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, text)
    
    if formula_text:
        text = text.replace("[成本逼近法×50%+市场比较法×50%]", f"[{formula_text}]")
        text = text.replace("“成本逼近法×50%+市场比较法×50%”", f"“{formula_text}”")
        text = text.replace("“{{ formula }}”", f"“{formula_text}”")
        text = text.replace("“{{ formula_display_text }}”", f"“{formula_text}”")
        text = re.sub(r"“[^”]+”", f"“{formula_text}”", text) if "“" in text and "公式" in text else text
    return text


def derive_valuation_descriptions(data: Dict[str, Any], *, overwrite: bool = False, preserve_dirty: bool = True) -> Dict[str, Any]:
    _sync_legacy_land_usage_fields(data)
    _sync_acquisition_fields(data)
    _derive_plot_ratio_display(data)
    _normalize_base_price_fields(data)
    _force_default_text_options(data)
    _preheal_prompt_fields(data)

    # V13.0: 效仿第三部分，第四部分测算依据文件只解析用户/前端传入内容。
    # 测试期默认值放在前端显式常量中，后端不再隐式写入地区政策，避免异地项目被硬编码污染。
    docs_list = _parse_basis_docs(data.get("valuation_basis_docs_list") or "")
    if docs_list:
        data["valuation_basis_docs_rendered"] = "、".join(docs_list)
        data["valuation_basis_docs_list"] = "\n".join(docs_list)
    else:
        data["valuation_basis_docs_list"] = ""
        data["valuation_basis_docs_rendered"] = "【请填写土地评估计算过程依据】"

    # 智能安全加载外部 YAML 长话术库
    import os
    import yaml
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    text_library_path = os.path.join(BASE_DIR, "text_library.yaml")
    text_lib = {}
    try:
        with open(text_library_path, 'r', encoding='utf-8') as f:
            text_lib = yaml.safe_load(f)
    except Exception:
        pass

    # V13.0: 动态提取外部 YAML 模板，进行成本逼近法计算过程前置段落的二级 Jinja2 自适应高保真渲染
    intro_template = text_lib.get("cost_approx_process_intro", "") if text_lib else ""
    cost_process_intro = ""
    if _bool(data, "use_cost_approx") and intro_template:
        from jinja2 import Template as JinjaTemplate
        # 预先将 data 合并入渲染上下文，确保地方区划和测算依据等变量可以渲染
        render_ctx = {}
        render_ctx.update(data)
        # 用基础占位符兜底，唤醒前端高亮跳转定位
        render_ctx["land_location"] = _text(data, "land_location", "估价对象坐落位置")
        render_ctx["local_city"] = _local_city(data)
        render_ctx["valuation_date"] = _text(data, "valuation_date", "【请填写估价期日】")
        render_ctx["valuation_basis_docs_rendered"] = data.get("valuation_basis_docs_rendered") or "【请填写土地评估计算过程依据】"
        
        try:
            cost_process_intro = JinjaTemplate(intro_template).render(render_ctx).strip()
        except Exception:
            pass
        analysis = data.get("cost_approx_analysis") or {}
        basis_intro = (
            (analysis.get("effective_narratives") or analysis.get("generated_narratives") or {}).get("cost_approx_basis_intro")
            or ""
        ).strip()
        if basis_intro:
            cost_process_intro = basis_intro.split("\n\n", 1)[0].strip() or cost_process_intro

    # 智能推导兜底选项，确保在独立后端调用（如测试用例或外部API）没有前端 watch 时，方案选项依然高精度匹配土地用途
    usage = str(data.get("land_usage") or data.get("land_usage_short") or "")
    is_industrial = any(word in usage for word in ("工业", "工矿", "仓储"))
    is_commercial = any(word in usage for word in ("商业", "商服", "商务"))
    is_residential = any(word in usage for word in ("住宅", "居住"))
    is_public = any(word in usage for word in ("公共", "公用", "科教", "机关", "教育", "医疗", "体育", "交通", "绿地", "开敞"))

    if not data.get("land_level_type"):
        if is_industrial:
            data["land_level_type"] = "base_land_price_expired"
        elif is_commercial:
            data["land_level_type"] = "commercial_level"
        elif is_public:
            data["land_level_type"] = "public_level"
        elif is_residential:
            data["land_level_type"] = "residential_level_3"

    if not data.get("method_combination_type"):
        if is_industrial:
            data["method_combination_type"] = "industrial_cost_and_market_average"
        elif is_commercial:
            data["method_combination_type"] = "commercial_market_income"
        elif is_public:
            data["method_combination_type"] = "public_service_cost_average"
        elif is_residential:
            data["method_combination_type"] = "residential_residual_only"

    if not data.get("infrastructure_type"):
        if is_industrial:
            data["infrastructure_type"] = "five_通_industrial"
        elif is_commercial:
            data["infrastructure_type"] = "five_通_commercial"
        elif is_public:
            data["infrastructure_type"] = "five_通_public"
        elif is_residential:
            data["infrastructure_type"] = "five_通_residential"

    category = infer_asset_use_category(data)
    label = asset_use_label(data, category)
    data["asset_use_category"] = category

    methods = _selected_methods(data)
    method_names = [item["name"] for item in methods]
    data["adopted_methods_summary"] = _join_names(method_names) if method_names else "______"

    weights = _weights_for_methods(data, methods)
    logic = _weight_logic(data)
    generated_formula = _formula_text(methods, weights, logic)
    formula_for_warning = _text(data, "formula_display_text") if not overwrite else generated_formula
    warnings = _weight_warnings(data, formula_for_warning or generated_formula, methods)
    warnings.extend(_base_price_policy_warnings(data))

    data["formula_display_text"] = generated_formula
    formula_text = generated_formula

    # 1. 估价方法选用理由 (valuation_method_reasons) 与 4. 价格加权确定理由 (final_price_determination)
    rationales = _get_combination_rationales(data, methods, category, label)
    
    # 2. 评估方法适用性按已选方法和资料条件自动生成，不再依赖前端方案下拉。
    val_applicability = _method_applicability(data, methods, category, label)

    # 组装 valuation_method_reasons：只承载采用/不采用理由。
    # 适用性分析由 valuation_method_applicability 单独承载，避免模板中两个占位符连续使用时重复输出同一段。
    adopt_part_rendered = _render_yaml_template(rationales["adopt_part"], data, formula_text)
    reason_parts = [adopt_part_rendered.strip()]
    
    exclude_part_raw = rationales["exclude_part"]
    if exclude_part_raw:
        exclude_part_rendered = _render_yaml_template(exclude_part_raw, data, formula_text)
        reason_parts.append("（2）未采用方法说明及客观排除理由如下：\n" + exclude_part_rendered.strip())
    combined_reasons = "\n\n".join(part for part in reason_parts if part)

    # 3. 基础设施开发程度由第二部分实际/设定开发程度派生。
    infra_detail = _infrastructure_detail(data, category, label)

    # 4. 组装合并后的 final_price_determination (确价理由 + 基础设施开发程度)
    final_price_determination_raw = _render_yaml_template(rationales["determination"], data, formula_text)
    combined_price_det = final_price_determination_raw.strip() + "\n\n" + infra_detail.strip()
    result_statement = _valuation_result_statement(data, methods, weights)

    generated = {
        "valuation_method_reasons": combined_reasons,
        "valuation_method_applicability": val_applicability,
        "infrastructure_detail": infra_detail,
        "formula_display_text": generated_formula,
        "final_price_determination": combined_price_det,
        "valuation_result_statement": result_statement,
        "cost_approx_land_class_intro": _cost_approx_land_class_intro(data) if _bool(data, "use_cost_approx") else "",
        "cost_approx_process_intro": cost_process_intro,
        "cost_approx_method_intro": COST_APPROX_INTRO if _bool(data, "use_cost_approx") else "",
        "market_comp_method_intro": MARKET_COMP_INTRO if _bool(data, "use_market_comp") else "",
        "income_cap_method_intro": INCOME_CAP_INTRO if _bool(data, "use_income_cap") else "",
        "benchmark_corr_method_intro": BENCHMARK_CORR_INTRO if _bool(data, "use_benchmark_corr") else "",
        "residual_method_intro": RESIDUAL_INTRO if _bool(data, "use_residual") else "",
    }

    for key, value in generated.items():
        if key in {
            "cost_approx_land_class_intro",
            "cost_approx_process_intro",
            "cost_approx_method_intro",
            "market_comp_method_intro",
            "income_cap_method_intro",
            "benchmark_corr_method_intro",
            "residual_method_intro",
        } and not value:
            data[key] = ""
        else:
            _assign_generated(data, key, value, overwrite)

    for key in VALUATION_TEXT_KEYS:
        _compile_for_key(data, key)

    data["valuation_warnings"] = warnings
    data["method_warnings"] = _get_method_warnings(data)
    return data
