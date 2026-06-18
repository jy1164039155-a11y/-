from pathlib import Path

import fitz


HERE = Path(__file__).resolve().parent
PDF = HERE / "cost_baozhen_qa.pdf"
doc = fitz.open(PDF)
needles = ("成本逼近法", "土地取得费", "675.3")
matched = []
for page_number, page in enumerate(doc, start=1):
    text = page.get_text()
    if any(needle in text for needle in needles):
        matched.append(page_number)

expanded = sorted(
    {
        page_number
        for match in matched
        for page_number in range(max(1, match - 1), min(len(doc), match + 1) + 1)
    }
)
for page_number in expanded:
    page = doc[page_number - 1]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
    pixmap.save(HERE / f"page-{page_number}.png")

print(f"pages={len(doc)}")
print(f"matches={matched}")
print(f"rendered={expanded}")
