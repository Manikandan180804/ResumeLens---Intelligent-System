@echo off
echo ============================================================
echo   Resume Intelligence System - Startup
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

echo [1] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2] Initializing database and models...
python initialize.py

echo.
echo ============================================================
echo  Starting services...
echo  - Backend API will start on http://localhost:8000
echo  - Open a SECOND terminal and run: streamlit run frontend/app.py
echo ============================================================
echo.

python -m uvicorn backend.main:app --reload --port 8000
