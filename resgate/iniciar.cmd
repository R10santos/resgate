@echo off
setlocal
cd /d "%~dp0"
if exist "dist\Eco7.exe" (
  "dist\Eco7.exe" %*
  if errorlevel 1 goto erro
) else (
  call jogar.bat %*
  if errorlevel 1 exit /b 1
)
exit /b 0
:erro
echo Nao foi possivel iniciar o jogo. Confira a mensagem de erro do executavel.
pause
exit /b 1
