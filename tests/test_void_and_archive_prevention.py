# -*- coding: utf-8 -*-
import pytest
from fastapi import HTTPException
from src.api import validate_render_payload
from src.schemas.land import LandValuationContract

def test_preview_mode_self_healing():
    """验证在普通预览模式下（archive_to_result 为 False），空值会被自愈填充为标准的【请填写...】占位符而绝不拦截。"""
    # 构造一个大部分必填字段都缺失的极简 payload
    data = {
        "client_name": None,
        "land_user": "",
        "report_no": "  ",
        "valuation_date": "______",
        "land_area": None,
        "building_area": 120.5,
        "plot_ratio": "______",
        "planning_approval_authority": None,
        "ownership_scenario_type": "new_grant",
        "asset_use_category": "residential",
        
        # 补充其他契约需要的基本派生输入以保证校验链路畅通
        "land_location": "道县工业路",
        "right_type": "出让",
        "land_usage": "城镇住宅用地",
        "land_usage_short": "住宅",
        "land_usage_full": "城镇住宅用地",
        "land_use_term": "70年",
        "report_date": "2026-06-02",
        "parcel_count": "一宗",
        "appraisal_org": "测试受托机构",
        "technical_report_no": "技报A",
    }
    
    # 显式确保 archive_to_result 为 False 或者是未提供
    data["archive_to_result"] = False
    
    # 调用校验函数，期望它能完美自愈通过，而不抛出任何异常
    try:
        contract = validate_render_payload(data)
        assert isinstance(contract, LandValuationContract)
    except HTTPException as e:
        pytest.fail(f"预览模式下的空值被错误拦截了: {e.detail}")
        
    # 断言：文本类型必填字段被填充为正确的中文热区占位符
    assert "请填写" in data["client_name"]
    assert "请填写" in data["land_user"]
    assert "请填写" in data["report_no"]
    assert "请填写" in data["valuation_date"]
    assert "请填写" in data["planning_approval_authority"]
    
    # 断言：数值型字段被填充为正确的字符串热区占位符
    assert "请填写" in data["land_area"]
    assert "请填写" in data["plot_ratio"]
    assert "请填写" in data["plot_ratio_display"]
    
    # 正常填写的数值字段保留其真实 float 类型
    assert data["building_area"] == 120.5


def test_archive_mode_strict_prevention():
    """验证在正式归档模式下（archive_to_result 为 True），空值或未填写占位符将被强力拦截并返回 422 报错。"""
    # 构造有缺失必填项的归档 payload
    data = {
        "client_name": None,  # 必填缺失
        "land_user": "张三",
        "report_no": "评报A",
        "valuation_date": "2026-06-02",
        "land_area": 1000.0,
        "building_area": 2000.0,
        "plot_ratio": 2.5,
        "planning_approval_authority": "通道县自规局",
        "ownership_scenario_type": "new_grant",
        "asset_use_category": "residential",
        "land_location": "道县工业路",
        "right_type": "出让",
        "land_usage": "城镇住宅用地",
        "land_usage_short": "住宅",
        "land_usage_full": "城镇住宅用地",
        "land_use_term": "70年",
        "report_date": "2026-06-02",
        "parcel_count": "一宗",
        "appraisal_org": "测试受托机构",
        "technical_report_no": "技报A",
    }
    
    data["archive_to_result"] = True  # 开启强力归档拦截
    
    # 调用校验函数，期望其抛出 422 异常
    with pytest.raises(HTTPException) as exc_info:
        validate_render_payload(data)
        
    assert exc_info.value.status_code == 422
    assert "正式归档失败" in exc_info.value.detail
    assert "委托人名称" in exc_info.value.detail


def test_registered_complete_strict_prevention():
    """验证已登记土地场景下，核心权属要素缺失或为占位符时在归档模式下同样会被强拦截。"""
    data = {
        "client_name": "委托人A",
        "land_user": "张三",
        "report_no": "评报A",
        "valuation_date": "2026-06-02",
        "land_area": 1000.0,
        "building_area": 2000.0,
        "plot_ratio": 2.5,
        "planning_approval_authority": "通道县自规局",
        
        # 激活已登记土地场景
        "ownership_scenario_type": "registered_complete",
        "right_cert_no": "【请填写土地证号】",  # 带有占位符
        
        "asset_use_category": "residential",
        "land_location": "道县工业路",
        "right_type": "出让",
        "land_usage": "城镇住宅用地",
        "land_usage_short": "住宅",
        "land_usage_full": "城镇住宅用地",
        "land_use_term": "70年",
        "report_date": "2026-06-02",
        "parcel_count": "一宗",
        "appraisal_org": "测试受托机构",
        "technical_report_no": "技报A",
    }
    
    data["archive_to_result"] = True
    
    with pytest.raises(HTTPException) as exc_info:
        validate_render_payload(data)
        
    assert exc_info.value.status_code == 422
    assert "权利证书号" in exc_info.value.detail
