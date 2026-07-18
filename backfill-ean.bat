@echo off
setlocal
set "ROOT=%~dp0"

set "PY=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=%ROOT%venv\Scripts\python.exe"

if not exist "%PY%" (
    echo No se encontro Python del entorno virtual.
    echo Buscado en: %ROOT%.venv\Scripts\python.exe y %ROOT%venv\Scripts\python.exe
    exit /b 1
)

cd /d "%ROOT%"

rem 1) Poblar la cache de EAN con los slugs que falten (incremental: cada noche
rem    drena lo que la cuota del retailer permita y retoma donde quedo).
"%PY%" -m app.backfill_ean %*

rem 2) Publicar a la base lo que se haya conseguido. Corre SIEMPRE, aunque el
rem    paso 1 se haya cortado por cuota: lo cacheado igual tiene que llegar a la
rem    base. --sin-scrape no le pide nada a los retailers.
"%PY%" -m app.actualizar_productos --sin-scrape
exit /b %ERRORLEVEL%
