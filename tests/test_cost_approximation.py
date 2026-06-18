# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from src.services.cost_approximation import (
    applicable_cost_basis,
    building_compensation_add_catalog,
    building_compensation_grade_options,
    building_compensation_policy_help,
    building_compensation_rows_for_county,
    calculate_cost_approximation,
    cost_basis_attachment_inventory,
    green_seedling_standard_for_county,
    suggest_compensation_zone,
    validate_yongzhou_local_compensation_xlsx,
    _sync_risk_groups,
)


BASE_DIR = Path(__file__).resolve().parents[1]

BAOZHEN_SAMPLE_DATA = {
    "county_name": "道县",
    "valuation_date": "2026-06-01",
    "transfer_purpose_mode": "办理土地使用权出让手续",
    "land_location_full": "道县西洲街道宝珍街六栋九号",
    "acquisition_land_class": "水田",
    "land_usage": "居住用地",
    "land_development_set": "五通一平",
}

BAOZHEN_LOCATION_LEVELS = ["较优", "劣", "优", "较劣", "优", "优", "较优", "较优", "较优", "较优", "劣", "优"]

BAOZHEN_LOCATION_DESCRIPTIONS = [
    "距汽车站较近",
    "距火车站远",
    "距商服中心近",
    "临交通次主道",
    "路网密度高",
    "对外交通便利",
    "环境质量较优",
    "人口较密集",
    "基础设施较完善",
    "地形较平坦",
    "宗地面积小",
    "宗地形状规则",
]

BAOZHEN_REFERENCE_POPULATION_CASES = [
    {
        "key": "reference",
        "name": "范本口径",
        "location": "道县西洲街道宝珍街六栋九号",
        "land_area_ha": "1",
        "population": "12.82",
        "confirmed": True,
    }
]


def _confirm_baozhen_analysis(analysis):
    for item in (
        analysis["policy_documents"]
        + analysis["acquisition_items"]
        + analysis["tax_items"]
        + analysis["development_items"]
        + analysis["usage_scenarios"]
        + analysis["building_compensation_rows"]
        + analysis["resettlement_population_cases"]
        + analysis["risk_items"]
    ):
        item["confirmed"] = True
    for item, level, description in zip(
        analysis["location_factors"],
        BAOZHEN_LOCATION_LEVELS,
        BAOZHEN_LOCATION_DESCRIPTIONS,
    ):
        item["level"] = level
        item["description"] = description
        item["confirmed"] = True
    return analysis


def _mixed_usage_payload():
    return {
        "county_name": "道县",
        "valuation_date": "2025-12-04",
        "acquisition_land_class": "水田",
        "land_usage": "商业服务业用地、居住用地",
        "land_development_set": "五通一平",
    }


def test_building_compensation_rows_for_dao_county_include_policy_source_and_pending_review():
    rows = building_compensation_rows_for_county(BASE_DIR, "道县")

    # i1：默认表单行保持范例同款（精简样例），不被政策目录回填污染。
    # 完整目录通过 building_compensation_add_catalog 暴露（见 test_building_catalog_fully_structured_from_policy_sources）。
    assert len(rows) == 4
    row_keys = {row["key"] for row in rows}
    assert {"house_compensation", "vacating_award", "moving_fee", "transition_fee"} == row_keys
    assert "grave_compensation" not in row_keys
    assert all(row["confirmed"] is False for row in rows)
    assert all(".xlsx" in row["source_path"] for row in rows)
    assert all(len(row["source_hash"]) == 64 for row in rows)
    moving = next(row for row in rows if row["key"] == "moving_fee")
    transition = next(row for row in rows if row["key"] == "transition_fee")
    vacating = next(row for row in rows if row["key"] == "vacating_award")
    house = next(row for row in rows if row["key"] == "house_compensation")
    assert moving["conversion_check"]["status"] == "match"
    assert transition["conversion_check"]["status"] == "match"
    assert vacating["conversion_check"]["status"] == "match"
    assert house["conversion_check"]["status"] == "match"
    assert house["pending_review"] is False
    assert house["standard"] == "1250"
    assert house["amount"] == "87500"
    assert house["structure_grade"] == "brick_mixed_2"
    assert len(house.get("grade_options") or []) >= 1
    assert len(vacating.get("grade_options") or []) >= 2
    assert building_compensation_grade_options(BASE_DIR, "道县", "house_compensation")[0]["standard"] == "1250"


def test_f3_building_row_quantity_change_syncs_acquisition_per_sqm():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "land_location_full": "道县西洲街道宝珍街六栋九号",
        "land_usage": "居住用地",
        "land_development_set": "五通一平",
        "cost_approx_analysis": {
            "resettlement_population_cases": [
                {"key": "case_a", "name": "案例A", "location": "道县", "land_area_ha": "10", "population": "100", "confirmed": True},
                {"key": "case_b", "name": "案例B", "location": "道县", "land_area_ha": "20", "population": "220", "confirmed": True},
                {"key": "case_c", "name": "案例C", "location": "道县", "land_area_ha": "30", "population": "360", "confirmed": True},
            ],
        },
    }
    result = calculate_cost_approximation(data, BASE_DIR)
    building_item = next(item for item in result["acquisition_items"] if item["key"] == "building_compensation")
    assert building_item["amount_per_sqm"] == "107.80"
    assert result["attachment_compensation_analysis"]["building_compensation_per_person"] == "98000.00"

    house = next(row for row in result["building_compensation_rows"] if row["key"] == "house_compensation")
    house["quantity"] = "80"
    house["confirmed"] = False
    data["cost_approx_analysis"] = result
    updated = calculate_cost_approximation(data, BASE_DIR)
    building_item = next(item for item in updated["acquisition_items"] if item["key"] == "building_compensation")
    assert updated["attachment_compensation_analysis"]["building_compensation_per_person"] == "110500.00"
    assert building_item["amount_per_sqm"] == "121.55"


def test_f3_vacating_grade_switch_recalculates_row_amount():
    rows = building_compensation_rows_for_county(BASE_DIR, "道县")
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "land_usage": "居住用地",
        "cost_approx_analysis": {"building_compensation_rows": rows},
    }
    result = calculate_cost_approximation(data, BASE_DIR)
    vacating = next(row for row in result["building_compensation_rows"] if row["key"] == "vacating_award")
    assert vacating["amount"] == "7000.00"

    signing = next(option for option in vacating["grade_options"] if option["key"] == "signing_award_80")
    vacating["structure_grade"] = signing["key"]
    vacating["standard"] = signing["standard"]
    vacating["confirmed"] = False
    data["cost_approx_analysis"] = result
    updated = calculate_cost_approximation(data, BASE_DIR)
    vacating_updated = next(row for row in updated["building_compensation_rows"] if row["key"] == "vacating_award")
    assert vacating_updated["standard"] == "80"
    assert vacating_updated["amount"] == "5600.00"


def test_building_compensation_policy_help_includes_grade_catalog_and_fixed_fees():
    help_data = building_compensation_policy_help(BASE_DIR, "道县")
    assert help_data["policy_document_no"] == "永政发〔2024〕4号"
    assert any(entry["option_key"] == "brick_mixed_2" for entry in help_data["entries"])
    assert any(entry["row_key"] == "moving_fee" for entry in help_data["entries"])
    assert any(entry["row_key"] == "transition_fee" for entry in help_data["entries"])
    assert len(help_data["paid_land_use_fee_standards"]) >= 10


def test_building_compensation_policy_help_attached_to_cost_analysis():
    result = calculate_cost_approximation({"county_name": "道县", "valuation_date": "2026-06-01"}, BASE_DIR)
    help_data = result.get("building_compensation_policy_help") or {}
    assert help_data.get("policy_document_no") == "永政发〔2024〕4号"
    assert len(help_data.get("entries") or []) >= 4


def test_green_seedling_standard_for_daoxian_and_tongdao_counties():
    daoxian_paddy = green_seedling_standard_for_county(BASE_DIR, "道县", "水田")
    assert daoxian_paddy["standard_per_mu"] == "2800"
    assert "永政发" in daoxian_paddy["source_note"]
    tongdao_paddy = green_seedling_standard_for_county(BASE_DIR, "通道县", "水田")
    assert tongdao_paddy["standard_per_mu"] == "1500"
    tongdao_dry = green_seedling_standard_for_county(BASE_DIR, "通道县", "旱地")
    assert tongdao_dry["standard_per_mu"] == "1000"
    tongdao_forest = green_seedling_standard_for_county(BASE_DIR, "通道县", "乔木林地")
    assert tongdao_forest["standard_per_mu"] == "4000"


def test_huaihua_building_add_catalog_for_tongdao_has_numeric_standards():
    catalog = building_compensation_add_catalog(BASE_DIR, "通道县")
    house = next(item for item in catalog if item["row_key"] == "house_compensation")
    decoration = next(item for item in catalog if item["row_key"] == "decoration_compensation")
    assert house["grade_options"][0]["standard"] == "1100"
    assert any(option["standard"] == "900" for option in house["grade_options"])
    assert decoration["grade_options"][0]["standard"] == "600"
    assert any(option["standard"] == "500" for option in decoration["grade_options"])
    assert house["template"]["standard"] == "900"
    assert decoration["template"]["standard"] == "500"


