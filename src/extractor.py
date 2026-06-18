import pandas as pd
import yaml
import re
from pathlib import Path
from jinja2 import Template

from src.services.land_usage import normalize_land_usage_fields

def format_excel_date(val):
    """
    Excel 专属智能日期转换器
    支持 float 序列号、datetime 对象以及标准时间字符串，一律规整为中文“年月日”格式。
    """
    if val is None:
        return ""
    if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace(".", "").isdigit()):
        try:
            from datetime import datetime, timedelta
            val_float = float(val)
            if 30000 < val_float < 60000:
                # 1900 是闰年 Excel Bug，从 1899-12-30 开始计算
                dt = datetime(1899, 12, 30) + timedelta(days=val_float)
                return dt.strftime("%Y年%m月%d日")
        except:
            pass
            
    if hasattr(val, "strftime"):
        return val.strftime("%Y年%m月%d日")
        
    val_str = str(val).strip()
    match_ymd = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val_str)
    if match_ymd:
        y, m, d = match_ymd.groups()
        return f"{y}年{int(m)}月{int(d)}日"
        
    return val_str

class KeyFieldError(Exception):
    pass

class SafeContextDict(dict):
    """
    数据清洗与安全兜底字典 (V8.0)
    当 Word 模板渲染调用缺失或空值变量时，自动拦截并回退为 '______'，并在日志中发出 Warning 警告，避免 KeyError 崩溃。
    """
    def __init__(self, data_dict, logger):
        super().__init__(data_dict)
        self.logger = logger

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
            if value is None or str(value).strip() == "":
                self.logger.warning(f"关键上下文字段 [{key}] 填报为空，已触发下划线兜底。")
                return "______"
            return value
        except KeyError:
            self.logger.warning(f"关键上下文字段 [{key}] 缺失！已自动拦截并生成防崩溃占位符。")
            return "______"

    def get(self, key, default=None):
        # 健全防御：仅当 key 存在于字典中时才调用 __getitem__ 拦截空值；
        # 否则安全返回 default（多为 None），绝不能无视 default 返回 '______' 从而污染 Jinja2 的内部控制变量。
        if key in self:
            return self[key]
        return default


