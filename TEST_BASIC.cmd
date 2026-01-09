@echo off
echo.
echo ================================
echo BASIC TEST
echo ================================
echo.
echo If you can see this, CMD scripts work!
echo.
echo Current directory: %CD%
echo.
echo Script location: %~dp0
echo.
echo Creating test.txt file...
echo This is a test > test.txt
echo.
if exist test.txt (
    echo SUCCESS: test.txt was created
    del test.txt
    echo test.txt cleaned up
) else (
    echo FAILED: Could not create test.txt
    echo You may have permission issues
)
echo.
echo ================================
echo Test Complete
echo ================================
echo.
pause
