# PastyNew Password Generator - build the Windows .exe (run on Windows!)
#
# PowerShell:
#     .\scripts\build_windows.ps1
#
# Produces:
#     dist\pastypw.exe                                        (portable)
#     dist\PastyNew-PasswordGenerator-Setup-1.0.0.exe       (installer, needs NSIS)
#
param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }

Step "Creating virtual environment"
if (-not (Test-Path ".venv-win")) {
    python -m venv .venv-win
}
& .\.venv-win\Scripts\python.exe -m pip install --upgrade pip | Out-Null
& .\.venv-win\Scripts\python.exe -m pip install PySide6 pyinstaller | Out-Null

Step "Generating icons (PNG + .ico)"
$env:QT_QPA_PLATFORM = "offscreen"
& .\.venv-win\Scripts\python.exe scripts\make_icons.py
& .\.venv-win\Scripts\python.exe scripts\make_windows_icon.py
Remove-Item Env:\QT_QPA_PLATFORM

Step "Building the portable executable"
& .\.venv-win\Scripts\python.exe -m PyInstaller `
    packaging\pyinstaller\pastypw-windows.spec `
    --noconfirm --clean --distpath dist --workpath build\pyinstaller

if (Test-Path "dist\pastypw.exe") {
    $size = [math]::Round((Get-Item dist\pastypw.exe).Length / 1MB, 1)
    Write-Host "    dist\pastypw.exe  ($size MB)" -ForegroundColor Green
}

if ($SkipInstaller) {
    Write-Host "done (installer skipped)" -ForegroundColor Green
    exit 0
}

Step "Building the NSIS installer"
$makensis = Get-Command makensis -ErrorAction SilentlyContinue
if (-not $makensis) {
    $makensisPath = "${env:ProgramFiles(x86)}\NSIS\makensis.exe"
    if (Test-Path $makensisPath) { $makensis = $makensisPath }
}

if (-not $makensis) {
    Write-Host @"
makensis was not found, skipping the installer.
  1. install NSIS: https://nsis.sourceforge.io/Download
  2. re-run:  .\scripts\build_windows.ps1
or just ship dist\pastypw.exe as a portable application.
"@ -ForegroundColor Yellow
    exit 0
}

& $makensis "-DpastypwExe=$Root\dist\pastypw.exe" packaging\windows\installer.nsi
if (Test-Path "dist\PastyNew-PasswordGenerator-Setup-1.0.0.exe") {
    $size = [math]::Round((Get-Item dist\PastyNew-PasswordGenerator-Setup-1.0.0.exe).Length / 1MB, 1)
    Write-Host "    dist\PastyNew-PasswordGenerator-Setup-1.0.0.exe  ($size MB)" -ForegroundColor Green
}

Write-Host "done" -ForegroundColor Green