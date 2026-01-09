@echo off

REM Setup logging
set "LOGFILE=%~dp0startup_log.txt"
echo ================================ > "%LOGFILE%"
echo Bird Tracker Startup Log >> "%LOGFILE%"
echo Date: %DATE% %TIME% >> "%LOGFILE%"
echo ================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo.
echo ================================
echo Bird Tracker - One-Click Startup
echo ================================
echo.
echo Logging to: startup_log.txt
echo.

REM Change to script directory immediately
echo Changing to project directory...
echo Changing to project directory... >> "%LOGFILE%"
cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Failed to change directory
    echo ERROR: Failed to change directory >> "%LOGFILE%"
    echo Attempted path: %~dp0 >> "%LOGFILE%"
    echo. >> "%LOGFILE%"
    echo See startup_log.txt for details
    pause
    exit /b 1
)
echo Project directory: %CD% >> "%LOGFILE%"
echo Project directory: %CD%
echo. >> "%LOGFILE%"
echo.

setlocal enabledelayedexpansion
if errorlevel 1 (
    echo ERROR: Failed to enable delayed expansion >> "%LOGFILE%"
    echo ERROR: Failed to enable delayed expansion
    pause
    exit /b 1
)

REM Check Python installation
echo [1/8] Checking for Python... >> "%LOGFILE%"
echo [1/8] Checking for Python...
where python >nul 2>&1
if errorlevel 1 (
    echo. >> "%LOGFILE%"
    echo ERROR: Python is NOT installed or not in PATH >> "%LOGFILE%"
    echo.
    echo ================================
    echo ERROR: Python is NOT installed or not in PATH
    echo ================================
    echo.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    echo After installing, restart this script
    echo See startup_log.txt for details
    echo.
    pause
    exit /b 1
)

echo Python found: >> "%LOGFILE%"
python --version >> "%LOGFILE%" 2>&1
where python >> "%LOGFILE%" 2>&1
echo Python found:
python --version
echo Location:
where python
echo. >> "%LOGFILE%"
echo.

REM Check Node/npm installation
echo [2/8] Checking for npm... >> "%LOGFILE%"
echo [2/8] Checking for npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo. >> "%LOGFILE%"
    echo ERROR: npm is NOT installed or not in PATH >> "%LOGFILE%"
    echo.
    echo ================================
    echo ERROR: npm is NOT installed or not in PATH
    echo ================================
    echo.
    echo Please install Node.js from https://nodejs.org/
    echo.
    echo After installing, restart this script
    echo See startup_log.txt for details
    echo.
    pause
    exit /b 1
)

echo npm found: >> "%LOGFILE%"
call npm --version >> "%LOGFILE%" 2>&1
echo npm found:
call npm --version
echo. >> "%LOGFILE%"
echo.

REM Install Python requirements
echo [3/8] Installing Python requirements... >> "%LOGFILE%"
echo [3/8] Installing Python requirements...
echo Changing to scripts directory... >> "%LOGFILE%"
echo Changing to scripts directory...
cd /d "%~dp0scripts"
echo Current directory: %CD% >> "%LOGFILE%"
if not exist "requirements.txt" (
    echo. >> "%LOGFILE%"
    echo ERROR: requirements.txt not found >> "%LOGFILE%"
    echo Expected file: %CD%\requirements.txt >> "%LOGFILE%"
    echo.
    echo ================================
    echo ERROR: requirements.txt not found
    echo ================================
    echo.
    echo Current directory: %CD%
    echo Expected file: %CD%\requirements.txt
    echo See startup_log.txt for details
    echo.
    pause
    exit /b 1
)

echo Installing: opencv-python, ultralytics, openai, numpy, python-dotenv >> "%LOGFILE%"
echo This may take 30-60 seconds... >> "%LOGFILE%"
echo Installing: opencv-python, ultralytics, openai, numpy, python-dotenv
echo This may take 30-60 seconds...
echo. >> "%LOGFILE%"
echo.

python -m pip install -r requirements.txt --disable-pip-version-check >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo. >> "%LOGFILE%"
    echo ERROR: Failed to install Python packages >> "%LOGFILE%"
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
    echo See startup_log.txt for details
    echo.
    pause
    exit /b 1
)
echo Python packages installed successfully >> "%LOGFILE%"
echo Python packages installed successfully
echo. >> "%LOGFILE%"
echo.

