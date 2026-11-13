@echo off
echo ============================================
echo   ORCA Backend Setup ^& Launch Script
echo   SIH26176 Maritime Safety System
echo ============================================
echo.

REM Check Python
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found! Install from https://python.org
    pause
    exit /b 1
)

if "%PORT%"=="" set PORT=8000

REM Create virtual environment if not exists
if not exist "venv\Scripts\python.exe" if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    python -m venv .venv
    echo Done.
) else (
    echo [1/4] Virtual environment already exists. Skipping.
)

REM Activate venv
echo [2/4] Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    call .venv\Scripts\activate.bat
)

REM Install dependencies
echo [3/4] Installing dependencies...
pip install -r requirements.txt --quiet
echo Done.

REM Launch FastAPI
echo [4/4] Starting ORCA Backend Server...
echo.
echo ============================================
echo  API Docs:    http://localhost:8000/docs
echo  Health:      http://localhost:8000/api/status
echo  Risk Zones:  http://localhost:8000/api/risk-zones
echo ============================================
echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port %PORT%

pause
