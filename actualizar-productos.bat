@echo off
setlocal
set "ROOT=%~dp0"

rem Acepta ambos nombres de entorno virtual (.venv es el default de python -m venv
rem en muchos setups; venv era el nombre usado antes). Sin esto la tarea
rem programada fallaba en silencio por no encontrar el interprete.
set "PY=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=%ROOT%venv\Scripts\python.exe"

if not exist "%PY%" (
    echo No se encontro Python del entorno virtual.
    echo Buscado en: %ROOT%.venv\Scripts\python.exe y %ROOT%venv\Scripts\python.exe
    echo Crealo con: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

cd /d "%ROOT%"
rem %* reenvia los argumentos, para poder correr cadenas sueltas:
rem   actualizar-productos.bat --solo lider
"%PY%" -m app.actualizar_productos %*
exit /b %ERRORLEVEL%
