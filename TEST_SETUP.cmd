@echo off
echo ================================
echo Bird Tracker - Setup Diagnostics
echo ================================
echo.

echo [Step 1] Checking Python...
python --version
if errorlevel 1 (
    echo FAILED: Python not found
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK
echo.

echo [Step 2] Checking npm...
call npm --version
if errorlevel 1 (
    echo FAILED: npm not found
    echo Install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)
echo OK
echo.

echo [Step 3] Checking file structure...
echo Current directory: %CD%
if not exist "package.json" (
    echo FAILED: package.json not found
    echo Make sure you're running this from the project root folder
    pause
    exit /b 1
)
echo - package.json: Found
if not exist "scripts\requirements.txt" (
    echo FAILED: scripts\requirements.txt not found
    pause
    exit /b 1
)
echo - scripts\requirements.txt: Found
if not exist "scripts\pilot_bird_counter_fixed.py" (
    echo FAILED: scripts\pilot_bird_counter_fixed.py not found
    pause
    exit /b 1
)
echo - scripts\pilot_bird_counter_fixed.py: Found
echo - scripts\pilot_analyze_captures_fixed.py: Found
echo OK
echo.

echo [Step 4] Testing Python pip...
python -m pip --version
if errorlevel 1 (
    echo FAILED: pip not working
    pause
    exit /b 1
)
echo OK
echo.

echo ================================
echo ALL CHECKS PASSED!
echo ================================
echo.
echo Your system is ready. You can now run START_BIRD_TRACKER.cmd
echo.
pause
