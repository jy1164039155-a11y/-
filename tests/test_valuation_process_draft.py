# -*- coding: utf-8 -*-
from pathlib import Path

from src.services.comparable_library import ComparableLibrary
from src.services.valuation_process_builder import build_valuation_process_draft
from tests.test_comparable_library import official_case
from tests.test_cost_approximation import _mixed_usage_payload
from tests.test_income_capitalization import _baozhen_income_payload


def test_process_draft_only_returns_selected_methods_and_builds_cost_workflow(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    draft = build_valuation_process_draft(
        {
            "use_cost_approx": True,
            "use_market_comp": True,
            "use_income_cap": False,
            "use_benchmark_corr": False,
            "use_residual": False,
            "land_usage_key": "industrial",
            "land_usage": "工矿用地",
            "market_comp_analysis": {
                "narrative_overrides": {
                    "market_comp_comparable_basis": "人工校核后的价格可比基础正文。"
                }
            },
        },
        library,
    )

    assert [item["method_key"] for item in draft["methods"]] == ["cost_approx", "market_comp"]
    cost = draft["methods"][0]
    assert cost["status"] == "incomplete"
    assert cost["complete"] is False
    assert len(cost["narratives"]) == 13
    assert len(cost["tables"]) == 6
    assert any("征地区片" in item["message"] for item in cost["warnings"])
    market = draft["methods"][1]
    assert market["status"] == "incomplete"
    assert [item["key"] for item in market["narratives"]] == [
        "market_comp_method_intro",
        "market_comp_step1_instances",
        "market_comp_comparable_basis",
        "market_comp_factor_selection",
        "market_comp_condition_intro",
        "market_comp_index_basis",
        "market_comp_step4_solve",
    ]
    basis = next(item for item in market["narratives"] if item["key"] == "market_comp_comparable_basis")
    assert basis["effective_text"] == "人工校核后的价格可比基础正文。"
    assert basis["override_text"] == "人工校核后的价格可比基础正文。"
    assert len(market["tables"]) == 5
    assert [item["key"] for item in market["content_blocks"]] == [
        "market_comp_method_intro",
        "market_comp_step1_instances",
        "market_comp_basic_rows",
        "market_comp_comparable_basis",
        "market_comp_factor_selection",
        "market_comp_condition_intro",
        "market_comp_factor_condition_rows",
        "market_comp_index_basis",
        "market_comp_time_index_rows",
        "market_comp_factor_index_rows",
        "market_comp_correction_rows",
        "market_comp_step4_solve",
        "market_comp_price",
    ]
    assert any("成交公告截图" in item["message"] for item in market["warnings"])
    evidence_warning = next(item for item in market["warnings"] if "成交公告截图" in item["message"])
    assert evidence_warning["target"] == "evidence"


def test_process_draft_requires_manual_basis_text_when_basis_needs_adjustment(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    draft = build_valuation_process_draft(
        {
            "use_cost_approx": False,
            "use_market_comp": True,
            "use_income_cap": False,
            "use_benchmark_corr": False,
            "use_residual": False,
            "market_comp_analysis": {"comparable_basis_status": "needs_adjustment"},
        },
        library,
    )

    market = draft["methods"][0]
    basis = next(item for item in market["narratives"] if item["key"] == "market_comp_comparable_basis")
    assert basis["review_state"] == "needs_adjustment"
    assert basis["complete"] is False
    assert any("价格可比基础标记为需要调整" in item["message"] for item in market["warnings"])


def test_process_draft_hides_unselected_market_method(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    draft = build_valuation_process_draft(
        {
            "use_cost_approx": False,
            "use_market_comp": False,
            "use_income_cap": True,
            "use_benchmark_corr": False,
            "use_residual": False,
        },
        library,
    )

    assert [item["method_key"] for item in draft["methods"]] == ["income_cap"]
    assert draft["methods"][0]["status"] == "incomplete"
    assert len(draft["methods"][0]["narratives"]) == 13
    assert any(item["key"] == "income_cap_price" for item in draft["methods"][0]["results"])
    assert not any(
        "完整结构化计算过程待建设" in item["message"]
        for item in draft["methods"][0]["warnings"]
    )


def test_income_process_hotspots_are_field_level_not_whole_paragraph(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    payload = _baozhen_income_payload()
    payload["use_income_cap"] = True
    payload["room_detail_location"] = "道江镇濂溪山庄宝珍街南六栋九号"
    draft = build_valuation_process_draft(payload, library)
    income = draft["methods"][0]
    sections = {item["key"]: item for item in income["narratives"]}

    factor_intro = sections["income_cap_rent_factor_intro"]
    assert factor_intro["segments"]
    assert not any(
        segment.get("text") == factor_intro["effective_text"] and (segment.get("field") or segment.get("fields"))
        for segment in factor_intro["segments"]
    )
    assert "income_cap_analysis" not in factor_intro["hotspot_refs"]

    gross_intro = sections["income_cap_gross_income_intro"]
    location_segments = [
        segment
        for segment in gross_intro["segments"]
        if "道江镇濂溪山庄宝珍街南六栋九号" in segment.get("text", "")
    ]
    assert location_segments
    assert location_segments[0].get("field") in {"room_detail_location", "land_location_full"}

    unit_price = sections["income_cap_unit_price_narrative"]
    assert not any(
        "元/平方米" in segment.get("text", "") and (segment.get("field") or segment.get("fields"))
        for segment in unit_price["segments"]
    )


def test_cost_process_hotspots_are_specific_to_cost_items_and_results(tmp_path):
    class CostOnlyLibrary:
        base_dir = Path(__file__).resolve().parents[1]

    library = CostOnlyLibrary()
    payload = _mixed_usage_payload()
    payload["use_cost_approx"] = True
    payload["use_market_comp"] = False
    payload["use_income_cap"] = False
    payload["use_benchmark_corr"] = False
    payload["use_residual"] = False

    draft = build_valuation_process_draft(payload, library)
    cost = draft["methods"][0]
    sections = {item["key"]: item for item in cost["narratives"]}

    acquisition_sections = [
        sections["cost_approx_acquisition_intro"],
        sections["cost_approx_attachment_population_narrative"],
        sections["cost_approx_acquisition_solve"],
    ]
    assert all(
        not any(
            segment.get("text") == acquisition["effective_text"] and (segment.get("field") or segment.get("fields"))
            for segment in acquisition["segments"]
        )
        for acquisition in acquisition_sections
    )
    refs = {
        ref
        for acquisition in acquisition_sections
        for ref in acquisition["hotspot_refs"]
    }
    assert "cost_approx_analysis.acquisition_items.land_compensation.standard_value" in refs
    assert "cost_approx_analysis.acquisition_items.land_compensation.amount_per_sqm" in refs
    assert "cost_approx_analysis.totals.acquisition_total" in refs

    all_refs = {
        ref
        for section in cost["narratives"]
        for ref in section.get("hotspot_refs") or []
    }
    assert "cost_approx_analysis.costs" not in all_refs
    assert not any(
        "元/平方米" in segment.get("text", "") and (segment.get("field") or segment.get("fields"))
        for section in cost["narratives"]
        for segment in section["segments"]
    )

    development = next(item for item in cost["tables"] if item["key"] == "cost_development_rows")
    assert development["rows"][-1]["cell_refs"][-1] == "cost_approx_analysis.totals.development_total"


def test_market_process_hotspots_use_case_factor_and_result_refs(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    for item in (
        official_case("A", "4311242024B000055", "10772.50", "145", "2024-08-05"),
        official_case("B", "4311242024B000016", "54307.30", "150", "2024-01-10"),
        official_case("C", "4311242024B000071", "6769.20", "149", "2024-08-26"),
    ):
        library.upsert_official_case(item)
    prepared = library.prepare_analysis(
        {
            "subject": {
                "valuation_date": "2025-01-01",
                "land_usage_key": "industrial",
                "land_usage": "工矿用地",
                "land_area": "11000",
                "land_use_term_years": "30",
                "land_development_set": "五通一平",
                "right_type": "出让",
            },
            "case_ids": ["A", "B", "C"],
            "monthly_growth_rate": "0",
            "land_reduction_rate": "5.4",
        }
    )
    for factor in prepared["factors"]:
        factor["review_status"] = "confirmed"
        factor["subject_value"] = factor.get("subject_value") or "与估价对象一致"
        for slot in ("A", "B", "C"):
            factor["cases"][slot]["value"] = factor["cases"][slot].get("value") or "与估价对象一致"
            factor["cases"][slot]["index"] = "100"
            factor["cases"][slot]["confirmed"] = True
    analysis = library.calculate_market_comparison(prepared)

    draft = build_valuation_process_draft(
        {
            "use_cost_approx": False,
            "use_market_comp": True,
            "use_income_cap": False,
            "use_benchmark_corr": False,
            "use_residual": False,
            "market_comp_analysis": analysis,
            "market_comp_evidence_snapshot_ids": ["ea", "eb", "ec"],
            "market_comp_location_snapshot_ids": ["la", "lb", "lc"],
            "market_comp_site_snapshot_ids": ["sa", "sb", "sc"],
        },
        library,
    )
    market = draft["methods"][0]
    sections = {item["key"]: item for item in market["narratives"]}

    step1 = sections["market_comp_step1_instances"]
    assert not any(
        segment.get("text") == step1["effective_text"] and (segment.get("field") or segment.get("fields"))
        for segment in step1["segments"]
    )
    assert "market_comp_analysis.selected_cases.0.electronic_supervision_no" in step1["hotspot_refs"]

    index_basis_refs = set(sections["market_comp_index_basis"]["hotspot_refs"])
    assert "market_comp_analysis.monthly_growth_rate" in index_basis_refs

    solve_refs = set(sections["market_comp_step4_solve"]["hotspot_refs"])
    assert "market_comp_analysis.calculations.A.corrected_price" in solve_refs
    assert "market_comp_analysis.market_comp_price" in solve_refs
    assert not any(
        "元/平方米" in segment.get("text", "") and (segment.get("field") or segment.get("fields"))
        for section in market["narratives"]
        for segment in section["segments"]
    )

    basic_table = next(item for item in market["tables"] if item["key"] == "market_comp_basic_rows")
    electronic_no_row = next(item for item in basic_table["rows"] if item["label"] == "电子监管号")
    assert electronic_no_row["cell_refs"][1] == "market_comp_analysis.selected_cases.0.electronic_supervision_no"
    time_table = next(item for item in market["tables"] if item["key"] == "market_comp_time_index_rows")
    time_index_row = next(item for item in time_table["rows"] if item["label"] == "交易期日指数")
    assert time_index_row["cell_refs"][2] == "market_comp_analysis.factors.transaction_time.cases.A.index"
