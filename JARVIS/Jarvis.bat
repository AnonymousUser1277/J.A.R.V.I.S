@echo off
cd /d "%~dp0"

:: --- STEP 1: Check for 'python' command ---
:: Run a tiny Python script to return exit code 0 if version >= 3.8, otherwise 1
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >NUL 2>&1

:: If exit code is 0, we are good.
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :Launch
)

:: If exit code is 1, found python but version is old.
if %errorlevel% equ 1 (
    goto :VersionTooLow
)

:: --- STEP 2: Check for 'python3' command (Fallback) ---
:: Some systems specifically use 'python3'
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >NUL 2>&1

if %errorlevel% equ 0 (
    set "PY_CMD=python3"
    goto :Launch
)
if %errorlevel% equ 1 (
    goto :VersionTooLow
)

:: --- STEP 3: Python not found at all ---
goto :PythonNotFound

:: ---------------- ERROR HANDLERS ----------------
:VersionTooLow
cls
color 4F
echo.
echo ==============================================================
echo  [CRITICAL ERROR] INSTALLED PYTHON VERSION IS TOO OLD
echo ==============================================================
echo.
echo  This program requires Python 3.8 or higher.
echo.
echo  Opening download page in 3 seconds...
timeout /t 3 >nul
start https://www.python.org/downloads/
echo Press any key to exit...And after installing python, run Jarvis.bat again.
pause
exit

:PythonNotFound
cls
color 4F
echo.
echo ==============================================================
echo  [CRITICAL ERROR] PYTHON NOT FOUND
echo ==============================================================
echo.
echo  Could not find 'python' or 'python3' in your system PATH.
echo  Please install Python 3.8+ and checks "Add to PATH" during install.
echo.
echo  Opening download page in 3 seconds...
timeout /t 3 >nul
start https://www.python.org/downloads/
echo Press any key to exit...And after installing python, run Jarvis.bat again.
pause
exit

:: ---------------- SUCCESS LAUNCH ----------------
:Launch
echo [INFO] Python 3.8+ detected.
echo [INFO] Launching Jarvis as Administrator...

:: We use %PY_CMD% to ensure we use the same python executable we just verified
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "Start-Process %PY_CMD% -ArgumentList 'main.py' -Verb RunAs"
