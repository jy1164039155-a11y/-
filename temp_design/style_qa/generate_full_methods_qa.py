from __future__ import annotations

import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.api import normalize_report_typography
from src.services.cost_approximation import calculate_cost_approximation
from src.services.cost_approximation_docx import apply_cost_approximation_to_docx
from src.services.income_capitalization_docx import apply_income_capitalization_to_docx
from src.services.market_comparison_docx import apply_market_comparison_to_docx
from tests.test_income_capitalization import _baozhen_income_payload


TEMPLATE = BASE_DIR / "01_Source" / "02_Word_Templates" / "自动生成的评估报告模板.docx"
OUTPUT = Path(__file__).parent / "full_methods_style_qa.docx"


def cost_data() -> dict:
    data = {
        "use_cost_approx": True,
        "county_name": "道县",
        "valuation_date": "2026-06-01",
        "transfer_purpose_mode": "办理土地使用权出让手续",
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
        + analysis["usage_scenarios"]
        + analysis["location_factors"]
    ):
        item["confirmed"] = True
    analysis["external_results"] = [
        {
            "key": "attachment",
            "result_type": "attachment_compensation",
            "label": "附着物补偿外部测算",
            "value": "138.81",
            "source_hash": "style-qa",
            "confirmed": True,
        }
    ]
    data["cost_approx_analysis"] = analysis
    return data


def market_data() -> dict:
    factor_row = {
        "group": "交易因素",
        "subgroup": "",
        "label": "土地用途",
        "subject": "居住用地",
        "a": "居住用地",
        "b": "居住用地",
        "c": "居住用地",
    }
    effective = {
        "market_comp_step1_instances": "根据替代原则，选择与估价对象用途相同、区位相近、交易时间接近的三宗土地交易案例作为比较实例。",
        "market_comp_comparable_basis": "比较实例与估价对象在付款方式、币种、货币单位、面积内涵和面积单位方面口径一致，价格可比基础相同，故无需调整。",
        "market_comp_factor_selection": "根据估价对象与比较实例的实际情况，选择交易因素、区域因素和个别因素进行比较修正。",
        "market_comp_condition_intro": "将估价对象与比较实例的因素条件进行整理，具体情况见比较因素条件说明表。",
        "market_comp_index_basis": "以估价对象各项因素条件指数为100，结合比较实例的实际条件编制比较因素条件指数表。",
        "market_comp_step4_solve": "采用连乘法计算各比较实例的修正系数，并取三宗比准价格的算术平均值作为市场比较法测算结果。",
    }
    return {
        "use_market_comp": True,
        "market_comp_analysis": {"effective_narratives": effective},
        "market_comp_basic_rows": [{"label": "案例来源", "a": "案例A", "b": "案例B", "c": "案例C"}],
        "market_comp_factor_condition_rows": [factor_row],
        "market_comp_time_index_rows": [{"label": "成交日期", "subject": "2026-06-01", "a": "2025-01-01", "b": "2025-02-01", "c": "2025-03-01"}],
        "market_comp_factor_index_rows": [dict(factor_row, subject="100", a="100", b="100", c="100")],
        "market_comp_correction_rows": [{"group": "交易因素", "subgroup": "", "label": "土地用途", "a": "1.0000", "b": "1.0000", "c": "1.0000"}],
    }


def main() -> None:
    shutil.copy(TEMPLATE, OUTPUT)
    data = {}
    data.update(cost_data())
    data.update(_baozhen_income_payload())
    data.update(market_data())
    data["use_cost_approx"] = True
    data["use_income_cap"] = True
    data["use_market_comp"] = True
    apply_cost_approximation_to_docx(str(OUTPUT), data, str(BASE_DIR))
    apply_income_capitalization_to_docx(str(OUTPUT), data)
    apply_market_comparison_to_docx(str(OUTPUT), data)
    normalize_report_typography(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    main()
