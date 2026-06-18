# -*- coding: utf-8 -*-
import re
from pathlib import Path

from src.services.ownership_builder import derive_ownership_descriptions
from src.services.valuation_builder import derive_valuation_descriptions


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "frontend" / "src" / "App.vue"


def _segment_fields(data, keys):
    fields = set()
    for key in keys:
        for segment in data.get(f"{key}_segments", []):
            if segment.get("field"):
                fields.add(segment["field"])
            fields.update(segment.get("fields", []))
    return fields


def _frontend_hotspot_contract():
    app = APP_PATH.read_text(encoding="utf-8")
    registry_block = app.split("const FIELD_REGISTRY = {", 1)[1].split(
        "// 渐进式多态桥接", 1
    )[0]
    registry = set(re.findall(r"^\s{2}([A-Za-z_]\w*):\s*\{", registry_block, re.M))

    detail_block = app.split("const detailFieldKeys = [", 1)[1].split("];", 1)[0]
    dynamic_targets = set(re.findall(r"'([A-Za-z_]\w*)'", detail_block))
    literal_targets = set(re.findall(r'id="focus_item_([A-Za-z_]\w*)"', app))

    aliases = {}
    for block_name in ("basePriceFieldAliases", "generalHotspotFieldAliases"):
        block = app.split(f"const {block_name} = {{", 1)[1].split("};", 1)[0]
        aliases.update(re.findall(r"^\s{2}([A-Za-z_]\w*):\s*'([A-Za-z_]\w*)'", block, re.M))
    aliases = dict(aliases)

    return app, registry, literal_targets, dynamic_targets, aliases


def _normalize_field(field, aliases):
    seen = set()
    while field in aliases and field not in seen:
        seen.add(field)
        field = aliases[field]
    return field


def test_cost_location_group_watch_initializes_after_cost_analysis():
    app = APP_PATH.read_text(encoding="utf-8")

    analysis_index = app.index("const costAnalysis = ref({")
    groups_index = app.index("const costLocationFactorGroups = computed(() => {")
    immediate_watch_index = app.index("watch(costLocationFactorGroups")

    assert analysis_index < groups_index < immediate_watch_index
    project_watch = app.split("// 监听要素，自动更新 project_name", 1)[1].split("onMounted(() => {", 1)[0]
    assert "nextTick(() => scheduleCostZoneRematch())" in project_watch
    assert "\n    scheduleCostZoneRematch();\n" not in project_watch


def _rich_payload():
    return {
        "client_name": "道县自然资源局",
        "transfer_purpose": "拟挂牌出让",
        "right_type": "出让",
        "registered_right_type": "划拨",
        "land_user": "某公司",
        "land_location": "道县工业园",
        "land_location_full": "道县工业园（A地块）",
        "county_name": "道县",
        "local_city": "永州市",
        "land_area": "123.45",
        "building_area": "350",
        "plot_ratio": "1.5",
        "land_use_term": "50年",
        "land_usage_key": "industrial",
        "land_usage": "工矿用地",
        "land_usage_short": "工矿用地",
        "land_usage_full": "工矿用地",
        "planning_approval_authority": "道县自然资源局",
        "land_development_actual": "宗地红线外五通，红线内场地平整",
        "land_development_set": "宗地红线外五通，红线内场地平整",
        "valuation_condition_type": "规划",
        "assumed_right_status": "无他项权利的完全权利条件",
        "valuation_date": "2026年6月4日",
        "use_cost_approx": True,
        "use_market_comp": True,
        "use_income_cap": True,
        "use_benchmark_corr": True,
        "use_residual": True,
        "cost_approx_price": "100",
        "market_comp_price": "200",
        "income_cap_price": "300",
        "benchmark_corr_price": "400",
        "residual_price": "500",
        "valuation_basis_docs_list": "《永州市集体土地与房屋征收补偿安置办法》",
        "acquisition_land_class": "林地",
        "acquisition_approval_doc_name": "关于某批次建设用地的批复",
        "acquisition_approval_doc_no": "湘政地〔2025〕1号",
        "acquisition_approval_doc_date": "2025年1月2日",
        "base_price_doc_no": "道政函〔2024〕1号",
        "base_price_doc_name": "《道县城镇基准地价更新成果》",
        "base_price_publish_date": "2024年1月1日",
        "base_price_base_date": "2023年1月1日",
        "base_price_doc_authority": "道县人民政府",
        "land_usage_basis": "《规划条件》",
        "land_area_basis": "《勘测定界图》",
        "basis_docs_list": "《规划条件》\n《勘测定界图》",
        "house_cert_no": "房字第001号",
        "registered_house_area": "350",
        "room_detail_location": "道县工业园A栋",
        "proof_doc_name": "《权属证明》",
        "proof_doc_date": "2025年1月1日",
        "buy_year": "2020年",
        "land_cert_no": "道国用第001号",
        "owner_name": "某公司",
        "registration_time": "2025年1月1日",
        "cadastral_map_no": "001",
        "parcel_no": "A-001",
    }