REM Check for OpenAI API key
echo. >> "%LOGFILE%"
echo [4/8] Checking OpenAI API key... >> "%LOGFILE%"
echo.
echo [4/8] Checking OpenAI API key...
if "%OPENAI_API_KEY%"=="" (
    echo WARNING: OPENAI_API_KEY environment variable is not set >> "%LOGFILE%"
    echo WARNING: OPENAI_API_KEY environment variable is not set
    echo The bird analysis feature will not work without it
    echo.
    set /p "user_key=Enter your OpenAI API key (or press Enter to skip): "
    if not "!user_key!"=="" (
        set "OPENAI_API_KEY=!user_key!"
        echo API key set for this session >> "%LOGFILE%"
        echo API key set for this session
    ) else (
        echo Continuing without API key >> "%LOGFILE%"
        echo Continuing without API key - only YOLO detection will work
    )
) else (
    echo OpenAI API key found >> "%LOGFILE%"
    echo OpenAI API key found
)

REM Install npm dependencies if needed
cd /d "%~dp0"
echo. >> "%LOGFILE%"
echo Returned to project directory: %CD% >> "%LOGFILE%"
echo Returned to project directory: %CD%
echo. >> "%LOGFILE%"
echo.

echo Checking for package.json... >> "%LOGFILE%"
echo Checking for package.json...
if not exist "package.json" (
    echo ERROR: package.json not found >> "%LOGFILE%"
    echo ERROR: package.json not found
    echo See startup_log.txt for details
    pause
    exit /b 1
)
echo package.json found >> "%LOGFILE%"
echo package.json found
echo. >> "%LOGFILE%"
echo.

echo Checking for node_modules... >> "%LOGFILE%"
echo Checking for node_modules...
if not exist "node_modules" (
    echo node_modules not found, need to install >> "%LOGFILE%"
    echo node_modules not found, need to install
    echo. >> "%LOGFILE%"
    echo [5/8] Installing npm dependencies (this may take a few minutes)... >> "%LOGFILE%"
    echo.
    echo [5/8] Installing npm dependencies (this may take a few minutes)...
    call npm install >> "%LOGFILE%" 2>&1
    if errorlevel 1 (
        echo. >> "%LOGFILE%"
        echo ERROR: Failed to install npm dependencies >> "%LOGFILE%"
        echo.
        echo ERROR: Failed to install npm dependencies
        echo Try running manually: npm install
        echo See startup_log.txt for details
        echo.
        pause
        exit /b 1
    )
    echo npm dependencies installed successfully >> "%LOGFILE%"
    echo npm dependencies installed successfully
) else (
    echo node_modules found >> "%LOGFILE%"
    echo node_modules found
    echo [5/8] npm dependencies already installed >> "%LOGFILE%"
    echo [5/8] npm dependencies already installed
)
echo. >> "%LOGFILE%"
echo.

REM Create initial metrics.json if it doesn't exist
echo [6/8] Initializing metrics file... >> "%LOGFILE%"
echo [6/8] Initializing metrics file...
cd /d "%~dp0"
echo Checking public directory... >> "%LOGFILE%"
echo Checking public directory...
if not exist "public" (
    echo Creating public directory... >> "%LOGFILE%"
    echo Creating public directory...
    mkdir public
)
if not exist "public\metrics.json" (
    echo Creating metrics.json... >> "%LOGFILE%"
    echo Creating metrics.json...
    echo {"total_visits":0,"visits":[],"species_counts":{}} > public\metrics.json
    echo Created initial metrics.json >> "%LOGFILE%"
    echo Created initial metrics.json
) else (
    echo metrics.json already exists >> "%LOGFILE%"
    echo metrics.json already exists
)
echo. >> "%LOGFILE%"
echo.

REM Build the dashboard
echo [7/8] Building dashboard... >> "%LOGFILE%"
echo [7/8] Building dashboard...
echo Running npm run build... >> "%LOGFILE%"
echo Running npm run build...
echo This may take 10-20 seconds... >> "%LOGFILE%"
echo This may take 10-20 seconds...
call npm run build >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo. >> "%LOGFILE%"
    echo ERROR: Failed to build dashboard >> "%LOGFILE%"
    echo.
    echo ERROR: Failed to build dashboard
    echo Try running manually: npm run build
    echo See startup_log.txt for details
    echo.
    pause
    exit /b 1
)
echo Dashboard built successfully >> "%LOGFILE%"
echo Dashboard built successfully
echo. >> "%LOGFILE%"
echo.

REM Start the Python scripts in background
echo [8/9] Starting bird detection scripts... >> "%LOGFILE%"
echo [8/9] Starting bird detection scripts...
echo Changing to scripts directory... >> "%LOGFILE%"
echo Changing to scripts directory...
cd /d "%~dp0scripts"
echo Current scripts directory: %CD% >> "%LOGFILE%"
echo Current scripts directory: %CD%
echo. >> "%LOGFILE%"
echo.

