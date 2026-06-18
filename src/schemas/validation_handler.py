# -*- coding: utf-8 -*-
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.schemas.land import LandValuationContract

# 1. 自动从核心强契约模型中提取最外层字段的中文业务映射字典
FIELD_TRANSLATION_MAP = {
    name: field.description or name 
    for name, field in LandValuationContract.model_fields.items()
}

# 2. 内置高频异常类型汉化对照表
ERROR_TYPE_MAP = {
    "missing": "必须填写，不能为空！",
    "float_parsing": "必须为纯数字（可带小数点），不能包含汉字或字母！",
    "decimal_parsing": "必须为合法的数值！",
    "integer_parsing": "必须为合法的整数！",
    "date_parsing": "请输入形如 2026-05-25 的标准日期格式！"
}

async def friendly_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    升级版：完美兼容一维字段与多维嵌套数组的桌面级业务汉化拦截器。
    读取核心 Pydantic 契约定义的 description，梯级检索，秒级向估价师反馈人类可读的填报引导信息。
    """
    errors_translated = []
    
    # 嵌套模型内层高频原子字段备用汉化字典，防止漏判
    NESTED_FIELD_MAP = {
        "name": "证明文件名称/证书名",
        "authority": "出具机关/批准机关",
        "no": "文号/字号",
        "date": "签署/发布日期",
        "fact": "证实事实情况",
        "role_desc": "评估依据角色"
    }
    
    for error in exc.errors():
        loc = error.get("loc", [])
        if not loc:
            continue
            
        # 1. 智能化提取核心字段名
        field_name = str(loc[-1])
        err_type = error.get("type", "invalid")
        
        # 2. 梯级检索汉化名称：契约模型元数据 -> 嵌套原子字典 -> 降级原文字段名
        cn_field = FIELD_TRANSLATION_MAP.get(field_name) or NESTED_FIELD_MAP.get(field_name, field_name)
        cn_err = ERROR_TYPE_MAP.get(err_type, error.get("msg", "格式错误"))
        
        # 3. 智能判断是否是嵌套列表/数组报错，如果是，自动拼接人类直观的组号/行号提示
        if len(loc) >= 3 and isinstance(loc[-2], int):
            row_num = loc[-2] + 1
            errors_translated.append(f"❌ 第 {row_num} 组数据填报错误：【{cn_field}】{cn_err}")
        else:
            errors_translated.append(f"❌ 填报错误：【{cn_field}】{cn_err}")
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False, 
            "detail": errors_translated
        }
    )
