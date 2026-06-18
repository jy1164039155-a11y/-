import pandas as pd
import yaml
import os

def generate_config():
    mapping_path = r"02_Process/预检清单.xlsx"
    config_path = r"02_Process/config.yaml"
    
    if not os.path.exists(mapping_path):
        print(f"找不到 {mapping_path}")
        return
        
    df = pd.read_excel(mapping_path)
    # We only care about rows that have '建议变量名' and '对应Excel字段'
    df_valid = df.dropna(subset=['建议变量名', '对应Excel字段']).copy()
    
    mapping_dict = {}
    for _, row in df_valid.iterrows():
        var_name = str(row['建议变量名']).strip()
        excel_field = str(row['对应Excel字段']).strip()
        if var_name and excel_field:
            mapping_dict[var_name] = excel_field
            
    config_data = {
        "mapping": mapping_dict,
        "conditions": {
            "land_status": "征收" # 占位符，等以后加入具体判断逻辑
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        
    print(f"成功生成 {config_path}，包含 {len(mapping_dict)} 个字段映射。")

if __name__ == "__main__":
    generate_config()
