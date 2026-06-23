@echo off
setlocal EnableDelayedExpansion

echo === Starting Mayhem Command Center ===
echo.

call venv\Scripts\activate.bat

:: Start backend
echo ^> Starting backend on port 8000

if exist .env (
    echo Using .env file
    start "MayhemBackend" /B cmd /c uvicorn backend.main:app --port 8000 --env-file .env
) else (
    echo No .env found, starting without it
    start "MayhemBackend" /B cmd /c uvicorn backend.main:app --port 8000
)

:: Wait for backend
set attempts=0

:waitBackend
curl -sf http://localhost:8000/docs >nul 2>&1

if not errorlevel 1 goto backendReady

set /A attempts+=1

if !attempts! GEQ 30 (
    echo Backend did not become ready after 30 seconds.
    goto startupFailed
)

echo Waiting for backend... (!attempts!s)
timeout /t 1 /nobreak >nul
goto waitBackend

:backendReady
echo Backend ready.

:: Start frontend
echo ^> Starting frontend on port 5173

pushd frontend
start "MayhemFrontend" /B cmd /c npm run dev
popd

echo.
echo =========================================
echo Mayhem is running!
echo.
echo Frontend UI: http://localhost:5173
echo Backend API: http://localhost:8000/docs
echo =========================================
echo.
echo Press any key to stop both servers.
pause >nul

echo.
echo Stopping servers...

taskkill /F /FI "WINDOWTITLE eq MayhemBackend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq MayhemFrontend*" >nul 2>&1

exit /b 0

:startupFailed
echo.
echo Failed to start backend.
pause
exit /b 1