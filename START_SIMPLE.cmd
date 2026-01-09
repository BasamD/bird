@echo off
echo.
echo ================================
echo Bird Tracker - SIMPLE VERSION
echo ================================
echo.
echo This version shows everything on screen
echo and keeps the window open.
echo.
pause

REM Setup logging
set "LOGFILE=%~dp0startup_log.txt"
echo Creating log file: %LOGFILE%
echo ================================ > "%LOGFILE%"
echo Bird Tracker Startup Log >> "%LOGFILE%"
echo Date: %DATE% %TIME% >> "%LOGFILE%"
echo ================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"
echo Log file created successfully
echo.

REM Change to project directory
echo [Step 1] Changing to project directory...
echo [Step 1] Changing to project directory... >> "%LOGFILE%"
cd /d "%~dp0"
echo Current directory: %CD%
echo Current directory: %CD% >> "%LOGFILE%"
echo. >> "%LOGFILE%"
echo.

REM Check Python
echo [Step 2] Checking for Python...
echo [Step 2] Checking for Python... >> "%LOGFILE%"
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found >> "%LOGFILE%"
    echo ERROR: Python is NOT installed or not in PATH
    echo.
    echo Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)
python --version
python --version >> "%LOGFILE%" 2>&1
where python
where python >> "%LOGFILE%" 2>&1
echo Python found successfully
echo. >> "%LOGFILE%"
echo.

REM Check npm
echo [Step 3] Checking for npm...
echo [Step 3] Checking for npm... >> "%LOGFILE%"
where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found >> "%LOGFILE%"
    echo ERROR: npm is NOT installed or not in PATH
    echo.
    echo Please install Node.js from https://nodejs.org
    echo.
    pause
    exit /b 1
)
call npm --version
call npm --version >> "%LOGFILE%" 2>&1
echo npm found successfully
echo. >> "%LOGFILE%"
echo.

REM Check if scripts directory exists
echo [Step 4] Checking scripts directory...
echo [Step 4] Checking scripts directory... >> "%LOGFILE%"
if not exist "scripts" (
    echo ERROR: scripts directory not found >> "%LOGFILE%"
    echo ERROR: scripts directory not found
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)
echo scripts directory found
echo scripts directory found >> "%LOGFILE%"
echo.

REM List what's in scripts
echo Files in scripts directory:
dir /b scripts
dir /b scripts >> "%LOGFILE%"
echo. >> "%LOGFILE%"
echo.

echo ================================
echo All basic checks passed!
echo ================================
echo.
echo Next steps:
echo 1. Check startup_log.txt
echo 2. If everything looks good, run START_BIRD_TRACKER.cmd
echo.
echo Log saved to: %LOGFILE%
echo.
pause
