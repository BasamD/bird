@echo off
echo.
echo ================================
echo Bird Tracker - One-Click Startup
echo ================================
echo.

REM Change to script directory immediately
echo Changing to project directory...
cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Failed to change directory
    echo Attempted path: %~dp0
    pause
    exit /b 1
)
echo Project directory: %CD%
echo.

setlocal enabledelayedexpansion
if errorlevel 1 (
    echo ERROR: Failed to enable delayed expansion
    pause
    exit /b 1
)

REM Check Python installation
echo [1/8] Checking for Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo ================================
    echo ERROR: Python is NOT installed or not in PATH
    echo ================================
    echo.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    echo After installing, restart this script
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo Location:
where python
echo.

REM Check Node/npm installation
echo [2/8] Checking for npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo.
    echo ================================
    echo ERROR: npm is NOT installed or not in PATH
    echo ================================
    echo.
    echo Please install Node.js from https://nodejs.org/
    echo.
    echo After installing, restart this script
    echo.
    pause
    exit /b 1
)

echo npm found:
call npm --version
echo.

REM Install Python requirements
echo [3/8] Installing Python requirements...
echo Changing to scripts directory...
cd /d "%~dp0scripts"
if not exist "requirements.txt" (
    echo.
    echo ================================
    echo ERROR: requirements.txt not found
    echo ================================
    echo.
    echo Current directory: %CD%
    echo Expected file: %CD%\requirements.txt
    echo.
    pause
    exit /b 1
)

echo Installing: opencv-python, ultralytics, openai, numpy, python-dotenv
echo This may take 30-60 seconds...
echo.

python -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo ================================
    echo ERROR: Failed to install Python packages
    echo ================================
    echo.
    echo Try manually:
    echo   cd scripts
    echo   pip install -r requirements.txt
    echo.
    echo Common fixes:
    echo - Run as Administrator
    echo - Update pip: python -m pip install --upgrade pip
    echo - Check internet connection
    echo.
    pause
    exit /b 1
)
echo Python packages installed successfully
echo.

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
echo Current scripts directory: %CD%
echo.

if not exist "pilot_bird_counter_fixed.py" (
    echo ERROR: pilot_bird_counter_fixed.py not found in scripts folder
    echo Files in scripts folder:
    dir /b
    echo.
    pause
    exit /b 1
)

echo Checking Python scripts before launching...
python pilot_bird_counter_fixed.py --help >nul 2>&1
if errorlevel 1 (
    echo WARNING: Bird counter script may have issues
)

echo.
echo Launching Bird Counter in new window...
start "Bird Counter [DO NOT CLOSE]" cmd /k "cd /d "%~dp0scripts" && echo =============================== && echo BIRD COUNTER && echo =============================== && echo. && echo Starting bird detection... && echo Press Ctrl+C to stop && echo. && python pilot_bird_counter_fixed.py || (echo. && echo =============================== && echo ERROR: Script crashed or failed && echo =============================== && echo. && pause)"
timeout /t 2 /nobreak >nul

echo Launching Bird Analyzer in new window...
start "Bird Analyzer [DO NOT CLOSE]" cmd /k "cd /d "%~dp0scripts" && echo =============================== && echo BIRD ANALYZER && echo =============================== && echo. && echo Starting bird analysis... && echo Press Ctrl+C to stop && echo. && python pilot_analyze_captures_fixed.py --watch || (echo. && echo =============================== && echo ERROR: Script crashed or failed && echo =============================== && echo. && pause)"
timeout /t 3 /nobreak >nul

echo.
echo Bird detection scripts launched successfully
echo Check the two new windows that opened
echo.

REM Start web server for dashboard
echo.
echo [9/9] Starting dashboard server...
cd /d "%~dp0"
echo Dashboard directory: %CD%
echo.

if not exist "public\dashboard.html" (
    echo WARNING: public\dashboard.html not found
    echo Checking dist folder...
    if exist "dist\dashboard.html" (
        echo Found dashboard in dist folder
        cd dist
    ) else (
        echo ERROR: No dashboard.html found in public or dist
        echo Files in public:
        dir /b public 2>nul
        echo Files in dist:
        dir /b dist 2>nul
        echo.
        echo Dashboard may not work properly
        pause
    )
) else (
    cd public
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
echo Current serving directory: %CD%
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
echo Opening browser to http://localhost:8080
start http://localhost:8080

REM Start Python HTTP server
echo Starting HTTP server on port 8080...
echo.
python -m http.server 8080

REM If we get here, the server stopped
echo.
echo ================================
echo Server Stopped
echo ================================
echo.
echo The HTTP server has stopped.
echo.
echo To restart:
echo 1. Close the Bird Counter and Bird Analyzer windows
echo 2. Run START_BIRD_TRACKER.cmd again
echo.
pause
