@echo off
echo ================================
echo Bird Tracker Startup Test
echo ================================
echo.

cd /d "%~dp0scripts"
echo Running test from: %CD%
echo.

python test_startup.py

echo.
echo ================================
echo Test complete
echo ================================
echo.
pause
