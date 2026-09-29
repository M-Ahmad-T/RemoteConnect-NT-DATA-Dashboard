@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Project virtual environment was not found.
    echo Create it with an installed Python, then install requirements:
    echo   py -3 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

rem Rebuild derived files on every launch so raw inputs and calculations stay aligned.
".venv\Scripts\python.exe" src\prepare_data.py
if errorlevel 1 (
    echo Data preparation failed. Check the source paths above and DATA_SOURCES.md.
    exit /b 1
)
if /i "%~1"=="--prepare-only" exit /b 0
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true
