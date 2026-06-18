param(
    [string]$PythonExe = "python",
    [switch]$OptionalOcrDeps
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Installing Python dependencies from $Root\requirements.txt"
& $PythonExe -m pip install -r requirements.txt

if ($OptionalOcrDeps) {
    Write-Host "Installing optional attachment text/OCR helpers"
    & $PythonExe -m pip install pymupdf pdfplumber paddleocr
}

Write-Host "Done. If frontend source changed, run: cd frontend; npm install; npm run build"
