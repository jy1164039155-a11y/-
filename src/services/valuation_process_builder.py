# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, List

from src.schemas.valuation_methods import (
    CalculationResult,
    MethodProcessDraft,
    ProcessContentBlock,
    ProcessNarrativeSection,
    ProcessTableSection,
    ValuationProcessDraft,
)
from src.services.market_comparison_structure import build_market_comparison_table_sections
from src.services.cost_approximation import calculate_cost_approximation
from src.services.benchmark_correction import calculate_benchmark_correction
from src.services.income_capitalization import calculate_income_capitalization
from src.services.ownership_builder import compile_desc_segments, _mark_literal_segments
from src.services.valuation_builder import derive_valuation_descriptions


METHODS = (
    ("cost_approx", "use_cost_approx", "成本逼近法", "cost_approx_analysis", "cost_approx_method_intro"),
    ("market_comp", "use_market_comp", "市场比较法", "market_comp_analysis", "market_comp_method_intro"),
    ("income_cap", "use_income_cap", "收益还原法", "income_cap_analysis", "income_cap_method_intro"),
    ("benchmark_corr", "use_benchmark_corr", "基准地价系数修正法", "benchmark_corr_analysis", "benchmark_corr_method_intro"),
    ("residual", "use_residual", "剩余法", "residual_analysis", "residual_method_intro"),
)

MARKET_NARRATIVE_SECTIONS = (
    ("market_comp_method_intro", "1. 方法定义、公式及变量解释", ["land_usage_key"]),
    ("market_comp_step1_instances", "2. 比较实例选择与公告证据", ["market_comp_analysis", "market_comp_evidence_snapshot_ids"]),
    ("market_comp_comparable_basis", "3. 建立价格可比基础", ["market_comp_analysis"]),
    ("market_comp_factor_selection", "4. 比较因素选择", ["market_comp_analysis"]),
    ("market_comp_condition_intro", "5. 比较因素条件说明", ["market_comp_factor_condition_rows"]),
    ("market_comp_index_basis", "6. 编制比较因素条件指数表", ["market_comp_factor_index_rows"]),
    ("market_comp_step4_solve", "7. 比准价格求取", ["market_comp_correction_rows", "market_comp_price"]),
)

COST_NARRATIVE_SECTIONS = (
    ("cost_approx_method_intro", "1. 方法定义、公式及变量解释", ["land_usage_key"]),
    ("cost_approx_basis_intro", "2. 测算依据与征收地类", ["acquisition_land_class", "acquisition_land_subclass", "acquisition_approval_doc_name"]),
    ("cost_approx_acquisition_intro", "3. 土地取得费及补偿标准", ["cost_approx_analysis", "acquisition_land_class", "acquisition_land_subclass"]),
    ("cost_approx_attachment_population_narrative", "4. 地上附着物补偿及安置人口", ["cost_approx_analysis"]),
    ("cost_approx_acquisition_solve", "5. 土地取得费求取", ["cost_approx_analysis"]),
    ("cost_approx_tax_narrative", "6. 相关税费", ["cost_approx_analysis"]),
    ("cost_approx_development_narrative", "7. 土地开发费", ["land_development_set", "cost_approx_analysis"]),
    ("cost_approx_interest_narrative", "8. 投资利息", ["cost_approx_analysis"]),
    ("cost_approx_profit_narrative", "9. 投资利润", ["cost_approx_analysis"]),
    ("cost_approx_value_added_narrative", "10. 土地增值收益", ["cost_approx_analysis"]),
    ("cost_approx_term_narrative", "11. 土地使用年期修正", ["land_use_term", "cost_approx_analysis"]),
    ("cost_approx_location_narrative", "12. 区位修正", ["cost_approx_analysis"]),
    ("cost_approx_solve_narrative", "13. 成本逼近法价格计算", ["cost_approx_analysis", "cost_approx_price"]),
)

