from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Any, Dict


BOC_LPR_URL = "https://www.boc.cn/fimarkets/lilv/fd32/201310/t20131031_2591219.html"


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _extract_lpr_from_text(text: str, *, source: str) -> Dict[str, Any]:
    normalized = _normalize_text(text)
    pattern = re.compile(
        r"(?P<date>20\d{2}[-年./]\d{1,2}[-月./]\d{1,2}日?).{0,80}?"
        r"(?P<one>\d+(?:\.\d+)?)\s*%?.{0,80}?"
        r"(?P<five>\d+(?:\.\d+)?)\s*%?"
    )
    candidates = []
    for match in pattern.finditer(normalized):
        one = float(match.group("one"))
        five = float(match.group("five"))
        if 1.0 <= one <= 8.0 and 1.0 <= five <= 8.0:
            candidates.append(
                {
                    "date": match.group("date").replace("年", "-").replace("月", "-").replace("日", ""),
                    "one_year": f"{one:.2f}",
                    "five_year": f"{five:.2f}",
                    "source": source,
                }
            )
    if not candidates:
        raise ValueError("未能识别LPR日期和利率。")
    candidates.sort(key=lambda item: item["date"], reverse=True)
    return candidates[0]


def _read_pdf_text(path: Path) -> str:
    try:
        import fitz  # type: ignore
    except Exception:
        fitz = None
    if fitz is not None:
        with fitz.open(path) as doc:
            return "\n".join(page.get_text("text") for page in doc)
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional runtime package
        raise RuntimeError("缺少PyMuPDF或pypdf，无法解析本地LPR PDF。") from exc
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def query_latest_lpr(base_dir: str | Path) -> Dict[str, Any]:
    errors = []
    try:
        with urllib.request.urlopen(BOC_LPR_URL, timeout=12) as response:
            raw = response.read()
        for encoding in ("utf-8", "gb18030"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                text = ""
        if text:
            result = _extract_lpr_from_text(text, source="中国银行官网")
            result["url"] = BOC_LPR_URL
            result["fetched"] = True
            return result
    except Exception as exc:  # network is a convenience, local PDF is the stable fallback
        errors.append(str(exc))

    pdf_path = Path(base_dir) / "01_Source" / "03_attachment" / "贷款市场报价利率（LPR）.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"未找到本地LPR文件：{pdf_path}；官网查询错误：{'；'.join(errors)}")
    text = _read_pdf_text(pdf_path)
    result = _extract_lpr_from_text(text, source="本地LPR PDF")
    result["url"] = str(pdf_path)
    result["fetched"] = False
    result["errors"] = errors
    return result
