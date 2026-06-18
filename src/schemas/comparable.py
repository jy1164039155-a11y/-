# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComparableCaseRecord(BaseModel):
    id: str
    source: str = "中国土地市场网"
    source_url: Optional[str] = None
    gd_guid: str
    electronic_supervision_no: Optional[str] = None
    project_name: Optional[str] = None
    location: Optional[str] = None
    administrative_region_code: Optional[str] = None
    administrative_region_name: Optional[str] = None
    land_usage_raw: Optional[str] = None
    land_usage_key: Optional[str] = None
    land_usage_first_level: Optional[str] = None
    supply_method: Optional[str] = None
    area_sqm: Optional[str] = None
    total_price_wan: Optional[str] = None
    unit_price_sqm: Optional[str] = None
    transaction_date: Optional[str] = None
    use_term_years: Optional[str] = None
    land_level: Optional[str] = None
    recipient: Optional[str] = None
    plot_ratio_min: Optional[str] = None
    plot_ratio_max: Optional[str] = None
    manual_fields: Dict[str, Any] = Field(default_factory=dict)
    manual_draft_fields: Dict[str, Any] = Field(default_factory=dict)
    official_fields: Dict[str, Any] = Field(default_factory=dict)
    fetched_at: Optional[str] = None
    updated_at: Optional[str] = None


class ComparableCaseSnapshot(BaseModel):
    snapshot_id: str
    case_id: str
    snapshot_hash: str
    data: Dict[str, Any]
    created_at: str
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    image_paths: List[str] = Field(default_factory=list)


class FactorLevel(BaseModel):
    label: str
    index: str
    description: str = ""


class FactorDefinition(BaseModel):
    key: str
    label: str
    group: str
    required: bool = True
    source: str = "manual"
    note: str = ""
    help_text: str = ""
    levels: List[FactorLevel] = Field(default_factory=list)
    review_status: str = "needs_review"
    order: int = 0
    enabled: bool = True


class FactorScheme(BaseModel):
    land_usage_key: str
    name: str
    factors: List[FactorDefinition] = Field(default_factory=list)
    updated_at: Optional[str] = None


class FactorCaseValue(BaseModel):
    value: Optional[Any] = None
    index: Optional[str] = None
    confirmed: bool = False
    level_label: Optional[str] = None
    source: str = "manual"
    override_reason: Optional[str] = None


class MarketComparisonFactor(BaseModel):
    key: str
    label: str
    group: str
    required: bool = True
    source: str = "manual"
    help_text: str = ""
    levels: List[FactorLevel] = Field(default_factory=list)
    review_status: str = "needs_review"
    subject_value: Optional[Any] = None
    subject_index: str = "100"
    cases: Dict[str, FactorCaseValue] = Field(default_factory=dict)


class MarketComparisonAnalysis(BaseModel):
    subject: Dict[str, Any] = Field(default_factory=dict)
    case_ids: List[str] = Field(default_factory=list)
    selected_cases: List[Dict[str, Any]] = Field(default_factory=list)
    factors: List[MarketComparisonFactor] = Field(default_factory=list)
    factor_scheme_snapshot: Optional[Dict[str, Any]] = None
    monthly_growth_rate: str = "0.13"
    land_reduction_rate: str = "5.4"
    comparable_basis_status: str = "consistent"
    calculations: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)
    complete: bool = False
    market_comp_price: Optional[str] = None
    evidence_snapshot_ids: List[str] = Field(default_factory=list)
    narrative_overrides: Dict[str, str] = Field(default_factory=dict)
    generated_narratives: Dict[str, str] = Field(default_factory=dict)
    effective_narratives: Dict[str, str] = Field(default_factory=dict)
    narrative_segment_sources: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)


class CrawlJobRequest(BaseModel):
    xzq_dm: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    land_usage_key: Optional[str] = None
    land_usage: Optional[str] = None
    supply_method: Optional[str] = None
    location: Optional[str] = None
    electronic_supervision_no: Optional[str] = None
    refresh_complete_details: bool = False


class MarketComparisonCalculateRequest(BaseModel):
    analysis: MarketComparisonAnalysis
