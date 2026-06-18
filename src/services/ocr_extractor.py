# -*- coding: utf-8 -*-
import re
from typing import Dict, Any
from src.schemas.attachments import PlanningConditionAttachment, clean_float_string
from src.services.land_usage import normalize_land_usage_fields


def _first_match(patterns, text: str):
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def _put_clean_float(target: Dict[str, Any], key: str, value: str | None):
    if not value:
        return
    try:
        target[key] = clean_float_string(value)
    except Exception:
        return


def _normalize_book_title(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip(" 　：:，,。；;")
    if not text:
        return None
    return text if text.startswith("《") and text.endswith("》") else f"《{text.strip('《》')}》"


def _normalize_doc_no(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip(" 　：:，,。；;")
    text = re.sub(r"^(?:为|是|编号为)", "", text)
    return text or None


def _normalize_plain_value(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip(" 　：:，,。；;")
    text = re.sub(r"^(?:为|是)", "", text)
    return text or None


def _extract_base_price_report_fields(clean_text: str, compact_text: str) -> Dict[str, Any]:
    extracted: Dict[str, Any] = {}

    doc_no = _first_match([
        r"(?:批准文号|发布文号|文号|发文字号)(?::|：)?([^\n，。；;]*?[〔\[]\d{4}[〕\]][0-9一二三四五六七八九十]+号)",
        r"([\u4e00-\u9fa5]{1,8}(?:政函|政发|政办发|自然资发|自资发|国土资发|土资发|资发)[〔\[]\d{4}[〕\]][0-9一二三四五六七八九十]+号)",
    ], compact_text)
    doc_name = _first_match([
        r"(?:文件名称|成果名称|报告名称)(?::|：)?(《[^》]*(?:基准地价|公示地价)[^》]*》)",
        r"(《[^》]*(?:基准地价|公示地价)[^》]*》)",
        r"(?:文件名称|成果名称|报告名称)(?::|：)?([^\n。；;]*(?:基准地价|公示地价)[^\n。；;]*)",
    ], clean_text)
    authority = _first_match([
        r"(?:批准机关|发布机关|批准单位|发布单位)(?::|：)?([\u4e00-\u9fa5]{3,30}(?:人民政府|自然资源局|自然资源和规划局|国土资源局|局|政府))",
        r"由([\u4e00-\u9fa5]{3,30}(?:人民政府|自然资源局|自然资源和规划局|国土资源局))批准",
    ], compact_text)
    publish_date = _first_match([
        r"(?:颁布实施时间|公布实施时间|实施时间|颁布日期|发布日期|公布日期)(?:为|:|：)?([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)",
        r"自([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)起(?:公布执行|实施|施行)",
        r"([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)(?:起)?(?:公布执行|实施|施行)",
    ], compact_text)
    base_date = _first_match([
        r"(?:估价基准日|基准地价估价基准日|基准日)(?:为|:|：)?([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)",
    ], compact_text)

    rule_doc_no = _first_match([
        r"(湘自资办发[〔\[]2022[〕\]]23号)",
        r"([\u4e00-\u9fa5]{1,8}自资办发[〔\[]\d{4}[〕\]]\d+号)",
    ], compact_text)
    rule_doc_name = _first_match([
        r"(《关于进一步做好湖南省公示地价体系建设和管理有关工作的通知》)",
        r"(《[^》]*公示地价体系建设和管理[^》]*》)",
    ], compact_text)

    normalized = {
        "base_price_doc_no": _normalize_doc_no(doc_no),
        "base_price_doc_name": _normalize_book_title(doc_name.strip("《》") if doc_name else None),
        "base_price_publish_date": publish_date,
        "base_price_base_date": base_date,
        "base_price_doc_authority": _normalize_plain_value(authority),
        "base_price_rule_doc_name": _normalize_book_title(rule_doc_name.strip("《》") if rule_doc_name else None),
        "base_price_rule_doc_no": _normalize_doc_no(rule_doc_no),
    }
    for key, value in normalized.items():
        if value:
            extracted[key] = value

    return extracted

def extract_metrics_from_text(raw_text: str, attachment_type: str) -> Dict[str, Any]:
    """
    极具实战防御力的本地离线启发式规则匹配引擎：
    利用一系列精心设计的中文正则表达式，在 OCR 提取出的非结构化纯文本中，
    自动、毫秒级且 100% 离线安全地检索、剥离并归纳出证书的核心指标。
    """
    # 仅清洗空格和回车符，保留换行符 \n 作为排版级逻辑截断，确保正则匹配的高保真度
    clean_text = raw_text.replace(" ", "").replace("\r", "")
    compact_text = clean_text.replace("\n", "")
    
    extracted_data = {}
    
    if attachment_type == "property_cert":
        # 1. 提取权利人/使用者
        land_user = _first_match([
            r"房屋所有权人\n([\u4e00-\u9fa5]{2,10})",
            r"土地权利人(?::|：)?([\u4e00-\u9fa5]{2,10})",
            r"(?:权利人|土地使用者|使用者|使用权人)(?::|：)?([\u4e00-\u9fa5]{2,10})",
            r"兹有([\u4e00-\u9fa5]{2,10})",
        ], clean_text)
        if land_user and ("享有" in land_user or "房屋所有权" in land_user):
            land_user = None
        
        # 2. 提取坐落位置 (防弹级行尾贪婪匹配，防止楼层与房号截断，将最长分支放前防泄露)
        land_location = _first_match([
            r"房屋坐落\n([^\n]+)",
            r"(?:房屋坐落位置|坐落位置|坐落|位置|地址)(?::|：)?([^\n]+)",
        ], clean_text) or _first_match([
            r"购得位于([\s\S]+?)(?:住房一套|住宅一套|房屋一套|。|；|;)",
            r"位于([\s\S]+?)(?:住房一套|住宅一套|房屋一套|。|；|;)",
        ], compact_text)
        
        # 3. 提取分摊使用权面积 (支持前置“约”口语前缀与各类物理单位污染)
        land_area = _first_match([
            r"(?:分摊土地使用权面积|分摊土地面积|使用权面积|土地面积|分摊面积)(?::|：)?(?:约)?([0-9\.]+)(?:平方米|㎡|sqm)?",
        ], clean_text)
        
        # 4. 提取权利性质/使用权类型
        right_type = _first_match([
            r"(?:权利性质|使用权类型|土地使用权类型|类型)(?:为|:|：)?(国有划拨|国有出让|出让|划拨|集体土地|国有储备)",
        ], compact_text)
        
        # 5. 提取设定用途
        land_usage = _first_match([
            r"规划用途\n([^\n]+)",
            r"(?:用途|设定用途|土地用途)(?::|：)?([\u4e00-\u9fa5]{2,16}(?:用地|住宅|工业|商业服务业|商服|仓储|住宅用地|工业用地))",
        ], clean_text)

        house_cert_no = _first_match([
            r"(?:房产证号|房屋所有权证号|房屋所有权证编号)(?:为|:|：)?([^，。；;]+?号)",
            r"(?:房产证号|房屋所有权证号|房屋所有权证编号)(?:为|:|：)?([^，。\n；;]+)",
            r"字第([0-9]+号)",
        ], compact_text)
        if house_cert_no and re.fullmatch(r"[0-9]+号", house_cert_no) and "道房权证" in clean_text:
            house_cert_no = f"道房权证字第{house_cert_no}"
        buy_year = _first_match([r"于([0-9]{4}年?)购得"], compact_text)
        registered_house_area = _first_match([
            r"建筑面积\(平方米\)\n([0-9\.]+)",
            r"(?:房屋登记面积|登记建筑面积|建筑面积)(?::|：)?(?:约)?([0-9\.]+)(?:平方米|㎡|sqm)?",
        ], clean_text)

        if land_user:
            extracted_data["land_user"] = land_user
        if land_location:
            extracted_data["land_location"] = land_location
            extracted_data["room_detail_location"] = land_location
            extracted_data["buy_location_desc"] = land_location
        _put_clean_float(extracted_data, "land_area", land_area)
        if right_type:
            extracted_data["right_type"] = right_type
            extracted_data["registered_right_type"] = right_type
        if land_usage:
            extracted_data["land_usage"] = land_usage
            normalize_land_usage_fields(extracted_data)
        if house_cert_no:
            extracted_data["house_cert_no"] = house_cert_no
        if buy_year:
            extracted_data["buy_year"] = buy_year
        if registered_house_area:
            extracted_data["registered_house_area"] = registered_house_area
        if "土地权属及性质证明" in clean_text[:80]:
            extracted_data["proof_doc_name"] = "土地权属及性质证明"
        
    elif attachment_type == "planning_condition":
        # 1. 提取批准机关
        authority_match = re.search(r"(?:批准机关|出具机关|发证机关|批准部门)(?::|：)?([\u4e00-\u9fa5]{3,15}(?:局|政府|委员会))", clean_text)
        planning_approval_authority = authority_match.group(1) if authority_match else "______"
        
        # 2. 提取规划容积率 (防弹级指标提取，支持“控制”等后缀与区间匹配)
        ratio_match = re.search(r"(?:容积率|设定的容积率)(?:[\u4e00-\u9fa5]{0,5})?(?::|：)?(?:[0-9\.]+-)?([0-9\.]+)", clean_text)
        plot_ratio = ratio_match.group(1) if ratio_match else "1.0"
        
        # 3. 提取建筑密度下限和上限
        density_match = re.search(r"(?:建筑密度|规划建筑密度)(?::|：)?([0-9%]+)-([0-9%]+)", clean_text)
        building_density_min = density_match.group(1) if density_match else "35%"
        building_density_max = density_match.group(2) if density_match else "55%"
        
        # 4. 提取规划绿地率
        green_match = re.search(r"(?:绿地率|规划绿地率)(?::|：)?(≤[0-9%]+|[0-9%]+)", clean_text)
        greening_rate = green_match.group(1) if green_match else "≤15%"
        
        # 5. 提取建筑限高
        height_match = re.search(r"(?:建筑限高|建筑高度限制|限高)(?::|：)?([0-9]+米|[0-9]+m)", clean_text)
        building_height_limit = height_match.group(1) if height_match else "24米"
        
        cond = PlanningConditionAttachment(
            planning_approval_authority=planning_approval_authority,
            building_density_min=building_density_min,
            building_density_max=building_density_max,
            plot_ratio_min="0.7",  # 默认兜底
            plot_ratio=plot_ratio,
            greening_rate=greening_rate,
            building_height_limit=building_height_limit
        )
        
        extracted_data = {
            "planning_approval_authority": cond.planning_approval_authority,
            "building_density_min": cond.building_density_min,
            "building_density_max": cond.building_density_max,
            "plot_ratio_min": cond.plot_ratio_min,
            "plot_ratio": cond.plot_ratio,
            "greening_rate": cond.greening_rate,
            "building_height_limit": cond.building_height_limit
        }

    elif attachment_type == "base_price_report":
        extracted_data = _extract_base_price_report_fields(clean_text, compact_text)
        
    return extracted_data
