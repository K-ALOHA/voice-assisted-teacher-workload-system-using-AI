@echo off
echo ==========================================
echo Voice-Assisted Teacher Workload Manager
echo Setup and Installation
echo ==========================================
echo.

echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo [X] Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [X] Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully!
echo.
echo ==========================================
echo Starting application...
echo ==========================================
echo.
echo The application will open in your browser.
echo Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
