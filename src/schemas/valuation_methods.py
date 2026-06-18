# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CalculationParameter(BaseModel):
    key: str
    label: str
    value: Optional[Any] = None
    unit: str = ""
    source: str = "manual"
    confirmed: bool = False


class MethodTable(BaseModel):
    key: str
    title: str
    report_title: str = ""
    columns: List[str] = Field(default_factory=list)
    header_rows: List[List[Dict[str, Any]]] = Field(default_factory=list)
    group_columns: List[int] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    source_target: str = ""


class CalculationResult(BaseModel):
    key: str
    label: str
    value: Optional[str] = None
    unit: str = ""
    formula: str = ""


class StructuredMethodAnalysis(BaseModel):
    parameters: List[CalculationParameter] = Field(default_factory=list)
    tables: List[MethodTable] = Field(default_factory=list)
    results: List[CalculationResult] = Field(default_factory=list)
    narratives: Dict[str, str] = Field(default_factory=dict)
    warnings: List[Dict[str, str]] = Field(default_factory=list)
    complete: bool = False


class CostPolicyDocument(BaseModel):
    key: str = ""
    name: str = ""
    document_no: str = ""
    publish_date: str = ""
    effective_date: str = ""
    expiry_date: str = ""
    region: str = "湖南省"
    source_path: str = ""
    source_hash: str = ""
    valuation_date: str = ""
    applicable: bool = True
    confirmed: bool = False
    role: str = ""
    source_type: str = "system_recommendation"
    reference_text: str = ""
    enabled: bool = True
    replaces_key: str = ""
    note: str = ""


class CostCalculationItem(BaseModel):
    key: str = ""
    label: str = ""
    name: str = ""
    category: str = ""
    standard_value: Optional[str] = None
    standard_unit: str = "元/平方米"
    quantity: Optional[str] = None
    coefficient: Optional[str] = None
    amount_per_sqm: Optional[str] = None
    computed_amount_per_sqm: Optional[str] = None
    exclusion_reason: str = ""
    rule_key: str = ""
    rule_snapshot: Dict[str, Any] = Field(default_factory=dict)
    grade_name: str = ""
    formula: str = ""
    source: str = "manual"
    source_note: str = ""
    policy_key: str = ""
    confirmed: bool = False
    enabled: bool = True


class ExternalCalculationResult(BaseModel):
    key: str
    result_type: str
    label: str
    value: Optional[str] = None
    unit: str = "元/平方米"
    software_name: str = ""
    software_version: str = ""
    source_file: str = ""
    source_sheet: str = ""
    source_cell: str = ""
    source_hash: str = ""
    calculated_at: str = ""
    note: str = ""
    confirmed: bool = False


class CostRiskItem(BaseModel):
    usage_key: str = ""
    group: str
    label: str
    group_weight: Optional[str] = None
    weight: Optional[str] = None
    level: str = ""
    adjustment_rate: Optional[str] = None
    confirmed: bool = False


class CostRiskGroup(BaseModel):
    usage_key: str = ""
    key: str = ""
    label: str = ""
    weight: Optional[str] = None
    computed_value: Optional[str] = None
    override_enabled: bool = False
    override_value: Optional[str] = None
    override_reason: str = ""
    effective_value: Optional[str] = None
    confirmed: bool = False


class CostLocationFactor(BaseModel):
    key: str = ""
    usage_key: str = ""
    group: str = ""
    label: str
    description: str = ""
    level: str = ""
    grade_amplitude: Optional[str] = None
    weight: Optional[str] = None
    correction_rate: Optional[str] = None
    source: str = "manual"
    confirmed: bool = False
    levels: List[str] = Field(default_factory=list)


class CostUsageScenario(BaseModel):
    key: str
    label: str
    use_term_years: Optional[str] = None
    profit_rate: Optional[str] = None
    value_added_rate: Optional[str] = None
    safe_rate: Optional[str] = None
    reduction_rate: Optional[str] = None
    location_correction_rate: Optional[str] = None
    confirmed: bool = False


class CostUsageResult(BaseModel):
    key: str
    label: str
    acquisition_total: str = "0"
    tax_total: str = "0"
    development_total: str = "0"
    interest: str = "0"
    profit: str = "0"
    cost_price: str = "0"
    value_added_income: str = "0"
    unlimited_price: str = "0"
    term_correction_factor: str = "1"
    comparable_price: str = "0"
    location_correction_rate: str = "0"
    final_price: str = "0"


