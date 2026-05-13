@echo off
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%venv\Scripts\python.exe"

if not exist "%PY%" (
    echo No se encontro Python del entorno virtual: %PY%
    exit /b 1
)

cd /d "%ROOT%"
"%PY%" -m app.actualizar_productos
exit /b %ERRORLEVEL%
