@echo off
echo ================================
echo Python Package Installation Test
echo ================================
echo.

cd /d "%~dp0scripts"
echo Current directory: %CD%
echo.

echo Checking for requirements.txt...
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found!
    pause
    exit /b 1
)
echo Found requirements.txt
echo.

echo Contents of requirements.txt:
echo --------------------------------
type requirements.txt
echo --------------------------------
echo.

echo Attempting to install packages...
echo.
echo [Output from pip install:]
echo.

python -m pip install -r requirements.txt

echo.
echo ================================
if errorlevel 1 (
    echo FAILED - See error above
    echo.
    echo Try these fixes:
    echo 1. Run as Administrator
    echo 2. Update pip: python -m pip install --upgrade pip
    echo 3. Install packages one by one manually
) else (
    echo SUCCESS - All packages installed
)
echo ================================
echo.
pause
