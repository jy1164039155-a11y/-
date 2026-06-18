# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient

from src.services.valuation_builder import derive_valuation_descriptions, _calculate_expired_years
from src.services.land_usage import normalize_land_usage_fields


def base_payload():
    return {
        "transfer_purpose": "拟挂牌出让",
        "right_type": "出让",
        "land_location": "道县双江镇城南街",
        "land_area": "25.32",
        "land_usage": "城镇住宅用地",
        "land_usage_short": "住宅用地",
        "land_development_actual": "宗地红线外五通，宗地红线内场地平整",
        "land_development_set": "宗地红线外五通，宗地红线内场地平整",
        "valuation_condition_type": "现状",
        "use_cost_approx": True,
        "use_market_comp": True,
        "use_income_cap": False,
        "use_benchmark_corr": False,
        "use_residual": False,
        "cost_approx_price": "189.9",
        "market_comp_price": "127.7",
        "income_cap_price": "1329.5",
        "benchmark_corr_price": "895.7",
        "residual_price": "2510.5",
        "show_price_in_text": True,
        "weight_logic_type": "simple_average",
    }


def test_residential_two_methods_generates_structured_text_and_segments():
    data = base_payload()

    derive_valuation_descriptions(data, overwrite=True)

    assert "选用理由" in data["valuation_method_reasons"]
    assert "成本逼近法" in data["valuation_method_reasons"]
    assert "未采用方法说明" in data["valuation_method_reasons"]
    assert "对已选估价方法进行适用性分析" in data["valuation_method_applicability"]
    assert "成本逼近法" in data["valuation_method_applicability"]
    assert "市场比较法" in data["valuation_method_applicability"]
    assert "五通" in data["infrastructure_detail"]
    assert data["formula_display_text"] == "成本逼近法×50%+市场比较法×50%"
    assert "成本逼近法是" in data["final_price_determination"]
    assert "成本逼近法：" not in data["final_price_determination"]
    assert any(seg.get("field") == "use_cost_approx" for seg in data["valuation_method_reasons_segments"])
    assert any(seg.get("field") == "right_type" for seg in data["valuation_method_applicability_segments"])
    assert any(seg.get("field") == "cost_approx_price" for seg in data["final_price_determination_segments"])


def _has_segment(segments, text, field):
    return any(seg.get("text") == text and seg.get("field") == field for seg in segments)


def missing_result_payload():
    data = base_payload()
    data.update(
        {
            "cost_approx_price": "",
            "market_comp_price": "",
            "show_price_in_text": True,
            "final_unit_price": "",
            "final_total_price": "",
            "final_total_price_upper": "",
            "valuation_basis_docs_list": "",
            "county_name": "",
            "planning_approval_authority": "",
        }
    )
    return data


def test_prompt_hotspots_are_mapped_for_missing_final_values():
    data = missing_result_payload()

    derive_valuation_descriptions(data, overwrite=True)

    result_segments = data["valuation_result_statement_segments"]
    assert data["final_unit_price"] == "【请填写土地单价】"
    assert data["final_total_price"] == "【请填写土地总价】"
    assert data["final_total_price_upper"] == "【请填写土地总价大写】"
    assert _has_segment(result_segments, "【请填写土地单价】", "final_unit_price")
    assert _has_segment(result_segments, "【请填写土地总价】", "final_total_price")
    assert _has_segment(result_segments, "【请填写土地总价大写】", "final_total_price_upper")
    assert _has_segment(data["final_price_determination_segments"], "【请填写成本逼近法单价】", "cost_approx_price")
    assert _has_segment(data["final_price_determination_segments"], "【请填写市场比较法单价】", "market_comp_price")
    assert _has_segment(data["cost_approx_process_intro_segments"], "【请填写土地评估计算过程依据】", "valuation_basis_docs_list")


