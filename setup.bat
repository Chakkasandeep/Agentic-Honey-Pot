@echo off
REM Honeypot API Quick Start Script for Windows

echo ==========================================
echo    Honeypot API Quick Start Setup
echo ==========================================
echo.

REM Check Python
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo Please install Python 3.9 or higher from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Setup environment
echo Setting up environment variables...
if not exist .env (
    copy .env.example .env
    echo .env file created from template
    echo.
    echo IMPORTANT: You need to update .env with your API keys:
    echo.
    echo 1. GROQ_API_KEY - Get from: https://console.groq.com/keys
    echo 2. HONEYPOT_API_KEY - Generate a secure random key
    echo.
    
    REM Generate API key
    python -c "import secrets; print('HONEYPOT_API_KEY=' + secrets.token_urlsafe(32))" > temp_key.txt
    for /f "tokens=*" %%a in (temp_key.txt) do set %%a
    del temp_key.txt
    
    echo Generated HONEYPOT_API_KEY
    echo.
    echo Opening .env file for editing...
    notepad .env
    echo.
    set /p CONTINUE="Have you added your GROQ_API_KEY to .env? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo Please add your GROQ_API_KEY to .env and run this script again
        pause
        exit /b 1
    )
) else (
    echo .env file already exists
)
echo.

echo Setup complete!
echo.
echo To start the server, run:
echo   python main.py
echo.
echo Or using uvicorn:
echo   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Next steps:
echo   1. Start the server
echo   2. Test with: python test_api.py
echo   3. Deploy to Railway/Render/Fly.io
echo   4. Submit to GUVI hackathon
echo.

set /p START="Would you like to start the server now? (y/n): "
if /i "%START%"=="y" (
    echo.
    echo Starting Honeypot API server...
    echo Server will be available at: http://localhost:8000
    echo API Documentation: http://localhost:8000/docs
    echo Press Ctrl+C to stop the server
    echo.
    python main.py
) else (
    echo.
    echo Setup complete! Good luck with the hackathon!
    pause
)