def test_huaihua_building_rows_for_tongdao_link_source_docs():
    rows = building_compensation_rows_for_county(BASE_DIR, "通道县")
    house = next(row for row in rows if row["key"] == "house_compensation")
    assert house["standard"] == "900"
    assert house["review_status"] == "verified_partial"
    assert "怀化市集体土地房屋征收补偿标准.doc" in house["source_path"]
    help_data = building_compensation_policy_help(BASE_DIR, "通道县")
    assert any(entry["standard"] == "900" for entry in help_data["entries"])
    assert any(entry["standard"] == "500" for entry in help_data["entries"])


def test_cost_basis_attachment_inventory_lists_collected_policy_files():
    daoxian_inventory = cost_basis_attachment_inventory(BASE_DIR, "道县")
    tongdao_inventory = cost_basis_attachment_inventory(BASE_DIR, "通道县")
    assert len(daoxian_inventory) >= 1
    assert len(tongdao_inventory) >= 1
    labels = [item["label"] for item in daoxian_inventory]
    assert any("永政发" in label for label in labels)
    tongdao_labels = [item["label"] for item in tongdao_inventory]
    assert any("怀化" in label for label in tongdao_labels)


def test_green_seedling_and_attachment_inventory_in_calculate_result():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "acquisition_land_class": "耕地",
            "acquisition_land_subclass": "水田",
        },
        BASE_DIR,
        include_pricing_assistant=False,
    )
    assert result.get("green_seedling_standard_per_mu") == "2800"
    assert "永政发" in (result.get("green_seedling_standard_source") or "")
    inventory = result.get("cost_basis_attachment_inventory") or []
    assert len(inventory) >= 1


def test_applicable_cost_basis_includes_green_seedling_and_inventory():
    basis = applicable_cost_basis(
        {
            "county_name": "通道县",
            "acquisition_land_subclass": "旱地",
        },
        BASE_DIR,
    )
    assert basis.get("green_seedling_standard_per_mu") == "1000"
    assert len(basis.get("cost_basis_attachment_inventory") or []) >= 1


def test_custom_building_compensation_row_included_in_attachment_total():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "cost_approx_analysis": {
            "resettlement_population_cases": [
                {"key": "case_a", "name": "案例A", "land_area_ha": "10", "population": "100", "confirmed": True},
            ],
        },
    }
    result = calculate_cost_approximation(data, BASE_DIR)
    base_per_person = float(result["attachment_compensation_analysis"]["building_compensation_per_person"])
    result["building_compensation_rows"].append(
        {
            "key": "custom_bonus",
            "label": "其他奖励",
            "standard": "50",
            "quantity": "70",
            "divisor": "1",
            "confirmed": False,
        }
    )
    data["cost_approx_analysis"] = result
    updated = calculate_cost_approximation(data, BASE_DIR)
    assert float(updated["attachment_compensation_analysis"]["building_compensation_per_person"]) == pytest.approx(
        base_per_person + 50 * 70, abs=0.01
    )


def test_pricing_assistant_includes_multiple_scenarios_with_final_prices():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_usage": "居住用地",
            "land_development_set": "五通一平",
            "acquisition_land_class": "耕地",
            "acquisition_land_subclass": "水田",
        },
        BASE_DIR,
        include_pricing_assistant=True,
    )
    assistant = result.get("pricing_assistant") or {}
    scenarios = assistant.get("scenarios") or []
    controls = assistant.get("controls") or []
    assert len(scenarios) >= 3
    assert len(controls) >= 10
    assert assistant.get("baseline_final_price")
    assert all(str(item.get("final_price") or "") for item in scenarios)
    paid_14 = next(item for item in scenarios if item["key"] == "paid_land_14")
    assert paid_14["changed_items"][0]["to"] == "十四等"
    assert float(paid_14["final_price"]) != float(scenarios[0]["final_price"])


def test_pricing_assistant_includes_building_compensation_row_controls():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_usage": "居住用地",
            "land_development_set": "五通一平",
            "acquisition_land_class": "水田",
        },
        BASE_DIR,
        include_pricing_assistant=True,
    )
    controls = result.get("pricing_assistant", {}).get("controls") or []
    building_controls = [item for item in controls if str(item.get("key") or "").startswith("building:")]
    assert building_controls
    assert any("表3-1" in str(item.get("label") or "") for item in building_controls)


def test_daoxian_policy_help_meets_f12_acceptance_threshold():
    help_data = building_compensation_policy_help(BASE_DIR, "道县")
    entries = help_data.get("entries") or []
    assert len(entries) >= 5
    assert any(entry.get("standard") for entry in entries)


def test_validate_yongzhou_local_compensation_xlsx_detects_attachment1_total():
    config = building_compensation_rows_for_county(BASE_DIR, "道县")
    validation = validate_yongzhou_local_compensation_xlsx(BASE_DIR, config)

    assert validation["ok"] is True
    assert validation["parsed"]["attachment1_brick_mixed_grade_ii"]["combined_rate"] == "1250"
    house_check = next(item for item in validation["checks"] if item["key"] == "house_compensation")
    assert house_check["expected"] == "1250"
    assert house_check["actual"] == "1250"
    assert house_check["status"] == "match"


def test_building_compensation_rows_for_tongdao_county_use_huaihua_catalog():
    rows = building_compensation_rows_for_county(BASE_DIR, "通道县")

    # i1（CH-1 决策）：默认表单行统一为范例 4 项 key（与 _default_building_compensation_rows 一致），
    # 怀化特有的装修/生产生活设施只进「从政策目录添加」。
    assert len(rows) == 4
    row_keys = {row["key"] for row in rows}
    assert {"house_compensation", "vacating_award", "moving_fee", "transition_fee"} == row_keys
    assert "decoration_compensation" not in row_keys
    assert "grave_compensation" not in row_keys
    assert all(row.get("source_path") for row in rows)
    assert any("怀化" in (row.get("source_path") or "") for row in rows)

    # 怀化特有装修仍可从政策目录添加。
    catalog_keys = {entry.get("row_key") for entry in building_compensation_add_catalog(BASE_DIR, "通道县")}
    assert "decoration_compensation" in catalog_keys


def test_i4_long_location_and_valuation_date_export_top_level_hotspot_fields():
    # i4：长地名（通道县双江镇城南街）与估价期日须导出顶层 field 路径，
    # 以便前端 focus_item_land_location_full / focus_item_valuation_date 命中跳转。
    long_location = "通道县双江镇城南街123号"
    result = calculate_cost_approximation(
        {
            "county_name": "通道县",
            "valuation_date": "2026-06-01",
            "land_location_full": long_location,
            "land_usage": "居住用地",
        },
        BASE_DIR,
    )

    basis_sources = result["narrative_segment_sources"]["cost_approx_basis_intro"]
    location_source = next(s for s in basis_sources if s["field"] == "land_location_full")
    valuation_source = next(s for s in basis_sources if s["field"] == "valuation_date")

    # field 必须是顶层键（无 cost_approx_analysis. 前缀），与前端 focus_item_* id 一致。
    assert location_source["field"] == "land_location_full"
    assert location_source["text"] == long_location
    assert valuation_source["field"] == "valuation_date"
    assert valuation_source["text"] == "2026-06-01"
    # 正文确实包含长地名，热区文本才能命中。
    assert long_location in result["generated_narratives"]["cost_approx_basis_intro"]


def test_local_compensation_policy_document_links_yongzhou_pdf_for_dao_county():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "acquisition_land_class": "水田",
            "land_usage": "居住用地",
        },
        BASE_DIR,
    )
    local_policy = next(item for item in result["policy_documents"] if item["key"] == "local_compensation_policy")

    assert "永州市人民政府关于印发" in local_policy["source_path"]
    assert local_policy["source_path"].endswith(".xlsx")
    assert len(local_policy["source_hash"]) == 64


def test_suggest_compensation_zone_matches_wanjiazhuang_xiadong():
    suggestion = suggest_compensation_zone(
        "道县万家庄街道办事处下洞村",
        BASE_DIR,
        county_name="道县",
        city_name="永州市",
    )

    assert suggestion["matched"] is True
    assert suggestion["compensation_zone"] == "Ⅰ"
    assert suggestion["confidence"] in {"village", "township_partial", "township"}
    assert "永州市农用地补偿区片划分表.docx" in suggestion["source_path"]
    assert len(suggestion["source_hash"]) == 64
    assert "万家庄" in suggestion["match_detail"] or "下洞" in suggestion["match_detail"]


def test_applicable_basis_applies_zone_suggestion_from_land_location_full():
    basis = applicable_cost_basis(
        {
            "county_name": "道县",
            "valuation_date": "2026-01-01",
            "acquisition_land_class": "水田",
            "land_location_full": "道县万家庄街道办事处下洞村",
        },
        BASE_DIR,
    )

    assert basis["compensation_zone"] == "Ⅰ"
    assert basis["compensation_zone_override"] is False
    assert basis["compensation_zone_suggestion"]["matched"] is True
    assert basis["province_compensation"]["base_per_mu"] == "66300"


def test_compensation_zone_override_keeps_manual_zone_when_location_unchanged():
    basis = applicable_cost_basis(
        {
            "county_name": "道县",
            "valuation_date": "2026-01-01",
            "acquisition_land_class": "水田",
            "land_location_full": "道县万家庄街道办事处下洞村",
            "cost_approx_analysis": {
                "compensation_zone": "Ⅱ",
                "basis_land_location_full": "道县万家庄街道办事处下洞村",
            },
        },
        BASE_DIR,
    )

    assert basis["compensation_zone_suggestion"]["compensation_zone"] == "Ⅰ"
    assert basis["compensation_zone"] == "Ⅱ"
    assert basis["compensation_zone_override"] is True
    assert basis["province_compensation"]["base_per_mu"] == "61800"