def test_cost_approx_land_class_intro_uses_acquisition_fields_not_land_usage():
    data = base_payload()
    data.update(
        {
            "land_location_full": "道县工业园（2025018号地块）",
            "land_usage": "工业用地",
            "land_usage_short": "工业用地",
            "acquisition_land_class": "水田",
            "acquisition_approval_doc_name": "关于道县某批次建设用地的批复",
            "acquisition_approval_doc_no": "湘政地〔2025〕1号",
            "acquisition_approval_doc_date": "2025年1月2日",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    text = data["cost_approx_land_class_intro"]
    assert "道县工业园（2025018号地块）" in text
    assert "《关于道县某批次建设用地的批复》（湘政地〔2025〕1号，2025年1月2日）" in text
    assert "征收地类为水田" in text
    assert "被征用的土地为水田" in text
    assert "工业用地" not in text
    assert not any("分项参数仍按林地测算" in warning["message"] for warning in data["method_warnings"])


def test_cost_approx_acquisition_fields_support_legacy_fallback():
    data = base_payload()
    data.update(
        {
            "original_land_owner_desc": "水田",
            "gov_approval_name": "关于某批次建设用地的批复",
            "gov_approval_no": "湘政地〔2024〕9号",
            "gov_approval_date": "2024年3月4日",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert data["acquisition_land_class"] == "水田"
    assert data["acquisition_approval_doc_name"] == "关于某批次建设用地的批复"
    assert "征收地类为水田" in data["cost_approx_land_class_intro"]


def test_cost_parameter_land_class_warning_is_not_emitted_for_forest_land():
    data = base_payload()
    data["acquisition_land_class"] = "乔木林地"

    derive_valuation_descriptions(data, overwrite=True)

    assert not any("分项参数仍按林地测算" in warning["message"] for warning in data["method_warnings"])


def test_cost_process_intro_uses_explicit_or_known_city_and_prompts_unknown_city():
    explicit = base_payload()
    explicit.update({"county_name": "浏阳市", "local_city": "长沙市"})
    derive_valuation_descriptions(explicit, overwrite=True)
    assert "湖南省、长沙市颁布其他各项文件" in explicit["cost_approx_process_intro"]

    known = base_payload()
    known["county_name"] = "道县"
    derive_valuation_descriptions(known, overwrite=True)
    assert "湖南省、永州市颁布其他各项文件" in known["cost_approx_process_intro"]

    unknown = base_payload()
    unknown["county_name"] = "某县"
    derive_valuation_descriptions(unknown, overwrite=True)
    assert "湖南省、【请填写所属市级】颁布其他各项文件" in unknown["cost_approx_process_intro"]
    assert _has_segment(unknown["cost_approx_process_intro_segments"], "【请填写所属市级】", "local_city")


def test_method_intro_and_cost_process_are_generated_only_for_selected_methods():
    data = base_payload()
    data.update(
        {
            "use_cost_approx": False,
            "use_market_comp": True,
            "use_income_cap": False,
            "cost_approx_land_class_intro": "旧征收地类说明",
            "cost_approx_process_intro": "旧成本过程说明",
            "cost_approx_method_intro": "旧成本公式",
            "income_cap_method_intro": "旧收益公式",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert data["cost_approx_land_class_intro"] == ""
    assert data["cost_approx_process_intro"] == ""
    assert data["cost_approx_method_intro"] == ""
    assert data["income_cap_method_intro"] == ""
    assert "市场比较法是" in data["market_comp_method_intro"]


def test_income_cap_formula_includes_exponent_marker():
    data = base_payload()
    data.update(
        {
            "use_cost_approx": False,
            "use_market_comp": False,
            "use_income_cap": True,
            "income_cap_price": "100",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert "（1＋r）^n" in data["income_cap_method_intro"]


def test_base_price_missing_prompts_are_mapped_for_hotspots():
    data = base_payload()
    data.update(
        {
            "use_benchmark_corr": False,
            "is_base_price_expired": True,
            "base_price_is_expired": True,
            "explain_unselected_methods": True,
            "base_price_doc_no": "",
            "base_price_doc_name": "",
            "base_price_publish_date": "",
            "base_price_base_date": "",
            "base_price_doc_authority": "",
            "valuation_date": "",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    segments = data["valuation_method_reasons_segments"]
    expected = [
        ("【请填写基准地价批准文号】", "base_price_doc_no"),
        ("【请填写基准地价文件名称】", "base_price_doc_name"),
        ("【请填写基准地价颁布实施日期】", "base_price_publish_date"),
        ("【请填写基准地价估价基准日】", "base_price_base_date"),
        ("【请填写基准地价批准机关】", "base_price_doc_authority"),
        ("【请填写估价期日】", "valuation_date"),
    ]
    for prompt, field in expected:
        assert _has_segment(segments, prompt, field)


def test_build_valuation_draft_returns_final_values_and_segments():
    from src import api

    client = TestClient(api.app)
    response = client.post(
        "/api/build-valuation-draft",
        json={"data": missing_result_payload(), "overwrite": True},
    )

    assert response.status_code == 200
    drafts = response.json()["data"]
    assert drafts["final_unit_price"] == "【请填写土地单价】"
    assert drafts["final_total_price"] == "【请填写土地总价】"
    assert drafts["final_total_price_upper"] == "【请填写土地总价大写】"
    assert _has_segment(drafts["valuation_result_statement_segments"], "【请填写土地单价】", "final_unit_price")
    assert _has_segment(drafts["valuation_result_statement_segments"], "【请填写土地总价】", "final_total_price")
    assert _has_segment(drafts["valuation_result_statement_segments"], "【请填写土地总价大写】", "final_total_price_upper")


def test_industrial_wording_focuses_on_production_support():
    data = base_payload()
    data.update(
        {
            "land_usage": "工业用地",
            "land_usage_short": "工业用地",
            "asset_use_category": "industrial",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert "工矿用地成本构成" in data["valuation_method_applicability"]
    assert "当地工矿用地成交或供应案例" in data["valuation_method_applicability"]
    assert "五通" in data["infrastructure_detail"]


def test_commercial_wording_uses_commercial_service_label():
    data = base_payload()
    data.update(
        {
            "land_usage": "商服用地",
            "land_usage_short": "商服用地",
            "asset_use_category": "commercial",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert "商业服务业" in data["valuation_method_applicability"]
    assert "五通" in data["infrastructure_detail"]


def test_public_service_wording():
    data = base_payload()
    data.update(
        {
            "land_usage": "公共管理与公共服务用地",
            "land_usage_short": "公共管理与公共服务用地",
            "asset_use_category": "public",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert "公共管理与公共服务" in data["valuation_method_applicability"]
    assert "公益属性" in data["infrastructure_detail"]


def test_other_category_uses_custom_description():
    data = base_payload()
    data.update(
        {
            "asset_use_category": "other",
            "asset_use_category_other": "交通运输用地",
            "land_usage": "交通运输用地",
            "land_usage_short": "交通运输用地",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert "交通运输用地" in data["infrastructure_detail"]


def test_weight_warning_when_formula_weight_sum_not_100():
    data = base_payload()
    data["formula_display_text"] = "成本逼近法×60%+市场比较法×30%"

    derive_valuation_descriptions(data, overwrite=False)

    assert any("权重合计为90%" in warning for warning in data["valuation_warnings"])


def test_weighted_average_uses_user_method_percentages():
    data = base_payload()
    data.update(
        {
            "weight_logic_type": "weighted_average",
            "method_weight_percentages": {
                "use_cost_approx": "60",
                "use_market_comp": "40",
            },
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert data["formula_display_text"] == "成本逼近法×60%+市场比较法×40%"
    assert data["final_unit_price"] == "165"
    assert "加权算术平均值" in data["final_price_determination"]


def test_median_logic_calculates_middle_price():
    data = base_payload()
    data.update(
        {
            "weight_logic_type": "median",
            "use_residual": True,
            "cost_approx_price": "100",
            "market_comp_price": "200",
            "residual_price": "400",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert data["formula_display_text"] == "成本逼近法、市场比较法和剩余法测算结果的中位数"
    assert data["final_unit_price"] == "200"
    assert "中位数" in data["final_price_determination"]


def test_mode_logic_requires_manual_price_without_unique_mode():
    data = base_payload()
    data.update(
        {
            "weight_logic_type": "mode",
            "cost_approx_price": "100",
            "market_comp_price": "200",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    assert data["requires_manual_final_price"] is True
    assert data["final_unit_price"] == "【请填写土地单价】"
    assert any("众数确价未形成唯一众数" in warning for warning in data["valuation_warnings"])


def test_legacy_simple_average_maps_to_equal_weighted_average():
    data = base_payload()
    data["weight_logic_type"] = "simple_average"

    derive_valuation_descriptions(data, overwrite=True)

    assert data["formula_display_text"] == "成本逼近法×50%+市场比较法×50%"
    assert data["final_unit_price"] == "159"


def test_missing_selected_method_price_returns_warning_without_fake_price():
    data = base_payload()
    data["market_comp_price"] = ""

    derive_valuation_descriptions(data, overwrite=True)

    assert any("市场比较法已勾选" in warning for warning in data["valuation_warnings"])
    assert "市场比较法单价为" not in data["final_price_determination"]


def test_manual_text_is_preserved_when_not_overwriting():
    data = base_payload()
    data["valuation_method_applicability"] = "用户手工整理的方法适用性正文。"
    data["valuation_method_reasons"] = "用户手工整理的方法理由正文。"

    derive_valuation_descriptions(data, overwrite=False)

    assert data["valuation_method_applicability"] == "用户手工整理的方法适用性正文。"
    assert data["valuation_method_reasons"] == "用户手工整理的方法理由正文。"
    assert data["valuation_method_applicability_segments"]
    assert data["valuation_method_reasons_segments"]


def test_overwrite_rebuilds_text_and_segments():
    data = base_payload()
    data["valuation_method_applicability"] = "旧正文"
    data["valuation_method_reasons"] = "旧理由"

    derive_valuation_descriptions(data, overwrite=True)

    assert data["valuation_method_applicability"] != "旧正文"
    assert data["valuation_method_reasons"] != "旧理由"
    assert "对已选估价方法进行适用性分析" in data["valuation_method_applicability"]
    assert "选用理由" in data["valuation_method_reasons"]
    assert data["valuation_method_applicability_segments"]
    assert data["valuation_method_reasons_segments"]


def test_unselected_methods_are_explained_by_default():
    data = base_payload()
    derive_valuation_descriptions(data, overwrite=True)
    assert "未采用方法说明" in data["valuation_method_reasons"]
    assert "收益还原法" in data["valuation_method_reasons"]

    data = base_payload()
    data["explain_unselected_methods"] = False
    derive_valuation_descriptions(data, overwrite=True)
    assert "未采用方法说明" in data["valuation_method_reasons"]
    assert "收益还原法" in data["valuation_method_reasons"]


def test_base_price_elapsed_years_uses_full_calendar_date():
    assert _calculate_expired_years("2026年04月23日", "2019年5月1日") == (6, "六")
    assert _calculate_expired_years("2026年05月02日", "2019年5月1日") == (7, "七")


def test_land_usage_key_derives_legacy_usage_and_classes():
    data = {"land_usage_key": "warehouse", "land_usage_other": "临时手填用途"}

    normalize_land_usage_fields(data)

    assert data["land_usage"] == "仓储用地"
    assert data["land_usage_short"] == "仓储用地"
    assert data["land_usage_full"] == "仓储用地"
    assert data["land_usage_other"] == ""
    assert data["land_usage_current_class"] == "仓储用地"
    assert data["land_usage_price_class"] == "仓储用地"


def test_unknown_land_usage_maps_to_other_and_preserves_original_text():
    data = {"land_usage": "混合创新产业用地"}

    normalize_land_usage_fields(data)

    assert data["land_usage_key"] == "other"
    assert data["land_usage_other"] == "混合创新产业用地"
    assert data["land_usage"] == "混合创新产业用地"
    assert data["land_usage_current_class"] == "混合创新产业用地"
    assert data["land_usage_price_class"] == "混合创新产业用地"


def test_base_price_exclusion_uses_dynamic_policy_fields():
    data = base_payload()
    data.update(
        {
            "valuation_date": "2026年05月02日",
            "county_name": "通道县",
            "explain_unselected_methods": True,
            "is_base_price_expired": True,
            "base_price_doc_no": "通政发〔2026〕1号",
            "base_price_doc_name": "《关于更新城镇基准地价标准和等级的通知》",
            "base_price_publish_date": "2020年1月6日",
            "base_price_base_date": "2019年5月1日",
            "base_price_doc_authority": "通道县自然资源局",
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    text = data["valuation_method_reasons"]
    assert "通政发〔2026〕1号" in text
    assert "《关于更新城镇基准地价标准和等级的通知》" in text
    assert "通道县自然资源局" in text
    assert "超过六年" in text
    assert "已满六年，超过六年" not in text
    assert "不得作为宗地评估基准地价系数修正法的依据" in text
    assert "道政函〔2019〕85号" not in text


def test_base_price_yaml_template_uses_dynamic_policy_fields_and_legacy_aliases():
    data = base_payload()
    data.update(
        {
            "valuation_date": "2026年05月02日",
            "land_usage": "工业用地",
            "land_usage_short": "工业用地",
            "asset_use_category": "industrial",
            "base_land_price_doc_no": "新政函〔2020〕8号",
            "base_land_price_doc_name": "《新晃县城镇基准地价更新成果公告》",
            "base_land_price_pub_date": "2020年3月1日",
            "base_land_price_value_date": "2019年5月1日",
            "base_land_price_doc_authority": "新晃县人民政府",
            "explain_unselected_methods": True,
            "is_base_price_expired": True,
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    text = data["valuation_method_reasons"]
    assert "新政函〔2020〕8号" in text
    assert "《新晃县城镇基准地价更新成果公告》" in text
    assert "新晃县人民政府" in text
    assert "距估价期日超过六年" in text
    assert "已满七年" not in text
    assert "{{ base_price" not in text


def test_base_price_exclusion_does_not_invent_missing_dates_or_years():
    data = base_payload()
    data.update(
        {
            "valuation_date": "2026年04月23日",
            "county_name": "通道县",
            "explain_unselected_methods": True,
            "is_base_price_expired": True,
        }
    )

    derive_valuation_descriptions(data, overwrite=True)

    text = data["valuation_method_reasons"]
    assert "______" not in text
    assert "【请填写基准地价批准机关】" in text
    assert _has_segment(data["valuation_method_reasons_segments"], "【请填写基准地价批准机关】", "base_price_doc_authority")
    assert "已超过六年" not in text
    assert "间隔年限需结合基准日和估价期日进一步核定" not in text
    assert "需补充基准地价文件及估价基准日后判断是否超过六年" in text
