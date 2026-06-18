# -*- coding: utf-8 -*-
import io
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime
from decimal import Decimal

import pytest

from src.services.comparable_library import (
    ComparableLibrary,
    LandChinaAccessGate,
    LandChinaClient,
    LandChinaRateLimitError,
    LANDCHINA_API,
    LANDCHINA_USER_AGENT,
    _repair_mojibake,
)
from src.services.land_usage import infer_land_usage_key, official_land_usage_code


def official_case(guid: str, supervision_no: str, area_sqm: str, unit_price: str, date_text: str = "2025-01-01"):
    total_wan = Decimal(area_sqm) * Decimal(unit_price) / Decimal("10000")
    return {
        "gdGuid": guid,
        "dzBaBh": supervision_no,
        "xmMc": f"测试项目{guid}",
        "tdZl": f"测试坐落{guid}",
        "xzqDm": "431124",
        "xzqFullName": "湖南省永州市道县",
        "tdYt": "工业用地",
        "gyFs": "挂牌出让",
        "gyMj": str(Decimal(area_sqm) / Decimal("10000")),
        "je": str(total_wan),
        "qdRq": date_text,
        "crNx": "30",
        "tdJb": "城区Ⅳ级",
        "srr": f"受让人{guid}",
    }


def test_official_mapping_unit_price_and_manual_fields_are_preserved(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    detail = official_case("A", "4311242024B000055", "10772.50", "145")

    saved = library.upsert_official_case(detail)
    assert saved["area_sqm"] == "10772.50"
    assert saved["unit_price_sqm"] == "145.00"
    assert saved["land_usage_key"] == "industrial"

    library.patch_case("A", {"development_level": "五通一平", "parcel_shape": "规则"})
    detail["xmMc"] = "官方刷新后的项目名称"
    refreshed = library.upsert_official_case(detail)
    assert refreshed["project_name"] == "官方刷新后的项目名称"
    assert refreshed["development_level"] == "五通一平"
    assert refreshed["manual_fields"]["parcel_shape"] == "规则"


def test_manual_draft_does_not_affect_effective_case_until_confirmed(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    library.upsert_official_case(official_case("A", "4311242024B000055", "10772.50", "145"))

    drafted = library.patch_case_draft(
        "A",
        {"development_level": "五通一平", "parcel_shape": "规则"},
    )

    assert drafted.get("development_level") is None
    assert drafted["manual_fields"] == {}
    assert drafted["manual_draft_fields"]["development_level"] == "五通一平"

    confirmed = library.confirm_case_manual_fields("A", ["development_level"])

    assert confirmed["development_level"] == "五通一平"
    assert confirmed["manual_fields"]["development_level"] == "五通一平"
    assert "development_level" not in confirmed["manual_draft_fields"]
    assert confirmed["manual_draft_fields"]["parcel_shape"] == "规则"


def test_factor_scheme_backfills_guidance_levels_and_review_state(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    saved = library.save_factor_scheme(
        "industrial",
        {
            "name": "旧工业方案",
            "factors": [
                {
                    "key": "transaction_condition",
                    "label": "交易情况",
                    "group": "交易因素",
                }
            ],
        },
    )

    factor = saved["factors"][0]
    assert factor["levels"][0] == {
        "label": "正常",
        "index": "100",
        "description": "选择“正常”时建议采用指数 100，采用前须由估价师结合实例资料确认。",
    }
    assert factor["review_status"] == "needs_review"
    assert factor["enabled"] is True
    assert factor["order"] == 0


def test_unknown_official_usage_maps_to_other(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    detail = official_case("X", "X-001", "10000", "100")
    detail["tdYt"] = "尚未纳入系统词典的新用途"
    saved = library.upsert_official_case(detail)
    assert saved["land_usage_raw"] == "尚未纳入系统词典的新用途"
    assert saved["land_usage_key"] == "other"


def test_landchina_mojibake_is_repaired_only_when_chinese_improves():
    assert _repair_mojibake("äºç±»å·¥ä¸ç¨å°") == "二类工业用地"
    assert _repair_mojibake("工业用地") == "工业用地"
    assert _repair_mojibake({"name": "éå¿"}) == {"name": "道县"}


def test_official_usage_details_map_to_unified_first_level_classes():
    assert infer_land_usage_key("二类工业用地") == "industrial"
    assert infer_land_usage_key("二类物流仓储用地") == "warehouse"
    assert infer_land_usage_key("普通商品住房用地(二类)") == "residential"
    assert infer_land_usage_key("公用设施营业网点用地") == "commercial"
    assert infer_land_usage_key("公用设施用地") == "utility"
    assert infer_land_usage_key("文体娱乐用地") == "public"
    assert infer_land_usage_key("公路用地") == "transportation"
    assert {
        key: official_land_usage_code(key)
        for key in (
            "residential",
            "public",
            "commercial",
            "industrial",
            "warehouse",
            "transportation",
            "utility",
            "green",
            "special",
        )
    } == {
        "residential": "V3-07",
        "public": "V3-08",
        "commercial": "V3-09",
        "industrial": "V3-10",
        "warehouse": "V3-11",
        "transportation": "V3-12",
        "utility": "V3-13",
        "green": "V3-14",
        "special": "V3-15",
    }


def test_date_range_defaults_to_short_slices_for_long_official_queries(tmp_path):
    library = ComparableLibrary(str(tmp_path))

    ranges = library._date_ranges({"start_date": "2025-01-01", "end_date": "2025-03-05"})
    assert ranges == [
        ("2025-01-01", "2025-01-31"),
        ("2025-02-01", "2025-02-28"),
        ("2025-03-01", "2025-03-05"),
    ]


def test_oversized_crawl_slice_is_split_while_listing(tmp_path):
    library = ComparableLibrary(str(tmp_path))

    class FakeClient:
        rate_limit_hits = 0

        def __init__(self):
            self.ranges = []

        def result_list(self, payload):
            start = payload["startDate"][:10]
            end = payload["endDate"][:10]
            self.ranges.append((start, end, payload["pageNum"]))
            if (start, end) == ("2025-01-01", "2025-01-10"):
                return {"total": 7001, "pages": 1, "list": []}
            return {"total": 0, "pages": 0, "list": []}

        def result_detail(self, guid):
            raise AssertionError("No details should be requested without list rows")

    fake = FakeClient()
    library.client = fake
    library.jobs["job"] = {
        "job_id": "job",
        "status": "queued",
        "filters": {"start_date": "2025-01-01", "end_date": "2025-01-10"},
        "cancel_requested": False,
    }
    library._run_crawl_job("job")

    assert fake.ranges[:3] == [
        ("2025-01-01", "2025-01-10", 1),
        ("2025-01-01", "2025-01-05", 1),
        ("2025-01-06", "2025-01-10", 1),
    ]
    assert library.get_crawl_job("job")["status"] == "completed"


def test_crawl_page_count_uses_total_when_official_pages_is_low():
    assert ComparableLibrary._crawl_page_count({"total": 81, "pages": 1, "list": [{"gdGuid": "A"}]}) == 3


def test_list_record_is_saved_and_does_not_downgrade_existing_detail(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    detail = official_case("A", "4311242024B000055", "10772.50", "145")
    saved = library.upsert_official_case(detail)
    assert saved["detail_status"] == "complete"

    list_record = {
        "gdGuid": "A",
        "xzqDm": "431124",
        "xzqFullName": "湖南省永州市道县",
        "tdZl": "列表刷新后的坐落",
        "tdYt": "工业用地",
        "gyFs": "挂牌出让",
        "gyMj": "1.07725",
        "qdRq": "2025-01-01",
        "_record_level": "list",
    }
    refreshed = library.upsert_official_case(list_record)
    assert refreshed["detail_status"] == "complete"
    assert refreshed["project_name"] == detail["xmMc"]
    assert refreshed["unit_price_sqm"] == "145.00"
    assert refreshed["location"] == "列表刷新后的坐落"


def test_export_cases_csv_uses_current_filters_and_manual_fields(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    first = official_case("A", "4311242024B000055", "10772.50", "145")
    second = official_case("B", "4311242024B000056", "10000", "120")
    second["xzqDm"] = "431230"
    library.upsert_official_case(first)
    library.upsert_official_case(second)
    library.patch_case("A", {"development_level": "五通一平"})

    content = library.export_cases_csv({"xzq_dm": "431124"}).decode("utf-8-sig")

    assert "电子监管号,项目名称,坐落" in content
    assert "4311242024B000055" in content
    assert "development_level" in content
    assert "4311242024B000056" not in content


def test_list_cases_can_filter_by_administrative_region_and_report_region_options(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    first = official_case("A", "4311242024B000055", "10772.50", "145")
    second = official_case("B", "4312302024B000056", "10000", "120")
    second["xzqDm"] = "431230"
    second["xzqFullName"] = "湖南省怀化市通道侗族自治县"
    library.upsert_official_case(first)
    library.upsert_official_case(second)

    filtered = library.list_cases({"xzq_dm": "431230", "page_size": 10})
    regions = library.list_case_regions()

    assert filtered["total"] == 1
    assert filtered["items"][0]["administrative_region_code"] == "431230"
    assert {
        (item["code"], item["name"], item["count"])
        for item in regions
    } == {
        ("431124", "湖南省永州市道县", 1),
        ("431230", "湖南省怀化市通道侗族自治县", 1),
    }


def test_crawl_keeps_all_list_records_when_detail_is_rate_limited(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    rows = [
        {
            "gdGuid": guid,
            "xzqDm": "431230",
            "xzqFullName": "湖南省怀化市通道侗族自治县",
            "tdZl": f"测试坐落{guid}",
            "tdYt": "工业用地",
            "gyFs": "挂牌出让",
            "gyMj": "1",
            "qdRq": "2025-01-01",
        }
        for guid in ("A", "B")
    ]

    class RateLimitedClient:
        rate_limit_hits = 1

        def result_list(self, payload):
            return {"total": 2, "pages": 1, "list": rows}

        def result_detail(self, guid):
            raise LandChinaRateLimitError("HTTP 418")

    library.client = RateLimitedClient()
    library.jobs["job"] = {
        "job_id": "job",
        "status": "queued",
        "filters": {"start_date": "2025-01-01", "end_date": "2025-12-31"},
        "cancel_requested": False,
    }
    library._run_crawl_job("job")

    job = library.get_crawl_job("job")
    assert job["status"] == "completed"
    assert job["saved"] == 2
    assert job["complete"] == 0
    assert job["partial"] == 2
    assert job["processed"] == 1
    assert "已停止详情补全" in job["stopped_reason"]
    assert library.list_cases({"page_size": 10})["total"] == 2


def test_crawl_saves_discovered_list_records_when_listing_is_rate_limited(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    row = {
        "gdGuid": "A",
        "xzqDm": "431124",
        "xzqFullName": "湖南省永州市道县",
        "tdZl": "测试坐落A",
        "tdYt": "工业用地",
        "gyFs": "挂牌出让",
        "gyMj": "1",
        "qdRq": "2025-01-01",
    }

    class RateLimitedListClient:
        rate_limit_hits = 1

        def result_list(self, payload):
            start = payload["startDate"][:10]
            if start == "2025-01-01":
                return {"total": 1, "pages": 1, "list": [row]}
            raise LandChinaRateLimitError("HTTP 418")

        def result_detail(self, guid):
            raise LandChinaRateLimitError("HTTP 418")

    library.client = RateLimitedListClient()
    library.jobs["job"] = {
        "job_id": "job",
        "status": "queued",
        "filters": {"start_date": "2025-01-01", "end_date": "2025-02-02"},
        "cancel_requested": False,
    }
    library._run_crawl_job("job")

    job = library.get_crawl_job("job")
    assert job["status"] == "completed"
    assert job["saved"] == 1
    assert job["partial"] == 1
    assert "列表访问受限" in job["stopped_reason"]
    assert library.list_cases({"page_size": 10})["total"] == 1


def test_crawl_splits_listing_range_when_proxy_times_out(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    row = {
        "gdGuid": "A",
        "xzqDm": "431124",
        "xzqFullName": "湖南省永州市道县",
        "tdZl": "测试坐落A",
        "tdYt": "工业用地",
        "gyFs": "挂牌出让",
        "gyMj": "1",
        "qdRq": "2025-01-01",
    }

    class TimeoutThenSplitClient:
        rate_limit_hits = 0

        def __init__(self):
            self.ranges = []

        def result_list(self, payload):
            start = payload["startDate"][:10]
            end = payload["endDate"][:10]
            self.ranges.append((start, end))
            if (start, end) == ("2025-01-01", "2025-01-31"):
                raise LandChinaRateLimitError("操作超时")
            if (start, end) == ("2025-01-01", "2025-01-16"):
                return {"total": 1, "pages": 1, "list": [row]}
            return {"total": 0, "pages": 0, "list": []}

        def result_detail(self, guid):
            return official_case("A", "A-001", "10000", "100")

    fake = TimeoutThenSplitClient()
    library.client = fake
    library.jobs["job"] = {
        "job_id": "job",
        "status": "queued",
        "filters": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
        "cancel_requested": False,
    }
    library._run_crawl_job("job")

    job = library.get_crawl_job("job")
    assert ("2025-01-01", "2025-01-16") in fake.ranges
    assert ("2025-01-17", "2025-01-31") in fake.ranges
    assert job["status"] == "completed"
    assert job["saved"] == 1
    assert library.list_cases({"page_size": 10})["total"] == 1


def test_crawl_uses_official_first_level_code_and_keeps_matching_details_only(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    rows = [
        {
            "gdGuid": "A",
            "xzqDm": "431230",
            "xzqFullName": "湖南省怀化市通道侗族自治县",
            "tdZl": "工业项目",
            "tdYt": "二类工业用地",
            "gyFs": "挂牌出让",
            "gyMj": "1",
            "qdRq": "2025-01-01",
        },
        {
            "gdGuid": "B",
            "xzqDm": "431230",
            "xzqFullName": "湖南省怀化市通道侗族自治县",
            "tdZl": "仓储项目",
            "tdYt": "二类物流仓储用地",
            "gyFs": "挂牌出让",
            "gyMj": "1",
            "qdRq": "2025-01-01",
        },
    ]

    class FakeClient:
        rate_limit_hits = 0
        payloads = []

        def result_list(self, payload):
            self.payloads.append(payload)
            return {"total": 2, "pages": 1, "list": rows}

        def result_detail(self, guid):
            assert guid == "A"
            detail = official_case("A", "A-001", "10000", "100")
            detail["tdYt"] = "二类工业用地"
            return detail

    fake = FakeClient()
    library.client = fake
    library.jobs["job"] = {
        "job_id": "job",
        "status": "queued",
        "filters": {
            "xzq_dm": "431230",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "land_usage_key": "industrial",
        },
        "cancel_requested": False,
    }
    library._run_crawl_job("job")

    job = library.get_crawl_job("job")
    cases = library.list_cases({"page_size": 10})
    assert job["official_land_usage_code"] == "V3-10"
    assert all(payload["tdYt"] == "V3-10" for payload in fake.payloads)
    assert cases["total"] == 1
    assert cases["items"][0]["land_usage_first_level"] == "工矿用地"


def test_crawl_payload_prefers_region_code_over_same_county_location_keyword(tmp_path):
    library = ComparableLibrary(str(tmp_path))

    payload = library._crawl_payload(
        {
            "xzq_dm": "431230",
            "location": "通道县",
            "start_date": "2026-04-01",
            "end_date": "2026-04-23",
        },
        1,
        "2026-04-01",
        "2026-04-23",
    )
    narrower_payload = library._crawl_payload(
        {
            "xzq_dm": "431230",
            "location": "双江镇",
            "start_date": "2026-04-01",
            "end_date": "2026-04-23",
        },
        1,
        "2026-04-01",
        "2026-04-23",
    )

    assert payload["xzqDm"] == "431230"
    assert payload["tdZl"] is None
    assert narrower_payload["tdZl"] == "双江镇"


def test_access_gate_shares_cooldown_and_crawl_lease_between_processes(tmp_path):
    db_path = tmp_path / "shared.sqlite3"
    first = LandChinaAccessGate(db_path)
    second = LandChinaAccessGate(db_path)

    first.block(60, 403, "forbidden")
    status = second.status()
    assert status["blocked"] is True
    assert status["last_http_status"] == "403"
    with pytest.raises(LandChinaRateLimitError, match="官网访问冷却中"):
        second.reserve_request(0)

    assert first.acquire_crawl("job-a") is True
    assert second.acquire_crawl("job-b") is False
    first.release_crawl("job-a")
    assert second.acquire_crawl("job-b") is True


def test_access_gate_clears_legacy_redirect_cooldown_on_init(tmp_path):
    db_path = tmp_path / "shared.sqlite3"
    first = LandChinaAccessGate(db_path)
    first.block(60, 302, "redirected to 404")

    refreshed = LandChinaAccessGate(db_path)
    status = refreshed.status()

    assert status["blocked"] is False
    assert status["remaining_seconds"] == 0
    assert status["last_http_status"] == "302"
    assert "已清除旧版重定向冷却状态" in status["last_reason"]


def test_access_gate_can_clear_cooldown_when_access_channel_changes(tmp_path):
    gate = LandChinaAccessGate(tmp_path / "shared.sqlite3")
    gate.block(60, 503, "cloud relay failed")

    gate.clear_cooldown("switched to direct")
    status = gate.status()

    assert status["blocked"] is False
    assert status["remaining_seconds"] == 0
    assert status["last_http_status"] == ""
    assert status["last_reason"] == "switched to direct"


def test_crawl_skips_complete_details_unless_force_refresh_is_selected(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    detail = official_case("A", "A-001", "10000", "100")
    library.upsert_official_case(detail)

    class FakeClient:
        rate_limit_hits = 0
        detail_calls = 0

        def result_list(self, payload):
            return {"total": 1, "pages": 1, "list": [detail]}

        def result_detail(self, guid):
            self.detail_calls += 1
            return detail

    fake = FakeClient()
    library.client = fake
    library.jobs["job"] = {
        "job_id": "job",
        "status": "queued",
        "filters": {"start_date": "2025-01-01", "end_date": "2025-12-31"},
        "cancel_requested": False,
    }
    library._run_crawl_job("job")

    assert library.get_crawl_job("job")["complete"] == 1
    assert fake.detail_calls == 0


def test_landchina_client_retries_http_418_with_shared_cooldown(monkeypatch):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"code": 200, "data": {"ok": True}}).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            calls.append(request)
            if len(calls) == 1:
                raise urllib.error.HTTPError(request.full_url, 418, "limited", {}, io.BytesIO())
            return Response()

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: FakeOpener())
    monkeypatch.setattr("src.services.comparable_library.time.sleep", lambda seconds: None)
    client = LandChinaClient(request_interval=0, detail_interval=0)
    result = client._post("/test", {}, retries=1, interval=0)

    assert result["data"]["ok"] is True
    assert client.rate_limit_hits == 1
    assert len(calls) == 2


def test_landchina_client_adds_official_hash_header(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"code": 200, "data": {"ok": True}}).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            captured["hash"] = request.get_header("Hash")
            captured["user_agent"] = request.get_header("User-agent")
            return Response()

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: FakeOpener())
    client = LandChinaClient(request_interval=0, detail_interval=0)
    client._post("/tGdxm/result/list", {}, retries=0, interval=0)

    expected = hashlib.sha256(
        f"{LANDCHINA_USER_AGENT}{datetime.now().day}list".encode("utf-8")
    ).hexdigest()
    assert captured["hash"] == expected
    assert captured["user_agent"] == LANDCHINA_USER_AGENT


def test_landchina_client_posts_through_configured_proxy(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"code": 200, "data": {"ok": True}}).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = {key.lower(): value for key, value in request.header_items()}
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return Response()

    def fake_build_opener(*handlers):
        captured["handler_types"] = [type(handler).__name__ for handler in handlers]
        return FakeOpener()

    monkeypatch.setattr(urllib.request, "build_opener", fake_build_opener)
    client = LandChinaClient(
        request_interval=0,
        detail_interval=0,
        proxy_url="http://117.72.179.235:8787/landchina/",
        proxy_token="secret-token",
    )
    result = client._post("/tGdxm/result/list", {"pageNum": 1}, retries=0, interval=0)

    assert result["data"]["ok"] is True
    assert captured["url"] == "http://117.72.179.235:8787/landchina"
    assert captured["body"] == {"path": "/tGdxm/result/list", "payload": {"pageNum": 1}}
    assert captured["headers"]["x-landchina-proxy-token"] == "secret-token"
    assert "hash" not in captured["headers"]
    assert "ProxyHandler" in captured["handler_types"]


def test_landchina_direct_request_bypasses_system_proxy(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"code": 200, "data": {"ok": True}}).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            return Response()

    def fake_build_opener(*handlers):
        captured["handlers"] = handlers
        return FakeOpener()

    monkeypatch.setattr(urllib.request, "build_opener", fake_build_opener)
    client = LandChinaClient(request_interval=0, detail_interval=0, proxy_url="")

    result = client._post("/tGdxm/result/list", {"pageNum": 1}, retries=0, interval=0)

    assert result["data"]["ok"] is True
    assert captured["url"] == f"{LANDCHINA_API}/tGdxm/result/list"
    proxy_handler = next(handler for handler in captured["handlers"] if isinstance(handler, urllib.request.ProxyHandler))
    assert proxy_handler.proxies == {}


def test_access_status_reports_proxy_channel(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    library.client = LandChinaClient(
        request_interval=0,
        detail_interval=0,
        access_gate=library.access_gate,
        proxy_url="http://117.72.179.235:8787/landchina/",
        proxy_token="secret-token",
    )

    status = library.get_access_status()

    assert status["proxy_enabled"] is True
    assert status["proxy_url"] == "http://117.72.179.235:8787/landchina"
    assert status["access_channel"] == "cloud_proxy"
    assert "proxy_token" not in status


def test_proxy_config_persists_masks_token_and_updates_runtime_client(tmp_path):
    library = ComparableLibrary(str(tmp_path))

    saved = library.save_proxy_config(
        {
            "enabled": True,
            "proxy_url": "http://117.72.179.235:8787/landchina/",
            "proxy_token": "secret-token",
        }
    )

    assert saved["enabled"] is True
    assert saved["proxy_url"] == "http://117.72.179.235:8787/landchina"
    assert saved["token_set"] is True
    assert "proxy_token" not in saved
    assert library.client.proxy_url == "http://117.72.179.235:8787/landchina"
    assert library.client.proxy_token == "secret-token"

    reloaded = ComparableLibrary(str(tmp_path))
    assert reloaded.get_proxy_config()["token_set"] is True
    assert reloaded.client.proxy_url == "http://117.72.179.235:8787/landchina"
    assert reloaded.client.proxy_token == "secret-token"

    reloaded.access_gate.block(60, 503, "cloud relay failed")
    disabled = reloaded.save_proxy_config({"enabled": False})
    assert disabled["enabled"] is False
    assert reloaded.client.proxy_url == ""
    assert reloaded.client.proxy_token == ""
    assert reloaded.access_gate.status()["blocked"] is False

    cleared = reloaded.save_proxy_config({"clear_token": True})
    assert cleared["token_set"] is False
    assert reloaded.client.proxy_token == ""


def test_proxy_gateway_failure_enters_short_cooldown(monkeypatch, tmp_path):
    access_gate = LandChinaAccessGate(tmp_path / "shared.sqlite3")
    calls = []
    body = json.dumps(
        {
            "error": "relay_failed",
            "official_status": 502,
            "message": "upstream bad gateway",
        }
    ).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            calls.append(request)
            raise urllib.error.HTTPError(request.full_url, 502, "Bad Gateway", {}, io.BytesIO(body))

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: FakeOpener())
    client = LandChinaClient(
        request_interval=0,
        detail_interval=0,
        access_gate=access_gate,
        proxy_url="http://117.72.179.235:8787/landchina/",
        proxy_token="secret-token",
    )

    with pytest.raises(LandChinaRateLimitError, match="云服务器中转访问官网临时失败"):
        client._post("/tGdxm/result/list", {}, retries=3, interval=0)

    status = access_gate.status()
    assert len(calls) == 1
    assert status["blocked"] is True
    assert status["last_http_status"] == "502"
    assert "官网状态 502" in status["last_reason"]


def test_proxy_timeout_failure_does_not_enter_cooldown(monkeypatch, tmp_path):
    access_gate = LandChinaAccessGate(tmp_path / "shared.sqlite3")
    body = json.dumps({"error": "relay_failed", "message": "操作超时"}).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 502, "Bad Gateway", {}, io.BytesIO(body))

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: FakeOpener())
    client = LandChinaClient(
        request_interval=0,
        detail_interval=0,
        access_gate=access_gate,
        proxy_url="http://117.72.179.235:8787/landchina/",
        proxy_token="secret-token",
    )

    with pytest.raises(LandChinaRateLimitError, match="操作超时"):
        client._post("/tGdxm/result/list", {}, retries=3, interval=0)

    status = access_gate.status()
    assert status["blocked"] is False
    assert status["last_http_status"] == "502"
    assert "操作超时" in status["last_reason"]


def test_landchina_redirect_to_404_records_failure_without_extending_cooldown(monkeypatch, tmp_path):
    db_path = tmp_path / "shared.sqlite3"
    access_gate = LandChinaAccessGate(db_path)
    calls = []

    class FakeOpener:
        def open(self, request, timeout):
            calls.append(request)
            raise urllib.error.HTTPError(
                request.full_url,
                302,
                "redirected",
                {"Location": "https://api.landchina.com/#/404"},
                io.BytesIO(),
            )

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: FakeOpener())
    client = LandChinaClient(request_interval=0, detail_interval=0, access_gate=access_gate)

    with pytest.raises(RuntimeError, match="重定向"):
        client._post("/tGdxm/result/list", {}, retries=1, interval=0)

    status = access_gate.status()
    assert len(calls) == 1
    assert status["blocked"] is False
    assert status["last_http_status"] == "302"
    assert "404" in status["last_reason"]


def test_landchina_redirect_without_location_does_not_crash(monkeypatch, tmp_path):
    access_gate = LandChinaAccessGate(tmp_path / "shared.sqlite3")

    class FakeOpener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 302, "redirected", {}, io.BytesIO())

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: FakeOpener())
    client = LandChinaClient(request_interval=0, detail_interval=0, access_gate=access_gate)

    with pytest.raises(RuntimeError, match="重定向"):
        client._post("/tGdxm/result/list", {}, retries=0, interval=0)

    status = access_gate.status()
    assert status["blocked"] is False
    assert status["last_http_status"] == "302"


