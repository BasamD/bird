@echo off
echo.
echo ================================
echo STARTUP DIAGNOSTIC TOOL
echo ================================
echo.
echo This will check all requirements for the bird tracker
echo.
pause

echo.
echo [CHECK 1/7] Python Installation
echo ================================
where python
if errorlevel 1 (
    echo [FAIL] Python NOT found in PATH
    echo Install from: https://www.python.org/downloads/
) else (
    echo [PASS] Python found
    python --version
    echo.
    echo Python location:
    where python
)
echo.
pause

echo.
echo [CHECK 2/7] pip Installation
echo ================================
python -m pip --version
if errorlevel 1 (
    echo [FAIL] pip is not working
) else (
    echo [PASS] pip is working
)
echo.
pause

echo.
echo [CHECK 3/7] Node.js and npm
echo ================================
where node
if errorlevel 1 (
    echo [FAIL] Node.js NOT found in PATH
    echo Install from: https://nodejs.org/
) else (
    echo [PASS] Node.js found
    node --version
)
echo.
where npm
if errorlevel 1 (
    echo [FAIL] npm NOT found in PATH
) else (
    echo [PASS] npm found
    call npm --version
)
echo.
pause

echo.
echo [CHECK 4/7] Python Requirements
echo ================================
cd /d "%~dp0scripts"
if not exist "requirements.txt" (
    echo [FAIL] requirements.txt not found
    echo Expected: %CD%\requirements.txt
) else (
    echo [PASS] requirements.txt exists
    echo.
    echo Checking installed packages...
    echo.
    python -c "import cv2; print('  opencv-python:', cv2.__version__)"
    if errorlevel 1 echo   [MISSING] opencv-python

    python -c "import ultralytics; print('  ultralytics:', ultralytics.__version__)"
    if errorlevel 1 echo   [MISSING] ultralytics

    python -c "import openai; print('  openai:', openai.__version__)"
    if errorlevel 1 echo   [MISSING] openai

    python -c "import numpy; print('  numpy:', numpy.__version__)"
    if errorlevel 1 echo   [MISSING] numpy

    python -c "import dotenv; print('  python-dotenv: installed')"
    if errorlevel 1 echo   [MISSING] python-dotenv
)
echo.
pause

echo.
echo [CHECK 5/7] Project Files
echo ================================
cd /d "%~dp0"
echo Project directory: %CD%
echo.
if exist "package.json" (echo [PASS] package.json exists) else (echo [FAIL] package.json missing)
if exist "scripts\config.py" (echo [PASS] config.py exists) else (echo [FAIL] config.py missing)
if exist "scripts\pilot_bird_counter_fixed.py" (echo [PASS] pilot_bird_counter_fixed.py exists) else (echo [FAIL] pilot_bird_counter_fixed.py missing)
if exist "scripts\pilot_analyze_captures_fixed.py" (echo [PASS] pilot_analyze_captures_fixed.py exists) else (echo [FAIL] pilot_analyze_captures_fixed.py missing)
echo.
pause

echo.
echo [CHECK 6/7] npm Dependencies
echo ================================
if exist "node_modules" (
    echo [PASS] node_modules folder exists
) else (
    echo [INFO] node_modules not found - will be installed on first run
)
echo.
pause

echo.
echo [CHECK 7/7] OpenAI API Key
echo ================================
cd /d "%~dp0scripts"
python -c "import sys; sys.path.insert(0, '.'); import config; key = config.OPENAI_API_KEY; print('[PASS] API key configured:', key[:8] + '...' + key[-8:] if key else '[FAIL] No API key found')"
echo.
echo Note: The API key can also be set in the .env file
echo.
pause

echo.
echo ================================
echo DIAGNOSTIC COMPLETE
echo ================================
echo.
echo If any checks failed, fix those issues before running START_BIRD_TRACKER.cmd
echo.
echo Common fixes:
echo   - Install missing Python packages: cd scripts ^&^& pip install -r requirements.txt
echo   - Install npm packages: npm install
echo   - Restart your terminal/CMD after installing Python or Node.js
echo.
pause
