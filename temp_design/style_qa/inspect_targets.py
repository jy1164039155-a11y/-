from __future__ import annotations

import json
from pathlib import Path

from docx import Document

from audit_docx_styles import _paragraph_info


TARGETS = (
    "★成本逼近法",
    "★市场比较法",
    "★收益还原法",
    "收益还原法是在",
    "法定有限年期",
    "P＝",
    "式中",
    "具体测算思路",
    "1、确定房地年总收益",
    "①月租金的确定",
    "表3-13",
    "表3-14",
    "表3-15",
    "表3-16",
    "2、确定房地年总费用",
)


def inspect(path: Path) -> dict:
    doc = Document(path)
    matches = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text and any(text.startswith(target) for target in TARGETS):
            matches.append(_paragraph_info(paragraph))
    return {"path": str(path), "matches": matches}


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2]
    paths = [
        base / "01_Source" / "02_Word_Templates" / "道县自然资源局办理土地使用权出让手续涉及的位于道县西洲街道宝珍街六栋九号的一宗住宅用途国有建设用地使用权市场价格评估.docx",
        base / "01_Source" / "02_Word_Templates" / "道县湖南紫金新材料产业集聚区（2025018号地块）——合并报告（定稿）.docx",
        base / "01_Source" / "02_Word_Templates" / "自动生成的评估报告模板.docx",
        base / "temp_design" / "income_cap_qa" / "income_cap_baozhen.docx",
    ]
    result = [inspect(path) for path in paths if path.exists()]
    (Path(__file__).parent / "target_styles.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