def test_applicable_basis_reads_dao_county_zone_and_freezes_source_hash():
    basis = applicable_cost_basis(
        {
            "county_name": "道县",
            "valuation_date": "2025年11月26日",
            "acquisition_land_class": "林地",
            "cost_approx_analysis": {"compensation_zone": "Ⅱ"},
        },
        BASE_DIR,
    )

    province = basis["province_compensation"]
    assert province["base_per_mu"] == "61800"
    assert province["coefficient"] == "0.67"
    assert province["recommended_amount_per_sqm"] == "62.11"
    assert province["applicable"] is True
    assert len(province["source_hash"]) == 64


def test_applicable_basis_matches_county_name_inside_long_location_text():
    basis = applicable_cost_basis(
        {
            "county_name": "道县西洲街道",
            "valuation_date": "2026-06-01",
            "acquisition_land_class": "水田",
            "cost_approx_analysis": {"compensation_zone": "Ⅰ"},
        },
        BASE_DIR,
    )

    province = basis["province_compensation"]
    assert province["county"] == "道县"
    assert province["base_per_mu"] == "66300"
    assert province["coefficient"] == "1"
    assert province["recommended_amount_per_sqm"] == "99.45"


def test_basis_rejects_policy_published_after_valuation_date():
    basis = applicable_cost_basis(
        {
            "county_name": "道县",
            "valuation_date": "2023-12-31",
            "acquisition_land_class": "林地",
        },
        BASE_DIR,
    )

    assert basis["province_compensation"]["applicable"] is False
    assert basis["province_compensation"]["recommended_amount_per_sqm"] == "0.00"
    assert any("不得直接采用" in item for item in basis["warnings"])


def test_mixed_usage_calculation_uses_structured_attachment_and_usage_specific_location_rates():
    data = _mixed_usage_payload()
    analysis = calculate_cost_approximation(data, BASE_DIR)
    for item in (
        analysis["policy_documents"]
        + analysis["acquisition_items"]
        + analysis["tax_items"]
        + analysis["development_items"]
        + analysis["usage_scenarios"]
        + analysis["building_compensation_rows"]
        + analysis["resettlement_population_cases"]
        + analysis["risk_items"]
    ):
        item["confirmed"] = True
    analysis["external_results"] = [
        {
            "key": "attachment-result",
            "result_type": "attachment_compensation",
            "label": "附着物补偿外部测算",
            "value": "138.81",
            "unit": "元/平方米",
            "source_hash": "evidence-hash",
            "confirmed": True,
        }
    ]
    analysis["location_factors"] = [
        {
            "usage_key": "commercial",
            "group": "区域及个别因素",
            "label": "商业用途综合区位修正",
            "correction_rate": "11.31",
            "confirmed": True,
        },
        {
            "usage_key": "residential",
            "group": "区域及个别因素",
            "label": "住宅用途综合区位修正",
            "correction_rate": "12.88",
            "confirmed": True,
        },
    ]
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)

    assert result["complete"] is True
    assert result["totals"] == {
        "acquisition_total": "103.65",
        "tax_total": "155.60",
        "acquisition_and_tax_total": "259.25",
        "development_total": "82.00",
        "interest": "9.01",
    }
    attachment = next(item for item in result["acquisition_items"] if item["key"] == "ground_attachment")
    assert attachment["amount_per_sqm"] == "4.20"
    assert attachment["source"] == "compat_derived"
    prices = {item["key"]: item["final_price"] for item in result["usage_results"]}
    assert prices == {"commercial": "573.9", "residential": "600.0"}
    assert "cost_approx_price" not in result


def test_unconfirmed_external_result_is_ignored_by_current_structured_cost_flow():
    data = _mixed_usage_payload()
    data["cost_approx_analysis"] = {
        "external_results": [
            {
                "key": "pending-result",
                "result_type": "attachment_compensation",
                "label": "待确认附着物补偿",
                "value": "138.81",
                "source_hash": "evidence-hash",
                "confirmed": False,
            }
        ]
    }

    result = calculate_cost_approximation(data, BASE_DIR)

    attachment = next(item for item in result["acquisition_items"] if item["key"] == "ground_attachment")
    assert attachment["amount_per_sqm"] == "4.20"
    assert attachment["source"] == "compat_derived"
    assert not any("外部软件测算结果尚未确认" in item["message"] for item in result["warnings"])


def test_confirmed_cost_items_rematch_when_compensation_zone_changes():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_class": "水田",
        "land_usage": "居住用地",
        "land_development_set": "五通一平",
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    for item in (
        analysis["policy_documents"]
        + analysis["acquisition_items"]
        + analysis["tax_items"]
        + analysis["development_items"]
    ):
        item["confirmed"] = True

    data["cost_approx_analysis"] = analysis
    data["cost_approx_analysis"]["compensation_zone"] = "Ⅱ"
    result = calculate_cost_approximation(data, BASE_DIR)

    land_comp = next(item for item in result["acquisition_items"] if item["key"] == "land_compensation")
    attachment = next(item for item in result["acquisition_items"] if item["key"] == "ground_attachment")
    assert result["basis_compensation_zone"] == "Ⅱ"
    assert land_comp["standard_value"] == "61800"
    assert land_comp["amount_per_sqm"] == "92.70"
    assert land_comp["confirmed"] is False
    assert attachment["standard_value"] == "2800"
    assert attachment["amount_per_sqm"] == "4.20"
    assert all(item["standard_value"] not in (None, "") for item in result["tax_items"])
    assert any("系统已按新口径重新匹配标准值" in item["message"] for item in result["warnings"])


def test_confirmed_cost_items_rematch_when_acquisition_land_subclass_changes():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_class": "耕地",
        "acquisition_land_subclass": "水田",
        "land_usage": "居住用地",
        "land_development_set": "五通一平",
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    for item in analysis["acquisition_items"] + analysis["tax_items"]:
        item["confirmed"] = True

    data["acquisition_land_class"] = "林地"
    data["acquisition_land_subclass"] = "乔木林地"
    data["cost_approx_analysis"] = analysis
    result = calculate_cost_approximation(data, BASE_DIR)

    land_comp = next(item for item in result["acquisition_items"] if item["key"] == "land_compensation")
    attachment = next(item for item in result["acquisition_items"] if item["key"] == "ground_attachment")
    taxes = {item["key"]: item for item in result["tax_items"]}
    assert result["basis_land_class"] == "乔木林地"
    assert land_comp["coefficient"] == "0.67"
    assert land_comp["amount_per_sqm"] == "66.63"
    assert attachment["standard_value"] == "4000"
    assert taxes["farmland_occupation_tax"]["coefficient"] == "0.8"
    assert taxes["farmland_occupation_tax"]["amount_per_sqm"] == "20.00"
    assert taxes["farmland_reclamation_fee"]["enabled"] is False
    assert taxes["forest_restoration_fee"]["enabled"] is True
    assert taxes["forest_restoration_fee"]["standard_value"] == ""
    assert all(not item["confirmed"] for item in result["tax_items"])


def test_confirmed_development_items_rematch_when_development_degree_changes():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_class": "水田",
        "land_usage": "居住用地",
        "land_development_set": "五通一平",
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    for item in analysis["development_items"]:
        item["confirmed"] = True

    data["land_development_set"] = "七通一平"
    data["cost_approx_analysis"] = analysis
    result = calculate_cost_approximation(data, BASE_DIR)

    development = {item["label"]: item for item in result["development_items"]}
    assert result["basis_development_set"] == "七通一平"
    assert {"通路", "通电", "供水", "排水", "通讯", "供气", "供热", "场地平整"} == set(development)
    assert development["供气"]["standard_value"] == "8"
    assert development["供热"]["standard_value"] == "8"
    assert result["totals"]["development_total"] == "98.00"
    assert all(not item["confirmed"] for item in development.values())


def test_confirmed_risk_items_derive_land_reduction_rate():
    data = _mixed_usage_payload()
    analysis = calculate_cost_approximation(data, BASE_DIR)
    commercial = next(item for item in analysis["usage_scenarios"] if item["key"] == "commercial")
    commercial["safe_rate"] = "1.4"
    analysis["risk_items"] = [
        {
            "usage_key": "commercial",
            "group": "政策风险",
            "label": "政策风险综合值",
            "weight": "0.4",
            "level": "较严重",
            "adjustment_rate": "4",
            "confirmed": True,
        },
        {
            "usage_key": "commercial",
            "group": "市场风险",
            "label": "市场风险综合值",
            "weight": "0.6",
            "level": "最严重",
            "adjustment_rate": "6",
            "confirmed": True,
        },
    ]
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)
    commercial = next(item for item in result["usage_scenarios"] if item["key"] == "commercial")

    assert commercial["reduction_rate"] == "6.60"
    assert any(item["key"] == "cost_risk_result_rows" for item in result["tables"])


def test_confirmed_policy_is_frozen_and_warns_when_valuation_date_changes():
    data = _mixed_usage_payload()
    analysis = calculate_cost_approximation(data, BASE_DIR)
    analysis["policy_documents"][0]["confirmed"] = True
    data["cost_approx_analysis"] = analysis
    data["valuation_date"] = "2023-12-31"

    result = calculate_cost_approximation(data, BASE_DIR)

    policy = result["policy_documents"][0]
    assert policy["valuation_date"] == "2025-12-04"
    assert policy["applicable"] is True
    assert result["complete"] is False
    assert any("冻结政策依据需重新校核" in item["message"] for item in result["warnings"])