def test_generated_hotspots_have_registered_and_focusable_frontend_targets():
    app, registry, literal_targets, dynamic_targets, aliases = _frontend_hotspot_contract()
    fields = set()

    valuation = _rich_payload()
    derive_valuation_descriptions(valuation, overwrite=True)
    fields.update(
        _segment_fields(
            valuation,
            [
                "valuation_method_reasons",
                "valuation_method_applicability",
                "final_price_determination",
                "valuation_result_statement",
                "infrastructure_detail",
                "cost_approx_land_class_intro",
                "cost_approx_process_intro",
            ],
        )
    )

    for scenario in ("new_grant", "historical_unregistered", "registered_complete"):
        ownership = _rich_payload()
        ownership["ownership_scenario_type"] = scenario
        derive_ownership_descriptions(ownership, overwrite=True)
        fields.update(
            _segment_fields(
                ownership,
                ["land_registration_desc", "land_right_desc", "land_use_status_desc"],
            )
        )

    normalized = {_normalize_field(field, aliases) for field in fields}
    missing_registry = sorted(field for field in normalized if field not in registry)
    missing_targets = sorted(
        field
        for field in normalized
        if field not in literal_targets
        and field not in dynamic_targets
        and f'focus_item_base_price_drawer_{field}"' not in app
    )

    assert not missing_registry
    assert not missing_targets


