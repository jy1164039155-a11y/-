# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "frontend" / "src" / "App.vue"
STYLE_PATH = ROOT / "frontend" / "src" / "style.css"


def _app():
    return APP_PATH.read_text(encoding="utf-8")


def test_market_analysis_lives_in_valuation_process_workspace():
    app = _app()
    p5 = app.split("""v-show="activeTab === 'p5'""", 1)[1].split(
        """v-show="activeTab === 'p6'""", 1
    )[0]
    p6 = app.split("""v-show="activeTab === 'p6'""", 1)[1].split(
        '<div class="base-price-drawer"', 1
    )[0]

    assert "实例与参数" in p5
    assert "因素确认" in p5
    assert "{ key: 'narratives', label: '正文与表格' }" in app
    assert "marketMonthlyGrowthRate" in p5
    assert "marketLandReductionRate" in p5
    assert "月增长率 %<input" not in p5
    assert "年期修正用土地还原率 %<input" not in p5
    assert "processRenderableContentBlocks(activeProcessMethod)" in p5
    assert "processTableHeaderRows" in p5
    assert "当前报告固定实例" not in p6
    assert "market-analysis-panel" not in p6
    assert "marketMonthlyGrowthRate" not in p6
    assert "marketLandReductionRate" not in p6


def test_comparable_library_has_focused_views_and_rule_save_guard():
    app = _app()
    assert "{ key: 'crawl', label: '数据抓取' }" in app
    assert "{ key: 'library', label: '案例检索与选取' }" in app
    assert "{ key: 'schemes', label: '规则管理' }" in app
    assert '@click="requestSaveFactorScheme"' in app
    assert "schemeChangeSummary" in app
    assert "showSchemeChangeDialog" in app
    assert '@change="toggleCloudProxyEnabled"' in app
    assert "已切换为本机直连，并清除旧通道冷却。" in app
    for field in (
        "building_form",
        "exterior",
        "entrance_door",
        "windows",
        "security_facilities",
        "floor_finish",
        "ceiling_finish",
        "newness_desc",
        "current_use_basis",
        "building_area_basis",
        "land_area_basis",
    ):
        assert f"incomeAnalysis.building_profile.{field}" in app
    assert 'v-model="incomeAnalysis.building_profile.current_use_condition"' not in app
    assert 'v-model="incomeAnalysis.building_profile.plot_ratio"' not in app
    assert 'v-model="incomeAnalysis.building_profile.set_plot_ratio"' not in app
    assert "引用第二部分设定容积率" in app
    assert "引用第二部分利用条件类型" in app


def test_income_instances_page_separates_house_facts_land_settings_and_rent_evidence():
    app = _app()

    for title in (
        "估价对象房屋情况",
        "1. 基本信息与现状利用",
        "2. 建筑结构与装饰装修",
        "3. 维护成新与耐用年限",
        "宗地指标与评估设定",
        "4. 面积、容积率及资料依据",
        "5. 本次评估设定",
        "租金比较实例 A/B/C",
    ):
        assert title in app
    assert "室内装修及配套" not in app
    assert "利用指标与依据" not in app
    assert "业主房屋所在层数" in app
    assert "地面情况" in app
    assert "室内地面" not in app
    assert "租金调查时点" in app
    assert "rentalUsageOptions" in app
    assert "incomeRentFactorScales" in app
    assert "normalizeIncomeFactorStandards" in app
    assert "normalizeIncomeFactorValue" in app
    assert "road_accessibility: { scaleType: 'ordered', values: ['通畅', '较通畅', '一般通畅', '较不通畅', '不通畅']" in app
    assert "transaction_condition: { scaleType: 'equality', values: ['正常交易', '非正常交易']" in app
    assert "填写非正常交易情况及人工调整依据" in app
    assert "人工填写指数" in app
    assert "incomeFactorSourceLabel" in app
    assert '@change="onRentUsageChange(item)"' in app
    assert '@input="onRentTransactionDateChange(item)"' in app
    assert "恢复实例引用" in app
    assert "sharedBasisReferenceOptions" in app
    assert "addCostPolicyDocument" in app
    assert ".hidden-file-input" in STYLE_PATH.read_text(encoding="utf-8")
    assert "区域平均空置率区间" in app
    assert "修正状态" in app
    assert "incomeFactorCaseStatus" in app
    assert "focusNestedProcessField" in app
    assert "processNarrativeSegments" in app
    assert "cell.ref && focusProcessSource(cell.ref)" in app
    assert "income_results?.annual_depreciation" in app
    assert "income_results?.building_current_value" in app
    assert "income_results?.building_annual_depreciation" not in app
    assert "income_results?.building_present_value" not in app


def test_benchmark_frontend_formula_preview_matches_usage_profiles():
    app = _app()

    assert "const benchmarkFormulaFactorKeys = computed(() => {" in app
    assert "if (usage === '居住用地') return ['base', 'ki', 'ky', 'kv', 'kt', 'ks', 'ka', 'ke', 'kto', 'kf'];" in app
    assert "if (usage === '工矿用地' || usage === '仓储用地') return ['base', 'ki', 'ky', 'kt', 'ks', 'ka', 'kf'];" in app
    assert "if (usage === '公用设施用地') return ['base', 'ky', 'kt', 'ks', 'ka', 'kf'];" in app
    assert ".map(key => benchmarkFormulaFactorValue(key, p))" in app
    assert "clearBenchmarkCornerFields();" in app
    assert "benchmarkAnalysis.value.is_corner = false;" in app


def test_comparable_cases_can_open_landchina_detail_page():
    app = _app()

    assert "landChinaSupplyDetailBaseUrl = 'https://www.landchina.com/#/landSupplyDetail'" in app
    assert "id=${encodeURIComponent(gdGuid)}" in app
    assert "type=${encodeURIComponent('供地结果')}" in app
    assert "sourceUrl.includes('/#/landSupplyDetail')" in app
    assert '@click="openLandChinaSupplyDetail(item)"' in app
    assert '@click="openLandChinaSupplyDetail(editingComparableCase)"' in app
    assert "@click=\"openLandChinaSupplyDetail(selectedComparableCase(slot))\"" in app
    assert "详情页</button>" in app
    assert app.count('@click="openLandChinaSupplyDetail(selectedComparableCase(slot))"') == 1
    assert "打开实例 {{ slot }} 详情" in app
    assert "打开供地结果页" not in app
    assert "openLandChinaResultNotice" not in app


def test_factor_confirmation_is_factor_level_and_drawer_is_opaque():
    app = _app()
    style = STYLE_PATH.read_text(encoding="utf-8")

    assert "@click=\"openFactorGuide(factor)\"" in app
    assert "@click=\"applyFactorLevel(level, slot)\"" in app
    assert "确认该因素 A/B/C" in app
    assert "confirmAllMarketFactors" not in app
    assert "activeFactorGuide.slot" not in app
    assert "var(--bg-main)" not in app
    assert "确认该因素 A/B/C" in app
    assert "factor.review_status = 'confirmed'" in app
    assert "热区：{{ warningActionLabel(warning) }}" in app
    assert 'id="market-evidence-panel"' in app
    assert "上传官网供地结果信息截图" in app
    assert "market_comp_location_snapshot_ids" in app
    assert "market_comp_site_snapshot_ids" in app
    assert "/api/comparable-library/evidence/manual" in app

    for name in (
        "--drawer-bg:",
        "--drawer-surface:",
        "--drawer-surface-strong:",
        "--drawer-overlay:",
        "--drawer-text-secondary:",
    ):
        assert style.count(name) == 2
