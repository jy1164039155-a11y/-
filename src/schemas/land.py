# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional, Dict, List

from src.schemas.comparable import MarketComparisonAnalysis
from src.schemas.valuation_methods import (
    BenchmarkCorrectionAnalysis,
    CostApproximationAnalysis,
    IncomeCapitalizationAnalysis,
    ResidualAnalysis,
)

class LandValuationContract(BaseModel):
    """
    全项目最高权威数据契约 (Data Contract) v3.0
    彻底告别任何 var_ 机器变量，100% 对齐全语义化占位符！
    """
    model_config = ConfigDict(populate_by_name=True)

    # 1. 📁 第一章：报告基本信息与地理区划
    client_name: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D2", 
        description="委托人名称（如道县自然资源局，用于智能派生地理区划）"
    )
    transfer_purpose_mode: str = Field("拟挂牌出让", description="出让行为选择模式，可选值：拟挂牌出让、办理土地使用权出让手续、其他")
    transfer_purpose: str = Field("拟挂牌出让", description="具体出让行为/目的名称（如选'其他'则为用户自定义文本）")
    project_name_suffix: str = Field("国有建设用地使用权市场价格评估", description="估价项目名称的后缀词语")
    project_name: Optional[str] = Field(None, description="估价项目名称")
    appraisal_org: str = Field(
        "湖南兆财不动产规划评估有限公司",
        alias="已开发建设土地（划拨办出让）!D6",
        description="受托估价机构名称"
    )
    land_user: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!E40", 
        description="土地使用者"
    )
    report_no: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D7", 
        description="评估报告编号"
    )
    technical_report_no: Optional[str] = Field(
        None,
        alias="已开发建设土地（划拨办出让）!J4",
        description="土地估价技术报告编号"
    )
    report_date: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D8", 
        description="报告出具日期"
    )
    report_valid_until: Optional[str] = Field(None, description="报告有效期截止日期")
    report_year_text: Optional[str] = Field(None, description="报告年份中文文本，如二〇二六年")
    valuation_date: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D15", 
        description="估价期日"
    )
    valuation_work_date: Optional[str] = Field(
        None,
        alias="已开发建设土地（划拨办出让）!D13",
        description="现场勘查与工作日期范围"
    )
    client_org_code: Optional[str] = Field(None, alias="已开发建设土地（划拨办出让）!E33", description="委托方统一社会信用代码")
    client_principal: Optional[str] = Field(None, alias="已开发建设土地（划拨办出让）!E34", description="委托方负责人")
    client_org_type: Optional[str] = Field(None, alias="已开发建设土地（划拨办出让）!E35", description="委托方机构性质")
    client_address: Optional[str] = Field(None, alias="已开发建设土地（划拨办出让）!E36", description="委托方机构地址")
    client_contact: Optional[str] = Field(None, alias="已开发建设土地（划拨办出让）!E37", description="委托方联系人")
    client_phone: Optional[str] = Field(None, alias="已开发建设土地（划拨办出让）!E38", description="委托方联系电话")
    client_postcode: Optional[str] = Field(None, alias="已开发建设土地（划拨办出让）!E39", description="委托方邮编")

    # 2. 📐 第二章：土地利用条件与规划限制指标
    land_location: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D3", 
        description="估价对象坐落位置（简称）"
    )
    land_plot_number: Optional[str] = Field("", description="地块编号或后缀描述，如'（2025018号地块）'")
    land_location_full: Optional[str] = Field(None, description="位置全称，自动拼接生成")
    parcel_count: str = Field(
        "一宗",
        alias="已开发建设土地（划拨办出让）!D4",
        description="宗地数量，如一宗、两宗"
    )
    county_name: Optional[str] = Field(None, description="估价所属县市简称，如道县、通道县")
    local_city: Optional[str] = Field(None, description="估价对象所属市级行政区，如永州市、怀化市")
    land_area: float = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!E19", 
        description="分摊土地使用权面积（平方米）"
    )
    building_area: float = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!E20", 
        description="建筑总面积（平方米）"
    )
    plot_ratio: float = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!E21", 
        description="规划容积率上限或固定值"
    )
    plot_ratio_mode: str = Field("range", description="规划容积率表达模式：range 表示范围值，fixed 表示固定值")
    plot_ratio_display: Optional[str] = Field(None, description="报告中用于展示规划容积率的文本，如0.7-4.23或4.23")
    set_plot_ratio_mode: str = Field("fixed", description="评估设定容积率表达模式：range 表示范围值，fixed 表示固定值")
    set_plot_ratio: Optional[float] = Field(None, description="评估设定容积率上限或固定值")
    set_plot_ratio_min: Optional[str] = Field(None, description="评估设定容积率下限")
    set_plot_ratio_display: Optional[str] = Field(None, description="评估设定容积率在报告中展示的拼接值")
    land_use_term: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!E25", 
        description="土地使用年限（如30年、70年）"
    )
    land_use_term_years: Optional[str] = Field(None, description="土地使用年限数字展示值，如70")
    right_type: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!E24", 
        description="设定土地使用权类型（如出让、划拨）"
    )
    land_usage: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D16", 
        description="设定土地用途全称（D16单元格）"
    )
    land_usage_key: Optional[str] = Field(None, description="土地用途下拉键")
    land_usage_other: Optional[str] = Field(None, description="其他土地用途原文")
    land_usage_current_class: Optional[str] = Field(None, description="兼容字段，当前与用地用海分类口径的土地用途保持一致")
    land_usage_price_class: Optional[str] = Field(None, description="按国土空间用途管制用地用海分类指南派生的价格测算口径一级类")
    land_usage_short: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D5", 
        description="土地设定用途简称"
    )
    land_usage_full: str = Field(
        ..., 
        alias="已开发建设土地（划拨办出让）!D16", 
        description="土地设定用途全称"
    )
    land_boundary_desc: Optional[str] = Field(
        None, 
        alias="已开发建设土地（划拨办出让）!E41",
        description="宗地四至状况"
    )
    
    # 规划条件特有指标参数（在 Web 界面可直接修改与保存，具有默认兜底，免于从 Excel 强制抓取 nan 导致崩溃）
    building_density_min: str = Field("35%", description="规划建筑密度下限")
    building_density_max: str = Field("55%", description="规划建筑密度上限")
    plot_ratio_min: str = Field("0.7", description="规划容积率下限")
    greening_rate: str = Field("≤15%", description="规划绿地率")
    building_height_limit: str = Field("24米", description="规划建筑限高")
    planning_approval_authority: Optional[str] = Field(None, description="规划条件批准机关")
    
    # 权属设定与自愈高语义字段
    valuation_condition_type: Optional[str] = Field(
        "现状", 
        alias="已开发建设土地（划拨办出让）!E18", 
        description="估价设定利用条件，如现状、规划"
    )
    registered_right_type: Optional[str] = Field(
        "行政划拨", 
        alias="已开发建设土地（划拨办出让）!E23", 
        description="原登记土地使用权类型，如行政划拨"
    )
    assumed_right_status: Optional[str] = Field(
        "无他项权利的完全权利条件", 
        alias="已开发建设土地（划拨办出让）!E28", 
        description="设定土地权利状态描述"
    )
    registered_proof_docs: Optional[str] = Field(
        None, 
        alias="已开发建设土地（划拨办出让）!E22", 
        description="原始权属登记的依据文书"
    )
    land_development_actual: Optional[str] = Field(
        None,
        alias="已开发建设土地（划拨办出让）!E26",
        description="估价期日实际土地开发程度"
    )
    land_development_set: Optional[str] = Field(
        None,
        alias="已开发建设土地（划拨办出让）!E27",
        description="估价设定土地开发程度"
    )
    entrusted_source_docs: Optional[str] = Field(
        None,
        alias="已开发建设土地（划拨办出让）!E56",
        description="委托方提供资料清单"
    )
    regional_factor_title: Optional[str] = Field("土地市场状况", description="区域环境分析子小节标题")
    other_special_notes_ref: Optional[str] = Field("第十一部分  其他需要说明的事项", description="特殊说明事项指向正文章节")

    # 3. ⚖️ 第四章：评估方法选择与加权确价
    cost_approx_price: Optional[str] = Field(None, description="成本逼近法单价")
    market_comp_price: Optional[str] = Field(None, description="市场比较法单价")
    income_cap_price: Optional[str] = Field(
        None, 
        alias="基本信息!F34",
        description="收益还原法单价"
    )
    benchmark_corr_price: Optional[str] = Field(
        None, 
        alias="基本信息!D34",
        description="基准地价系数修正法单价"
    )
    residual_price: Optional[str] = Field(None, description="剩余法单价")
    market_comp_analysis: Optional[MarketComparisonAnalysis] = Field(None, description="市场比较法结构化分析快照")
    market_comp_step1_instances: Optional[str] = Field(None, description="市场比较法比较实例选择正文")
    market_comp_basic_rows: List[Dict[str, Any]] = Field(default_factory=list, description="比较实例基本情况表行")
    market_comp_factor_condition_rows: List[Dict[str, Any]] = Field(default_factory=list, description="因素条件说明表行")
    market_comp_time_index_rows: List[Dict[str, Any]] = Field(default_factory=list, description="交易期日指数表行")
    market_comp_factor_index_rows: List[Dict[str, Any]] = Field(default_factory=list, description="因素条件指数表行")
    market_comp_correction_rows: List[Dict[str, Any]] = Field(default_factory=list, description="因素修正系数表行")
    market_comp_step4_solve: Optional[str] = Field(None, description="市场比较法求价正文")
    market_comp_comparable_basis: Optional[str] = Field(None, description="市场比较法建立价格可比基础正文")
    market_comp_factor_selection: Optional[str] = Field(None, description="市场比较法比较因素选择正文")
    market_comp_condition_intro: Optional[str] = Field(None, description="市场比较法因素条件说明正文")
    market_comp_index_basis: Optional[str] = Field(None, description="市场比较法因素条件指数编制依据正文")
    market_comp_verification: Optional[str] = Field(None, description="市场比较法系统核验正文")
    market_comp_evidence_snapshot_ids: List[str] = Field(default_factory=list, description="比较实例成交公告证据快照")
    market_comp_location_snapshot_ids: List[str] = Field(default_factory=list, description="比较实例位置图证据快照")
    market_comp_site_snapshot_ids: List[str] = Field(default_factory=list, description="比较实例现状图证据快照")
    instance_a_desc: Optional[str] = Field(None, description="比较实例A兼容正文")
    instance_b_desc: Optional[str] = Field(None, description="比较实例B兼容正文")
    instance_c_desc: Optional[str] = Field(None, description="比较实例C兼容正文")

    # 其余四种方法先建立结构化骨架；旧字段继续作为兼容渲染输出。
    cost_approx_analysis: Optional[CostApproximationAnalysis] = Field(None, description="成本逼近法结构化测算骨架")
    income_cap_analysis: Optional[IncomeCapitalizationAnalysis] = Field(None, description="收益还原法结构化测算骨架，租金实例独立保存")
    benchmark_corr_analysis: Optional[BenchmarkCorrectionAnalysis] = Field(None, description="基准地价系数修正法结构化测算骨架")
    residual_analysis: Optional[ResidualAnalysis] = Field(None, description="剩余法结构化测算骨架，商品房销售实例独立保存")
    base_price_doc_no: Optional[str] = Field(None, description="基准地价批准或发布文号")
    base_price_doc_name: Optional[str] = Field(None, description="基准地价公布或更新文件名称")
    base_price_doc_authority: Optional[str] = Field(None, description="基准地价批准或发布机关")
    base_price_rule_doc_name: Optional[str] = Field(
        "《关于进一步做好湖南省公示地价体系建设和管理有关工作的通知》",
        description="基准地价更新管理依据文件名称"
    )
    base_price_rule_doc_no: Optional[str] = Field("湘自资办发[2022]23号", description="基准地价更新管理依据文件文号")
    base_price_update_cycle_years_text: Optional[str] = Field("三", description="基准地价全面更新周期年限文本")
    base_price_disable_threshold_years_text: Optional[str] = Field("六", description="不得作为依据的超期年限文本")
    base_price_elapsed_years_text: Optional[str] = Field(None, description="基准地价基准日至估价期日的已满年限中文文本")
    base_price_elapsed_years_number: Optional[int] = Field(None, description="基准地价基准日至估价期日的已满年限数字")
    expired_years_text: Optional[str] = Field(None, description="【兼容】基准地价已满年限中文文本")

    # 控制开关与确价逻辑
    use_cost_approx: bool = Field(True, description="采用成本逼近法")
    use_market_comp: bool = Field(True, description="采用市场比较法")
    use_income_cap: bool = Field(False, description="采用收益还原法")
    use_benchmark_corr: bool = Field(False, description="采用基准地价系数修正法")
    use_residual: bool = Field(False, description="采用剩余法")
    
    is_base_price_expired: bool = Field(True, description="基准地价是否超期")
    show_price_in_text: bool = Field(True, description="正文中是否显示单价")
    weight_logic_type: Optional[str] = Field("weighted_average", description="确价逻辑：weighted_average、median、mode；兼容 simple_average、single_dominance")
    method_weight_percentages: Optional[Dict[str, str]] = Field(None, description="按估价方法 flag 存储的权重百分比，如 use_cost_approx=50")
    dominant_method_name: Optional[str] = Field("剩余法", description="主导评估方法名称")
    formula_display_text: Optional[str] = Field("成本逼近法×50%+市场比较法×50%", description="系统生成的确价公式或统计口径展现")
    land_level_type: Optional[str] = Field("residential_level_3", description="评估方法适用性长文本方案")
    method_combination_type: Optional[str] = Field("residential_residual_only", description="确价理由长文本方案")
    infrastructure_type: Optional[str] = Field("five_通_residential", description="基础设施开发程度长文本方案")
    weight_rationale_text: Optional[str] = Field("", description="采用方法加权理由阐述")
    explain_unselected_methods: bool = Field(True, description="是否在方法理由中说明未采用的估价方法")
    
    # 证据字段（Nullable可选字段，防老项目闪退）
    comparable_case_count: Optional[int] = Field(None, description="可比交易案例数量")
    case_similarity_level: Optional[str] = Field(None, description="案例可比性：高/中/低")
    case_time_valid: Optional[bool] = Field(None, description="案例交易时间是否处于合理区间")
    market_activity_level: Optional[str] = Field(None, description="同类用地市场活跃程度")

    has_stable_income_data: Optional[bool] = Field(None, description="是否具备稳定收益或租金资料")
    income_can_be_separated: Optional[bool] = Field(None, description="土地纯收益是否可从混合收益中合理剥离")
    rent_market_activity_level: Optional[str] = Field(None, description="租赁市场活跃程度")
    cap_rate_source_available: Optional[bool] = Field(None, description="还原率来源是否可靠")

    has_development_plan: Optional[bool] = Field(None, description="是否具备明确开发或再开发方案")
    development_value_measurable: Optional[bool] = Field(None, description="开发完成后价值是否可合理预测")
    construction_cost_available: Optional[bool] = Field(None, description="追加建设成本资料是否可采")
    sales_or_rent_forecast_reliable: Optional[bool] = Field(None, description="销售或租赁预测资料是否可靠")

    has_land_acquisition_cost_docs: Optional[bool] = Field(None, description="是否具备土地取得成本资料")
    has_development_cost_docs: Optional[bool] = Field(None, description="是否具备土地开发成本资料")
    cost_data_reliable: Optional[bool] = Field(None, description="成本参数是否可靠")
    cost_market_gap_risk: Optional[str] = Field(None, description="成本与市场价值脱节风险：高/中/低")

    base_price_in_coverage: Optional[bool] = Field(None, description="是否处于基准地价覆盖范围")
    base_price_has_applicable_use: Optional[bool] = Field(None, description="是否有对应基准地价用途体系")
    base_price_base_date: Optional[str] = Field(None, description="基准地价估价基准日")
    base_price_publish_date: Optional[str] = Field(None, description="基准地价公布或实施日期")
    base_price_is_expired: Optional[bool] = Field(None, description="基准地价是否可能过期")
    method_warning_acknowledged: Optional[Dict[str, bool]] = Field(None, description="估价师已确认的预警项")
    valuation_method_reasons: Optional[str] = Field(None, description="估价方法选用及适用性说明合并正文（格式内容与报告一字不差）")
    valuation_method_applicability: Optional[str] = Field(None, description="评估方法适用性自动生成段落（保留向下兼容）")
    final_price_determination: Optional[str] = Field(None, description="地价确定及加权确价理由合并正文（格式内容与报告一字不差）")
    valuation_result_statement: Optional[str] = Field(None, description="确定估价结果最终正文")
    final_unit_price: Optional[str] = Field(None, description="最终评估地面单价（元/平方米）")
    final_total_price: Optional[str] = Field(None, description="最终估价总价（万元）")
    final_total_price_upper: Optional[str] = Field(None, description="最终估价总价人民币大写")
    requires_manual_final_price: Optional[bool] = Field(False, description="众数等统计口径未能自动形成唯一最终价时提示人工定价")
    infrastructure_detail: Optional[str] = Field(None, description="基础设施开发程度自动生成段落（保留向下兼容）")
    cost_approx_land_class_intro: Optional[str] = Field(None, description="成本逼近法征收地类及批复依据说明段落")
    cost_approx_process_intro: Optional[str] = Field(None, description="成本逼近法计算过程前置说明段落")
    cost_approx_method_intro: Optional[str] = Field(None, description="成本逼近法定义及公式说明")
    market_comp_method_intro: Optional[str] = Field(None, description="市场比较法定义及公式说明")
    income_cap_method_intro: Optional[str] = Field(None, description="收益还原法定义及公式说明")
    benchmark_corr_method_intro: Optional[str] = Field(None, description="基准地价系数修正法定义及公式说明")
    residual_method_intro: Optional[str] = Field(None, description="剩余法定义及公式说明")
    valuation_basis_docs_rendered: Optional[str] = Field(None, description="估价过程测算依据文件清单规范化渲染文本")

    # 4. 📜 第三章：土地权属及证照信息（智能草稿生成 + 最终文本）
    ownership_scenario_type: str = Field("new_grant", description="权属草稿生成情形：new_grant、historical_unregistered、registered_complete、mixed_manual")
    land_status_type: str = Field("new_grant", description="土地权属场景分支控制（旧字段兼容，渲染时自动同步 ownership_scenario_type）")
    asset_use_category: str = Field("residential", description="土地用途内部大类：residential、industrial、commercial、public、other")
    asset_use_category_other: Optional[str] = Field(None, description="用途话术类型选择 other 时的用户自定义用途名称")
    include_registration_risk_note: bool = Field(False, description="是否由用户主动追加登记风险提示")
    registration_risk_note: Optional[str] = Field("", description="用户选择追加的登记风险提示文本")
    has_other_rights_limit: bool = Field(False, description="是否存在他项权利限制")
    other_rights_limit_desc: Optional[str] = Field("", description="他项权利限制具体情况说明")
    land_registration_desc: Optional[str] = Field(None, description="土地登记状况最终正文")
    land_right_desc: Optional[str] = Field(None, description="土地权利状况最终正文")
    land_use_status_desc: Optional[str] = Field(None, description="土地利用现状最终正文")

    basis_docs_list: Optional[str] = Field(None, description="权属与规划依据文件原始输入清单（多行）")
    valuation_basis_docs_list: Optional[str] = Field(None, description="估价过程测算依据文件清单（多行）")
    basis_docs_rendered: Optional[str] = Field(None, description="渲染规范化后的书名号文本，用于裸列文件名（如《文件A》、《文件B》）")
    basis_docs_phrase: Optional[str] = Field(None, description="组装完成的句式片段，用于句首引入（如：根据《文件A》、《文件B》等资料）")

    acquisition_land_class: Optional[str] = Field(None, description="成本逼近法采用的征收地类，不从土地用途派生")
    acquisition_land_subclass: Optional[str] = Field(None, description="成本逼近法费用测算采用的征收地类细分类")
    acquisition_land_class_confirmed: bool = Field(True, description="成本逼近法征收地类是否已经估价师确认")
    local_compensation_policy_name: Optional[str] = Field(None, description="成本逼近法采用的市县级征地补偿安置政策名称")
    local_compensation_policy_no: Optional[str] = Field(None, description="成本逼近法采用的市县级征地补偿安置政策文号")
    local_compensation_policy_date: Optional[str] = Field(None, description="成本逼近法采用的市县级征地补偿安置政策日期")
    acquisition_approval_doc_name: Optional[str] = Field(None, description="征地或农用地转用批复文件名称")
    acquisition_approval_doc_no: Optional[str] = Field(None, description="征地或农用地转用批复文号")
    acquisition_approval_doc_date: Optional[str] = Field(None, description="征地或农用地转用批复日期")

    # 旧版向下兼容字段（Legacy）
    gov_approval_name: Optional[str] = Field(None, description="【废弃兼容】政府批复文件名称")
    gov_approval_no: Optional[str] = Field(None, description="【废弃兼容】政府批复文号")
    gov_approval_date: Optional[str] = Field(None, description="【废弃兼容】政府批复日期")
    original_land_owner_desc: Optional[str] = Field(None, description="原土地权属状况描述")
    approval_transfer_date: Optional[str] = Field(None, description="批准转让日期")
    approval_authority: Optional[str] = Field(None, description="批准机关")
    
    house_cert_name: Optional[str] = Field(None, description="房屋所有权证名称")
    house_cert_no: Optional[str] = Field(None, description="房屋所有权证编号")
    area_docs_desc_name: Optional[str] = Field(None, description="面积依据文件名")
    room_detail_location: Optional[str] = Field(None, description="房间详细位置坐落")
    proof_doc_name: Optional[str] = Field(None, description="权属证明文件名")
    proof_doc_date: Optional[str] = Field(None, description="权属证明日期")
    user_identity: Optional[str] = Field(None, description="土地使用者身份")
    buy_year: Optional[str] = Field(None, description="购房年份")
    buy_location_desc: Optional[str] = Field(None, description="购房坐落地点描述")
    registered_house_area: Optional[str] = Field(None, description="房证登记建筑面积")
    
    land_cert_name: Optional[str] = Field(None, description="土地使用权证或不动产权证名称")
    land_cert_no: Optional[str] = Field(None, description="土地使用权证或不动产权证编号")
    land_use_type: Optional[str] = Field(None, description="登记土地使用权类型")
    land_usage_basis: Optional[str] = Field(None, description="土地用途依据文件或手填内容")
    land_area_basis: Optional[str] = Field(None, description="使用权面积依据文件或手填内容")

    # 5. 🛠️ 后端智能拼装生成的证明大话术字段（用于直接在 Word 中高保真展示）
    proof_house_cert_doc: Optional[str] = Field(None, description="原始房屋所有权证证明话术")
    proof_house_apply_doc: Optional[str] = Field(None, description="原始房屋登记申请证明话术")
    proof_house_stub_doc: Optional[str] = Field(None, description="原始房屋证书存根证明话术")
    proof_gov_accept_doc: Optional[str] = Field(None, description="原始政府受理行政许可话术")
    proof_land_register_doc: Optional[str] = Field(None, description="原始土地登记审批证明话术")
    proof_land_area_doc: Optional[str] = Field(None, description="原始土地分摊面积明细证明话术")
