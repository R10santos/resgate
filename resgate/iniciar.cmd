@echo off
cd /d "%~dp0"
if exist "dist\Eco7.exe" (
  start "" "dist\Eco7.exe"
) else (
  call jogar.bat
)