class DataExtractor:
    def __init__(self, excel_path, config_path, logger):
        self.excel_path = excel_path
        self.config_path = config_path
        self.logger = logger
        self.config = self._load_config()
        self.excel_data = self._load_excel_data()

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败 {self.config_path}: {e}")
            raise

    def _load_excel_data(self):
        self.logger.info(f"开始读取测算表: {self.excel_path}")
        try:
            xl = pd.ExcelFile(self.excel_path)
            sheets_data = {}
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(self.excel_path, sheet_name=sheet_name, header=None)
                sheets_data[sheet_name] = df
            self.logger.info("测算表读取完成。")
            return sheets_data
        except Exception as e:
            self.logger.error(f"读取测算表失败: {e}")
            raise

    def extract_data(self):
        self.logger.info("开始提取数据...")
        mapping = self.config.get("mapping", {})
        extracted = {}

        for var_name, excel_field in mapping.items():
            # excel_field format expected: 'SheetName!A1'
            if not excel_field or '!' not in str(excel_field):
                self.logger.warning(f"变量 {var_name} 的映射格式不正确或为空: {excel_field}")
                extracted[var_name] = ""
                continue

            try:
                # Clean up single quotes and dollar signs
                excel_field_clean = excel_field.replace("'", "").replace("$", "")
                sheet_name, cell_coord = excel_field_clean.split('!', 1)
                
                # Match sheet name
                matched_sheet = None
                if sheet_name in self.excel_data:
                    matched_sheet = sheet_name
                else:
                    # Fallback for garbled sheet names (try to match first sheet or index)
                    # We know '已开发建设' is usually the first sheet
                    if "已开发建设" in sheet_name and len(self.excel_data) > 0:
                        matched_sheet = list(self.excel_data.keys())[0]
                    elif "基本信息" in sheet_name and len(self.excel_data) > 1:
                        matched_sheet = list(self.excel_data.keys())[1]

                if not matched_sheet:
                    self.logger.error(f"找不到工作表: {sheet_name}")
                    raise KeyFieldError(f"Sheet '{sheet_name}' not found for variable '{var_name}'")

                df = self.excel_data[matched_sheet]
                
                # Parse 'A1', 'B2', etc.
                match = re.match(r"([A-Z]+)(\d+)", cell_coord)
                if not match:
                    raise ValueError(f"Invalid cell format: {cell_coord}")
                    
                col_str, row_str = match.groups()
                
                # Convert column letters to index (A=0, B=1, ..., Z=25, AA=26)
                col_idx = 0
                for char in col_str:
                    col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                col_idx -= 1
                
                # Row index (1-based to 0-based)
                row_idx = int(row_str) - 1
                
                val = df.iloc[row_idx, col_idx]
                
                if pd.isna(val) or str(val).strip() == "":
                    err_msg = f"关键字段缺失: 变量 '{var_name}' 对应的单元格 {excel_field} 为空。"
                    self.logger.error(err_msg)
                    raise KeyFieldError(err_msg)
                
                # 智能清洗：日期变量格式化为中文年月日，四至描述整理整齐
                if "date" in var_name:
                    extracted[var_name] = format_excel_date(val)
                elif var_name == "land_boundary_desc":
                    cleaned_val = str(val).strip()
                    # 去除所有不必要的首尾和内部多余空格，保持整洁流畅
                    extracted[var_name] = re.sub(r'\s+', '', cleaned_val)
                else:
                    extracted[var_name] = str(val).strip()
            except KeyFieldError:
                raise
            except Exception as e:
                err_msg = f"提取变量 '{var_name}' ({excel_field}) 时出错: {e}"
                self.logger.error(err_msg)
                raise KeyFieldError(err_msg)

        # Merge other conditions from config
        conditions = self.config.get("conditions", {})
        extracted.update(conditions)

        # 1. 🔗 智能地名衔接与派生 (client_name -> local_county_full, local_county, local_gov)
        client_name = extracted.get("client_name", "")
        local_county_full = ""
        local_county = ""
        local_gov = ""
        if client_name:
            match = re.search(r"^(.*?(?:自治县|县|区|市))", client_name)
            if match:
                local_county_full = match.group(1)
                if "自治县" in local_county_full:
                    # 智能擦除常见少数民族自治县后缀，绝对精准提取主区划名称并拼接为简称县
                    name = local_county_full.replace("自治县", "")
                    for suffix in ["侗族", "苗族", "瑶族", "壮族", "土家族", "哈尼族", "傣族", "回族", "藏族", "蒙古族", "黎族", "羌族", "畲族", "彝族"]:
                        name = name.replace(suffix, "")
                    local_county = name + "县"
                else:
                    local_county = local_county_full
                local_gov = local_county_full + "人民政府"
        
        extracted["local_county_full"] = local_county_full
        extracted["local_county"] = local_county
        extracted["local_gov"] = local_gov
        
        # 智能规划指标批准机关兜底
        if "planning_approval_authority" not in extracted:
            extracted["planning_approval_authority"] = f"{local_county}自然资源局" if local_county else "道县自然资源局"
            
        self.logger.info(f"成功自动派生地理衔接占位符: local_county_full='{local_county_full}', local_county='{local_county}', local_gov='{local_gov}', planning_approval_authority='{extracted['planning_approval_authority']}'")

        # 3. 🎯 派生基准地价相关字段（支持用户在 config.yaml -> conditions 下自行填写）
        if "base_land_price_expire_limit" not in extracted:
            extracted["base_land_price_expire_limit"] = "六"
            self.logger.warning("未配置 [base_land_price_expire_limit] 基准地价超期年限，自动使用默认兜底值: '六'")
        else:
            extracted["base_land_price_expire_limit"] = str(extracted["base_land_price_expire_limit"]).strip()

        if "is_base_price_expired" in extracted:
            val_expired = extracted["is_base_price_expired"]
            if isinstance(val_expired, str):
                extracted["is_base_price_expired"] = val_expired.lower() in ("true", "1", "yes", "y", "是")
            else:
                extracted["is_base_price_expired"] = bool(val_expired)

        # 基准地价政策依据只做新旧字段对齐，不再注入某一县市的固定文号或日期。
        base_price_aliases = {
            "base_land_price_doc_no": "base_price_doc_no",
            "base_land_price_doc_name": "base_price_doc_name",
            "base_land_price_publish_date": "base_price_publish_date",
            "base_land_price_pub_date": "base_price_publish_date",
            "base_land_price_date": "base_price_base_date",
            "base_land_price_value_date": "base_price_base_date",
            "base_land_price_doc_authority": "base_price_doc_authority",
        }
        for old_key, new_key in base_price_aliases.items():
            if old_key in extracted and new_key not in extracted:
                extracted[new_key] = extracted[old_key]

        # ==============================================================================
        # 🧩 【双轨制自适应智能默认兜底与方法采用状态提取】
        # ==============================================================================
        usage = extracted.get("land_usage_short", "")
        is_industrial = "工业" in usage or "工业用地" in usage
        
        # 1. 采用状态兜底
        methods_keys = ["use_cost_approx", "use_market_comp", "use_income_cap", "use_benchmark_corr", "use_residual"]
        for key in methods_keys:
            if key not in extracted:
                if is_industrial:
                    extracted[key] = key in ["use_cost_approx", "use_market_comp"]
                else:
                    extracted[key] = key in ["use_residual"]
            else:
                # 转换 string 形式的 bool
                val = extracted[key]
                if isinstance(val, str):
                    extracted[key] = val.lower() in ("true", "1", "yes", "y", "是")
                else:
                    extracted[key] = bool(val)
                    
        # 确保 use_cost_approach 再次对齐
        extracted["use_cost_approach"] = extracted["use_cost_approx"]

        # 2. 测算价格与控制开关兜底
        if "show_price_in_text" not in extracted:
            extracted["show_price_in_text"] = True if is_industrial else False
        else:
            val_show = extracted["show_price_in_text"]
            if isinstance(val_show, str):
                extracted["show_price_in_text"] = val_show.lower() in ("true", "1", "yes", "y", "是")
            else:
                extracted["show_price_in_text"] = bool(val_show)

        price_defaults = {
            "cost_approx_price": "189.9",
            "market_comp_price": "127.7",
            "income_cap_price": "2510.5",
            "benchmark_corr_price": "159",
            "residual_price": "2510.5",
            "county_name": extracted.get("local_county", "道县"),
            "building_density_min": "35%",
            "building_density_max": "55%",
            "plot_ratio_mode": "range",
            "plot_ratio_min": "0.7",
            "greening_rate": "≤15%",
            "building_height_limit": "24米"
        }
        for k, v in price_defaults.items():
            if k not in extracted:
                extracted[k] = v

        if "parcel_count" not in extracted or not str(extracted.get("parcel_count")).strip():
            extracted["parcel_count"] = "一宗"

        plot_ratio_mode = str(extracted.get("plot_ratio_mode") or "range").strip()
        plot_ratio_min = str(extracted.get("plot_ratio_min") or "").strip()
        plot_ratio_value = str(extracted.get("plot_ratio") or "").strip()
        if plot_ratio_mode == "range" and plot_ratio_min:
            extracted["plot_ratio_display"] = f"{plot_ratio_min}-{plot_ratio_value}"
        else:
            extracted["plot_ratio_display"] = plot_ratio_value

        normalize_land_usage_fields(extracted)

        if not extracted.get("land_use_term_years"):
            match_years = re.search(r"\d+(?:\.\d+)?", str(extracted.get("land_use_term", "")))
            extracted["land_use_term_years"] = match_years.group(0) if match_years else str(extracted.get("land_use_term", ""))

        # 3. 确价加权合成逻辑自适应
        if "weight_logic_type" not in extracted:
            extracted["weight_logic_type"] = "weighted_average"
        if "dominant_method_name" not in extracted:
            extracted["dominant_method_name"] = "剩余法"
        if "formula_display_text" not in extracted:
            extracted["formula_display_text"] = "成本逼近法×50%+市场比较法×50%"
        if "weight_rationale_text" not in extracted:
            extracted["weight_rationale_text"] = "剩余法..."

        # 4. 采用方法总结 adopted_methods_summary 智能无语病自动拼装
        methods = []
        if extracted["use_cost_approx"]:
            methods.append("成本逼近法")
        if extracted["use_market_comp"]:
            methods.append("市场比较法")
        if extracted["use_income_cap"]:
            methods.append("收益还原法")
        if extracted["use_benchmark_corr"]:
            methods.append("基准地价系数修正法")
        if extracted["use_residual"]:
            methods.append("剩余法")

        if len(methods) == 1:
            extracted["adopted_methods_summary"] = methods[0]
        elif len(methods) > 1:
            extracted["adopted_methods_summary"] = "、".join(methods[:-1]) + "和" + methods[-1]
        else:
            extracted["adopted_methods_summary"] = "______"

        # 2. 🧩 模块化长文本二级内存微渲染 (Micro-Rendering)
        text_library_path = Path(self.config_path).resolve().parent / "text_library.yaml"
        text_lib = {}
        try:
            with open(text_library_path, 'r', encoding='utf-8') as f:
                text_lib = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载外部长文本库失败: {e}")

        land_level_type = conditions.get("land_level_type", "residential_level_3")
        method_combination_type = conditions.get(
            "method_combination_type",
            "industrial_cost_and_market_average" if is_industrial else "residential_residual_only",
        )
        infrastructure_type = conditions.get(
            "infrastructure_type",
            "five_通_industrial" if is_industrial else "five_通_residential",
        )
        extracted["land_level_type"] = land_level_type
        extracted["method_combination_type"] = method_combination_type
        extracted["infrastructure_type"] = infrastructure_type

        val_method_app = ""
        final_price_det = ""
        infra_detail = ""
        if text_lib:
            val_method_app = text_lib.get("valuation_method_applicability_scheme", {}).get(land_level_type, "")
            final_price_det = text_lib.get("final_price_determination_scheme", {}).get(method_combination_type, "")
            infra_detail = text_lib.get("infrastructure_detail_scheme", {}).get(infrastructure_type, "")

        # 利用 Jinja2 对提取出来的长文本段落执行二级微渲染
        render_ctx = {}
        render_ctx.update(extracted)

        if val_method_app:
            try:
                val_method_app = Template(val_method_app).render(render_ctx)
            except Exception as render_err:
                self.logger.warning(f"微渲染方案二适用性段落失败: {render_err}")
        if final_price_det:
            try:
                final_price_det = Template(final_price_det).render(render_ctx)
            except Exception as render_err:
                self.logger.warning(f"微渲染方案三加权调和段落失败: {render_err}")
        if infra_detail:
            try:
                infra_detail = Template(infra_detail).render(render_ctx)
            except Exception as render_err:
                self.logger.warning(f"微渲染方案四开发程度段落失败: {render_err}")

        extracted["valuation_method_applicability"] = val_method_app
        extracted["final_price_determination"] = final_price_det
        extracted["infrastructure_detail"] = infra_detail
        self.logger.info("长文本二级微渲染组装顺利完成并塞入安全上下文。")

        self.logger.info(f"数据提取成功，共提取 {len(extracted)} 个字段。")
        return SafeContextDict(extracted, self.logger)
