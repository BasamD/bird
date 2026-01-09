@echo off
echo.
echo ================================
echo Startup Log Viewer
echo ================================
echo.

if not exist "startup_log.txt" (
    echo No log file found yet
    echo Run START_BIRD_TRACKER.cmd first to generate a log
    echo.
    pause
    exit /b
)

echo Displaying startup_log.txt:
echo.
echo ================================
type startup_log.txt
echo ================================
echo.
echo End of log
echo.
pause
