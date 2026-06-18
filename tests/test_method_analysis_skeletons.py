# -*- coding: utf-8 -*-
from src.schemas.land import LandValuationContract
from tests.test_valuation_builder import base_payload


def test_other_four_methods_have_typed_independent_analysis_skeletons():
    payload = base_payload()
    payload.update(
        {
            "client_name": "道县自然资源局",
            "land_user": "测试权利人",
            "appraisal_org": "测试机构",
            "report_no": "测试报告",
            "technical_report_no": "测试技术报告",
            "report_date": "2026年6月4日",
            "valuation_date": "2026年6月4日",
            "building_area": 100,
            "plot_ratio": 1,
            "land_use_term": "30年",
            "land_usage_key": "industrial",
            "land_usage_full": "工矿用地",
            "land_usage_other": "",
            "planning_approval_authority": "道县自然资源局",
            "ownership_scenario_type": "new_grant",
            "asset_use_category": "industrial",
            "cost_approx_analysis": {"acquisition_items": [{"name": "土地取得费"}]},
            "income_cap_analysis": {"rent_instances": [{"name": "租金实例A"}]},
            "benchmark_corr_analysis": {"factor_items": [{"name": "区位因素"}]},
            "residual_analysis": {"property_sale_instances": [{"name": "商品房销售实例A"}]},
        }
    )
    contract = LandValuationContract(**payload)
    assert contract.income_cap_analysis.rent_instances[0]["name"] == "租金实例A"
    assert contract.residual_analysis.property_sale_instances[0]["name"] == "商品房销售实例A"
    assert not hasattr(contract.residual_analysis, "rent_instances")
