@echo off
REM This version has detailed logging and won't close on errors

cd /d "%~dp0"

echo ========================================
echo Bird Tracker Startup (WITH LOGGING)
echo ========================================
echo.
echo Project Directory: %CD%
echo Current Time: %TIME%
echo.

setlocal enabledelayedexpansion

REM Create a log file
set LOGFILE=%CD%\startup_log.txt
echo Startup Log - %DATE% %TIME% > "%LOGFILE%"
echo. >> "%LOGFILE%"

echo [STEP 1] Checking Python...
python --version 2>&1 >> "%LOGFILE%"
python --version
if errorlevel 1 (
    echo ERROR: Python not found! >> "%LOGFILE%"
    echo.
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo ✓ Python OK
echo.

echo [STEP 2] Checking npm...
call npm --version 2>&1 >> "%LOGFILE%"
call npm --version
if errorlevel 1 (
    echo ERROR: npm not found! >> "%LOGFILE%"
    echo.
    echo ERROR: npm is not installed
    pause
    exit /b 1
)
echo ✓ npm OK
echo.

echo [STEP 3] Checking Python packages...
cd scripts
python test_startup.py
set TEST_RESULT=%ERRORLEVEL%
python test_startup.py >> "..\%LOGFILE%" 2>&1
cd ..

if %TEST_RESULT% neq 0 (
    echo.
    echo WARNING: Some tests failed (see above)
    echo Check the log file: %LOGFILE%
    echo.
    echo Do you want to continue anyway? (Y/N)
    set /p continue=
    if /i not "!continue!"=="Y" (
        echo Startup cancelled
        pause
        exit /b 1
    )
)
echo ✓ Tests passed
echo.

echo [STEP 4] Building dashboard...
call npm run build 2>&1 >> "%LOGFILE%"
if errorlevel 1 (
    echo ERROR: Build failed! >> "%LOGFILE%"
    echo.
    echo ERROR: Dashboard build failed
    type "%LOGFILE%"
    pause
    exit /b 1
)
echo ✓ Dashboard built
echo.

echo [STEP 5] Creating required directories and files...
if not exist "public\metrics.json" (
    echo {"total_visits":0,"visits":[],"species_counts":{}} > public\metrics.json
    echo ✓ Created metrics.json
)
echo.

echo [STEP 6] Starting Python scripts...
cd scripts

echo Starting Bird Counter...
start "Bird Counter [DO NOT CLOSE]" cmd /k "title Bird Counter && echo ============================================ && echo Bird Counter - Live Detection && echo ============================================ && echo. && echo Starting... && echo. && python pilot_bird_counter_fixed.py || (echo. && echo ERROR: Script crashed! && echo Check the error above && echo. && pause)"

timeout /t 3 /nobreak >nul

echo Starting Bird Analyzer...
start "Bird Analyzer [DO NOT CLOSE]" cmd /k "title Bird Analyzer && echo ============================================ && echo Bird Analyzer - AI Analysis && echo ============================================ && echo. && echo Starting... && echo. && python pilot_analyze_captures_fixed.py --watch || (echo. && echo ERROR: Script crashed! && echo Check the error above && echo. && pause)"

cd ..
echo ✓ Python scripts launched
echo.

echo [STEP 7] Starting web server...
echo.

REM Determine which folder to serve
if exist "dist\dashboard.html" (
    set SERVE_DIR=dist
    echo Serving from: dist\
) else if exist "public\dashboard.html" (
    set SERVE_DIR=public
    echo Serving from: public\
) else (
    echo WARNING: No dashboard.html found
    set SERVE_DIR=public
)

cd !SERVE_DIR!

echo.
echo ========================================
echo ✓ STARTUP COMPLETE
echo ========================================
echo.
echo Bird Counter:  Running in separate window
echo Bird Analyzer: Running in separate window
echo Dashboard URL: http://localhost:8080
echo Serving from:  %CD%
echo.
echo Opening browser in 3 seconds...
echo.
echo TO STOP:
echo   1. Press Ctrl+C in this window
echo   2. Close the Bird Counter window
echo   3. Close the Bird Analyzer window
echo.
echo Log file: %LOGFILE%
echo ========================================
echo.

timeout /t 3 /nobreak >nul

echo Starting HTTP server on port 8080...
start http://localhost:8080

python -m http.server 8080

REM If we get here, server stopped
echo.
echo ========================================
echo Server stopped
echo ========================================
echo.
pause
