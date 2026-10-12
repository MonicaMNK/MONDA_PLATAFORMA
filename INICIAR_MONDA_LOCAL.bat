@echo off
setlocal
cd /d "%~dp0"
if exist ".venv-local\Scripts\python.exe" (
  ".venv-local\Scripts\python.exe" scripts\run_local.py %*
) else (
  echo Falta el entorno Python 3.12. Consulta docs\PRUEBA_LOCAL.md.
  exit /b 1
)
endlocal
