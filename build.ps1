# Build the standalone .exe with PyInstaller.
#
# Usage:
#     .\build.ps1
#
# Output: dist\itunes-library-helper.exe

$ErrorActionPreference = "Stop"

Write-Host "==> Cleaning previous build artifacts..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

if (-not (Test-Path .venv)) {
    Write-Host "==> Creating virtual environment (.venv)..." -ForegroundColor Cyan
    py -3.12 -m venv .venv
}

Write-Host "==> Activating venv..." -ForegroundColor Cyan
. .\.venv\Scripts\Activate.ps1

Write-Host "==> Installing dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

Write-Host "==> Building with PyInstaller..." -ForegroundColor Cyan
pyinstaller itunes-library-helper.spec --noconfirm --clean

Write-Host ""
Write-Host "==> Done!" -ForegroundColor Green
Write-Host "Built: dist\itunes-library-helper.exe"