def test_all_perspective_hotspots_share_repeatable_highlight_and_reveal_flow():
    app = APP_PATH.read_text(encoding="utf-8")
    assert app.count("activeFlickerField.value = targetField;") == 1
    assert app.count("triggerFieldHighlight(targetField") >= 3
    assert "focusNestedProcessField" in app
    assert "income_cap_analysis." in app
    assert app.count("revealFieldElement(el);") >= 3
    assert "plot_ratio_display: 'plot_ratio'" in app
    assert "cost_approx_analysis: 'costs'" in app
    assert 'id="focus_item_cost_approx_analysis"' in app
    assert "const isProcessField = (" in app
    assert "activeTab.value = isProcessField ? 'p5' : (metadata?.tab || 'p5');" in app
    assert "formFields[targetField]" not in app
    assert app.count("FIELD_REGISTRY[targetField]") >= 3
    assert "costFocusId('effective_local_city')" in app
    assert "costFocusId('attachment_compensation_analysis.building_compensation_per_person')" in app
    assert "costFocusId('building_compensation_rows.' + index + '.amount')" in app
    assert 'id="focus_item_cost_approx_policy"' in app
    assert 'id="focus_item_cost_approx_adjustments"' in app
    assert "resolveProcessFocusElement(targetField)" in app
    assert "processWorkspaceFallbackIds" in app
    assert "computed-ref-span" in app
    assert "computed-ref-cell" in app
    assert "isComputedHotspotField(cell.ref)" in app
    assert "onCostCompensationZoneChange" in app
    assert "rematchCostApproximation" in app
    assert "onBuildingCompensationGradeChange" in app
    assert "openCostBuildingCompensationHelp" in app
    assert "buildingRowStandardReadonly" in app
    assert "costBuildingHelpOpen" in app
    assert "cost-help-icon-btn" in app
    assert "addCostBuildingCompensationRow" in app
    assert "costBuildingPolicyHelp" in app
    assert "costPricingAssistantOpen" in app
    assert "openCostPricingAssistant" in app
    assert "recalculateCostPricingSandboxFromMain" in app
    assert "cost_pricing_preview_mode" in app
    assert "building:" in app
    assert "pricing_assistant" in app
    assert "building_compensation_policy_help" in app
    assert "costBasisAttachmentInventory" in app
    assert "cost_basis_attachment_inventory" in app
    assert "测算依据文件清单" in app
    assert "structured_status" in app
    assert "structured_item_count" in app
    assert "next_action" in app
    assert "costAttachmentStructuredStatus" in app
    assert "costAttachmentPriceFields" in app
    assert "costAttachmentFieldLabel" in app
    assert "removeCostLocationFactor" in app
    assert "restoreCostLocationFactors" in app
    assert "costDeletedTemplateLocationFactors" in app
    assert "测算项目</th><th>结果</th><th>单位" not in app
    assert "外部软件测算结果与证据" not in app
    assert 'id="focus_item_local_compensation_policy_name"' in app
    assert 'id="focus_item_acquisition_land_class_confirmed"' in app
    assert "local_compensation_policy_name:" in app
    assert "costHasMultipleUsagePrices" in app
    assert "cost-rounding-trace-list" in app


def test_cost_process_draft_policy_hotspots_have_frontend_targets(tmp_path):
    from src.services.comparable_library import ComparableLibrary
    from src.services.valuation_process_builder import build_valuation_process_draft

    app, registry, literal_targets, dynamic_targets, aliases = _frontend_hotspot_contract()
    library = ComparableLibrary(str(tmp_path))
    draft = build_valuation_process_draft(
        {
            **_rich_payload(),
            "acquisition_land_class": "耕地",
            "acquisition_land_subclass": "水田",
            "land_usage": "居住用地",
            "county_name": "道县",
        },
        library,
    )
    cost = next(item for item in draft["methods"] if item["method_key"] == "cost_approx")
    refs = {
        ref
        for section in cost["narratives"]
        for ref in section.get("hotspot_refs") or []
    }
    for field in (
        "local_compensation_policy_name",
        "local_compensation_policy_no",
        "local_compensation_policy_date",
        "acquisition_land_class",
        "acquisition_land_subclass",
    ):
        assert field in registry
        assert field in literal_targets or field in dynamic_targets
    assert "cost_approx_analysis.totals.development_total" in {
        cell_ref
        for table in cost["tables"]
        for row in table.get("rows") or []
        for cell_ref in row.get("cell_refs") or []
        if cell_ref
    }


def test_cost_location_interaction_uses_lightweight_latest_only_workflow():
    app = APP_PATH.read_text(encoding="utf-8")

    assert "payload.cost_interactive_mode = true;" in app
    assert "payload.cost_pricing_preview_mode = true;" in app
    assert "new AbortController()" in app
    assert "costInteractiveRequestSeq" in app
    assert "applyCostInteractiveAnalysis" in app
    assert "recalculateLocalLocationResults" in app
    assert "await flushCostInteractiveCalculation();" in app
    assert ":key=\"factor.key || `location_factor_${index}`\"" in app
    assert "v-if=\"costWorkspaceView === 'adjustments'\"" in app
    assert "v-show=\"costWorkspaceView === 'adjustments'\"" not in app
    assert not re.search(r"watch\(\s*costAnalysis,\s*\(newVal\)", app)
