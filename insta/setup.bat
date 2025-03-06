@echo off
setlocal EnableDelayedExpansion


:: Define initial paths
set "SCRIPT_DIR=%~dp0"
set "LOG_FILE=%TEMP%\insta_uploader.log"

:: Clear previous log
echo [%DATE% %TIME%] Starting setup > "%LOG_FILE%"
echo Starting setup...

:: Step 1: Find extracted files in TEMP (for .exe case)
set "TEMP_DIR="
for /d %%i in ("%TEMP%\*") do (
    if exist "%%i\main.py" (
        set "TEMP_DIR=%%i\"
        echo [%DATE% %TIME%] Found temp folder with main.py: !TEMP_DIR! >> "%LOG_FILE%"
        goto :found_temp
    )
)
:found_temp

:: Set paths based on temp folder if found, otherwise use SCRIPT_DIR
if defined TEMP_DIR (
    set "PYTHON_SCRIPT=!TEMP_DIR!main.py"
    set "REQUIREMENTS=!TEMP_DIR!requirements.txt"
) else (
    set "PYTHON_SCRIPT=%SCRIPT_DIR%main.py"
    set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
)

echo [%DATE% %TIME%] PYTHON_SCRIPT: %PYTHON_SCRIPT% >> "%LOG_FILE%""
echo [%DATE% %TIME%] REQUIREMENTS: %REQUIREMENTS% >> "%LOG_FILE%"

:: Step 2: Check if Python is installed
echo Checking for Python...
echo [%DATE% %TIME%] Checking Python... >> "%LOG_FILE%"
python --version >nul 2>&1
if errorlevel 0 (
    echo Python is installed.
    echo [%DATE% %TIME%] Python found. >> "%LOG_FILE%"
) else (
    echo Python not found. Please download from https://www.python.org/downloads/
    echo [%DATE% %TIME%] Python not found. >> "%LOG_FILE%"
    set /p "INSTALL=Do you want to open the Python download page? (y/n): "
    echo [%DATE% %TIME%] User input: !INSTALL! >> "%LOG_FILE%"
    if /i "!INSTALL!"=="y" (
        start https://www.python.org/downloads/
        echo Install Python ^(ensure 'Add to PATH' is checked^) and rerun this script.
        pause
        exit /b 1
    ) else (
        echo Cannot proceed without Python. Exiting...
        pause
        exit /b 1
    )
)

:: Step 3: Check if pip is available
echo Checking for pip...
echo [%DATE% %TIME%] Checking pip... >> "%LOG_FILE%"
python -m pip --version >nul 2>&1
if errorlevel 0 (
    echo pip is installed.
    echo [%DATE% %TIME%] pip found. >> "%LOG_FILE%"
) else (
    echo pip not found. Installing...
    echo [%DATE% %TIME%] Installing pip... >> "%LOG_FILE%"
    python -m ensurepip --upgrade >> "%LOG_FILE" 2>&1
    python -m pip install --upgrade pip >> "%LOG_FILE" 2>&1
    if errorlevel 1 (
        echo Failed to install pip. Check log at %LOG_FILE%
        pause
        exit /b 1
    )
)

:: Step 4: Install required libraries
if exist "%REQUIREMENTS%" (
    echo Installing libraries from requirements.txt...
    echo [%DATE% %TIME%] Installing from requirements.txt... >> "%LOG_FILE%"
    python -m pip install -r "%REQUIREMENTS%" >> "%LOG_FILE" 2>&1
    if errorlevel 1 (
        echo Failed to install libraries. Check log at %LOG_FILE%
        pause
        exit /b 1
    )
) 



:: Step 6: Check if Python script exists
if not exist "%PYTHON_SCRIPT%" (
    echo Error: SpotifyAdBlock.py not found at %PYTHON_SCRIPT%
    echo [%DATE% %TIME%] Error: %PYTHON_SCRIPT% not found! >> "%LOG_FILE%"
    pause
    exit /b 1
)

:: Step 7: Run the Python script in a new window
echo Starting main.py...
echo [%DATE% %TIME%] Running %PYTHON_SCRIPT%... >> "%LOG_FILE%"
start "" python "%PYTHON_SCRIPT%"
echo main.py launched.

echo Done!
echo [%DATE% %TIME%] Setup completed successfully. >> "%LOG_FILE%"
pause
exit /b 0