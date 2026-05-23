@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM RenUniversal Project Windows Helper Script
REM ============================================================

set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "SERVER_SCRIPT=%PROJECT_ROOT%backend\stream_server.py"
set "REQUIREMENTS=%PROJECT_ROOT%backend\requirements.txt"

if "%1"=="" goto help
if /i "%1"=="help" goto help
if /i "%1"=="setup" goto setup
if /i "%1"=="run" goto run
if /i "%1"=="start" goto run
if /i "%1"=="test" goto test
if /i "%1"=="clean" goto clean
if /i "%1"=="install" goto install

echo Invalid command: %1
goto help

:help
echo.
echo   ======================================================
echo         RenUniversal Agent - Windows Command Helper
echo   ======================================================
echo.
echo   renuniversal.bat setup    - Initialize Python virtual env and dependencies
echo   renuniversal.bat run      - Run the Agent server in foreground
echo   renuniversal.bat start    - Same as run
echo   renuniversal.bat test     - Run architecture validation tests
echo   renuniversal.bat clean    - Clear cache and logs
echo   renuniversal.bat install ^<path^> - Install a .renuniversal plugin
echo.
exit /b 0

:setup
echo === Initialize RenUniversal Agent Environment (Windows) ===
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python is not installed or not in PATH. Please install Python 3.9 - 3.11.
    exit /b 1
)

if not exist "%VENV_DIR%" (
    echo - Creating virtual environment...
    python -m venv "%VENV_DIR%"
) else (
    echo - Virtual environment already exists.
)

echo - Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip

echo - Installing dependencies...
"%VENV_PIP%" install -r "%REQUIREMENTS%"

if not exist "%PROJECT_ROOT%skills" mkdir "%PROJECT_ROOT%skills"
if not exist "%PROJECT_ROOT%events" mkdir "%PROJECT_ROOT%events"

echo.
echo === Setup Complete! Run 'renuniversal.bat run' to start the server ===
exit /b 0

:run
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Please run 'renuniversal.bat setup' first.
    exit /b 1
)
if not exist "%SERVER_SCRIPT%" (
    echo [Error] Server script not found: %SERVER_SCRIPT%
    exit /b 1
)

echo === Starting RenUniversal Agent Server (Press Ctrl+C to stop) ===
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
"%VENV_PYTHON%" "%SERVER_SCRIPT%"
exit /b 0

:test
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Please run 'renuniversal.bat setup' first.
    exit /b 1
)
echo === Running Architecture Validation Tests ===
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
"%VENV_PYTHON%" "%PROJECT_ROOT%backend\test_architecture.py"
exit /b 0

:clean
echo === Cleaning temporary files ===
del /Q "%PROJECT_ROOT%agent.log" 2>nul
del /Q "%PROJECT_ROOT%preferences.json" 2>nul
del /Q "%PROJECT_ROOT%backend\core\.status.tmp" 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo - Clean complete
exit /b 0

:install
if "%2"=="" (
    echo [Error] Please provide the path to the plugin folder.
    echo Usage: renuniversal.bat install ^<path^>
    exit /b 1
)
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Please run 'renuniversal.bat setup' first.
    exit /b 1
)
echo === Installing Plugin from %2 ===
"%VENV_PYTHON%" tools\installer.py "%2"
exit /b 0
