from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOFFICE = ROOT / "tools" / "LibreOffice-25.8.7" / "program" / "soffice.com"
DOCX = HERE / "cost_baozhen_qa.docx"
PDF = HERE / "cost_baozhen_qa.pdf"
BASELINE_DIR = HERE / "baseline_675"
RENDER_V2 = HERE / "render_v2"


def run(args: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(args, cwd=cwd or HERE, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "").strip())


def convert_docx_to_pdf() -> None:
    sys.path.insert(0, str(ROOT))
    from src.api import safe_convert_with_libreoffice

    safe_convert_with_libreoffice(str(DOCX), str(PDF), timeout=120)
    if not PDF.exists():
        raise RuntimeError(f"PDF not generated: {PDF}")


def main() -> None:
    python = sys.executable
    run([python, str(HERE / "build_qa.py")], cwd=HERE)
    convert_docx_to_pdf()
    run([python, str(HERE / "render_cost_pages.py")], cwd=HERE)
    run([python, str(HERE / "render_selected_cost_pages.py")], cwd=HERE)

    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manifest = BASELINE_DIR / "baseline_manifest.txt"
    lines = [f"refreshed_at={stamp}", f"final_price=675.3", f"docx={DOCX.name}", f"pdf={PDF.name}", ""]

    for pattern in ("page-*.png",):
        for source in sorted(HERE.glob(pattern)):
            target = BASELINE_DIR / source.name
            shutil.copy2(source, target)
            lines.append(f"root={source.name}")

    if RENDER_V2.exists():
        render_target = BASELINE_DIR / "render_v2"
        if render_target.exists():
            shutil.rmtree(render_target)
        shutil.copytree(RENDER_V2, render_target)
        for source in sorted(render_target.glob("page-*.png")):
            lines.append(f"render_v2={source.name}")

    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(manifest)
    print(f"baseline_dir={BASELINE_DIR}")


if __name__ == "__main__":
    main()
