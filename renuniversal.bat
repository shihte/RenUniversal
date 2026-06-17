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
set "LOG_FILE=%PROJECT_ROOT%agent.log"
set "PID_FILE=%PROJECT_ROOT%.agent.pid"

if "%1"=="" goto help
if /i "%1"=="help"    goto help
if /i "%1"=="doctor"  goto doctor
if /i "%1"=="setup"   goto setup
if /i "%1"=="run"     goto run
if /i "%1"=="start"   goto start
if /i "%1"=="stop"    goto stop
if /i "%1"=="restart" goto restart
if /i "%1"=="status"  goto status
if /i "%1"=="cli"     goto cli
if /i "%1"=="clean"   goto clean
if /i "%1"=="install" goto install
if /i "%1"=="build"   goto build

echo Invalid command: %1
goto help

REM ============================================================
:help
REM ============================================================
echo.
echo   ======================================================
echo         RenUniversal Agent - Windows Command Helper
echo   ======================================================
echo.
echo   .\renuniversal.bat doctor   - Diagnose environment and check dependencies
echo   .\renuniversal.bat setup    - Initialize Python virtual env and dependencies
echo   .\renuniversal.bat run      - Run Agent server in foreground (Ctrl+C to stop)
echo   .\renuniversal.bat start    - Start Agent server in background
echo   .\renuniversal.bat stop     - Stop background Agent server
echo   .\renuniversal.bat restart  - Restart background Agent server
echo   .\renuniversal.bat status   - Show background server status
echo   .\renuniversal.bat cli      - Headless CLI mode (JSON output to stdout)
echo   .\renuniversal.bat clean    - Clear cache and logs
echo   .\renuniversal.bat install ^<path^>  - Install a .renuniversal plugin
echo   .\renuniversal.bat build --name ^<N^> --skills ^<S^> --events ^<E^> --apps ^<A^>
echo.
echo   Extra args can be appended after the command, e.g.:
echo   .\renuniversal.bat run --host 0.0.0.0 --enable-tunnel --auth user:pass
echo.
exit /b 0

REM ============================================================
:doctor
REM ============================================================
echo === RenUniversal 環境診斷 (Doctor) ===
echo.

echo ^> 1. 偵測 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    [X] Python not found in PATH. Please install Python 3.9-3.12.
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo    [OK] %%v
)
echo.

echo ^> 2. 檢查虛擬環境...
if exist "%VENV_PYTHON%" (
    for /f "tokens=*" %%v in ('"%VENV_PYTHON%" --version 2^>^&1') do echo    [OK] venv Python: %%v
) else (
    echo    [X] Virtual environment not found. Run: .\renuniversal.bat setup
)
echo.

echo ^> 3. 檢查關鍵套件...
if exist "%VENV_PYTHON%" (
    for %%p in (flask cv2 mediapipe numpy loguru pydantic) do (
        "%VENV_PYTHON%" -c "import %%p" >nul 2>&1
        if errorlevel 1 (echo    [X] %%p missing) else (echo    [OK] %%p)
    )
)
echo.

echo ^> 4. 檢查 AI 模型...
if exist "%PROJECT_ROOT%backend\models\face_landmarker.task" (
    echo    [OK] face_landmarker.task
) else (
    echo    [X] face_landmarker.task missing - run setup again
)
if exist "%PROJECT_ROOT%backend\models\pose_landmarker_lite.task" (
    echo    [OK] pose_landmarker_lite.task
) else (
    echo    [X] pose_landmarker_lite.task missing - run setup again
)
echo.

echo ^> 5. 檢查伺服器腳本...
if exist "%SERVER_SCRIPT%" (echo    [OK] %SERVER_SCRIPT%) else (echo    [X] Missing: %SERVER_SCRIPT%)
echo.
echo === 診斷完成 ===
exit /b 0

REM ============================================================
:setup
REM ============================================================
echo === Initialize RenUniversal Agent Environment (Windows) ===
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python is not installed or not in PATH. Please install Python 3.9-3.12.
    exit /b 1
)

