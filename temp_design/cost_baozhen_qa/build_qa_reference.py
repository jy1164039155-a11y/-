from pathlib import Path
import shutil
import sys


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.services.cost_approximation import calculate_cost_approximation
from src.services.cost_approximation_docx import apply_cost_approximation_to_docx


TEMPLATE = BASE_DIR / "01_Source" / "02_Word_Templates" / "自动生成的评估报告模板.docx"
OUTPUT = Path(__file__).with_name("cost_baozhen_qa_reference.docx")

REFERENCE_POPULATION_CASES = [
    {
        "key": "reference",
        "name": "范本口径",
        "location": "道县西洲街道宝珍街六栋九号",
        "land_area_ha": "1",
        "population": "12.82",
        "confirmed": True,
    }
]

data = {
    "use_cost_approx": True,
    "use_market_comp": False,
    "use_income_cap": False,
    "use_benchmark_corr": False,
    "use_residual": False,
    "county_name": "道县",
    "valuation_date": "2026-06-01",
    "transfer_purpose_mode": "办理土地使用权出让手续",
    "land_location_full": "道县西洲街道宝珍街六栋九号",
    "acquisition_land_class": "水田",
    "land_usage": "居住用地",
    "land_development_set": "五通一平",
}

analysis = calculate_cost_approximation(data, BASE_DIR)
analysis["resettlement_population_cases"] = [dict(item) for item in REFERENCE_POPULATION_CASES]
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
levels = ["较优", "劣", "优", "较劣", "优", "优", "较优", "较优", "较优", "较优", "劣", "优"]
descriptions = [
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
for item, level, description in zip(analysis["location_factors"], levels, descriptions):
    item["level"] = level
    item["description"] = description
    item["confirmed"] = True
data["cost_approx_analysis"] = analysis

result = calculate_cost_approximation(data, BASE_DIR)
data["cost_approx_analysis"] = result
assert result["totals"]["acquisition_total"] == "238.26", result["totals"]["acquisition_total"]
assert result["usage_results"][0]["final_price"] == "942.5", result["usage_results"][0]["final_price"]
assert result["usage_results"][0]["location_correction_rate"] == "21.00", result["usage_results"][0]["location_correction_rate"]
shutil.copy(TEMPLATE, OUTPUT)
apply_cost_approximation_to_docx(str(OUTPUT), data, str(BASE_DIR))

print(OUTPUT)
print(result["totals"]["acquisition_total"])
print(result["usage_results"][0]["final_price"])
