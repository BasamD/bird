@echo off
echo Testing logging system...

REM Setup logging
set "LOGFILE=%~dp0test_startup_log.txt"
echo ================================ > "%LOGFILE%"
echo Test Startup Log >> "%LOGFILE%"
echo Date: %DATE% %TIME% >> "%LOGFILE%"
echo ================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo Step 1: Testing basic echo
echo Step 1: Testing basic echo >> "%LOGFILE%"

echo Step 2: Current directory is %CD%
echo Step 2: Current directory is %CD% >> "%LOGFILE%"

echo Step 3: Checking Python
where python >> "%LOGFILE%" 2>&1
echo Python check completed >> "%LOGFILE%"

echo.
echo ================================
echo Test completed!
echo ================================
echo Check test_startup_log.txt to see if logging worked
echo.
pause
