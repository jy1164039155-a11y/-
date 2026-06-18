# -*- coding: utf-8 -*-
from src.services.ownership_builder import derive_ownership_descriptions


def base_payload():
    return {
        "land_location": "道县月岩西路",
        "land_area": "120.5",
        "building_area": "350.0",
        "land_user": "王某",
        "land_usage": "商业服务业用地",
        "land_usage_short": "商服用地",
        "right_type": "出让",
        "registered_right_type": "划拨",
        "land_development_actual": "宗地红线外五通，红线内场地平整",
        "land_development_set": "宗地红线外五通，红线内场地平整",
        "valuation_condition_type": "现状",
        "assumed_right_status": "无他项权利的完全权利条件",
    }


def test_commercial_new_grant_uses_commercial_wording():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"

    derive_ownership_descriptions(data)

    assert data["asset_use_category"] == "commercial"
    assert "商业服务业用地" in data["land_registration_desc"]
    assert "商业或商服" not in data["land_registration_desc"]
    assert "商业服务业建设用地" in data["land_use_status_desc"]
    assert "房改" not in data["land_registration_desc"]
    assert "估价对象现为划拨用地" not in data["land_right_desc"]


def test_single_land_usage_field_backfills_legacy_usage_fields():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["land_usage"] = "工业用地"
    data["land_usage_short"] = ""
    data["land_usage_full"] = ""

    derive_ownership_descriptions(data)

    assert data["land_usage_short"] == "工矿用地"
    assert data["land_usage_full"] == "工矿用地"
    assert "土地用途为工矿用地" in data["land_registration_desc"]


def test_usage_basis_and_land_use_term_have_hotspots():
    data = base_payload()
    data.update(
        {
            "ownership_scenario_type": "new_grant",
            "land_usage_basis": "《关于国有建设用地的规划条件的函》（2025年9月11日）",
            "land_use_term": "30年",
        }
    )

    derive_ownership_descriptions(data)

    def has_ref(field):
        return any(seg.get("field") == field or field in seg.get("fields", []) for seg in data["land_registration_desc_segments"])

    assert any(seg.get("field") == "land_usage_basis" for seg in data["land_registration_desc_segments"])
    assert has_ref("land_usage")
    assert has_ref("land_use_term")


def test_area_or_ownership_basis_prompt_has_hotspot():
    data = base_payload()
    data.update(
        {
            "ownership_scenario_type": "new_grant",
            "gov_approval_name": "关于某地块规划条件的函",
            "land_area_basis": "",
        }
    )

    derive_ownership_descriptions(data)

    assert "【请填写使用权面积或权属依据】" in data["land_registration_desc"]
    assert any(
        seg.get("text") == "【请填写使用权面积或权属依据】" and seg.get("field") == "land_area_basis"
        for seg in data["land_registration_desc_segments"]
    )


def test_other_rights_limit_generation():
    # 1. 默认无限制场景下的顺畅公文测试
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["has_other_rights_limit"] = False

    derive_ownership_descriptions(data)

    assert "根据委托方提供资料及现场勘查" in data["land_right_desc"]
    assert "未发现地上、地下相邻关系方面对估价结果产生重大影响的权利限制" in data["land_right_desc"]
    assert "估价对象未设置抵押权、担保权、地役权、租赁权等已披露的他项权利限制。" in data["land_right_desc"]

    # 2. 勾选有他项限制但为空时的占位符测试
    data["land_right_desc"] = ""
    data["has_other_rights_limit"] = True
    data["other_rights_limit_desc"] = ""
    derive_ownership_descriptions(data)

    assert "估价对象存在他项权利限制，具体限制情况为：【请填写他项权利限制说明】。" in data["land_right_desc"]

    # 3. 勾选有他项限制且手写时的精准回填测试
    data["land_right_desc"] = ""
    data["has_other_rights_limit"] = True
    data["other_rights_limit_desc"] = "已被抵押给中国工商银行，抵押金额为300万元"
    derive_ownership_descriptions(data)

    assert "估价对象存在他项权利限制，具体限制情况为：已被抵押给中国工商银行，抵押金额为300万元。" in data["land_right_desc"]