BENCHMARK_NARRATIVE_SECTIONS = (
    ("benchmark_corr_method_intro", "基准地价系数修正法估价过程", ["land_usage_key"]),
    ("benchmark_corr_base_price", "1、基准地价评估依据", ["benchmark_corr_analysis"]),
    ("benchmark_corr_formula", "2、基准地价系数修正法的基本公式", ["benchmark_corr_analysis"]),
    ("benchmark_corr_po", "3、确定基准地价（Po）", ["benchmark_corr_analysis", "land_location_full"]),
    ("benchmark_corr_route_price", "路线价（Po）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_kv", "4、容积率修正系数（Kv）的确定", ["benchmark_corr_analysis", "plot_ratio"]),
    ("benchmark_corr_ky", "5、土地使用年期修正系数（Ky）的确定", ["benchmark_corr_analysis", "land_use_term"]),
    ("benchmark_corr_kt", "6、期日修正系数（Kt）的确定", ["benchmark_corr_analysis", "valuation_date"]),
    ("benchmark_corr_ki", "7、区域因素修正系数（∑Ki）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_frontage_special_intro", "商服用地临街宗地特别因素修正", ["benchmark_corr_analysis", "land_area"]),
    ("benchmark_corr_kc", "街角地修正系数（Kc）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_kd", "临街深度修正系数（Kd）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_kk", "临街宽度修正系数（Kk）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_ks", "8、宗地面积修正系数（Ks）的确定", ["benchmark_corr_analysis", "land_area", "land_area_mode"]),
    ("benchmark_corr_ka", "9、宗地形状修正系数（Ka）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_ku", "周边土地利用类型修正系数（Ku）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_ke", "10、景观环境修正系数（Ke）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_kto", "11、建筑物朝向修正系数（Kto）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_kf", "12、开发程度修正额（Kf）的确定", ["benchmark_corr_analysis"]),
    ("benchmark_corr_solve", "13、基准地价系数修正法地价计算", ["benchmark_corr_analysis", "benchmark_corr_price"]),
)

INCOME_NARRATIVE_SECTIONS = (
    ("income_cap_method_intro", "1. 方法定义、公式及测算思路", []),
    ("income_cap_gross_income_intro", "2. 地上建筑物与租金实例说明", ["room_detail_location", "land_location_full", "building_area", "land_area"]),
    ("income_cap_rent_factor_intro", "3. 编制租金案例比较因素表", []),
    ("income_cap_rent_factor_basis", "4. 租金比较因素修正说明", []),
    ("income_cap_rent_solve_narrative", "5. 求取住宅用房月租金", []),
    ("income_cap_annual_gross_narrative", "6. 确定房地年总收益", ["building_area"]),
    ("income_cap_expense_narrative", "7. 确定房地年总费用", []),
    ("income_cap_real_estate_net_narrative", "8. 房地年纯收益", []),
    ("income_cap_building_income_intro", "9. 房屋年纯收益与还原率说明", []),
    ("income_cap_building_income_solve", "10. 房屋年纯收益求取", []),
    ("income_cap_land_income_narrative", "11. 土地年纯收益", []),
    ("income_cap_total_price_narrative", "12. 待估宗地总地价", ["land_use_term"]),
    ("income_cap_unit_price_narrative", "13. 宗地单位面积地价", ["income_cap_price"]),
)


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value)


SEGMENT_CONTAINER_KEYS = {
    "generated_narratives",
    "effective_narratives",
    "narrative_overrides",
    "narrative_segment_sources",
    "tables",
    "results",
    "warnings",
    "content_blocks",
}


def _flatten_analysis_values(value: Any, prefix: str) -> Dict[str, Any]:
    flattened: Dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in SEGMENT_CONTAINER_KEYS:
                continue
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(_flatten_analysis_values(item, child_prefix))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, dict) and item.get("slot"):
                child_key = str(item.get("slot"))
            elif isinstance(item, dict) and item.get("key"):
                child_key = str(item.get("key"))
            else:
                child_key = str(index)
            child_prefix = f"{prefix}.{child_key}" if prefix else child_key
            flattened.update(_flatten_analysis_values(item, child_prefix))
    else:
        text = str(value or "").strip()
        if text and len(text) <= 80:
            flattened[prefix] = text
    return flattened


