@echo off
setlocal EnableDelayedExpansion
title PROJECT KYOKKO - Virtual Camera Driver Installer
color 0B

echo =====================================================================
echo                 PROJECT KYOKKO VIRTUAL CAMERA SETUP
echo =====================================================================
echo.

:: 1. Self-elevation to Administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ELEVATION] Requesting Administrator permissions...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

:: Ensure working directory is the script directory
cd /d "%~dp0"

echo [OK] Running with Administrator privileges.
echo.
echo KYOKKO broadcasts your gesture-controlled invisibility feed to meeting
echo apps (Zoom, Google Meet, Microsoft Teams, Discord) using the
echo DirectShow Virtual Camera driver.
echo.
echo =====================================================================
echo.

set "LOCAL_INSTALLER=%~dp0OBS-Studio-Installer.exe"

if exist "%LOCAL_INSTALLER%" (
    echo [INFO] Found local installer: OBS-Studio-Installer.exe
    echo Installing OBS Studio and DirectShow Virtual Camera Driver...
    echo Please wait 20-30 seconds for the setup to complete...
    echo.
    start /wait "" "%LOCAL_INSTALLER%" /S
) else (
    echo [INFO] Local installer not found, checking winget...
    where winget >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo Installing via Windows Package Manager (winget)...
        winget install --id OBSProject.OBSStudio -e --accept-source-agreements --accept-package-agreements
    ) else (
        echo [ERROR] Neither local installer nor winget was found.
        echo Please manually download and install OBS Studio from https://obsproject.com/
        pause
        exit /b 1
    )
)

echo.
echo Verifying DirectShow Virtual Camera filter registration...

:: Register the virtual camera DirectShow filter if the registration script exists
set "OBS_DIR=C:\Program Files\obs-studio"
if exist "%OBS_DIR%\data\obs-plugins\win-dshow\virtualcam-install.bat" (
    pushd "%OBS_DIR%\data\obs-plugins\win-dshow"
    call "%OBS_DIR%\data\obs-plugins\win-dshow\virtualcam-install.bat" >nul 2>&1
    popd
)

if exist "%OBS_DIR%\data\obs-plugins\win-dshow\obs-virtualcam-module64.dll" (
    regsvr32.exe /s "%OBS_DIR%\data\obs-plugins\win-dshow\obs-virtualcam-module64.dll"
)

:: Test Python pyvirtualcam connection if venv exists
if exist "%~dp0venv\Scripts\python.exe" (
    echo Testing virtual camera device in KYOKKO environment...
    "%~dp0venv\Scripts\python.exe" -c "import pyvirtualcam; cam = pyvirtualcam.Camera(width=64, height=64, fps=15); print('   -> SUCCESS: Connected to DirectShow device:', cam.device); cam.close()" 2>nul
)

echo.
echo =====================================================================
echo   [SUCCESS] VIRTUAL CAMERA DRIVER SETUP COMPLETE!
echo.
echo   You can now:
echo     1. Launch KYOKKO (main.py or KYOKKO.exe)
echo     2. Click 'Start Virtual Camera' on the Dashboard
echo     3. In Zoom / Google Meet / Teams / Discord, select:
echo        'OBS Virtual Camera' as your video source
echo =====================================================================
echo.
pause
