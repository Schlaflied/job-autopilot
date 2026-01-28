@echo off
echo ========================================================
echo   Starting Chrome for Job Autopilot (Debug Port 9222)
echo ========================================================
echo.
echo [IMPORTANT]
echo If you have other Chrome windows open, this will open a 
echo SEPARATE Chrome instance with a new profile.
echo.
echo This is required for the automation to control the browser.
echo.

:: Try standard locations or PATH
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else (
    set CHROME_PATH=chrome.exe
)

:: Launch with separate profile to avoid conflicts
start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir="C:\temp\job_autopilot_chrome_profile" --no-first-run --no-default-browser-check

echo Chrome launched! 
echo 1. Log in to LinkedIn in this new window.
echo 2. Return to the Coffee Chat Center.
echo 3. Click "Test Connection".
echo.
pause