def test_confirmed_cost_basis_rematches_zone_and_invalidates_affected_items():
    data = _mixed_usage_payload()
    analysis = calculate_cost_approximation(data, BASE_DIR)
    compensation = next(item for item in analysis["acquisition_items"] if item["key"] == "land_compensation")
    compensation["confirmed"] = True
    analysis["compensation_zone"] = "Ⅱ"
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)
    compensation = next(item for item in result["acquisition_items"] if item["key"] == "land_compensation")

    assert compensation["standard_value"] == "61800"
    assert compensation["amount_per_sqm"] == "92.70"
    assert compensation["confirmed"] is False
    assert result["basis_compensation_zone"] == "Ⅱ"
    assert any("系统已按新口径重新匹配标准值" in item["message"] for item in result["warnings"])


def test_confirmed_cost_item_backfills_missing_standard_without_overwriting_amount():
    data = _mixed_usage_payload()
    data["cost_approx_analysis"] = {
        "compensation_zone": "Ⅰ",
        "acquisition_items": [
            {
                "key": "land_compensation",
                "label": "征地补偿费和安置补助费",
                "category": "acquisition",
                "standard_value": "",
                "coefficient": "",
                "amount_per_sqm": "88.88",
                "confirmed": True,
                "enabled": True,
            }
        ],
    }

    result = calculate_cost_approximation(data, BASE_DIR)
    compensation = next(item for item in result["acquisition_items"] if item["key"] == "land_compensation")

    assert compensation["standard_value"] == "66300"
    assert compensation["coefficient"] == "1"
    assert compensation["amount_per_sqm"] == "88.88"


def test_manual_land_compensation_coefficient_recalculates_amount_and_narrative():
    data = _mixed_usage_payload()
    analysis = calculate_cost_approximation(data, BASE_DIR)
    compensation = next(item for item in analysis["acquisition_items"] if item["key"] == "land_compensation")
    compensation["confirmed"] = True
    compensation["coefficient"] = "0"
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)
    compensation = next(item for item in result["acquisition_items"] if item["key"] == "land_compensation")

    assert compensation["standard_value"] == "66300"
    assert compensation["coefficient"] == "0"
    assert compensation["amount_per_sqm"] == "0.00"
    assert result["totals"]["acquisition_total"] == "4.20"
    narrative = result["generated_narratives"]["cost_approx_acquisition_narrative"]
    assert "地类修正系数为0" not in narrative
    assert "经估价师确认" not in narrative
    assert "不计取" not in narrative
    assert "征地补偿费和安置补助费=0.00元/平方米" not in narrative


def test_baozhen_street_residential_sample_uses_simple_location_sum_and_matches_price():
    data = dict(BAOZHEN_SAMPLE_DATA)
    analysis = calculate_cost_approximation(data, BASE_DIR)
    _confirm_baozhen_analysis(analysis)
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)

    residential = result["usage_results"][0]
    scenario = result["usage_scenarios"][0]
    assert scenario["profit_rate"] == "20"
    assert scenario["value_added_rate"] == "35"
    assert scenario["reduction_rate"] == "6.5"
    assert residential["profit"] == "68.25"
    assert residential["value_added_income"] == "146.48"
    assert residential["location_correction_rate"] == "21.00"
    assert residential["final_price"] == "675.3"
    assert result["complete"] is True
    assert "投资利润=（103.65+155.60+82.00）×20%=68.25元/平方米" in result["generated_narratives"]["cost_approx_profit_narrative"]
    acquisition_narrative = result["generated_narratives"]["cost_approx_acquisition_narrative"]
    assert "地类修正系数为1" not in acquisition_narrative
    assert "征地补偿费和安置补助费=66300×0.0015=99.45元/平方米" in acquisition_narrative
    assert [item["key"] for item in result["tables"]] == [
        "cost_building_compensation_rows",
        "cost_resettlement_population_rows",
        "cost_acquisition_tax_rows",
        "cost_development_rows",
        "cost_risk_impact_rows",
        "cost_risk_weight_rows",
        "cost_risk_assignment_rows",
        "cost_risk_result_rows",
        "cost_location_rule_rows",
        "cost_location_rows",
    ]


def test_baozhen_reference_attachment_inputs_match_report_price_942_5():
    data = dict(BAOZHEN_SAMPLE_DATA)
    analysis = calculate_cost_approximation(data, BASE_DIR)
    analysis["resettlement_population_cases"] = [dict(item) for item in BAOZHEN_REFERENCE_POPULATION_CASES]
    _confirm_baozhen_analysis(analysis)
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)
    attachment = result["attachment_compensation_analysis"]
    acquisition_items = {item["key"]: item for item in result["acquisition_items"]}

    assert attachment["building_compensation_per_person"] == "98000.00"
    assert attachment["average_population_per_ha"] == "12.82"
    assert attachment["building_compensation_per_sqm"] == "125.64"
    assert attachment["green_seedling_per_sqm"] == "4.20"
    assert attachment["attachment_compensation_per_sqm"] == "129.84"
    assert acquisition_items["land_compensation"]["amount_per_sqm"] == "99.45"
    assert acquisition_items["building_compensation"]["amount_per_sqm"] == "125.64"
    assert acquisition_items["seedling_compensation"]["amount_per_sqm"] == "4.20"
    assert result["totals"]["acquisition_total"] == "229.29"
    assert result["totals"]["tax_total"] == "155.60"
    assert result["totals"]["development_total"] == "82.00"
    assert result["totals"]["interest"] == "12.78"

    residential = result["usage_results"][0]
    assert residential["profit"] == "93.38"
    assert residential["value_added_income"] == "200.57"
    assert residential["location_correction_rate"] == "21.00"
    assert residential["final_price"] == "924.7"
    assert result["complete"] is True


def test_new_cost_analysis_defaults_to_confirmed_cultivated_paddy_and_derives_usage_label():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_usage_key": "住宅用地",
            "land_usage_price_class": "居住用地",
            "land_usage": "不应覆盖用途场景",
        },
        BASE_DIR,
    )

    assert result["acquisition_land_class"] == "耕地"
    assert result["acquisition_land_subclass"] == "水田"
    assert result["acquisition_land_class_confirmed"] is True
    assert result["usage_scenarios"][0]["label"] == "居住用地"
    assert "被征用的土地为耕地" in result["generated_narratives"]["cost_approx_basis_intro"]


def test_baozhen_attachment_calculation_table_shapes_and_hotspot_sources():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_location_full": "道县西洲街道宝珍街六栋九号",
            "land_usage": "居住用地",
            "land_development_set": "五通一平",
            "cost_approx_analysis": {
                "resettlement_population_cases": [
                    {"key": "case_a", "name": "案例A", "location": "道县", "land_area_ha": "10", "population": "100", "confirmed": True},
                    {"key": "case_b", "name": "案例B", "location": "道县", "land_area_ha": "20", "population": "220", "confirmed": True},
                    {"key": "case_c", "name": "案例C", "location": "道县", "land_area_ha": "30", "population": "360", "confirmed": True},
                ],
            },
        },
        BASE_DIR,
    )

    attachment = result["attachment_compensation_analysis"]
    assert attachment["building_compensation_per_person"] == "98000.00"
    assert attachment["average_population_per_ha"] == "11.00"
    assert attachment["attachment_compensation_per_sqm"] == "112.00"

    tables = {item["key"]: item for item in result["tables"]}
    assert tables["cost_building_compensation_rows"]["columns"] == [
        "补偿项目名称",
        "附着物补偿标准（元/平方米）",
        "计算基数",
        "人均合法建筑面积（平方米）",
        "补偿金额（元）",
        "备注",
    ]
    assert tables["cost_resettlement_population_rows"]["columns"] == [
        "项目名称",
        "位置",
        "用地面积（公顷）",
        "安置农业人口（人）",
        "安置人口数折合人/公顷",
    ]
    assert tables["cost_acquisition_tax_rows"]["columns"][0] == "土地取得费（元/平方米）"
    assert tables["cost_development_rows"]["rows"][0]["cells"][0] == "费用（元/平方米）"

    sources = result["narrative_segment_sources"]
    basis_fields = {item["field"] for item in sources["cost_approx_basis_intro"]}
    acquisition_fields = {item["field"] for item in sources["cost_approx_acquisition_intro"]}
    tax_fields = {item["field"] for item in sources["cost_approx_tax_narrative"]}
    assert {"acquisition_land_class", "valuation_date", "cost_approx_analysis.effective_local_city"} <= basis_fields
    assert {"county_name", "acquisition_land_subclass"} <= acquisition_fields
    assert all(
        not str(item.get("text", "")).startswith("《中华人民共和国土地管理法》")
        for item in sources["cost_approx_acquisition_intro"]
    )
    assert "valuation_basis_docs_list" in tax_fields
    assert "《中华人民共和国土地管理法》（根据2019年8月26日" in result["generated_narratives"]["cost_approx_acquisition_intro"]


def test_manual_policy_replacement_disables_recommendation_and_invalidates_affected_fee():
    data = _mixed_usage_payload()
    analysis = calculate_cost_approximation(data, BASE_DIR)
    analysis["policy_documents"].append(
        {
            "key": "manual_province_policy",
            "name": "人工替换征地补偿政策",
            "role": "province_compensation",
            "source_type": "manual",
            "reference_text": "人工替换征地补偿政策",
            "enabled": True,
            "replaces_key": "hunan_compensation_2024",
            "applicable": True,
            "confirmed": False,
        }
    )
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)
    system_policy = next(item for item in result["policy_documents"] if item["key"] == "hunan_compensation_2024")
    fee = next(item for item in result["acquisition_items"] if item["key"] == "land_compensation")

    assert system_policy["enabled"] is False
    assert fee["policy_key"] == "manual_province_policy"
    assert fee["standard_value"] == ""
    assert fee["amount_per_sqm"] == ""
    assert fee["confirmed"] is False


