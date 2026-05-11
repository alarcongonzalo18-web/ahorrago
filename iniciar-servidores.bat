@echo off
set "ROOT=%~dp0"

start "AhorraGo API" /D "%ROOT%" "%ROOT%venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8001
start "AhorraGo Frontend" /D "%ROOT%" "%ROOT%venv\Scripts\python.exe" -m http.server 5500

timeout /t 2 /nobreak > nul
start "" "http://localhost:5500/frontend/"