if not exist "%VENV_DIR%" (
    echo - Creating virtual environment...
    python -m venv "%VENV_DIR%"
) else (
    echo - Virtual environment already exists.
)

echo - Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip --quiet

echo - Installing core dependencies...
for /f "usebackq eol=# tokens=*" %%a in ("%REQUIREMENTS%") do (
    set "pkg=%%a"
    if not "!pkg!"=="" (
        echo    ... Installing: !pkg!
        "%VENV_PIP%" install "!pkg!" --quiet
    )
)
echo    All packages installed successfully!

echo - Downloading MediaPipe AI models...
if not exist "%PROJECT_ROOT%backend\models" mkdir "%PROJECT_ROOT%backend\models"
if not exist "%PROJECT_ROOT%backend\models\face_landmarker.task" (
    echo    Downloading face_landmarker.task...
    curl -sSL "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task" -o "%PROJECT_ROOT%backend\models\face_landmarker.task"
) else (
    echo    face_landmarker.task already present.
)
if not exist "%PROJECT_ROOT%backend\models\pose_landmarker_lite.task" (
    echo    Downloading pose_landmarker_lite.task...
    curl -sSL "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task" -o "%PROJECT_ROOT%backend\models\pose_landmarker_lite.task"
) else (
    echo    pose_landmarker_lite.task already present.
)

if not exist "%PROJECT_ROOT%skills" mkdir "%PROJECT_ROOT%skills"
if not exist "%PROJECT_ROOT%events" mkdir "%PROJECT_ROOT%events"

echo.
echo === Setup Complete! Run '.\renuniversal.bat run' to start the server ===
exit /b 0

REM ============================================================
:run
REM ============================================================
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Run '.\renuniversal.bat setup' first.
    exit /b 1
)
if not exist "%SERVER_SCRIPT%" (
    echo [Error] Server script not found: %SERVER_SCRIPT%
    exit /b 1
)
shift
set "EXTRA_ARGS="
:run_args
if "%~1"=="" goto run_go
set "EXTRA_ARGS=%EXTRA_ARGS% %~1"
shift
goto run_args
:run_go
echo === Starting RenUniversal Agent Server (Ctrl+C to stop) ===
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
"%VENV_PYTHON%" "%SERVER_SCRIPT%"%EXTRA_ARGS%
exit /b 0

REM ============================================================
:start
REM ============================================================
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Run '.\renuniversal.bat setup' first.
    exit /b 1
)
if not exist "%SERVER_SCRIPT%" (
    echo [Error] Server script not found: %SERVER_SCRIPT%
    exit /b 1
)
if exist "%PID_FILE%" (
    set /p EXISTING_PID=<"%PID_FILE%"
    if not "!EXISTING_PID!"=="" (
        tasklist /FI "PID eq !EXISTING_PID!" 2>nul | findstr /I "python" >nul
        if not errorlevel 1 (
            echo Agent is already running (PID !EXISTING_PID!). Use '.\renuniversal.bat restart'.
            exit /b 1
        )
        del /Q "%PID_FILE%" 2>nul
    )
)
shift
set "EXTRA_ARGS="
:start_args
if "%~1"=="" goto start_go
set "EXTRA_ARGS=%EXTRA_ARGS% %~1"
shift
goto start_args
:start_go
echo === Starting RenUniversal Agent Server in background ===
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
powershell -Command "$p = Start-Process -FilePath '%VENV_PYTHON%' -ArgumentList ('\"' + '%SERVER_SCRIPT%' + '\" %EXTRA_ARGS%') -NoNewWindow -RedirectStandardOutput '%LOG_FILE%' -RedirectStandardError '%LOG_FILE%' -PassThru; $p.Id | Out-File -FilePath '%PID_FILE%' -Encoding ASCII -NoNewline" 2>nul
timeout /t 3 /nobreak >nul
if exist "%PID_FILE%" (
    set /p NEW_PID=<"%PID_FILE%"
    echo    [OK] Agent started (PID !NEW_PID!)
    echo    Log:     %LOG_FILE%
    echo    Monitor: http://localhost:8080
) else (
    echo    [X] Failed to start. Check log: %LOG_FILE%
    exit /b 1
)
exit /b 0

