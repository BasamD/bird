@echo off
echo.
echo ================================
echo Testing Steps 5-9
echo ================================
echo.
echo This will test what comes after step 4
echo (where the script appeared to stop)
echo.
pause

REM Setup logging
set "LOGFILE=%~dp0test_continue_log.txt"
echo ================================ > "%LOGFILE%"
echo Test Continue Log >> "%LOGFILE%"
echo Date: %DATE% %TIME% >> "%LOGFILE%"
echo ================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

cd /d "%~dp0"
echo Current directory: %CD%
echo Current directory: %CD% >> "%LOGFILE%"
echo.

echo [TEST 5] Checking for package.json...
echo [TEST 5] Checking for package.json... >> "%LOGFILE%"
if not exist "package.json" (
    echo ERROR: package.json not found
    echo ERROR: package.json not found >> "%LOGFILE%"
    pause
    exit /b 1
)
echo package.json found
echo package.json found >> "%LOGFILE%"
echo.

echo [TEST 5] Checking for node_modules...
echo [TEST 5] Checking for node_modules... >> "%LOGFILE%"
if not exist "node_modules" (
    echo node_modules NOT found
    echo node_modules NOT found >> "%LOGFILE%"
    echo You need to run: npm install
) else (
    echo node_modules found
    echo node_modules found >> "%LOGFILE%"
)
echo.

echo [TEST 6] Checking for public directory...
echo [TEST 6] Checking for public directory... >> "%LOGFILE%"
if not exist "public" (
    echo public directory NOT found
    echo public directory NOT found >> "%LOGFILE%"
) else (
    echo public directory found
    echo public directory found >> "%LOGFILE%"
)
echo.

echo [TEST 6] Checking for metrics.json...
echo [TEST 6] Checking for metrics.json... >> "%LOGFILE%"
if not exist "public\metrics.json" (
    echo metrics.json NOT found
    echo metrics.json NOT found >> "%LOGFILE%"
) else (
    echo metrics.json found
    echo metrics.json found >> "%LOGFILE%"
)
echo.

echo [TEST 7] Checking npm...
echo [TEST 7] Checking npm... >> "%LOGFILE%"
where npm >nul 2>&1
if errorlevel 1 (
    echo npm NOT found
    echo npm NOT found >> "%LOGFILE%"
) else (
    echo npm found
    echo npm found >> "%LOGFILE%"
)
echo.

echo [TEST 8] Checking scripts directory...
echo [TEST 8] Checking scripts directory... >> "%LOGFILE%"
if not exist "scripts" (
    echo scripts directory NOT found
    echo scripts directory NOT found >> "%LOGFILE%"
) else (
    echo scripts directory found
    echo scripts directory found >> "%LOGFILE%"

    echo Files in scripts:
    dir /b scripts
    echo Files in scripts: >> "%LOGFILE%"
    dir /b scripts >> "%LOGFILE%"
)
echo.

echo [TEST 9] Checking for Python scripts...
echo [TEST 9] Checking for Python scripts... >> "%LOGFILE%"
if exist "scripts\pilot_bird_counter_fixed.py" (
    echo pilot_bird_counter_fixed.py found
    echo pilot_bird_counter_fixed.py found >> "%LOGFILE%"
) else (
    echo pilot_bird_counter_fixed.py NOT found
    echo pilot_bird_counter_fixed.py NOT found >> "%LOGFILE%"
)

if exist "scripts\pilot_analyze_captures_fixed.py" (
    echo pilot_analyze_captures_fixed.py found
    echo pilot_analyze_captures_fixed.py found >> "%LOGFILE%"
) else (
    echo pilot_analyze_captures_fixed.py NOT found
    echo pilot_analyze_captures_fixed.py NOT found >> "%LOGFILE%"
)
echo.

echo ================================
echo All Tests Complete
echo ================================
echo.
echo Log saved to: test_continue_log.txt
echo.
pause
