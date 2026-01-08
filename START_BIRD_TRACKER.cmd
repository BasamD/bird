@echo off

REM Change to script directory immediately
cd /d "%~dp0"

echo ================================
echo Bird Tracker - One-Click Startup
echo ================================
echo.
echo Project directory: %CD%
echo.
echo Starting checks...
echo.

setlocal enabledelayedexpansion

REM Check Python installation
echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/8] Python found
python --version

REM Check Node/npm installation
echo Checking for npm...
call npm --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [2/8] npm found
npm --version

REM Install Python requirements
echo.
echo [3/8] Installing Python requirements...
cd /d "%~dp0scripts"
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found in scripts folder
    echo Current directory: %CD%
    pause
    exit /b 1
)
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Python requirements
    echo Try running manually: cd scripts ^&^& pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo Python requirements installed successfully

REM Check for OpenAI API key
echo.
echo [4/8] Checking OpenAI API key...
if "%OPENAI_API_KEY%"=="" (
    echo WARNING: OPENAI_API_KEY environment variable is not set
    echo The bird analysis feature will not work without it
    echo.
    set /p "user_key=Enter your OpenAI API key (or press Enter to skip): "
    if not "!user_key!"=="" (
        set "OPENAI_API_KEY=!user_key!"
        echo API key set for this session
    ) else (
        echo Continuing without API key - only YOLO detection will work
    )
) else (
    echo OpenAI API key found
)

REM Install npm dependencies if needed
cd /d "%~dp0"
echo.
echo Current directory: %CD%
if not exist "package.json" (
    echo ERROR: package.json not found
    pause
    exit /b 1
)
if not exist "node_modules" (
    echo.
    echo [5/8] Installing npm dependencies (this may take a few minutes)...
    call npm install
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install npm dependencies
        echo Try running manually: npm install
        echo.
        pause
        exit /b 1
    )
    echo npm dependencies installed successfully
) else (
    echo [5/8] npm dependencies already installed
)

REM Create initial metrics.json if it doesn't exist
echo.
echo [6/8] Initializing metrics file...
cd /d "%~dp0"
if not exist "public\metrics.json" (
    echo {"total_visits":0,"visits":[],"species_counts":{}} > public\metrics.json
    echo Created initial metrics.json
) else (
    echo metrics.json already exists
)

REM Build the dashboard
echo.
echo [7/8] Building dashboard...
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Failed to build dashboard
    echo Try running manually: npm run build
    echo.
    pause
    exit /b 1
)
echo Dashboard built successfully

REM Start the Python scripts in background
echo.
echo [8/9] Starting bird detection scripts...
cd /d "%~dp0scripts"
if not exist "pilot_bird_counter_fixed.py" (
    echo ERROR: pilot_bird_counter_fixed.py not found in scripts folder
    pause
    exit /b 1
)

REM Start bird counter
start "Bird Counter" cmd /k "python pilot_bird_counter_fixed.py"
timeout /t 2 /nobreak >nul

REM Start analyzer (in watch mode)
start "Bird Analyzer" cmd /k "python pilot_analyze_captures_fixed.py --watch"
timeout /t 2 /nobreak >nul

echo Bird detection scripts started in separate windows

REM Start web server for dashboard
echo.
echo [9/9] Starting dashboard server...
cd /d "%~dp0public"
if not exist "dashboard.html" (
    echo WARNING: dashboard.html not found, but continuing...
)

echo.
echo ================================
echo STARTUP COMPLETE!
echo ================================
echo.
echo Bird Counter: Running (separate window)
echo Bird Analyzer: Running (separate window)
echo Dashboard: http://localhost:8080
echo.
echo The dashboard will open in your browser in 3 seconds...
echo.
echo To stop everything:
echo - Close this window
echo - Close the "Bird Counter" window
echo - Close the "Bird Analyzer" window
echo.
echo Press Ctrl+C to stop the dashboard server
echo ================================
echo.

REM Wait a moment for Python scripts to initialize
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:8080

REM Start Python HTTP server
python -m http.server 8080

REM If we get here, something went wrong
echo.
echo Server stopped. Press any key to exit.
pause >nul
