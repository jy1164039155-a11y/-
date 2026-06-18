import os
import docx
from datetime import datetime
from docxtpl import DocxTemplate

class ReportGenerator:
    def __init__(self, template_path, output_dir, logger):
        self.template_path = template_path
        self.output_dir = output_dir
        self.logger = logger
        self.version = "1.0.0"

    def generate(self, context_data, excel_name, md5_checksum):
        self.logger.info("开始渲染 Word 模板...")
        try:
            doc = DocxTemplate(self.template_path)
            
            # Context injection
            doc.render(context_data)
            
            # Traceability Fingerprint
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fingerprint = (
                f"\n--- [数据溯源指纹] ---\n"
                f"源数据文件: {excel_name}\n"
                f"文件MD5校验码: {md5_checksum}\n"
                f"生成时间: {timestamp}\n"
                f"工具版本: {self.version}\n"
                f"-----------------------"
            )
            
            p = doc.add_paragraph()
            p.paragraph_format.space_before = docx.shared.Pt(12)
            run = p.add_run(fingerprint)
            run.font.name = '仿宋_GB2312'
            run.font.size = docx.shared.Pt(9.5)
            run.font.color.rgb = docx.shared.RGBColor(128, 128, 128)
            
            # 强保中文字体为 仿宋_GB2312
            from docx.oxml.ns import qn
            rPr = run._r.get_or_add_rPr()
            rFonts = rPr.get_or_add_rFonts()
            rFonts.set(qn('w:eastAsia'), '仿宋_GB2312')
            rFonts.set(qn('w:ascii'), '仿宋_GB2312')
            rFonts.set(qn('w:hAnsi'), '仿宋_GB2312')
            rFonts.set(qn('w:cs'), '仿宋_GB2312')
            
            # Ensure output directory
            project_name = context_data.get("land_location", "未命名项目").replace("/", "_").replace("\\", "_")
            date_str = datetime.now().strftime("%Y%m%d")
            out_folder = os.path.join(self.output_dir, f"{date_str}_{project_name}")
            
            if not os.path.exists(out_folder):
                os.makedirs(out_folder)
            
            # Output file name: [ProjectNo]_[Location]_[Timestamp].docx
            report_no = context_data.get("report_no", "未知编号").replace("/", "_")
            time_str = datetime.now().strftime("%H%M")
            out_filename = f"{report_no}_{project_name}_{date_str}_{time_str}.docx"
            out_path = os.path.join(out_folder, out_filename)
            
            doc.save(out_path)
            self.logger.info(f"模板渲染成功，保存至: {out_path}")
            return out_path
        except Exception as e:
            self.logger.error(f"渲染模板时出错: {e}")
            raise
