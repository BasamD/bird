@echo off
echo.
echo ================================
echo Bird Tracker - Keep Window Open
echo ================================
echo.
echo This version keeps the window open even after successful startup
echo.
pause

REM Call the main startup script and keep window open
call START_BIRD_TRACKER.cmd

echo.
echo ================================
echo Script execution finished
echo ================================
echo.
echo Check startup_log.txt for details
echo.
pause
