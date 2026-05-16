@echo off
setlocal enabledelayedexpansion
title VAULT_OPUS INSTALLER (Windows – Admin Required)
set "LOG_FILE=%TEMP%\vault_opus_install.log"

:: --- Colour control (respect NO_COLOR) ---
if "%NO_COLOR%"=="" (
    set "RED=[31m"
    set "GREEN=[32m"
    set "BLUE=[34m"
    set "CYAN=[36m"
    set "YELLOW=[33m"
    set "BOLD=[1m"
    set "NC=[0m"
) else (
    set "RED=" & set "GREEN=" & set "BLUE=" & set "CYAN=" & set "YELLOW=" & set "BOLD=" & set "NC="
)

:: --- Logging function ---
set "LOG_ENABLED=1"
call :log "=== VAULT_OPUS INSTALL STARTED ==="

:: --- ADMIN CHECK & ELEVATION ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[WARNING]%NC% This installer requires Administrator privileges.
    echo %CYAN%[INFO]%NC% Attempting to relaunch as administrator...
    :: Create a temporary VBS script to elevate
    set "vbs=%temp%\getadmin.vbs"
    > "%vbs%" echo Set UAC = CreateObject^("Shell.Application"^)
    >>"%vbs%" echo UAC.ShellExecute "%~s0", "", "", "runas", 1
    cscript //nologo "%vbs%"
    del "%vbs%" 2>nul
    exit /b
)

:: If we get here, we are admin
echo %GREEN%[OK]%NC% Running with Administrator privileges.

:: --- Parse command line arguments ---
set "SKIP_NODE=0"
set "SKIP_FRONTEND=0"
set "AUTO_INSTALL=0"
set "UNINSTALL=0"
set "HELP=0"
:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--skip-node" set "SKIP_NODE=1"
if /i "%~1"=="--skip-frontend" set "SKIP_FRONTEND=1"
if /i "%~1"=="--auto-install" set "AUTO_INSTALL=1"
if /i "%~1"=="--uninstall" set "UNINSTALL=1"
if /i "%~1"=="--help" set "HELP=1"
shift
goto :parse_args
:args_done

if "%HELP%"=="1" (
    echo Usage: %~nx0 [options]
    echo Options:
    echo   --skip-node        Skip Node.js installation even if missing
    echo   --skip-frontend    Skip npm install for frontend directories
    echo   --auto-install     Automatically answer Yes to all prompts
    echo   --uninstall        Remove venv, node_modules, and config backup
    echo   --help             Show this help
    echo.
    echo Example: %~nx0 --auto-install --skip-frontend
    pause
    exit /b 0
)

if "%UNINSTALL%"=="1" goto :uninstall

:: --- Banner ---
cls
echo.
echo %CYAN%%BOLD% __      __    _    _   _ _   _______    ____   _____  _    _  _____ %NC%
echo %CYAN%%BOLD% \ \    / /   / \  | | | | | |__   __|  / __ \ |  __ \| |  | |/ ____|%NC%
echo %CYAN%%BOLD%  \ \  / /   / _ \ | | | | |    | |    | |  | || |__) | |  | | (___  %NC%
echo %CYAN%%BOLD%   \ \/ /   / ___ \| | | | |    | |    | |  | ||  ___/| |  | |\___ \ %NC%
echo %CYAN%%BOLD%    \  /   / /   \ \ |_| | |____| |    | |__| || |    | |__| |____) |%NC%
echo %CYAN%%BOLD%     \/   /_/     \_\____|______|_|     \____/ |_|     \____/|_____/ %NC%
echo.
echo %BLUE%%BOLD%>>> THE INFINITY CLOUD STORAGE PROJECT <<< %NC%
echo.

:: --- 1. Python bootstrap ---
call :log "Checking Python"
call :check_python
if %errorlevel% neq 0 exit /b 1

:: --- 2. Node.js bootstrap ---
if "%SKIP_NODE%"=="1" (
    echo %YELLOW%[SKIP]%NC% Node.js installation skipped by user.
    set "HAS_NODE=0"
) else (
    call :check_node
)

:: --- 3. Virtual environment and Python deps ---
call :setup_venv
if %errorlevel% neq 0 exit /b 1

:: --- 4. Config setup ---
call :configure_discord

:: --- 5. Frontend npm (optional) ---
if "%SKIP_FRONTEND%"=="1" (
    echo %YELLOW%[SKIP]%NC% Frontend npm install skipped by user.
) else if "%HAS_NODE%"=="0" (
    echo %YELLOW%[WARNING]%NC% Node.js not available, skipping frontend setup.
) else (
    call :setup_frontend
)

echo.
echo %GREEN%%BOLD%VAULT_OPUS Installation Complete!%NC%
echo Log file: %LOG_FILE%
echo.
echo Run the app with:
echo   - CLI: venv\Scripts\python.exe src\VAULT_OPUS.py
echo   - GUI BACKEND: venv\Scripts\python.exe src\WI\server.py
echo   - Desktop GUI: cd src\WI\client ^&^& npm run dev
echo   - Android GUI: cd src\WI\mobile ^&^& npm run android
pause
goto :eof

:: ------------------------------------------------------------
:: Functions (same as upgraded version – omitted for brevity)
:: ------------------------------------------------------------

:log
echo %date% %time% - %* >> "%LOG_FILE%"
if not "%*"=="" echo %*
goto :eof

:check_python
... (same as previous upgraded version) ...
goto :eof

:check_node
... (same as previous upgraded version) ...
goto :eof

:setup_venv
... (same as previous upgraded version) ...
goto :eof

:configure_discord
... (same as previous upgraded version) ...
goto :eof

:setup_frontend
... (same as previous upgraded version) ...
goto :eof

:refresh_env
... (same as previous upgraded version) ...
goto :eof

:uninstall
echo %BOLD%Uninstalling VAULT_OPUS...%NC%
if exist "venv" (
    echo Removing virtual environment...
    rmdir /s /q venv
)
if exist "src\WI\client\node_modules" (
    echo Removing client node_modules...
    rmdir /s /q "src\WI\client\node_modules"
)
if exist "src\WI\mobile\node_modules" (
    echo Removing mobile node_modules...
    rmdir /s /q "src\WI\mobile\node_modules"
)
if exist "src\config.json.bak.*" (
    echo Removing config backups...
    del /q src\config.json.bak.*
)
echo %GREEN%Uninstall complete.%NC%
pause
exit /b 0