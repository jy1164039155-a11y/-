# -*- coding: utf-8 -*-
import sys
import os

# 将项目根目录加入 python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.ocr_extractor import extract_metrics_from_text

def test_property_cert_extraction():
    """测试：离线不动产权证文本提取（夹带物理单位杂质）"""
    # 模拟 OCR 吐出的凌乱文本
    raw_ocr_text = (
        "不动产权证书登记信息：\n"
        " 土地权利人: 王汝冲\n"
        " 房屋坐落位置: 道县月岩西路皮革厂家属楼3栋4层404房\n"
        " 分摊土地使用权面积: 约 15.20 平方米 (sqm) \n"
        " 权利性质: 国有划拨土地\n"
        " 设定用途: 城镇住宅用地 (城镇住宅)\n"
    )
    
    extracted = extract_metrics_from_text(raw_ocr_text, "property_cert")
    
    # 验证提取的准确性
    assert extracted["land_user"] == "王汝冲"
    assert extracted["land_location"] == "道县月岩西路皮革厂家属楼3栋4层404房"
    assert extracted["land_area"] == 15.20  # 自动剥离“约”、“平方米(sqm)”且成功转换为 float
    assert extracted["right_type"] == "国有划拨"
    assert extracted["land_usage_key"] == "residential"
    assert extracted["land_usage"] == "居住用地"
    assert extracted["land_usage_current_class"] == "居住用地"
    assert extracted["land_usage_price_class"] == "居住用地"
    
    print("[SUCCESS] 离线不动产权证高杂质文本提取测试大通过！")


def test_planning_condition_extraction():
    """测试：离线规划条件函文本提取（夹带范围容积率与单位）"""
    raw_ocr_text = (
        "发证机关/批准部门：道县自然资源局 \n"
        "规划控制指标：\n"
        " 容积率控制: 0.7 - 1.50 范围上限\n"
        " 规划建筑密度限制: 35%-55% 区间\n"
        " 规划绿地率标准: ≤15% 比例\n"
        " 建筑高度限制/限高: 24米 高度 \n"
    )
    
    extracted = extract_metrics_from_text(raw_ocr_text, "planning_condition")
    
    # 验证提取的准确性
    assert extracted["planning_approval_authority"] == "道县自然资源局"
    assert extracted["plot_ratio"] == 1.50  # 自动提取范围上限“1.50”并成功清洗为 float
    assert extracted["building_density_min"] == "35%"
    assert extracted["building_density_max"] == "55%"
    assert extracted["greening_rate"] == "≤15%"
    assert extracted["building_height_limit"] == "24米"
    
    print("[SUCCESS] 离线规划条件高杂质文本提取测试大通过！")


def test_land_ownership_proof_extraction_without_fake_area():
    raw_ocr_text = (
        "土地权属及性质证明\n"
        "兹有王汝冲，身份证号码：432923197312254139，为道县皮革厂工作人员，"
        "根据房改房政策于2004年购得位于道州月岩西路皮革厂家属楼3栋4层404住房一套，"
        "房产证号：道房权证字第713000590号，房屋登记面积74.55平方米。"
        "其房屋分摊土地使用权类型为国有划拨，因历史遗留问题，土地暂未办理土地权属登记。"
    )

    extracted = extract_metrics_from_text(raw_ocr_text, "property_cert")

    assert extracted["land_user"] == "王汝冲"
    assert extracted["house_cert_no"] == "道房权证字第713000590号"
    assert extracted["registered_house_area"] == "74.55"
    assert extracted["registered_right_type"] == "国有划拨"
    assert extracted["proof_doc_name"] == "土地权属及性质证明"
    assert "land_area" not in extracted


def test_house_cert_pdf_text_layer_layout_extraction():
    raw_ocr_text = (
        "根据《中华人民共和国物权法》,房\n"
        "屋所有权证书是权利人享有房屋所有权的\n"
        "证明。\n"
        "字第 71300059号\n"
        "道房权证\n"
        "房屋状况\n"
        "土地状况\n"
        "房屋所有权人\n"
        "王汝冲\n"
        "共 有情况\n"
        "房 屋坐落\n"
        "道县月岩西路\n"
        "规划用途\n"
        "住宅\n"
        "建筑面积(平方米)\n"
        "74.55\n"
    )

    extracted = extract_metrics_from_text(raw_ocr_text, "property_cert")

    assert extracted["land_user"] == "王汝冲"
    assert extracted["land_location"] == "道县月岩西路"
    assert extracted["house_cert_no"] == "道房权证字第71300059号"
    assert extracted["registered_house_area"] == "74.55"
    assert extracted["land_usage_key"] == "residential"
    assert extracted["land_usage"] == "居住用地"


def test_base_price_report_extraction():
    raw_ocr_text = (
        "通道县城镇基准地价更新成果\n"
        "文件名称为《关于更新城区基准地价和制订11个建制镇基准地价的通告》\n"
        "批准文号为道政函〔2019〕85号，批准机关为通道县自然资源局。\n"
        "颁布实施时间为2019年11月22日，城区基准地价估价基准日为2019年5月1日。\n"
        "根据《关于进一步做好湖南省公示地价体系建设和管理有关工作的通知》（湘自资办发[2022]23号）执行。"
    )

    extracted = extract_metrics_from_text(raw_ocr_text, "base_price_report")

    assert extracted["base_price_doc_name"] == "《关于更新城区基准地价和制订11个建制镇基准地价的通告》"
    assert extracted["base_price_doc_no"] == "道政函〔2019〕85号"
    assert extracted["base_price_doc_authority"] == "通道县自然资源局"
    assert extracted["base_price_publish_date"] == "2019年11月22日"
    assert extracted["base_price_base_date"] == "2019年5月1日"
    assert extracted["base_price_rule_doc_no"] == "湘自资办发[2022]23号"
    assert "base_price_is_expired" not in extracted

if __name__ == "__main__":
    test_property_cert_extraction()
    test_planning_condition_extraction()