def test_bayi_fuel_station_cost_workbook_gold_standard_with_config_and_cascade_rounding():
    data = {
        "county_name": "道县",
        "local_city": "永州市",
        "valuation_date": "2026-01-01",
        "land_location_full": "道县万家庄街道办事处下洞村秀鱼塘",
        "acquisition_land_class": "耕地",
        "acquisition_land_subclass": "水田",
        "land_usage": "商业服务业用地",
        "land_usage_key": "商服用地",
        "land_usage_price_class": "商业服务业用地",
        "land_use_term_years": "15.27",
        "land_development_set": "五通一平",
        "cost_approx_analysis": {
            "compensation_zone": "Ⅰ",
            "development_cycle_years": "1",
            "interest_rate": "3",
            "risk_mode": "analysis",
        },
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    for item in analysis["policy_documents"] + analysis["acquisition_items"] + analysis["tax_items"] + analysis["development_items"]:
        item["confirmed"] = True
    for row in analysis["building_compensation_rows"]:
        row["confirmed"] = True
    analysis["resettlement_population_cases"] = [
        {"key": "case_a", "name": "案例A", "location": "道县", "land_area_ha": "1", "population": "12.82", "confirmed": True},
        {"key": "case_b", "name": "案例B", "location": "道县", "land_area_ha": "1", "population": "12.82", "confirmed": True},
        {"key": "case_c", "name": "案例C", "location": "道县", "land_area_ha": "1", "population": "12.82", "confirmed": True},
    ]
    scenario = analysis["usage_scenarios"][0]
    scenario.update(
        {
            "confirmed": True,
            "use_term_years": "15.27",
            "profit_rate": "14",
            "value_added_rate": "40",
            "safe_rate": "1.46",
            "reduction_rate": "6.7",
        }
    )
    for item in analysis["risk_items"]:
        item["level"] = "A"
        item["adjustment_rate"] = "8"
        item["confirmed"] = True
    for group in analysis["risk_groups"]:
        group["override_enabled"] = True
        group["confirmed"] = True
        if "政策" in group["label"]:
            group["override_value"] = "6.00"
        elif "经济" in group["label"]:
            group["override_value"] = "5.50"
        elif "社会" in group["label"]:
            group["override_value"] = "4.00"
    amp2_used = 0
    amp1_used = 0
    for factor in analysis["location_factors"]:
        levels = factor.get("levels") or ["优", "较优", "一般", "较劣", "劣"]
        if factor.get("grade_amplitude") == "2":
            factor["level"] = levels[0] if amp2_used < 2 else levels[1]
            amp2_used += 1
        else:
            factor["level"] = levels[1] if amp1_used < 2 else levels[2]
            amp1_used += 1
        factor["description"] = factor["level"]
        factor["confirmed"] = True
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)
    usage_result = result["usage_results"][0]
    acquisition = {item["key"]: item for item in result["acquisition_items"]}
    taxes = {item["key"]: item for item in result["tax_items"]}

    assert result["policy_config_version"]
    assert acquisition["land_compensation"]["amount_per_sqm"] == "99.45"
    assert acquisition["building_compensation"]["amount_per_sqm"] == "125.64"
    assert acquisition["seedling_compensation"]["amount_per_sqm"] == "4.20"
    assert result["totals"]["acquisition_total"] == "229.29"
    assert taxes["water_conservancy_fund"]["amount_per_sqm"] == "1.60"
    assert taxes["farmland_occupation_tax"]["amount_per_sqm"] == "25.00"
    assert taxes["farmland_reclamation_fee"]["amount_per_sqm"] == "99.00"
    assert taxes["social_security_fund"]["amount_per_sqm"] == "30.00"
    assert result["totals"]["tax_total"] == "155.60"
    assert result["totals"]["development_total"] == "82.00"
    assert result["totals"]["interest"] == "12.78"
    assert usage_result["profit"] == "65.36"
    assert usage_result["cost_price"] == "545.03"
    assert usage_result["value_added_income"] == "218.01"
    assert usage_result["unlimited_price"] == "763.04"
    assert usage_result["term_correction_factor"] == "0.6285"
    assert usage_result["comparable_price"] == "479.57"
    assert usage_result["location_correction_rate"] == "16.00"
    assert usage_result["final_price"] == "556.3"
    assert "经估价师确认" not in result["generated_narratives"]["cost_approx_solve_narrative"]


def test_disabled_tax_items_no_empty_headers_continuous_numbering():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_class": "建设用地",
        "acquisition_land_subclass": "其它建设用地",
        "land_usage": "商服",
        "land_development_set": "五通一平",
        "cost_approx_analysis": {
            "tax_items": [
                {"key": "water_conservancy_fund", "label": "水利建设基金", "enabled": True, "amount_per_sqm": "1.60"},
                {"key": "farmland_occupation_tax", "label": "耕地占用税", "enabled": False},
                {"key": "farmland_reclamation_fee", "label": "耕地开垦费", "enabled": False},
                {"key": "social_security_fund", "label": "社会保障资金", "enabled": True, "amount_per_sqm": "30.00"},
                {"key": "forest_restoration_fee", "label": "森林植被恢复费", "enabled": False}
            ],
            "acquisition_items": [],
            "development_items": [],
            "totals": {
                "acquisition_total": "100.00",
                "tax_total": "31.60",
                "development_total": "80.00",
                "interest": "10.00"
            },
            "usage_scenarios": {},
            "usage_results": {}
        }
    }
    
    from src.services.cost_approximation import _build_narratives
    analysis = data["cost_approx_analysis"]
    narratives = _build_narratives(data, analysis)
    
    tax_text = narratives["cost_approx_tax_narrative"]
    
    assert "耕地占用税" not in tax_text
    assert "耕地开垦费" not in tax_text
    assert "森林植被恢复费" not in tax_text
    
    assert "①水利建设基金" in tax_text
    assert "②社会保障资金" in tax_text
    assert "③" not in tax_text
    assert "1.60＋30.00" in tax_text
    assert "31.60" in tax_text


def test_development_survey_cases_default_and_average():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_development_set": "五通一平",
        },
        BASE_DIR,
    )

    cases = result["development_survey_cases"]
    assert len(cases) == 3
    assert result["development_survey_analysis"]["status"] == "pending"

    cases[0].update(
        {
            "name": "案例A",
            "location": "道县城区",
            "survey_date": "2026-01-01",
            "source_type": "询价记录",
            "development_set": "五通一平",
            "total_per_sqm": "80",
            "confirmed": True,
        }
    )
    cases[1].update({"name": "案例B", "total_per_sqm": "82", "confirmed": True})
    cases[2].update({"name": "案例C", "total_per_sqm": "84", "confirmed": True})
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_development_set": "五通一平",
            "cost_approx_analysis": {**result, "development_survey_cases": cases},
        },
        BASE_DIR,
    )

    assert result["development_survey_analysis"]["average_total_per_sqm"] == "82.00"
    assert result["development_survey_analysis"]["status"] == "ready"
    assert not any("尚未附项目调查资料" in item["message"] for item in result["warnings"])
    dev_item = next(item for item in result["development_items"] if item["label"] == "通路")
    assert dev_item["source"] == "project_survey_pending"


def test_gas_station_extraction():
    from src.services.cost_approximation import extract_gas_station_location, extract_gas_station_details
    
    # Test case 1: normal gas station other_info and address
    address = "永州市零陵区萍阳南路"
    other_info = "该加油站有双层防爆汽油罐3个，每个30立方米。双层防爆柴油罐2个，每个50立方米。双枪加油机4台，加注机1台。有罩棚面积100.5平方米，罐区面积50.8平方米，站房及辅助用房面积120.50平方米，便利店面积35.5平方米。"
    
    loc = extract_gas_station_location(address, other_info)
    assert loc["city"] == "永州市"
    assert loc["district"] == "零陵区"
    assert loc["detail"] == "萍阳南路"
    
    details = extract_gas_station_details(other_info)
    assert details["canopy_area"] == 100.5
    assert details["tank_area"] == 50.8
    assert details["office_area"] == 120.5
    assert details["store_area"] == 35.5
    assert details["dispenser_count"] == 4
    assert details["loader_count"] == 1
    assert len(details["tanks"]) == 5  # 3 petrol + 2 diesel
    
    petrol_tanks = [t for t in details["tanks"] if t["type"] == "汽油罐"]
    diesel_tanks = [t for t in details["tanks"] if t["type"] == "柴油罐"]
    assert len(petrol_tanks) == 3
    assert all(t["volume"] == 30.0 and t["is_double_wall"] for t in petrol_tanks)
    assert len(diesel_tanks) == 2
    assert all(t["volume"] == 50.0 and t["is_double_wall"] for t in diesel_tanks)

    # Test case 2: fallback and no info
    loc_empty = extract_gas_station_location("", "湖南省永州市零陵区芝山路123号")
    assert loc_empty["city"] == "永州市"
    assert loc_empty["district"] == "零陵区"
    assert loc_empty["detail"] == "芝山路123号"
    
    details_empty = extract_gas_station_details("无任何有用信息")
    assert details_empty["canopy_area"] is None
    assert details_empty["tanks"] == []




