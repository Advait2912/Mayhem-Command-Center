@echo off
setlocal enabledelayedexpansion

echo === Starting GridLock Command Center ===

:: 1️⃣ Start the FastAPI backend
echo -^> Starting backend on port 8000
call venv\Scripts\activate.bat
start "" /B uvicorn backend.main:app --port 8000

:: Wait for backend to become responsive (poll /docs)
set "attempts=0"
:waitBackend
if %attempts% GEQ 30 (
    echo Backend did not become ready after %attempts% seconds – proceeding anyway.
    goto :afterWait
)
timeout /t 1 /nobreak >nul
curl -s http://localhost:8000/docs >nul 2>&1
if errorlevel 1 (
    set /A attempts+=1
    echo Waiting for backend... (%attempts%s)
    goto :waitBackend
)
:afterWait

echo -^> Starting frontend on port 5173
cd frontend
start "" /B npm run dev
cd ..

echo.
echo =========================================
echo [OK] GridLock is running!
echo    Frontend UI: http://localhost:5173
echo    Backend API: http://localhost:8000/docs
echo =========================================
echo Press any key to stop both servers.
pause >nul

echo Stopping servers...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