def test_registered_complete_requires_core_fields():
    import pytest
    from fastapi import HTTPException
    from src.api import validate_render_payload

    data = base_payload()
    data["ownership_scenario_type"] = "registered_complete"
    
    # 填满其它字段，故意空出地籍图号，并显式声明为正式归档模式以开启强拦截
    data.update({
        "client_name": "委托人",
        "appraisal_org": "评估机构",
        "report_no": "报告号",
        "right_cert_no": "证号1号",
        "owner_name": "王某",
        "registration_time": "2026年5月29日",
        "cadastral_map_no": "/",
        "parcel_no": "宗地1号",
        "land_use_term": "70年",
        "archive_to_result": True
    })

    with pytest.raises(HTTPException) as excinfo:
        validate_render_payload(data)
        
    assert excinfo.value.status_code == 422
    assert "cadastral_map_no" in str(excinfo.value.detail) or "地籍图号" in str(excinfo.value.detail)


def test_historical_unregistered_ignores_unrelated_land_cert_defaults():
    data = base_payload()
    data["ownership_scenario_type"] = "historical_unregistered"
    data["asset_use_category"] = "residential"
    data["land_cert_name"] = "不动产权证书"
    data["land_cert_no"] = "湘（2026）测试不动产权第000001号"
    data["house_cert_no"] = "房字第001号"

    derive_ownership_descriptions(data)

    assert "湘（2026）测试不动产权第000001号" not in data["land_registration_desc"]
    assert "房字第001号" in data["land_registration_desc"]
    assert "土地使用者待依法供应后确定" not in data["land_registration_desc"]


def test_other_category_uses_custom_label():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["land_usage_key"] = "other"
    data["land_usage_other"] = "交通运输用地"

    derive_ownership_descriptions(data)

    assert "交通运输用地" in data["land_registration_desc"]
    assert "交通运输用地" in data["land_use_status_desc"]


def test_basis_docs_list_normalizes_and_deduplicates():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["basis_docs_list"] = "道县补充规划条件会议纪要\n《关于某某地块的规划批复》（道规〔2023〕1号）\n道县补充规划条件会议纪要"

    derive_ownership_descriptions(data)

    assert data["basis_docs_rendered"] == "《道县补充规划条件会议纪要》、《关于某某地块的规划批复》（道规〔2023〕1号）"
    assert data["basis_docs_phrase"] == "根据《道县补充规划条件会议纪要》、《关于某某地块的规划批复》（道规〔2023〕1号）等资料"
    assert "《道县补充规划条件会议纪要》、《关于某某地块的规划批复》（道规〔2023〕1号）" in data["land_registration_desc"]


def test_basis_docs_keeps_commas_inside_brackets():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["basis_docs_list"] = "关于某地块的规划批复（道规〔2023〕1号，2023年5月1日）\n会议纪要"

    derive_ownership_descriptions(data)

    assert data["basis_docs_rendered"] == "《关于某地块的规划批复》（道规〔2023〕1号，2023年5月1日）、《会议纪要》"
    assert "《2023年5月1日》" not in data["basis_docs_rendered"]


def test_no_duplicate_basis_phrase_prefix():
    data = base_payload()
    data["ownership_scenario_type"] = "registered_complete"
    data["basis_docs_list"] = "不动产权证书"
    data["land_cert_no"] = "湘（2026）测试不动产权第000001号"

    derive_ownership_descriptions(data)

    assert "根据根据" not in data["land_registration_desc"]


def test_mixed_manual_still_derives_basis_docs_phrase():
    data = base_payload()
    data["ownership_scenario_type"] = "mixed_manual"
    data["basis_docs_list"] = "土地权属证明"

    derive_ownership_descriptions(data)

    assert data["basis_docs_rendered"] == "《土地权属证明》"
    assert data["basis_docs_phrase"] == "根据《土地权属证明》"
    assert "land_registration_desc" not in data


def test_manual_text_is_preserved_when_not_overwriting():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["land_registration_desc"] = "用户已经手工整理的最终登记状况正文。"

    derive_ownership_descriptions(data, overwrite=False)

    assert data["land_registration_desc"] == "用户已经手工整理的最终登记状况正文。"
    assert data["land_registration_desc_segments"]


