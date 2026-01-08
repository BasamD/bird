@echo off
echo Script started successfully
echo.

echo ================================
echo Bird Tracker - One-Click Startup
echo ================================
echo.

REM Enable delayed expansion AFTER showing we've started
setlocal enabledelayedexpansion
if errorlevel 1 (
    echo FAILED at setlocal
    pause
    exit /b 1
)

echo [1/8] Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python not found
    pause
    exit /b 1
)
echo.

echo [2/8] Checking npm...
call npm --version
if errorlevel 1 (
    echo.
    echo ERROR: npm not found
    pause
    exit /b 1
)
echo.

echo [3/8] Installing Python requirements...
cd /d "%~dp0scripts"
echo Current directory: %CD%
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Python packages
    echo Try manually: cd scripts ^&^& pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo Done
echo.

echo [4/8] Checking OpenAI API key...
if "%OPENAI_API_KEY%"=="" (
    echo WARNING: No OpenAI API key set
    set /p "user_key=Enter OpenAI API key (or press Enter to skip): "
    if not "!user_key!"=="" (
        set "OPENAI_API_KEY=!user_key!"
        echo Key set for this session
    ) else (
        echo Skipping - only YOLO detection will work
    )
) else (
    echo Key found
)
echo.

echo [5/8] Checking npm dependencies...
cd /d "%~dp0"
if not exist "node_modules" (
    echo Installing npm packages (this may take 2-5 minutes)...
    call npm install
    if errorlevel 1 (
        echo.
        echo ERROR: npm install failed
        pause
        exit /b 1
    )
    echo Done
) else (
    echo Already installed
)
echo.

echo [6/8] Creating metrics.json...
if not exist "public\metrics.json" (
    echo {"total_visits":0,"visits":[],"species_counts":{}} > public\metrics.json
)
echo Done
echo.

echo [7/8] Building dashboard...
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    echo Try manually: npm run build
    echo.
    pause
    exit /b 1
)
echo Done
echo.

echo [8/8] Starting bird detection...
cd /d "%~dp0scripts"
start "Bird Counter" cmd /k "python pilot_bird_counter_fixed.py"
timeout /t 2 /nobreak >nul
start "Bird Analyzer" cmd /k "python pilot_analyze_captures_fixed.py --watch"
timeout /t 2 /nobreak >nul
echo Scripts started in new windows
echo.

echo ================================
echo STARTUP COMPLETE!
echo ================================
echo.
echo Bird detection is running in 2 separate windows
echo Dashboard will start at http://localhost:8080
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0public"
timeout /t 2 /nobreak >nul
start http://localhost:8080
python -m http.server 8080

echo.
echo Server stopped.
pause
