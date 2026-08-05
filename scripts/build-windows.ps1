# build-windows.ps1 — Construit l'application desktop College Aureole (Windows).
#
# Prérequis (à installer une seule fois) :
#   - Python 3.10+ (ajouté au PATH)
#   - Rust : https://rustup.rs (toolchain "stable-msvc", + Visual Studio Build Tools
#     avec la charge "Desktop development with C++")
#   - Node.js 18+ et npm
#
# À exécuter depuis n'importe où :
#   powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
#
# Résultat :
#   - Installateur : frontend\src-tauri\target\release\bundle\nsis\*.exe
#   - Sidecar backend : frontend\src-tauri\binaries\college-aureole-backend-x86_64-pc-windows-msvc.exe
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..").Path

Write-Host "==> 1/3 Sidecar backend (PyInstaller)"
Set-Location "$ROOT\backend"
if (-not (Test-Path "venv\Scripts\python.exe")) {
    python -m venv venv
}
$PY = "venv\Scripts\python.exe"
& $PY -m pip install --upgrade pip
& $PY -m pip install -r requirements.txt pyinstaller
& $PY -m PyInstaller --noconfirm college-aureole-backend.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller a échoué" }

$triple = "x86_64-pc-windows-msvc"
$destDir = "$ROOT\frontend\src-tauri\binaries"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
Copy-Item "dist\college-aureole-backend.exe" `
    "$destDir\college-aureole-backend-$triple.exe" -Force

Write-Host "==> 2/3 Frontend"
Set-Location "$ROOT\frontend"
npm install
npm run build

Write-Host "==> 3/3 Application Tauri (installateur NSIS)"
npm run tauri build -- --bundles nsis

Write-Host "`nTerminé. Installateur : $ROOT\frontend\src-tauri\target\release\bundle\nsis\*.exe"
