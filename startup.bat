@echo off
REM ============================================================
REM  AI Product CRM - Startup
REM  Launches the Streamlit UI and/or FastAPI REST API.
REM  Run from the project root after running setup.bat.
REM ============================================================

setlocal

cd /d "%~dp0"

REM ------------------------------------------------------------------
REM 1. Check Python virtual environment
REM ------------------------------------------------------------------
echo.
echo ============================================================
echo   AI Product CRM - Startup
echo ============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first in this directory.
    echo.
    pause
    exit /b 1
)

echo [OK] Python virtual environment found.

REM ------------------------------------------------------------------
REM 2. Check .env configuration
REM ------------------------------------------------------------------
if not exist ".env" (
    echo [WARNING] .env not found.
    echo           Copying .env.example to .env ...
    copy ".env.example" ".env" >nul
    echo           IMPORTANT: Open .env and set your provider/model settings.
    echo.
) else (
    echo [OK] .env configuration found.
)

REM ------------------------------------------------------------------
REM 3. Choose what to start
REM ------------------------------------------------------------------
echo.
echo What would you like to start?
echo.
echo   [1] Streamlit UI only  (http://localhost:8501)
echo   [2] FastAPI API only   (http://localhost:8000)
echo   [3] BOTH UI + API
echo   [4] Exit
echo.
set /p CHOICE="Enter your choice (1/2/3/4): "

if "%CHOICE%"=="4" (
    echo.
    echo Exiting. Goodbye!
    exit /b 0
)

REM ------------------------------------------------------------------
REM 4. Warn if Ollama is required but not detected (local deployments)
REM ------------------------------------------------------------------
findstr /b "ROUTER_MODEL=" ".env" | findstr /i "ollama/" >nul
if not errorlevel 1 (
    powershell -command "try { $r = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 3 -UseBasicParsing; if ($r.StatusCode -ne 200) { exit 1 } } catch { exit 1 }"
    if errorlevel 1 (
        echo.
        echo [WARNING] Your .env uses ollama models but Ollama does not appear
        echo           to be running. Start it in another terminal with:
        echo.
        echo             ollama serve
        echo.
        echo           Or set cloud providers (groq/openai/...) in .env.
        echo.
    ) else (
        echo [OK] Ollama is running.
    )
)

REM ------------------------------------------------------------------
REM 5. Launch selection
REM ------------------------------------------------------------------
echo.
echo Starting: insist on the selected service(s). Press Ctrl+C to stop.
echo.

if "%CHOICE%"=="1" (
    echo   * Streamlit UI: http://localhost:8501
    echo.
    start "CRM - Streamlit UI" cmd /k "venv\Scripts\python.exe -m streamlit run app\chat.py"
) else if "%CHOICE%"=="2" (
    echo   * FastAPI API : http://localhost:8000  (docs at /docs)
    echo.
    start "CRM - FastAPI API" cmd /k "venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
) else if "%CHOICE%"=="3" (
    echo   * Streamlit UI: http://localhost:8501
    echo   * FastAPI API : http://localhost:8000  (docs at /docs)
    echo.
    start "CRM - Streamlit UI" cmd /k "venv\Scripts\python.exe -m streamlit run app\chat.py"
    start "CRM - FastAPI API" cmd /k "venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
) else (
    echo [ERROR] Invalid choice. Please run again and pick 1, 2, 3, or 4.
    echo.
    pause
    exit /b 1
)

echo.
echo Done launching. Each service opens in its own window.
echo Close those windows (Ctrl+C) to stop the service.
echo.
pause
endlocal
