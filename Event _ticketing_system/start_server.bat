@echo off
title Event Ticketing REST API Server - SWC3633/SWC4443
color 0b
echo ======================================================================
echo    EVENT TICKETING AND VENUE BOOKING SYSTEM - RESTful WEB API
echo    Course: SWC3633 / SWC4443 Web API Development (UPTM)
echo ======================================================================
echo.
cd /d "%~dp0"
echo [INFO] Working Directory: %CD%
echo [INFO] Checking if port 8000 is already active...

netstat -ano | findstr :8000 | findstr LISTENING >nul
if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] The Backend Server is ALREADY RUNNING on http://127.0.0.1:8000!
    echo [INFO] You do not need to start it again.
    echo [INFO] Direct Web App: http://127.0.0.1:8000
    echo [INFO] Swagger Docs:   http://127.0.0.1:8000/docs
    echo.
    pause
    exit /b 0
)

echo [INFO] Launching server on http://127.0.0.1:8000 ...
echo [INFO] Direct Web App:   http://127.0.0.1:8000
echo [INFO] Swagger UI Docs:  http://127.0.0.1:8000/docs
echo [INFO] ReDoc Docs:       http://127.0.0.1:8000/redoc
echo.
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
