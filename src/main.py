import os
import sys
import json
from datetime import datetime

# Local module imports
from utils import setup_logger, get_file_md5
from extractor import DataExtractor, KeyFieldError
from generator import ReportGenerator

def main():
    logger = setup_logger("logs")
    logger.info("=== 评估报告自动化工具开始运行 ===")
    
    excel_path = r"01_Source/01_Excel_Sheets/HP_测算表_20260521.xlsx"
    config_path = r"02_Process/config.yaml"
    template_path = r"01_Source/02_Word_Templates/自动生成的评估报告模板.docx"
    output_dir = r"03_Result"
    snapshot_dir = r"02_Process/mapping_logs"

    try:
        # 1. 验证关键文件是否存在
        for path in [excel_path, config_path, template_path]:
            if not os.path.exists(path):
                logger.error(f"严重错误: 找不到关键文件 {path}")
                sys.exit(1)

        # 2. 计算源文件 MD5 指纹
        md5_checksum = get_file_md5(excel_path)
        excel_name = os.path.basename(excel_path)
        logger.info(f"源文件 {excel_name} 的 MD5 校验码: {md5_checksum}")

        # 3. 提取数据
        extractor = DataExtractor(excel_path, config_path, logger)
        context_data = extractor.extract_data()

        # 4. 生成映射快照 (Mapping Snapshot)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = os.path.join(snapshot_dir, f"snapshot_{timestamp}.json")
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, ensure_ascii=False, indent=2)
        logger.info(f"映射快照已保存至: {snapshot_file}")

        # 5. 生成报告
        generator = ReportGenerator(template_path, output_dir, logger)
        out_path = generator.generate(context_data, excel_name, md5_checksum)
        
        logger.info(f"=== 运行结束。报告已成功生成: {out_path} ===")

    except KeyFieldError as e:
        logger.error("因关键字段缺失，程序已安全中断。")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"程序运行中发生未预期错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