if not exist "pilot_bird_counter_fixed.py" (
    echo ERROR: pilot_bird_counter_fixed.py not found >> "%LOGFILE%"
    dir /b >> "%LOGFILE%"
    echo ERROR: pilot_bird_counter_fixed.py not found in scripts folder
    echo Files in scripts folder:
    dir /b
    echo See startup_log.txt for details
    echo.
    pause
    exit /b 1
)

echo Checking Python scripts before launching... >> "%LOGFILE%"
echo Checking Python scripts before launching...
python pilot_bird_counter_fixed.py --help >nul 2>&1
if errorlevel 1 (
    echo WARNING: Bird counter script may have issues >> "%LOGFILE%"
    echo WARNING: Bird counter script may have issues
) else (
    echo Bird counter script looks good >> "%LOGFILE%"
    echo Bird counter script looks good
)
echo. >> "%LOGFILE%"
echo.

echo Launching Bird Counter in new window... >> "%LOGFILE%"
echo Launching Bird Counter in new window...
start "Bird Counter [DO NOT CLOSE]" cmd /k "cd /d "%~dp0scripts" && echo =============================== && echo BIRD COUNTER && echo =============================== && echo. && echo Starting bird detection... && echo Press Ctrl+C to stop && echo. && python pilot_bird_counter_fixed.py || (echo. && echo =============================== && echo ERROR: Script crashed or failed && echo =============================== && echo. && pause)"
timeout /t 2 /nobreak >nul

echo Launching Bird Analyzer in new window... >> "%LOGFILE%"
echo Launching Bird Analyzer in new window...
start "Bird Analyzer [DO NOT CLOSE]" cmd /k "cd /d "%~dp0scripts" && echo =============================== && echo BIRD ANALYZER && echo =============================== && echo. && echo Starting bird analysis... && echo Press Ctrl+C to stop && echo. && python pilot_analyze_captures_fixed.py --watch || (echo. && echo =============================== && echo ERROR: Script crashed or failed && echo =============================== && echo. && pause)"
echo Waiting for scripts to initialize... >> "%LOGFILE%"
echo Waiting for scripts to initialize...
timeout /t 3 /nobreak >nul

echo Bird detection scripts launched successfully >> "%LOGFILE%"
echo Bird detection scripts launched successfully
echo Check the two new windows that opened >> "%LOGFILE%"
echo Check the two new windows that opened
echo. >> "%LOGFILE%"
echo.

REM Start web server for dashboard
echo [9/9] Starting dashboard server... >> "%LOGFILE%"
echo [9/9] Starting dashboard server...
echo Returning to project directory... >> "%LOGFILE%"
echo Returning to project directory...
cd /d "%~dp0"
echo Dashboard directory: %CD% >> "%LOGFILE%"
echo Dashboard directory: %CD%
echo. >> "%LOGFILE%"
echo.

if not exist "public\dashboard.html" (
    echo WARNING: public\dashboard.html not found >> "%LOGFILE%"
    echo WARNING: public\dashboard.html not found
    echo Checking dist folder... >> "%LOGFILE%"
    echo Checking dist folder...
    if exist "dist\dashboard.html" (
        echo Found dashboard in dist folder >> "%LOGFILE%"
        echo Found dashboard in dist folder
        cd dist
    ) else (
        echo ERROR: No dashboard.html found in public or dist >> "%LOGFILE%"
        dir /b public >> "%LOGFILE%" 2>&1
        dir /b dist >> "%LOGFILE%" 2>&1
        echo ERROR: No dashboard.html found in public or dist
        echo Files in public:
        dir /b public 2>nul
        echo Files in dist:
        dir /b dist 2>nul
        echo See startup_log.txt for details
        echo.
        echo Dashboard may not work properly
        pause
    )
) else (
    cd public
    echo Serving from: %CD% >> "%LOGFILE%"
)

echo. >> "%LOGFILE%"
echo ================================ >> "%LOGFILE%"
echo STARTUP COMPLETE! >> "%LOGFILE%"
echo ================================ >> "%LOGFILE%"
echo Current serving directory: %CD% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

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
echo Opening browser to http://localhost:8080 >> "%LOGFILE%"
echo Opening browser to http://localhost:8080
start http://localhost:8080

REM Start Python HTTP server
echo Starting HTTP server on port 8080... >> "%LOGFILE%"
echo Starting HTTP server on port 8080...
echo. >> "%LOGFILE%"
echo.
python -m http.server 8080 >> "%LOGFILE%" 2>&1

REM If we get here, the server stopped
echo. >> "%LOGFILE%"
echo Server stopped at %TIME% >> "%LOGFILE%"
echo ================================ >> "%LOGFILE%"
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
echo Full log saved to: startup_log.txt
echo.
pause