class CostApproximationAnalysis(StructuredMethodAnalysis):
    acquisition_land_class: str = "耕地"
    acquisition_land_subclass: str = "水田"
    acquisition_land_class_confirmed: bool = True
    compensation_zone: str = "Ⅰ"
    compensation_zone_override: bool = False
    compensation_zone_source_path: str = ""
    compensation_zone_suggestion: Dict[str, Any] = Field(default_factory=dict)
    basis_land_location_full: str = ""
    basis_valuation_date: str = ""
    basis_land_class: str = ""
    basis_compensation_zone: str = ""
    basis_development_set: str = ""
    policy_basis: Dict[str, Any] = Field(default_factory=dict)
    local_compensation_policy_name: str = ""
    local_compensation_policy_no: str = ""
    local_compensation_policy_date: str = ""
    green_seedling_standard_per_mu: str = ""
    location_correction_mode: str = "direct_sum"
    location_template_key: str = ""
    location_template_snapshot: Dict[str, Any] = Field(default_factory=dict)
    policy_config_version: str = ""
    policy_config_hash: str = ""
    risk_mode: str = "direct"
    risk_scheme_key: str = "hunan_general"
    risk_groups: List[CostRiskGroup] = Field(default_factory=list)
    policy_documents: List[CostPolicyDocument] = Field(default_factory=list)
    acquisition_items: List[CostCalculationItem] = Field(default_factory=list)
    tax_items: List[CostCalculationItem] = Field(default_factory=list)
    development_items: List[CostCalculationItem] = Field(default_factory=list)
    development_survey_cases: List[Dict[str, Any]] = Field(default_factory=list)
    development_survey_analysis: Dict[str, str] = Field(default_factory=dict)
    building_compensation_rows: List[Dict[str, Any]] = Field(default_factory=list)
    resettlement_population_cases: List[Dict[str, Any]] = Field(default_factory=list)
    attachment_compensation_analysis: Dict[str, str] = Field(default_factory=dict)
    external_results: List[ExternalCalculationResult] = Field(default_factory=list)
    development_cycle_years: str = "1"
    interest_rate: str = "3"
    acquisition_investment_fraction: str = "1"
    development_investment_fraction: str = "0.5"
    risk_items: List[CostRiskItem] = Field(default_factory=list)
    location_factors: List[CostLocationFactor] = Field(default_factory=list)
    usage_scenarios: List[CostUsageScenario] = Field(default_factory=list)
    usage_results: List[CostUsageResult] = Field(default_factory=list)
    totals: Dict[str, str] = Field(default_factory=dict)
    rounding_trace: List[Dict[str, str]] = Field(default_factory=list)
    cost_approx_price: Optional[str] = None
    narrative_overrides: Dict[str, str] = Field(default_factory=dict)
    generated_narratives: Dict[str, str] = Field(default_factory=dict)
    effective_narratives: Dict[str, str] = Field(default_factory=dict)
    narrative_segment_sources: Dict[str, List[Dict[str, str]]] = Field(default_factory=dict)
    content_blocks: List[Dict[str, str]] = Field(default_factory=list)
    effective_local_city: str = ""


class IncomeCapitalizationAnalysis(StructuredMethodAnalysis):
    rent_instances: List[Dict[str, Any]] = Field(default_factory=list)
    rent_factor_items: List[Dict[str, Any]] = Field(default_factory=list)
    building_profile: Dict[str, Any] = Field(default_factory=dict)
    income_parameters: Dict[str, Any] = Field(default_factory=dict)
    expense_parameters: Dict[str, Any] = Field(default_factory=dict)
    cap_rate_parameters: Dict[str, Any] = Field(default_factory=dict)
    rent_calculations: List[Dict[str, Any]] = Field(default_factory=list)
    income_results: Dict[str, str] = Field(default_factory=dict)
    income_cap_price: Optional[str] = None
    narrative_overrides: Dict[str, str] = Field(default_factory=dict)
    generated_narratives: Dict[str, str] = Field(default_factory=dict)
    effective_narratives: Dict[str, str] = Field(default_factory=dict)


class BenchmarkCorrectionAnalysis(StructuredMethodAnalysis):
    factor_items: List[Dict[str, Any]] = Field(default_factory=list)
    land_usage: str = ""
    land_level: str = ""
    plot_ratio: str = ""
    land_use_term: str = ""
    land_area: str = ""
    land_area_mode: str = ""
    frontage_mode: str = ""
    route_segment_id: str = ""
    route_price: str = ""
    route_price_source_note: str = ""
    route_price_override_reason: str = ""
    route_road_type: str = ""
    frontage_depth_m: str = ""
    frontage_width_m: str = ""
    is_corner: bool = False
    corner_price_ratio: str = ""
    corner_coefficient: str = ""
    ku_grade: str = ""
    area_grade: str = ""
    shape_grade: str = ""
    landscape_grade: str = ""
    orientation: str = ""
    development_adjustment: str = ""
    development_note: str = ""
    region_factor_selections: List[Dict[str, Any]] = Field(default_factory=list)
    benchmark_corr_price: Optional[str] = None
    narrative_overrides: Dict[str, str] = Field(default_factory=dict)
    generated_narratives: Dict[str, str] = Field(default_factory=dict)
    effective_narratives: Dict[str, str] = Field(default_factory=dict)
    narrative_segment_sources: Dict[str, List[Dict[str, str]]] = Field(default_factory=dict)
    content_blocks: List[Dict[str, str]] = Field(default_factory=list)


class ResidualAnalysis(StructuredMethodAnalysis):
    property_sale_instances: List[Dict[str, Any]] = Field(default_factory=list)


class ProcessNarrativeSection(BaseModel):
    key: str
    title: str
    generated_text: str = ""
    effective_text: str = ""
    override_text: Optional[str] = None
    segments: List[Dict[str, Any]] = Field(default_factory=list)
    hotspot_refs: List[str] = Field(default_factory=list)
    editable: bool = True
    complete: bool = False
    review_state: str = "normal"
    review_message: str = ""
    warnings: List[Dict[str, str]] = Field(default_factory=list)


class ProcessTableSection(BaseModel):
    key: str
    title: str
    report_title: str = ""
    columns: List[str] = Field(default_factory=list)
    header_rows: List[List[Dict[str, Any]]] = Field(default_factory=list)
    group_columns: List[int] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    source_target: str = ""


class ProcessContentBlock(BaseModel):
    type: str
    key: str


class MethodProcessDraft(BaseModel):
    method_key: str
    name: str
    status: str = "skeleton"
    complete: bool = False
    narratives: List[ProcessNarrativeSection] = Field(default_factory=list)
    tables: List[ProcessTableSection] = Field(default_factory=list)
    content_blocks: List[ProcessContentBlock] = Field(default_factory=list)
    results: List[CalculationResult] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)


class ValuationProcessDraft(BaseModel):
    methods: List[MethodProcessDraft] = Field(default_factory=list)