def test_segments_generation_and_security():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["land_location"] = "道县<script>alert(1)</script>月岩西路"

    derive_ownership_descriptions(data)

    assert "land_registration_desc_segments" in data
    assert "land_right_desc_segments" in data
    assert "land_use_status_desc_segments" in data

    reg_segments = data["land_registration_desc_segments"]
    assert len(reg_segments) > 0

    found_ref = False
    for seg in reg_segments:
        assert "text" in seg
        if "field" in seg and seg["field"] == "land_location":
            assert seg["text"] == "道县<script>alert(1)</script>月岩西路"
            found_ref = True

    assert found_ref, "应该成功识别并切割出包含危险标签的 land_location 字段"


def test_land_level_never_outputs_raw_placeholder_when_base_price_missing():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["is_base_price_expired"] = True

    derive_ownership_descriptions(data)

    assert "8. 土地级别" in data["land_registration_desc"]
    assert "______" not in data["land_registration_desc"]
    assert "不写入未经核定的文号、日期或年限" in data["land_registration_desc"]


def test_stale_registration_desc_with_placeholder_is_rebuilt():
    data = base_payload()
    data["ownership_scenario_type"] = "new_grant"
    data["land_registration_desc"] = "8. 土地级别：批准文号为______。"

    derive_ownership_descriptions(data, overwrite=False)

    assert "______" not in data["land_registration_desc"]
    assert "8. 土地级别" in data["land_registration_desc"]


def test_land_level_elapsed_years_calculated_from_dates():
    data = base_payload()
    data.update(
        {
            "ownership_scenario_type": "new_grant",
            "is_base_price_expired": True,
            "valuation_date": "2026年04月23日",
            "base_price_doc_no": "道政函〔2019〕85号",
            "base_price_doc_name": "《关于更新城区基准地价和制订11个建制镇基准地价的通告》",
            "base_price_publish_date": "2019年11月22日",
            "base_price_base_date": "2019年5月1日",
            "base_price_doc_authority": "通道县自然资源局",
        }
    )

    derive_ownership_descriptions(data)

    assert data["base_price_is_expired"] is False
    assert "距估价期日超过六年" not in data["land_registration_desc"]
    assert "调查最新公示地价成果" in data["land_registration_desc"]


def test_land_level_expires_only_when_elapsed_years_exceed_threshold():
    data = base_payload()
    data.update(
        {
            "ownership_scenario_type": "new_grant",
            "valuation_date": "2026年05月02日",
            "base_price_doc_no": "道政函〔2019〕85号",
            "base_price_doc_name": "《关于更新城区基准地价和制订11个建制镇基准地价的通告》",
            "base_price_publish_date": "2019年11月22日",
            "base_price_base_date": "2019年5月1日",
            "base_price_doc_authority": "通道县自然资源局",
        }
    )

    derive_ownership_descriptions(data)

    assert data["base_price_is_expired"] is True
    assert "距估价期日超过六年" in data["land_registration_desc"]
    assert "已满六年，超过六年" not in data["land_registration_desc"]


def test_residential_historical_unregistered_matches_reference_structure():
    data = base_payload()
    data.update(
        {
            "ownership_scenario_type": "historical_unregistered",
            "land_usage": "住宅用地",
            "land_usage_short": "住宅用地",
            "land_location": "道县月岩西路",
            "room_detail_location": "道县月岩西路皮革厂家属楼3栋4层404房",
            "land_area": "15.20",
            "building_area": "74.55",
            "registered_house_area": "74.55",
            "land_user": "王汝冲",
            "buy_year": "2004年",
            "house_cert_no": "道房权证字第713000590号",
            "registered_right_type": "国有划拨",
        }
    )

    derive_ownership_descriptions(data, overwrite=True)

    text = data["land_registration_desc"]
    assert "2. 土地权利性质：国有划拨用地，现拟办理出让手续。" in text
    assert "权利演变与依据" not in text
    assert "3. 权利演变" not in text
    assert "估价对象位于道县月岩西路皮革厂家属楼3栋4层404房，建筑面积74.55平方米，分摊土地使用权面积15.20平方米" in text
    assert "估价对象土地使用者为王汝冲" in text
    assert "房屋权属证明号为道房权证字第713000590号" in text
