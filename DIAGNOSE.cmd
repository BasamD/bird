@echo off
echo ================================
echo Bird Tracker Diagnostics
echo ================================
echo.

cd /d "%~dp0"
echo Working Directory: %CD%
echo.

echo [1] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)
echo.

echo [2] Checking Python packages...
echo.
python -c "import cv2; print('✓ opencv-python:', cv2.__version__)"
if errorlevel 1 echo ✗ opencv-python NOT installed
python -c "import ultralytics; print('✓ ultralytics:', ultralytics.__version__)"
if errorlevel 1 echo ✗ ultralytics NOT installed
python -c "import openai; print('✓ openai:', openai.__version__)"
if errorlevel 1 echo ✗ openai NOT installed
python -c "import numpy; print('✓ numpy:', numpy.__version__)"
if errorlevel 1 echo ✗ numpy NOT installed
echo.

echo [3] Checking project structure...
echo.
if exist "scripts\pilot_bird_counter_fixed.py" (
    echo ✓ pilot_bird_counter_fixed.py found
) else (
    echo ✗ pilot_bird_counter_fixed.py NOT FOUND
)
if exist "scripts\pilot_analyze_captures_fixed.py" (
    echo ✓ pilot_analyze_captures_fixed.py found
) else (
    echo ✗ pilot_analyze_captures_fixed.py NOT FOUND
)
if exist "scripts\config.py" (
    echo ✓ config.py found
) else (
    echo ✗ config.py NOT FOUND
)
if exist "public\dashboard.html" (
    echo ✓ public\dashboard.html found
) else (
    echo ✗ public\dashboard.html NOT FOUND
)
if exist "dist\dashboard.html" (
    echo ✓ dist\dashboard.html found
) else (
    echo ✗ dist\dashboard.html NOT FOUND
)
echo.

echo [4] Checking environment variables...
if "%OPENAI_API_KEY%"=="" (
    echo ✗ OPENAI_API_KEY not set
) else (
    echo ✓ OPENAI_API_KEY is set
)
echo.

echo [5] Testing Python script syntax...
cd scripts
echo Testing pilot_bird_counter_fixed.py...
python -m py_compile pilot_bird_counter_fixed.py
if errorlevel 1 (
    echo ✗ Syntax errors in pilot_bird_counter_fixed.py
) else (
    echo ✓ pilot_bird_counter_fixed.py syntax OK
)

echo Testing pilot_analyze_captures_fixed.py...
python -m py_compile pilot_analyze_captures_fixed.py
if errorlevel 1 (
    echo ✗ Syntax errors in pilot_analyze_captures_fixed.py
) else (
    echo ✓ pilot_analyze_captures_fixed.py syntax OK
)
cd ..
echo.

echo [6] Checking YOLO model...
cd scripts
python -c "from ultralytics import YOLO; m=YOLO('yolov8n.pt'); print('✓ YOLO model loaded successfully')" 2>nul
if errorlevel 1 (
    echo ✗ YOLO model failed to load (will download on first run)
) else (
    echo ✓ YOLO model ready
)
cd ..
echo.

echo ================================
echo Diagnostic Complete
echo ================================
echo.
echo If all checks passed, try running START_BIRD_TRACKER.cmd
echo.
pause