def test_disabled_tax_items_exclude_empty_headers_and_renumber_correctly():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_class": "建设用地",
        "acquisition_land_subclass": "裸地",
        "land_usage": "商业服务业用地",
        "land_development_set": "五通一平",
    }
    result = calculate_cost_approximation(data, BASE_DIR)
    tax_narrative = result["generated_narratives"]["cost_approx_tax_narrative"]
    
    # 耕地开垦费和森林植被恢复费被禁用，不应该出现在大标题中
    assert "③耕地开垦费" not in tax_narrative
    assert "耕地开垦费" not in tax_narrative
    assert "⑤森林植被恢复费" not in tax_narrative
    assert "森林植被恢复费" not in tax_narrative
    
    # 水利建设基金、耕地占用税、社会保障资金应是启用的，且序号应连续为 ①、②、③
    assert "①水利建设基金" in tax_narrative
    assert "②耕地占用税" in tax_narrative
    assert "③社会保障资金" in tax_narrative
    
    # 各项税费合计公式不能带有 ＋0 或者多余的零值符号
    assert "则：各项税费合计为=" in tax_narrative


def _cultivated_cost_data(**overrides):
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_class": "耕地",
        "acquisition_land_subclass": "水田",
        "land_usage": "商服",
        "land_development_set": "五通一平",
    }
    data.update(overrides)
    return data


def test_farmland_reclamation_fee_defaults_to_medium_paddy_for_paddy():
    result = calculate_cost_approximation(_cultivated_cost_data(), BASE_DIR)
    reclamation = next(item for item in result["tax_items"] if item["key"] == "farmland_reclamation_fee")
    assert reclamation["grade_name"] == "中等水田"
    assert reclamation["standard_value"] == "6.6"
    assert reclamation["amount_per_sqm"] == "99.00"
    assert reclamation["rule_key"] == "hunan_farmland_reclamation_medium_paddy_2019"


@pytest.mark.parametrize(
    ("grade_name", "standard_value", "amount_per_sqm", "rule_key"),
    [
        ("优等水田", "7.8", "117.00", "hunan_farmland_reclamation_superior_paddy_2019"),
        ("高等水田", "7.4", "111.00", "hunan_farmland_reclamation_high_paddy_2019"),
        ("中等水田", "6.6", "99.00", "hunan_farmland_reclamation_medium_paddy_2019"),
        ("低等水田", "5.9", "88.50", "hunan_farmland_reclamation_low_paddy_2019"),
    ],
)
def test_farmland_reclamation_fee_matches_paddy_grade(grade_name, standard_value, amount_per_sqm, rule_key):
    data = _cultivated_cost_data(
        cost_approx_analysis={
            "tax_items": [
                {
                    "key": "farmland_reclamation_fee",
                    "label": "耕地开垦费",
                    "grade_name": grade_name,
                    "enabled": True,
                }
            ]
        }
    )
    result = calculate_cost_approximation(data, BASE_DIR)
    reclamation = next(item for item in result["tax_items"] if item["key"] == "farmland_reclamation_fee")
    assert reclamation["grade_name"] == grade_name
    assert reclamation["standard_value"] == standard_value
    assert reclamation["amount_per_sqm"] == amount_per_sqm
    assert reclamation["rule_key"] == rule_key


def test_farmland_reclamation_fee_matches_dryland_grade():
    data = _cultivated_cost_data(
        acquisition_land_subclass="旱地",
        cost_approx_analysis={
            "tax_items": [
                {
                    "key": "farmland_reclamation_fee",
                    "label": "耕地开垦费",
                    "grade_name": "旱地",
                    "enabled": True,
                }
            ]
        },
    )
    result = calculate_cost_approximation(data, BASE_DIR)
    reclamation = next(item for item in result["tax_items"] if item["key"] == "farmland_reclamation_fee")
    assert reclamation["grade_name"] == "旱地"
    assert reclamation["standard_value"] == "3.8"
    assert reclamation["amount_per_sqm"] == "57.00"
    assert reclamation["rule_key"] == "hunan_farmland_reclamation_dryland_2019"


def test_farmland_reclamation_fee_recalculates_when_grade_switches():
    data = _cultivated_cost_data(
        cost_approx_analysis={
            "tax_items": [
                {
                    "key": "farmland_reclamation_fee",
                    "label": "耕地开垦费",
                    "grade_name": "中等水田",
                    "standard_value": "6.6",
                    "amount_per_sqm": "99.00",
                    "rule_key": "hunan_farmland_reclamation_medium_paddy_2019",
                    "enabled": True,
                    "confirmed": False,
                }
            ]
        }
    )
    result = calculate_cost_approximation(data, BASE_DIR)
    reclamation = next(item for item in result["tax_items"] if item["key"] == "farmland_reclamation_fee")
    assert reclamation["amount_per_sqm"] == "99.00"

    reclamation["grade_name"] = "优等水田"
    reclamation["confirmed"] = False
    data["cost_approx_analysis"]["tax_items"] = [reclamation]
    switched = calculate_cost_approximation(data, BASE_DIR)
    updated = next(item for item in switched["tax_items"] if item["key"] == "farmland_reclamation_fee")
    assert updated["grade_name"] == "优等水田"
    assert updated["standard_value"] == "7.8"
    assert updated["amount_per_sqm"] == "117.00"
    assert updated["rule_key"] == "hunan_farmland_reclamation_superior_paddy_2019"


def test_water_conservancy_fund_recalculates_when_paid_land_grade_switches():
    data = _cultivated_cost_data(
        cost_approx_analysis={
            "tax_items": [
                {
                    "key": "water_conservancy_fund",
                    "label": "水利建设基金",
                    "grade_name": "十三等",
                    "standard_value": "10",
                    "amount_per_sqm": "1.60",
                    "rule_key": "hunan_water_conservancy_fund_2011",
                    "enabled": True,
                    "confirmed": False,
                }
            ]
        }
    )
    result = calculate_cost_approximation(data, BASE_DIR)
    water = next(item for item in result["tax_items"] if item["key"] == "water_conservancy_fund")
    assert water["grade_name"] == "十三等"
    assert water["amount_per_sqm"] == "1.60"

    water["grade_name"] = "十二等"
    water["confirmed"] = False
    data["cost_approx_analysis"]["tax_items"] = [water]
    switched = calculate_cost_approximation(data, BASE_DIR)
    updated = next(item for item in switched["tax_items"] if item["key"] == "water_conservancy_fund")
    assert updated["grade_name"] == "十二等"
    assert updated["standard_value"] == "20.00"
    assert updated["amount_per_sqm"] == "2.00"
    warning_messages = [
        warning if isinstance(warning, str) else str(warning.get("message") or "")
        for warning in (switched.get("warnings") or [])
    ]
    assert any("新增建设用地土地有偿使用费" in message for message in warning_messages)
    assert any("水利建设基金" in message for message in warning_messages)
    assert any("十三等" in message for message in warning_messages)


def _forest_cost_data(**overrides):
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_class": "林地",
        "acquisition_land_subclass": "乔木林地",
        "land_usage": "商服",
        "land_development_set": "五通一平",
    }
    data.update(overrides)
    return data


def test_forest_restoration_fee_disabled_for_non_forest_land():
    result = calculate_cost_approximation(_cultivated_cost_data(), BASE_DIR)
    forest = next(item for item in result["tax_items"] if item["key"] == "forest_restoration_fee")
    assert forest["enabled"] is False
    assert forest["source"] == "not_applicable"
    assert forest["amount_per_sqm"] == "0.00"
    assert forest["standard_value"] == "0.00"
    assert "森林植被恢复费暂未配置有效标准" not in " ".join(
        item["message"] for item in result.get("warnings") or []
    )


def test_forest_restoration_fee_enabled_pending_policy_for_forest_land():
    result = calculate_cost_approximation(_forest_cost_data(), BASE_DIR)
    forest = next(item for item in result["tax_items"] if item["key"] == "forest_restoration_fee")
    reclamation = next(item for item in result["tax_items"] if item["key"] == "farmland_reclamation_fee")
    assert forest["enabled"] is True
    assert forest["source"] == "policy_config_missing"
    assert forest["standard_value"] in (None, "")
    assert forest["amount_per_sqm"] in (None, "")
    assert reclamation["enabled"] is False
    assert any(
        "森林植被恢复费暂未配置有效标准" in item["message"]
        for item in result.get("warnings") or []
    )


@pytest.mark.parametrize(
    "land_subclass",
    ["乔木林地", "竹林地", "灌木林地", "其他林地"],
)
def test_forest_restoration_fee_enabled_for_forest_subclasses(land_subclass):
    result = calculate_cost_approximation(
        _forest_cost_data(acquisition_land_subclass=land_subclass),
        BASE_DIR,
    )
    forest = next(item for item in result["tax_items"] if item["key"] == "forest_restoration_fee")
    assert forest["enabled"] is True
    assert forest["source"] == "policy_config_missing"


def test_forest_restoration_fee_manual_amount_included_in_tax_total():
    data = _forest_cost_data()
    result = calculate_cost_approximation(data, BASE_DIR)
    taxes = {item["key"]: item for item in result["tax_items"]}
    base_tax_total = float(result["totals"]["tax_total"])

    forest = taxes["forest_restoration_fee"]
    forest["standard_value"] = "18.50"
    forest["amount_per_sqm"] = "18.50"
    forest["confirmed"] = False
    result["tax_items"] = list(result["tax_items"])
    data["cost_approx_analysis"] = result

    updated = calculate_cost_approximation(data, BASE_DIR)
    forest_updated = next(item for item in updated["tax_items"] if item["key"] == "forest_restoration_fee")
    assert forest_updated["amount_per_sqm"] == "18.50"
    assert float(updated["totals"]["tax_total"]) == pytest.approx(base_tax_total + 18.50, abs=0.01)


