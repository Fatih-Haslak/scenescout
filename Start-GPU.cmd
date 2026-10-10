@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start.ps1" -Backend cuda %*
if errorlevel 1 pause
