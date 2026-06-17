@echo off

echo Starting Backend...

start cmd /k "cd backend && call venv\Scripts\activate && uvicorn main:app --reload"

timeout /t 3 > nul

echo Starting Frontend...

start cmd /k "cd frontend && npm run dev"

echo.
echo GridLock Command Center Starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo Swagger: http://localhost:8000/docs
echo.

pause