def test_forest_restoration_narrative_references_xiangcaishui_2024_10():
    data = _forest_cost_data()
    result = calculate_cost_approximation(data, BASE_DIR)
    forest = next(item for item in result["tax_items"] if item["key"] == "forest_restoration_fee")
    forest["amount_per_sqm"] = "22.00"
    result["tax_items"] = list(result["tax_items"])
    data["cost_approx_analysis"] = result

    updated = calculate_cost_approximation(data, BASE_DIR)
    narrative = updated["generated_narratives"]["cost_approx_tax_narrative"]
    assert "湘财税〔2024〕10号" in narrative
    assert "森林植被恢复费" in narrative
    assert "22.00" in narrative


def test_forest_restoration_fee_confirmed_preserved_on_recalc():
    data = _forest_cost_data()
    result = calculate_cost_approximation(data, BASE_DIR)
    forest = next(item for item in result["tax_items"] if item["key"] == "forest_restoration_fee")
    forest["standard_value"] = "20.00"
    forest["amount_per_sqm"] = "20.00"
    forest["confirmed"] = True
    result["tax_items"] = list(result["tax_items"])
    data["cost_approx_analysis"] = result

    updated = calculate_cost_approximation(data, BASE_DIR)
    forest_updated = next(item for item in updated["tax_items"] if item["key"] == "forest_restoration_fee")
    assert forest_updated["confirmed"] is True
    assert forest_updated["amount_per_sqm"] == "20.00"


def test_forest_to_cultivated_switch_disables_restoration_fee():
    data = _forest_cost_data()
    analysis = calculate_cost_approximation(data, BASE_DIR)
    for item in analysis["tax_items"]:
        if item["key"] == "forest_restoration_fee":
            item["standard_value"] = "20.00"
            item["amount_per_sqm"] = "20.00"
            item["confirmed"] = True

    data["acquisition_land_class"] = "耕地"
    data["acquisition_land_subclass"] = "水田"
    data["cost_approx_analysis"] = analysis
    result = calculate_cost_approximation(data, BASE_DIR)

    forest = next(item for item in result["tax_items"] if item["key"] == "forest_restoration_fee")
    reclamation = next(item for item in result["tax_items"] if item["key"] == "farmland_reclamation_fee")
    assert forest["enabled"] is False
    assert forest["amount_per_sqm"] == "0.00"
    assert reclamation["enabled"] is True
    assert forest["confirmed"] is False


def test_sync_risk_groups_honors_legacy_combined_rate_override():
    groups = _sync_risk_groups(
        [{"group": "政策", "weight": "0.4", "adjustment_rate": "5", "confirmed": True}],
        [{"key": "政策", "label": "政策", "combined_rate": "9.50"}],
    )
    assert groups[0]["override_enabled"] is True
    assert groups[0]["effective_value"] == "9.50"


def test_risk_mode_analysis_blocks_complete_without_risk_confirmation():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "acquisition_land_subclass": "水田",
            "cost_approx_analysis": {"risk_mode": "analysis"},
        },
        BASE_DIR,
        include_pricing_assistant=False,
    )
    for item in result.get("policy_documents") or []:
        if item.get("enabled", True):
            item["confirmed"] = True
    for item in result.get("acquisition_items") or []:
        if item.get("enabled", True):
            item["confirmed"] = True
    for item in result.get("tax_items") or []:
        if item.get("enabled", True):
            item["confirmed"] = True
    for item in result.get("development_items") or []:
        if item.get("enabled", True):
            item["confirmed"] = True
    for item in result.get("usage_scenarios") or []:
        item["confirmed"] = True
    for item in result.get("location_factors") or []:
        item["confirmed"] = True
    for item in result.get("risk_items") or []:
        item["confirmed"] = False
    for item in result.get("risk_groups") or []:
        item["confirmed"] = False
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "acquisition_land_subclass": "水田",
        "cost_approx_analysis": result,
    }
    blocked = calculate_cost_approximation(data, BASE_DIR, include_pricing_assistant=False)
    assert blocked["complete"] is False


def test_pending_green_seedling_blocks_complete_for_unmatched_county():
    result = calculate_cost_approximation(
        {
            "county_name": "长沙市",
            "valuation_date": "2026-06-01",
            "acquisition_land_subclass": "水田",
        },
        BASE_DIR,
        include_pricing_assistant=False,
    )
    assert any("青苗补偿标准沿用默认口径" in str(item.get("message") or "") for item in result.get("warnings") or [])
    assert result["complete"] is False


def test_tongdao_attachment_inventory_prefers_huaihua_zone_over_yongzhou():
    inventory = cost_basis_attachment_inventory(BASE_DIR, "通道县")
    zone_labels = [item["label"] for item in inventory if "区片" in item.get("label", "")]
    assert not any("永州市农用地补偿区片划分表" == label for label in zone_labels)


def test_unknown_county_attachment_inventory_does_not_fall_back_to_yongzhou_zone():
    inventory = cost_basis_attachment_inventory(BASE_DIR, "长沙市")
    zone_labels = [item["label"] for item in inventory if "区片" in item.get("label", "")]
    assert "永州市农用地补偿区片划分表" not in zone_labels
    assert not any("永州" in str(item.get("label") or "") for item in inventory)


def test_manual_confirmed_seedling_override_resolves_pending_policy_block():
    data = {
        "county_name": "长沙市",
        "valuation_date": "2026-06-01",
        "acquisition_land_subclass": "水田",
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    seedling = next(item for item in analysis["acquisition_items"] if item["key"] == "seedling_compensation")
    seedling.update(
        {
            "standard_value": "3000",
            "amount_per_sqm": "4.50",
            "computed_amount_per_sqm": "4.50",
            "source": "manual_policy_replacement",
            "source_note": "当前项目人工调查采用值",
            "confirmed": True,
        }
    )
    data["cost_approx_analysis"] = analysis

    updated = calculate_cost_approximation(data, BASE_DIR)

    assert not any("青苗补偿标准沿用默认口径" in str(item.get("message") or "") for item in updated["warnings"])
    updated_seedling = next(item for item in updated["acquisition_items"] if item["key"] == "seedling_compensation")
    assert updated_seedling["source"] == "manual_policy_replacement"
    assert updated_seedling["amount_per_sqm"] == "4.50"


def test_pricing_preview_uses_unconfirmed_manual_location_adjustment():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "land_usage": "居住用地",
        "acquisition_land_subclass": "水田",
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    baseline_price = analysis["usage_results"][0]["final_price"]
    factor = analysis["location_factors"][0]
    factor.update({"correction_rate": "20", "correction_rate_manual": True, "confirmed": False})
    data["cost_approx_analysis"] = analysis

    normal = calculate_cost_approximation(data, BASE_DIR)
    preview = calculate_cost_approximation({**data, "cost_pricing_preview_mode": True}, BASE_DIR)

    assert normal["usage_results"][0]["final_price"] == baseline_price
    assert preview["usage_results"][0]["final_price"] != baseline_price
    assert preview["location_factors"][0]["confirmed"] is False


def test_pricing_preview_uses_unconfirmed_risk_group_override():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "land_usage": "居住用地",
        "acquisition_land_subclass": "水田",
        "cost_approx_analysis": {"risk_mode": "analysis"},
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    analysis["usage_scenarios"][0]["safe_rate"] = "1.50"
    group = analysis["risk_groups"][0]
    group.update({"override_enabled": True, "override_value": "12", "confirmed": False})
    data["cost_approx_analysis"] = analysis

    normal = calculate_cost_approximation(data, BASE_DIR)
    preview = calculate_cost_approximation({**data, "cost_pricing_preview_mode": True}, BASE_DIR)

    assert preview["usage_results"][0]["final_price"] != normal["usage_results"][0]["final_price"]
    assert preview["risk_groups"][0]["confirmed"] is False


def test_internal_cost_calculation_skips_pricing_assistant_by_default():
    result = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_usage": "居住用地",
            "acquisition_land_subclass": "水田",
        },
        BASE_DIR,
    )
    assert "pricing_assistant" not in result


def test_county_matcher_distinguishes_tongdao_from_daoxian():
    from src.services.cost_approximation import _county_matches, _province_compensation_row

    # '道县' is a trailing substring of '通道县' but they are different counties.
    assert _county_matches("通道县", "道县") is False
    assert _county_matches("道县", "通道县") is False
    # Same base name with a different administrative level is not the same area.
    assert _county_matches("洪江市", "洪江区") is False
    assert _county_matches("长沙市", "长沙县") is False
    # Autonomous-county long form matches its short form.
    assert _county_matches("通道县", "通道侗族自治县") is True
    # A clean county token leading a longer location string still matches.
    assert _county_matches("道县西洲街道", "道县") is True

    tongdao = _province_compensation_row(BASE_DIR, "通道县")
    assert tongdao.get("city") == "怀化市"
    assert "通道" in str(tongdao.get("county") or "")
    daoxian = _province_compensation_row(BASE_DIR, "道县")
    assert daoxian.get("city") == "永州市"
    assert daoxian.get("county") == "道县"