def test_market_comparison_reproduces_corrected_sample_result_and_freezes_cases(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    cases = [
        official_case("A", "4311242024B000055", "10772.50", "145"),
        official_case("B", "4311242024B000016", "54307.30", "150"),
        official_case("C", "4311242024B000071", "6769.20", "149"),
    ]
    for item in cases:
        library.upsert_official_case(item)

    prepared = library.prepare_analysis(
        {
            "subject": {
                "valuation_date": "2025-01-01",
                "land_usage_key": "industrial",
                "land_usage": "工矿用地",
                "land_area": "11000",
                "land_use_term_years": "30",
                "land_development_set": "五通一平",
                "right_type": "出让",
            },
            "case_ids": ["A", "B", "C"],
            "monthly_growth_rate": "0",
            "land_reduction_rate": "5.4",
        }
    )
    target_indexes = {"A": "115.6738", "B": "115.8033", "C": "114.6418"}
    for factor in prepared["factors"]:
        factor["subject_value"] = factor.get("subject_value") or "与估价对象一致"
        for slot in ("A", "B", "C"):
            factor["cases"][slot]["value"] = factor["cases"][slot].get("value") or "与估价对象一致"
            factor["cases"][slot]["index"] = "100"
            factor["cases"][slot]["confirmed"] = True
        if factor["key"] == "planning_restriction":
            for slot in ("A", "B", "C"):
                factor["cases"][slot]["index"] = target_indexes[slot]
    prepared["narrative_overrides"] = {
        "market_comp_comparable_basis": "人工校核后的价格可比基础正文。"
    }

    result = library.calculate_market_comparison(prepared)
    calculations = {item["slot"]: item for item in result["calculations"]}
    assert calculations["A"]["correction_coefficient"] == "0.8645"
    assert result["market_comp_price"] == "128.3"
    assert result["complete"] is True
    assert not any("规则仍待校核" in item["message"] for item in result["warnings"])
    assert result["effective_narratives"]["market_comp_comparable_basis"] == "人工校核后的价格可比基础正文。"
    assert result["generated_narratives"]["market_comp_comparable_basis"] != "人工校核后的价格可比基础正文。"
    assert "交易情况" in result["market_comp_index_basis"]
    assert "请校核" not in result["market_comp_index_basis"]

    changed = cases[0].copy()
    changed["je"] = "9999"
    library.upsert_official_case(changed)
    frozen = library.calculate_market_comparison(result)
    assert frozen["selected_cases"][0]["unit_price_sqm"] == "145.00"
    assert frozen["market_comp_price"] == "128.3"
    assert frozen["effective_narratives"]["market_comp_comparable_basis"] == "人工校核后的价格可比基础正文。"


def test_market_render_fields_include_case_descriptions_without_review_placeholders(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    for item in (
        official_case("A", "4311242024B000055", "10772.50", "145", "2024-08-05"),
        official_case("B", "4311242024B000016", "54307.30", "150", "2024-01-10"),
        official_case("C", "4311242024B000071", "6769.20", "149", "2024-08-26"),
    ):
        library.upsert_official_case(item)
    library.patch_case(
        "A",
        {
            "development_level": "红线外“五通”及宗地红线内“场地平整”",
            "road_network": "乌家山路、东环一路",
            "traffic_condition": "顺畅",
            "infrastructure_guarantee": "大于95%",
            "adjacent_road": "次干道",
            "parcel_shape": "基本规则",
            "terrain": "平坦",
            "geology": "优",
            "bearing_capacity": "大于25T/㎡",
            "disaster_frequency": "100年一遇",
        },
    )

    prepared = library.prepare_analysis(
        {
            "subject": {
                "valuation_date": "2025-01-01",
                "land_usage_key": "industrial",
                "land_usage": "工矿用地",
                "land_area": "11000",
                "land_use_term_years": "30",
                "land_development_set": "五通一平",
                "right_type": "出让",
            },
            "case_ids": ["A", "B", "C"],
            "monthly_growth_rate": "0",
            "land_reduction_rate": "5.4",
        }
    )
    for factor in prepared["factors"]:
        factor["subject_value"] = factor.get("subject_value") or "与估价对象一致"
        for slot in ("A", "B", "C"):
            factor["cases"][slot]["value"] = factor["cases"][slot].get("value") or "与估价对象一致"
            factor["cases"][slot]["index"] = "100"
            factor["cases"][slot]["confirmed"] = True

    result = library.calculate_market_comparison(prepared)
    step1 = result["market_comp_step1_instances"]

    assert "比较实例A：该实例为受让人A以挂牌出让方式取得（电子监管号为4311242024B000055）" in step1
    assert "区域内路网由乌家山路、东环一路构成" in step1
    assert "交易时宗地基础设施状况为红线外“五通”及宗地红线内“场地平整”" in step1
    assert "土地使用权挂牌出让价格为145.00元/平方米" in step1
    assert "比较实例B：" in step1
    assert "比较实例C：" in step1
    assert result["instance_a_desc"] in step1

    rendered = "\n".join(result["generated_narratives"].values())
    for marker in ("【请", "【待", "请核实", "请配置", "请校核", "待计算"):
        assert marker not in rendered


def test_market_render_fields_do_not_prompt_to_configure_factors_when_using_default_scheme(tmp_path):
    library = ComparableLibrary(str(tmp_path))

    result = library.build_render_fields(
        {"subject": {"land_usage_key": "industrial", "land_usage": "工矿用地"}}
    )

    assert "请配置比较因素" not in result["market_comp_factor_selection"]
    assert "①交易时间" in result["market_comp_factor_selection"]
    assert "市场比较法因子方案" not in result["market_comp_factor_selection"]
    assert result["market_comp_comparable_basis"].count("\n") == 3
    assert "月平均增长率" not in result["market_comp_index_basis"]
    assert "土地还原率" not in result["market_comp_index_basis"]
    assert "待计算" not in result["market_comp_step4_solve"]


def test_market_render_fields_only_describe_parameters_when_adjustment_is_needed(tmp_path):
    library = ComparableLibrary(str(tmp_path))
    for item in (
        official_case("A", "4311242024B000055", "10772.50", "145", "2024-08-05"),
        official_case("B", "4311242024B000016", "54307.30", "150", "2024-01-10"),
        official_case("C", "4311242024B000071", "6769.20", "149", "2024-08-26"),
    ):
        library.upsert_official_case(item)

    prepared = library.prepare_analysis(
        {
            "subject": {
                "valuation_date": "2025-01-01",
                "land_usage_key": "industrial",
                "land_usage": "工矿用地",
                "land_use_term_years": "30",
            },
            "case_ids": ["A", "B", "C"],
            "monthly_growth_rate": "0.13",
            "land_reduction_rate": "5.4",
        }
    )
    result = library.calculate_market_comparison(prepared)

    assert "月平均增长率0.13%" in result["market_comp_index_basis"]
    assert "土地还原率5.4%" not in result["market_comp_index_basis"]
    assert len(result["market_comp_time_index_rows"]) == 3
    assert result["market_comp_verification"] == ""
