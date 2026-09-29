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

".venv\Scripts\python.exe" -m streamlit run app.py
