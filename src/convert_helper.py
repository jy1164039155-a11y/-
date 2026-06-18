# -*- coding: utf-8 -*-
import sys
import os
import pythoncom
import win32com.client

def convert_single_file(docx_path: str, pdf_path: str):
    """独立的 COM 另存为 PDF 执行逻辑"""
    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        abs_docx = os.path.abspath(docx_path)
        abs_pdf = os.path.abspath(pdf_path)
        
        try:
            word = win32com.client.Dispatch("Word.Application")
        except Exception:
            try:
                word = win32com.client.Dispatch("WPS.Application")
            except Exception:
                sys.stderr.write("未检测到本地 Microsoft Word 或 WPS Office\n")
                sys.exit(2)
                
        word.Visible = False
        word.DisplayAlerts = False # 绝杀弹窗
        
        doc = word.Documents.Open(abs_docx, ReadOnly=True)
        doc.SaveAs(abs_pdf, FileFormat=17)
        doc.Close(0)
        doc = None
        sys.stdout.write("SUCCESS\n")
    except Exception as e:
        sys.stderr.write(f"COM 另存为 PDF 崩溃: {e}\n")
        sys.exit(3)
    finally:
        if doc is not None:
            try:
                doc.Close(0)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("用法: convert_helper.py <docx_path> <pdf_path>\n")
        sys.exit(1)
    convert_single_file(sys.argv[1], sys.argv[2])