def test_attachment_inventory_dedups_counties_and_localizes_status():
    from src.services.cost_approximation import _attachment_status_label, _dedup_counties_display

    assert _dedup_counties_display(["通道县", "通道侗族自治县"]) == ["通道县"]
    assert _attachment_status_label("scan_pending_structuring") == "已扫描·待结构化"
    assert _attachment_status_label("available") == "可用"

    inventory = cost_basis_attachment_inventory(BASE_DIR, "通道县")
    for item in inventory:
        display = item.get("counties_display") or []
        # Display list must not show both '通道县' and '通道侗族自治县' at once.
        assert not ("通道县" in display and "通道侗族自治县" in display)
        # Status must always be a friendly label, never a raw backend token.
        assert "scan" not in str(item.get("status_label") or "")
        assert "pending" not in str(item.get("status_label") or "")


def test_building_catalog_fully_structured_from_policy_sources():
    # F-task acceptance: 道县/通道县 政策目录项目数远多于 4，且关键标准值与原件一致。
    dao_catalog = building_compensation_add_catalog(BASE_DIR, "道县")
    tongdao_catalog = building_compensation_add_catalog(BASE_DIR, "通道县")
    assert len(dao_catalog) >= 18
    assert len(tongdao_catalog) >= 15

    def _option(catalog, row_key, option_key):
        entry = next(item for item in catalog if item["row_key"] == row_key)
        return next(opt for opt in entry["grade_options"] if opt["key"] == option_key)

    # 道县 道政发〔2020〕2号：房屋钢混重置价1600、坟墓无棺1500、围墙24砖眠墙120。
    assert _option(dao_catalog, "house_compensation", "rc_concrete")["standard"] == "1600"
    assert _option(dao_catalog, "grave_compensation", "grave_no_coffin")["standard"] == "1500"
    assert _option(dao_catalog, "enclosing_wall", "wall_24_solid")["standard"] == "120"
    # 砖混二等仍为默认首项 1250，金标准计算不受影响。
    assert building_compensation_grade_options(BASE_DIR, "道县", "house_compensation")[0]["standard"] == "1250"

    # 通道县 怀化附件7/9/10：房屋钢筋砼框架1100、坟墓砼坟8000、晒坪岩板坪65。
    assert _option(tongdao_catalog, "house_compensation", "rc_frame")["standard"] == "1100"
    assert _option(tongdao_catalog, "grave_compensation", "concrete_grave")["standard"] == "8000"
    assert _option(tongdao_catalog, "drying_floor", "rock_slab_floor")["standard"] == "65"

    # 单位本地化：政策一览不再把非㎡项目硬编码为 元/平方米。
    dao_help = building_compensation_policy_help(BASE_DIR, "道县")
    grave_help = next(e for e in dao_help["entries"] if e["option_key"] == "grave_no_coffin")
    assert grave_help["standard_unit"] == "元/冢"
    # 未能从原件提取金额的项目（变压器）标记 pending。
    transformer = next(item for item in dao_catalog if item["row_key"] == "transformer")
    assert transformer["grade_options"][0]["standard"] == ""


def test_building_catalog_available_for_county_names_with_admin_suffix():
    # The county_name field often carries a township/street or city qualifier;
    # the standards overview and "从政策目录添加" must still resolve policy data.
    for county in ("道县", "道县西洲街道", "永州市道县"):
        assert building_compensation_add_catalog(BASE_DIR, county), f"{county} 应能取到建筑物补偿政策目录"
        assert (building_compensation_policy_help(BASE_DIR, county) or {}).get("entries"), f"{county} 应能取到政策标准一览"
        assert building_compensation_grade_options(BASE_DIR, county, "house_compensation"), f"{county} 应能取到等级选项"
    for county in ("通道县", "通道县某镇", "通道侗族自治县"):
        assert building_compensation_add_catalog(BASE_DIR, county), f"{county} 应能取到怀化建筑物补偿政策目录"
    # The '道县' trap must remain excluded: 通道县 must not borrow 道县's catalog scope.
    daoxian_help = building_compensation_policy_help(BASE_DIR, "道县")
    tongdao_help = building_compensation_policy_help(BASE_DIR, "通道县")
    assert daoxian_help.get("source_file") != tongdao_help.get("source_file")


def test_pricing_assistant_location_factor_uses_grade_options():
    from src.services.cost_approximation import _pricing_assistant_controls

    analysis = calculate_cost_approximation(
        {
            "county_name": "道县",
            "valuation_date": "2026-06-01",
            "land_usage": "居住用地",
            "acquisition_land_subclass": "水田",
        },
        BASE_DIR,
    )
    assert analysis.get("location_correction_mode") == "direct_sum"
    controls = _pricing_assistant_controls(analysis)
    location_controls = [c for c in controls if str(c.get("key", "")).startswith("location:")]
    assert location_controls, "调价助手应包含区位修正控件"
    for control in location_controls:
        # In direct_sum mode the control must be a grade selector, not a free value.
        assert control.get("type") == "grade"
        assert control.get("options"), "区位控件应提供优劣度选项"


def test_zone_suggestion_never_falls_back_to_another_city_or_county():
    no_city = suggest_compensation_zone(
        "长沙市望城区某街道",
        BASE_DIR,
        county_name="长沙市",
        city_name="",
    )
    assert no_city["matched"] is False
    assert "永州市农用地补偿区片划分表" not in no_city["source_path"]
    assert any("不得自动读取其他地市" in warning for warning in no_city["warnings"])

    wrong_county = suggest_compensation_zone(
        "长沙市望城区某街道",
        BASE_DIR,
        county_name="长沙市",
        city_name="永州市",
    )
    assert wrong_county["matched"] is False
    assert any("不得回退搜索其他县市" in warning for warning in wrong_county["warnings"])


def test_interactive_cost_calculation_is_lightweight_and_uses_current_location_grade():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "land_usage": "居住用地",
        "acquisition_land_subclass": "水田",
    }
    initial = calculate_cost_approximation(data, BASE_DIR)
    baseline_price = initial["usage_results"][0]["final_price"]
    factor = initial["location_factors"][0]
    factor["level"] = (factor.get("levels") or ["优"])[0]
    factor["confirmed"] = False
    factor["correction_rate_manual"] = False
    data["cost_approx_analysis"] = initial
    data["cost_interactive_mode"] = True
    data["cost_pricing_preview_mode"] = True

    result = calculate_cost_approximation(
        data,
        BASE_DIR,
        include_pricing_assistant=False,
        include_catalog_metadata=False,
        include_process_output=False,
    )

    assert result["usage_results"][0]["final_price"] != baseline_price
    for key in (
        "pricing_assistant",
        "cost_basis_attachment_inventory",
        "building_compensation_add_catalog",
        "building_compensation_policy_help",
        "generated_narratives",
        "effective_narratives",
        "narrative_segment_sources",
        "tables",
        "content_blocks",
        "results",
    ):
        assert key not in result
    assert "cost_basis_attachment_inventory" not in result["policy_basis"]


def test_pricing_assistant_baseline_uses_latest_unconfirmed_location_grade():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "land_usage": "居住用地",
        "acquisition_land_subclass": "水田",
    }
    initial = calculate_cost_approximation(data, BASE_DIR)
    factor = initial["location_factors"][0]
    factor["level"] = (factor.get("levels") or ["优"])[0]
    factor["confirmed"] = False
    factor["correction_rate_manual"] = False
    data["cost_approx_analysis"] = initial
    data["cost_pricing_preview_mode"] = True

    result = calculate_cost_approximation(data, BASE_DIR, include_pricing_assistant=True)

    assert result["pricing_assistant"]["baseline_final_price"] == result["usage_results"][0]["final_price"]
    assert result["usage_results"][0]["location_correction_rate"] != "0.00"


def test_disabled_location_factor_is_excluded_from_cost_outputs():
    data = {
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "land_location_full": "道县西洲街道宝珍街六栋九号",
        "land_usage": "居住用地",
    }
    analysis = calculate_cost_approximation(data, BASE_DIR)
    for factor in analysis["location_factors"]:
        factor.update({"correction_rate": "0.00", "correction_rate_manual": True, "confirmed": True})
    disabled_label = analysis["location_factors"][0]["label"]
    analysis["location_factors"][0].update(
        {
            "enabled": False,
            "confirmed": False,
            "correction_rate": "50.00",
            "correction_rate_manual": True,
        }
    )
    data["cost_approx_analysis"] = analysis

    result = calculate_cost_approximation(data, BASE_DIR)

    assert result["usage_results"][0]["location_correction_rate"] == "0.00"
    assert not any("区位修正因素仍有未确认项目" in item["message"] for item in result["warnings"])
    location_table = next(table for table in result["tables"] if table["key"] == "cost_location_rows")
    assert disabled_label not in str(location_table["rows"])


def test_cost_basis_inventory_exposes_structured_status_and_targets():
    inventory = cost_basis_attachment_inventory(BASE_DIR, "道县")
    statuses = {item.get("structured_status") for item in inventory}
    labels = {item.get("label") for item in inventory}

    assert "structured" in statuses
    assert "needs_grade_selection" in statuses
    assert "manual_input" in statuses
    assert "土地开发费调查资料" not in labels
    assert "投资利润率及土地增值收益率" not in labels
    assert any(
        item.get("structured_item_count", 0) > 0
        for item in inventory
        if item.get("structured_status") == "structured"
    )
    assert any(item.get("price_fields") and item.get("target_ref") for item in inventory)
    social = next(item for item in inventory if "社会保障" in item.get("label", "") or "社保" in item.get("label", ""))
    assert social["structured_status"] == "manual_input"
    for item in inventory:
        if item.get("structured_status") == "pending_structuring":
            assert "加入配置" in item.get("next_action", "")
