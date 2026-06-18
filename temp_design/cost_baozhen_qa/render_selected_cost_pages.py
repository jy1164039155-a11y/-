from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "cost_baozhen_qa.docx"
OUTPUT = ROOT / "render_v2"
SOFFICE = ROOT.parents[1] / "tools" / "LibreOffice-25.8.7" / "program" / "soffice.com"
PAGES = range(112, 122)


def convert(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, timeout=120, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).decode(errors="ignore"))


OUTPUT.mkdir(parents=True, exist_ok=True)
for page_number in PAGES:
    with tempfile.TemporaryDirectory(prefix=f"cost_page_{page_number}_") as temp:
        stage = Path(temp)
        source = stage / "input.docx"
        shutil.copy2(DOCX, source)
        profile_docx = stage / "profile_docx"
        profile_png = stage / "profile_png"
        profile_docx.mkdir()
        profile_png.mkdir()
        filter_data = (
            'pdf:writer_pdf_Export:{"PageRange":{"type":"string","value":"'
            f"{page_number}"
            '"}}'
        )
        convert(
            [
                str(SOFFICE),
                "--headless",
                "--invisible",
                "--nologo",
                "--nofirststartwizard",
                "--nolockcheck",
                "--norestore",
                f"-env:UserInstallation={profile_docx.as_uri()}",
                "--convert-to",
                filter_data,
                "--outdir",
                str(stage),
                str(source),
            ]
        )
        pdf = stage / "input.pdf"
        convert(
            [
                str(SOFFICE),
                "--headless",
                "--invisible",
                "--nologo",
                "--nofirststartwizard",
                "--nolockcheck",
                "--norestore",
                f"-env:UserInstallation={profile_png.as_uri()}",
                "--convert-to",
                "png",
                "--outdir",
                str(stage),
                str(pdf),
            ]
        )
        shutil.copy2(stage / "input.png", OUTPUT / f"page-{page_number}.png")

print(f"rendered={list(PAGES)}")