def _is_useful_process_segment_value(ref: str, value: Any) -> bool:
    text = str(value or "").strip()
    if not text or text in {"待校核", "【待校核】", "______", "合理"}:
        return False
    if any(token in ref for token in (".group", ".label", ".source", "source_doc", "_range_label", ".confirmed", "_source_ref")):
        return False
    if text in {"元/平方米", "元/㎡", "元/m2", "元/平方米·月", "元/㎡·月", "元/m2·月", "住宅", "居住", "用地"}:
        return False
    if len(text) <= 1:
        return False
    compact_number = text.replace(".", "", 1).replace("%", "", 1)
    if compact_number.isdigit() and len(text) <= 3:
        return False
    return True


def _mark_contextual_segment(
    segments: List[Dict[str, Any]],
    literal: str,
    field_name: str,
    *,
    prefix: str = "",
    suffix: str = "",
) -> List[Dict[str, Any]]:
    if not literal:
        return segments
    if not prefix and not suffix:
        return _mark_literal_segments(segments, literal, field_name, override_existing=False)
    pattern = re.compile(f"({re.escape(prefix)})({re.escape(literal)})({re.escape(suffix)})")
    marked: List[Dict[str, Any]] = []
    for seg in segments:
        if "field" in seg or "fields" in seg:
            marked.append(seg)
            continue
        seg_text = str(seg.get("text") or "")
        cursor = 0
        matched = False
        for match in pattern.finditer(seg_text):
            matched = True
            if match.start() > cursor:
                marked.append({"text": seg_text[cursor:match.start()]})
            if match.group(1):
                marked.append({"text": match.group(1)})
            marked.append({"text": match.group(2), "field": field_name})
            if match.group(3):
                marked.append({"text": match.group(3)})
            cursor = match.end()
        if matched:
            if cursor < len(seg_text):
                marked.append({"text": seg_text[cursor:]})
        else:
            marked.append(seg)
    return marked


