@echo off
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv is required. Install from https://docs.astral.sh/uv/getting-started/installation/
  echo Kurulum icin README.tr.md dosyasini acin.
  pause
  exit /b 1
)
uv run --frozen scenescout --open-browser
if errorlevel 1 pause
