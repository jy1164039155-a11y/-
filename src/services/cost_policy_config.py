from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable


def _config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "cost_approx_policy_rules.json"


def load_cost_policy_config() -> Dict[str, Any]:
    path = _config_path()
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    data["source_path"] = str(path)
    data["source_hash"] = hashlib.sha256(raw).hexdigest()
    return data


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip().replace("年", "-").replace("月", "-").replace("日", "")
    try:
        parts = [int(item) for item in text.split("-") if item][:3]
        return date(*parts) if len(parts) == 3 else None
    except ValueError:
        return None


def _region_score(rule: Dict[str, Any], county_name: str, city_name: str) -> int:
    candidates = [str(rule.get("region") or ""), *(str(item) for item in rule.get("aliases") or [])]
    level = str(rule.get("region_level") or "")
    if level == "county" and any(item and (item in county_name or county_name in item) for item in candidates):
        return 3
    if level == "city" and any(item and (item in city_name or city_name in item) for item in candidates):
        return 2
    if level == "province" and "湖南" in str(rule.get("region") or ""):
        return 1
    return 0


def find_policy_rule(
    config: Dict[str, Any],
    fee_key: str,
    *,
    county_name: str,
    city_name: str,
    valuation_date: Any,
    land_subclass: str,
    grade_name: str = "",
) -> Dict[str, Any]:
    target_date = _parse_date(valuation_date)
    requested_grade = str(grade_name or "").strip()
    matches = []
    for rule in config.get("policy_rules") or []:
        if rule.get("fee_key") != fee_key:
            continue
        score = _region_score(rule, county_name, city_name)
        if not score:
            continue
        subclasses = rule.get("land_subclasses") or ["*"]
        if "*" not in subclasses and not any(item in land_subclass or land_subclass in item for item in subclasses):
            continue
        start = _parse_date(rule.get("effective_date"))
        end = _parse_date(rule.get("expiry_date"))
        if target_date and ((start and target_date < start) or (end and target_date > end)):
            continue
        rule_grade = str(rule.get("grade_name") or "").strip()
        if requested_grade and rule_grade and rule_grade != requested_grade:
            continue
        matches.append((score, start or date.min, rule))
    if not matches:
        return {}
    if requested_grade:
        matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return deepcopy(matches[0][2])
    default_rules = [item for item in matches if item[2].get("is_default")]
    if default_rules:
        default_rules.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return deepcopy(default_rules[0][2])
    matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return deepcopy(matches[0][2])


def get_location_template(config: Dict[str, Any], template_key: str) -> Dict[str, Any]:
    return deepcopy((config.get("location_templates") or {}).get(template_key) or {})


def get_risk_scheme(config: Dict[str, Any], scheme_key: str = "hunan_general") -> Dict[str, Any]:
    return deepcopy((config.get("risk_schemes") or {}).get(scheme_key) or {})


def default_location_template_key(usage_keys: Iterable[str]) -> str:
    keys = set(usage_keys)
    if "commercial" in keys:
        return "commercial_fuel_station"
    if "residential" in keys:
        return "residential_general"
    return "custom"
