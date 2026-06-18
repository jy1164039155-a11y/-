# -*- coding: utf-8 -*-
import re
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Any

def clean_float_string(val: Any) -> float:
    """
    极其强韧的物理浮点数抽取过滤器：
    利用正则表达式物理抽离所有中西文物理单位与口语化杂质（如“15.2平方米”、“约15.2”等），
    确保回填进 Pydantic float 字段时不会触发类型爆红异常。
    """
    if val is None:
        raise ValueError("输入值不能为空")
    
    val_str = str(val).strip()
    if not val_str:
        raise ValueError("输入字符串为空")
        
    # 利用正则提取第一个合法的正负浮点数/整数
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    if not match:
        raise ValueError(f"无法在文本 '{val_str}' 中抽离出有效的数值")
        
    return float(match.group(0))


class PropertyCertAttachment(BaseModel):
    """不动产权证书 / 国有土地使用证 附件提取子契约"""
    model_config = ConfigDict(populate_by_name=True)

    land_user: str = Field(..., description="权利人")
    land_location: str = Field(..., description="坐落位置")
    land_area: float = Field(..., description="分摊使用权面积")
    right_type: str = Field(..., description="权利性质/使用权类型")
    land_usage: str = Field(..., description="用途")

    @model_validator(mode='before')
    @classmethod
    def clean_attachment_fields(cls, data: Any) -> Any:
        """Pydantic v2 前置模型校验器：在强打死之前，完成数字正则清洗"""
        if isinstance(data, dict):
            if "land_area" in data and data["land_area"] is not None:
                try:
                    data["land_area"] = clean_float_string(data["land_area"])
                except Exception as e:
                    raise ValueError(f"【分摊土地面积】数字提取清洗失败: {e}")
        return data


class PlanningConditionAttachment(BaseModel):
    """关于国有建设用地的规划条件的函 附件提取子契约"""
    model_config = ConfigDict(populate_by_name=True)

    planning_approval_authority: str = Field(..., description="批准机关")
    building_density_min: str = Field("35%", description="规划建筑密度下限")
    building_density_max: str = Field("55%", description="规划建筑密度上限")
    plot_ratio_min: str = Field("0.7", description="规划容积率下限")
    plot_ratio: float = Field(..., description="规划容积率")
    greening_rate: str = Field("≤15%", description="规划绿地率")
    building_height_limit: str = Field("24米", description="规划建筑限高")

    @model_validator(mode='before')
    @classmethod
    def clean_attachment_fields(cls, data: Any) -> Any:
        """Pydantic v2 前置模型校验器：在强打死之前，完成数字正则清洗"""
        if isinstance(data, dict):
            if "plot_ratio" in data and data["plot_ratio"] is not None:
                try:
                    data["plot_ratio"] = clean_float_string(data["plot_ratio"])
                except Exception as e:
                    raise ValueError(f"【规划容积率】数字提取清洗失败: {e}")
        return data