def _apply_explicit_narrative_segments(
    segments: List[Dict[str, Any]], entries: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    full_text = "".join(str(segment.get("text") or "") for segment in segments)
    if not full_text:
        return segments

    marked_spans: List[tuple[int, int, Dict[str, Any]]] = []
    cursor = 0
    for segment in segments:
        text = str(segment.get("text") or "")
        end = cursor + len(text)
        if text and (segment.get("field") or segment.get("fields")):
            attributes = {key: value for key, value in segment.items() if key != "text"}
            marked_spans.append((cursor, end, attributes))
        cursor = end

    def overlaps_marked(start: int, end: int) -> bool:
        return any(start < marked_end and end > marked_start for marked_start, marked_end, _ in marked_spans)

    for entry in sorted(
        entries or [],
        key=lambda item: (int(item.get("priority") or 0), len(str(item.get("text") or ""))),
        reverse=True,
    ):
        literal = str(entry.get("text") or "").strip()
        field_name = str(entry.get("field") or "").strip()
        if not literal or not field_name:
            continue
        prefix = str(entry.get("prefix") or "")
        suffix = str(entry.get("suffix") or "")
        if prefix or suffix:
            pattern = re.compile(f"({re.escape(prefix)})({re.escape(literal)})({re.escape(suffix)})")
            matches = ((match.start(2), match.end(2)) for match in pattern.finditer(full_text))
        else:
            pattern = re.compile(re.escape(literal))
            matches = ((match.start(), match.end()) for match in pattern.finditer(full_text))
        for start, end in matches:
            if overlaps_marked(start, end):
                continue
            marked_spans.append((start, end, {"field": field_name}))

    marked_spans.sort(key=lambda item: item[0])
    rebuilt: List[Dict[str, Any]] = []
    cursor = 0
    for start, end, attributes in marked_spans:
        if start > cursor:
            rebuilt.append({"text": full_text[cursor:start]})
        rebuilt.append({"text": full_text[start:end], **attributes})
        cursor = end
    if cursor < len(full_text):
        rebuilt.append({"text": full_text[cursor:]})
    return rebuilt


def _normalize_process_segment_sources(analysis_key: str, analysis: Dict[str, Any], source_values: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(source_values)
    if analysis_key == "income_cap_analysis":
        profile = analysis.get("building_profile") or {}
        location_ref = str(profile.get("building_location_source_ref") or "").strip()
        location_value = normalized.pop("income_cap_analysis.building_profile.building_location", None)
        if location_value:
            normalized[location_ref or "income_cap_analysis.building_profile.building_location"] = location_value
        valuation_date = normalized.pop("income_cap_analysis.expense_parameters.valuation_date", None)
        if valuation_date:
            normalized["valuation_date"] = valuation_date
    return {
        ref: value
        for ref, value in normalized.items()
        if _is_useful_process_segment_value(ref, value)
    }


def _narrative_segments(text: str, analysis_key: str, analysis: Dict[str, Any], fallback_refs: List[str]) -> List[Dict[str, Any]]:
    source_values = _flatten_analysis_values(analysis, analysis_key)
    for ref in fallback_refs:
        if ref == analysis_key or ref.endswith("_analysis"):
            continue
        if ref not in source_values and ref in analysis:
            value = str(analysis.get(ref) or "").strip()
            if value:
                source_values[ref] = value
    source_values = _normalize_process_segment_sources(analysis_key, analysis, source_values)
    return compile_desc_segments(text, source_values)


def _narrative_section(
    key: str,
    title: str,
    generated: Dict[str, str],
    effective: Dict[str, str],
    overrides: Dict[str, str],
    hotspot_refs: List[str],
    *,
    segments: List[Dict[str, Any]] | None = None,
) -> ProcessNarrativeSection:
    generated_text = str(generated.get(key) or "")
    effective_text = str(effective.get(key) or generated_text)
    segment_refs: List[str] = []
    for segment in segments or []:
        if segment.get("field"):
            segment_refs.append(str(segment.get("field")))
        for field in segment.get("fields") or []:
            segment_refs.append(str(field))
    broad_refs = {
        "cost_approx_analysis",
        "cost_approx_analysis.acquisition_items",
        "cost_approx_analysis.tax_items",
        "cost_approx_analysis.development_items",
        "cost_approx_analysis.usage_scenarios",
        "cost_approx_analysis.usage_results",
        "market_comp_analysis",
        "market_comp_analysis.selected_cases",
        "market_comp_analysis.factors",
        "income_cap_analysis",
    }
    clean_segment_refs = [ref for ref in segment_refs if ref not in broad_refs]
    merged_refs = (
        list(dict.fromkeys(clean_segment_refs))
        if clean_segment_refs
        else list(dict.fromkeys(hotspot_refs))
    )
    return ProcessNarrativeSection(
        key=key,
        title=title,
        generated_text=generated_text,
        effective_text=effective_text,
        override_text=str(overrides[key]) if key in overrides else None,
        segments=segments or [],
        hotspot_refs=merged_refs,
        complete=bool(effective_text.strip()) and "【待" not in effective_text and "【请" not in effective_text,
    )


def _market_process(data: Dict[str, Any], comparable_library: Any) -> MethodProcessDraft:
    analysis = _as_dict(data.get("market_comp_analysis"))
    warnings: List[Dict[str, str]] = []
    if analysis:
        try:
            if len(analysis.get("case_ids") or []) == 3:
                analysis = comparable_library.calculate_market_comparison(analysis)
            else:
                analysis.update(comparable_library.build_render_fields(analysis))
        except (KeyError, ValueError) as exc:
            warnings.append({"level": "warning", "message": str(exc)})
            analysis.update(comparable_library.build_render_fields(analysis))
    else:
        analysis = comparable_library.build_render_fields({})

    generated = analysis.get("generated_narratives") or {}
    effective = analysis.get("effective_narratives") or generated
    overrides = analysis.get("narrative_overrides") or {}
    explicit_sources = analysis.get("narrative_segment_sources") or {}
    warnings.extend(analysis.get("warnings") or [])
    evidence_ids = data.get("market_comp_evidence_snapshot_ids") or analysis.get("evidence_snapshot_ids") or []
    if len(evidence_ids) < 3:
        warnings.append(
            {
                "level": "warning",
                "message": "比较实例 A/B/C 成交公告截图尚未全部上传。",
                "target": "evidence",
            }
        )
    location_ids = data.get("market_comp_location_snapshot_ids") or []
    if len(location_ids) < 3:
        warnings.append(
            {
                "level": "warning",
                "message": "比较实例 A/B/C 位置图尚未全部上传。",
                "target": "evidence",
            }
        )
    site_ids = data.get("market_comp_site_snapshot_ids") or []
    if len(site_ids) < 3:
        warnings.append(
            {
                "level": "warning",
                "message": "比较实例 A/B/C 现状图尚未全部上传。",
                "target": "evidence",
            }
        )
    basis_needs_adjustment = analysis.get("comparable_basis_status") == "needs_adjustment"
    basis_has_override = "market_comp_comparable_basis" in overrides and bool(
        str(overrides.get("market_comp_comparable_basis") or "").strip()
    )
    if basis_needs_adjustment and not basis_has_override:
        warnings.append(
            {
                "level": "warning",
                "message": "价格可比基础标记为需要调整，请在最终正文中修改该段后再归档。",
                "target": "narratives",
            }
        )
    complete = bool(analysis.get("complete")) and len(evidence_ids) >= 3 and not (
        basis_needs_adjustment and not basis_has_override
    )
    tables = [
        ProcessTableSection(**item)
        for item in build_market_comparison_table_sections(dict(data, market_comp_analysis=analysis))
    ]

    def market_segments(key: str, refs: List[str]) -> List[Dict[str, Any]]:
        text = str((effective or generated).get(key) or "")
        if key in explicit_sources:
            segments = compile_desc_segments(text, {})
        else:
            segments = _narrative_segments(text, "market_comp_analysis", analysis, refs)
        return _apply_explicit_narrative_segments(segments, explicit_sources.get(key) or [])

    narratives = [
        _narrative_section(
            key,
            title,
            generated,
            effective,
            overrides,
            refs,
            segments=market_segments(key, refs),
        )
        for key, title, refs in MARKET_NARRATIVE_SECTIONS
    ]
    basis_section = next(item for item in narratives if item.key == "market_comp_comparable_basis")
    if basis_needs_adjustment:
        basis_section.review_state = "needs_adjustment"
        basis_section.review_message = "价格口径存在差异，请直接在最终正文中修改本段；完成修改后系统才允许正式归档。"
        basis_section.complete = basis_has_override
    content_order = [
        ("narrative", "market_comp_method_intro"),
        ("narrative", "market_comp_step1_instances"),
        ("table", "market_comp_basic_rows"),
        ("narrative", "market_comp_comparable_basis"),
        ("narrative", "market_comp_factor_selection"),
        ("narrative", "market_comp_condition_intro"),
        ("table", "market_comp_factor_condition_rows"),
        ("narrative", "market_comp_index_basis"),
        ("table", "market_comp_time_index_rows"),
        ("table", "market_comp_factor_index_rows"),
        ("table", "market_comp_correction_rows"),
        ("narrative", "market_comp_step4_solve"),
        ("result", "market_comp_price"),
    ]
    return MethodProcessDraft(
        method_key="market_comp",
        name="市场比较法",
        status="complete" if complete else "incomplete",
        complete=complete,
        narratives=narratives,
        tables=tables,
        content_blocks=[ProcessContentBlock(type=kind, key=key) for kind, key in content_order],
        results=[
            CalculationResult(
                key="market_comp_price",
                label="市场比较法最终单价",
                value=analysis.get("market_comp_price") or data.get("market_comp_price"),
                unit="元/平方米",
                formula="三宗比较实例比准价格的算术平均值",
            )
        ],
        warnings=list({item.get("message"): item for item in warnings if item.get("message")}.values()),
    )


def _cost_process(data: Dict[str, Any], base_dir: str) -> MethodProcessDraft:
    analysis = calculate_cost_approximation(data, base_dir)
    generated = analysis.get("generated_narratives") or {}
    effective = analysis.get("effective_narratives") or generated
    overrides = analysis.get("narrative_overrides") or {}
    explicit_sources = analysis.get("narrative_segment_sources") or {}

    def cost_segments(key: str, refs: List[str]) -> List[Dict[str, Any]]:
        text = str((effective or generated).get(key) or "")
        if key in explicit_sources:
            segments = compile_desc_segments(text, {})
        else:
            segments = _narrative_segments(text, "cost_approx_analysis", analysis, refs)
        return _apply_explicit_narrative_segments(segments, explicit_sources.get(key) or [])

    narratives = [
        _narrative_section(
            key,
            title,
            generated,
            effective,
            overrides,
            refs,
            segments=cost_segments(key, refs),
        )
        for key, title, refs in COST_NARRATIVE_SECTIONS
    ]
    visible_table_keys = {
        str(block.get("key") or "")
        for block in analysis.get("content_blocks") or []
        if block.get("type") == "table"
    }
    tables = [
        ProcessTableSection(**item)
        for item in analysis.get("tables") or []
        if str(item.get("key") or "") in visible_table_keys
    ]
    results = [CalculationResult(**item) for item in analysis.get("results") or []]
    content_order = [
        (str(item.get("type") or ""), str(item.get("key") or ""))
        for item in analysis.get("content_blocks") or []
        if item.get("type") and item.get("key")
    ]
    content_order.extend(("result", item.key) for item in results)
    return MethodProcessDraft(
        method_key="cost_approx",
        name="成本逼近法",
        status="complete" if analysis.get("complete") else "incomplete",
        complete=bool(analysis.get("complete")),
        narratives=narratives,
        tables=tables,
        content_blocks=[ProcessContentBlock(type=kind, key=key) for kind, key in content_order],
        results=results,
        warnings=analysis.get("warnings") or [],
    )


def _benchmark_corr_process(data: Dict[str, Any], base_dir: str) -> MethodProcessDraft:
    analysis = calculate_benchmark_correction(data, base_dir)
    generated = analysis.get("generated_narratives") or {}
    effective = analysis.get("effective_narratives") or generated
    overrides = analysis.get("narrative_overrides") or {}
    explicit_sources = analysis.get("narrative_segment_sources") or {}

    def benchmark_segments(key: str, refs: List[str]) -> List[Dict[str, Any]]:
        text = str((effective or generated).get(key) or "")
        if key in explicit_sources:
            segments = compile_desc_segments(text, {})
        else:
            segments = _narrative_segments(text, "benchmark_corr_analysis", analysis, refs)
        return _apply_explicit_narrative_segments(segments, explicit_sources.get(key) or [])

    narratives = [
        _narrative_section(
            key,
            title,
            generated,
            effective,
            overrides,
            refs,
            segments=benchmark_segments(key, refs),
        )
        for key, title, refs in BENCHMARK_NARRATIVE_SECTIONS
    ]
    visible_table_keys = {
        str(block.get("key") or "")
        for block in analysis.get("content_blocks") or []
        if block.get("type") == "table"
    }
    tables = [
        ProcessTableSection(**item)
        for item in analysis.get("tables") or []
        if str(item.get("key") or "") in visible_table_keys
    ]
    results = [CalculationResult(**item) for item in analysis.get("results") or []]
    content_order = [
        (str(item.get("type") or ""), str(item.get("key") or ""))
        for item in analysis.get("content_blocks") or []
        if item.get("type") and item.get("key")
    ]
    return MethodProcessDraft(
        method_key="benchmark_corr",
        name="基准地价系数修正法",
        status="complete" if analysis.get("complete") else "incomplete",
        complete=bool(analysis.get("complete")),
        narratives=narratives,
        tables=tables,
        content_blocks=[ProcessContentBlock(type=kind, key=key) for kind, key in content_order],
        results=results,
        warnings=analysis.get("warnings") or [],
    )


def _income_process(data: Dict[str, Any]) -> MethodProcessDraft:
    analysis = calculate_income_capitalization(data)
    generated = analysis.get("generated_narratives") or {}
    effective = analysis.get("effective_narratives") or generated
    overrides = analysis.get("narrative_overrides") or {}
    explicit_sources = analysis.get("narrative_segment_sources") or {}

    def income_segments(key: str, refs: List[str]) -> List[Dict[str, Any]]:
        text = str((effective or generated).get(key) or "")
        if key in explicit_sources:
            segments = compile_desc_segments(text, {})
        else:
            segments = _narrative_segments(text, "income_cap_analysis", analysis, refs)
        return _apply_explicit_narrative_segments(segments, explicit_sources.get(key) or [])

    narratives = [
        _narrative_section(
            key,
            title,
            generated,
            effective,
            overrides,
            refs,
            segments=income_segments(key, refs),
        )
        for key, title, refs in INCOME_NARRATIVE_SECTIONS
    ]
    tables = [ProcessTableSection(**item) for item in analysis.get("tables") or []]
    results = [CalculationResult(**item) for item in analysis.get("results") or []]
    content_order = [
        ("narrative", "income_cap_method_intro"),
        ("narrative", "income_cap_gross_income_intro"),
        ("table", "income_rent_evidence_rows"),
        ("narrative", "income_cap_rent_factor_intro"),
        ("table", "income_rent_condition_rows"),
        ("narrative", "income_cap_rent_factor_basis"),
        ("table", "income_rent_index_rows"),
        ("table", "income_rent_correction_rows"),
        ("narrative", "income_cap_rent_solve_narrative"),
        ("narrative", "income_cap_annual_gross_narrative"),
        ("narrative", "income_cap_expense_narrative"),
        ("narrative", "income_cap_real_estate_net_narrative"),
        ("narrative", "income_cap_building_income_intro"),
        ("table", "income_cap_rate_rows"),
        ("narrative", "income_cap_building_income_solve"),
        ("narrative", "income_cap_land_income_narrative"),
        ("narrative", "income_cap_total_price_narrative"),
        ("narrative", "income_cap_unit_price_narrative"),
        ("result", "income_cap_price"),
    ]
    return MethodProcessDraft(
        method_key="income_cap",
        name="收益还原法",
        status="complete" if analysis.get("complete") else "incomplete",
        complete=bool(analysis.get("complete")),
        narratives=narratives,
        tables=tables,
        content_blocks=[ProcessContentBlock(type=kind, key=key) for kind, key in content_order],
        results=results,
        warnings=analysis.get("warnings") or [],
    )


def _skeleton_process(
    method_key: str,
    name: str,
    analysis_value: Any,
    intro_key: str,
    generated_data: Dict[str, Any],
) -> MethodProcessDraft:
    analysis = _as_dict(analysis_value)
    intro = str(generated_data.get(intro_key) or "")
    narratives = [
        ProcessNarrativeSection(
            key=intro_key,
            title="方法定义、公式及变量解释",
            generated_text=intro,
            effective_text=intro,
            editable=False,
            complete=bool(intro),
        )
    ]
    for key, text in (analysis.get("narratives") or {}).items():
        narratives.append(
            ProcessNarrativeSection(
                key=str(key),
                title=str(key),
                generated_text=str(text or ""),
                effective_text=str(text or ""),
                editable=False,
                complete=bool(str(text or "").strip()),
            )
        )
    tables = [
        ProcessTableSection(
            key=str(item.get("key") or ""),
            title=str(item.get("title") or item.get("key") or "结构化表格"),
            columns=list(item.get("columns") or []),
            rows=list(item.get("rows") or []),
        )
        for item in analysis.get("tables") or []
    ]
    results = [CalculationResult(**item) for item in analysis.get("results") or []]
    warnings = list(analysis.get("warnings") or [])
    warnings.append({"level": "info", "message": "该方法当前仅展示类型化骨架，完整结构化计算过程待建设。"})
    return MethodProcessDraft(
        method_key=method_key,
        name=name,
        status="skeleton",
        complete=False,
        narratives=narratives,
        tables=tables,
        results=results,
        warnings=warnings,
    )


def build_valuation_process_draft(data: Dict[str, Any], comparable_library: Any) -> Dict[str, Any]:
    generated_data = derive_valuation_descriptions(deepcopy(data), overwrite=False)
    methods: List[MethodProcessDraft] = []
    for method_key, flag, name, analysis_key, intro_key in METHODS:
        if not bool(data.get(flag)):
            continue
        if method_key == "cost_approx":
            methods.append(_cost_process(generated_data, comparable_library.base_dir))
        elif method_key == "market_comp":
            methods.append(_market_process(generated_data, comparable_library))
        elif method_key == "income_cap":
            methods.append(_income_process(generated_data))
        elif method_key == "benchmark_corr":
            methods.append(_benchmark_corr_process(generated_data, comparable_library.base_dir))
        else:
            methods.append(_skeleton_process(method_key, name, data.get(analysis_key), intro_key, generated_data))
    return ValuationProcessDraft(methods=methods).model_dump()
