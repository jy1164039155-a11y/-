import pandas as pd
import os
import re

def auto_mapping():
    excel_path = r"01_Source/01_Excel_Sheets/HP_测算表_20260521.xlsx"
    mapping_path = r"02_Process/预检清单.xlsx"
    
    if not os.path.exists(excel_path) or not os.path.exists(mapping_path):
        print("文件不存在")
        return

    # 1. 加载测算表所有数据 (data_only=True 获取计算后的值)
    print("正在加载测算表...")
    xl = pd.ExcelFile(excel_path)
    excel_data = {}
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        # 建立 值 -> 坐标 的映射
        for r_idx, row in df.iterrows():
            for c_idx, val in enumerate(row):
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str not in excel_data:
                        excel_data[val_str] = f"{sheet_name}!{chr(65+c_idx % 26)}{r_idx+1}"

    # 2. 读取预检清单
    print("正在加载预检清单...")
    mapping_df = pd.read_excel(mapping_path)
    
    # 常用变量名映射表（语义化建议）
    semantic_map = {
        "通道侗族自治县自然资源局": "client_name",
        "通道县自然资源局": "client_name",
        "双江镇城南街": "land_location",
        "住宅": "land_usage",
        "出让": "right_type",
        "国有土地使用权": "land_right_name",
        "评估报告": "report_type",
        "估价对象": "valuation_object",
    }

    def suggest_variable(text):
        text = str(text)
        # 匹配日期格式 YYYY年MM月DD日
        if re.search(r"\d{4}年\d{1,2}月\d{1,2}日", text):
            if "价值时点" in text or "2026" in text:
                return "valuation_date"
            return "report_date"
        
        # 匹配报告编号 ZC0005
        if re.search(r"[A-Z]{2}\d{4}", text):
            return "report_no"
        
        # 匹配面积 (含数字)
        if re.search(r"\d+\.?\d*", text) and ("平方米" in text or len(text) < 10):
            return "area_val"

        # 语义匹配
        for key, var in semantic_map.items():
            if key in text:
                return var
        
        return "var_" + str(len(text))

    # 3. 执行匹配
    print("开始执行自动匹配...")
    for idx, row in mapping_df.iterrows():
        original_word = str(row["标黄原词"]).strip()
        
        # 查找 Excel 对应字段
        excel_field = excel_data.get(original_word, "")
        if not excel_field:
            # 模糊查找：如果 Word 里的词包含在 Excel 单元格里，或者反之
            for val_str, coord in excel_data.items():
                if original_word in val_str or val_str in original_word:
                    if len(val_str) > 2: # 避免匹配太短的字符
                        excel_field = coord
                        break
        
        mapping_df.at[idx, "对应Excel字段"] = excel_field
        
        # 建议变量名
        if pd.isna(row["建议变量名"]) or row["建议变量名"] == "":
            mapping_df.at[idx, "建议变量名"] = suggest_variable(original_word)

    # 4. 回写
    mapping_df.to_excel(mapping_path, index=False)
    print(f"自动填写完成！已更新: {mapping_path}")

if __name__ == "__main__":
    auto_mapping()