REM ============================================================
:stop
REM ============================================================
echo === Stopping RenUniversal Agent Server ===
set "KILLED=0"
if exist "%PID_FILE%" (
    set /p STOP_PID=<"%PID_FILE%"
    if not "!STOP_PID!"=="" (
        taskkill /PID !STOP_PID! /F >nul 2>&1
        if not errorlevel 1 (
            echo    Terminated PID !STOP_PID!
            set "KILLED=1"
        )
    )
    del /Q "%PID_FILE%" 2>nul
)
if "%KILLED%"=="0" (
    echo    No PID file found, searching by process name...
    for /f "skip=2 tokens=2" %%p in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST 2^>nul ^| findstr /I "PID"') do (
        wmic process where "ProcessId='%%p'" get CommandLine 2>nul | findstr /I "stream_server" >nul
        if not errorlevel 1 (
            taskkill /PID %%p /F >nul 2>&1
            echo    Terminated PID %%p
            set "KILLED=1"
        )
    )
)
if "%KILLED%"=="1" (echo [OK] Agent stopped.) else (echo    No running Agent process found.)
exit /b 0

REM ============================================================
:restart
REM ============================================================
call "%~f0" stop
timeout /t 2 /nobreak >nul
shift
set "EXTRA_ARGS="
:restart_args
if "%~1"=="" goto restart_go
set "EXTRA_ARGS=%EXTRA_ARGS% %~1"
shift
goto restart_args
:restart_go
call "%~f0" start%EXTRA_ARGS%
exit /b 0

REM ============================================================
:status
REM ============================================================
echo === RenUniversal Agent Status ===
set "FOUND=0"
if exist "%PID_FILE%" (
    set /p STATUS_PID=<"%PID_FILE%"
    if not "!STATUS_PID!"=="" (
        tasklist /FI "PID eq !STATUS_PID!" 2>nul | findstr /I "python" >nul
        if not errorlevel 1 (
            echo    [Running] PID !STATUS_PID!
            set "FOUND=1"
        ) else (
            echo    [X] PID file exists but process has exited
            del /Q "%PID_FILE%" 2>nul
        )
    )
)
if "%FOUND%"=="0" echo    [Stopped] No Agent process found.
exit /b 0

REM ============================================================
:cli
REM ============================================================
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Run '.\renuniversal.bat setup' first.
    exit /b 1
)
shift
set "EXTRA_ARGS="
:cli_args
if "%~1"=="" goto cli_go
set "EXTRA_ARGS=%EXTRA_ARGS% %~1"
shift
goto cli_args
:cli_go
echo === Starting RenUniversal in CLI mode (headless) ===
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
"%VENV_PYTHON%" "%SERVER_SCRIPT%" --cli%EXTRA_ARGS%
exit /b 0

REM ============================================================
:clean
REM ============================================================
echo === Cleaning temporary files ===
del /Q "%LOG_FILE%" 2>nul
del /Q "%PID_FILE%" 2>nul
del /Q "%PROJECT_ROOT%preferences.json" 2>nul
del /Q "%PROJECT_ROOT%backend\core\.status.tmp" 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo - Clean complete
exit /b 0

REM ============================================================
:install
REM ============================================================
if "%2"=="" (
    echo [Error] Please provide the path to the plugin folder.
    echo Usage: .\renuniversal.bat install ^<path^>
    exit /b 1
)
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Run '.\renuniversal.bat setup' first.
    exit /b 1
)
echo === Installing Plugin from %2 ===
"%VENV_PYTHON%" tools\installer.py "%2"
exit /b 0

REM ============================================================
:build
REM ============================================================
if not exist "%VENV_PYTHON%" (
    echo [Error] Virtual environment not found. Run '.\renuniversal.bat setup' first.
    exit /b 1
)
shift
set "CMD_ARGS="
:build_args
if "%~1"=="" goto build_go
set "CMD_ARGS=%CMD_ARGS% %1"
shift
goto build_args
:build_go
"%VENV_PYTHON%" tools\builder.py%CMD_ARGS%
exit /b 0
