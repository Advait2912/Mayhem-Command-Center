@echo off
setlocal

echo === Setting up Mayhem Command Center (Windows) ===
echo.

:: Remove old venv if it exists
if exist venv (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

:: Create virtual environment
echo [1/3] Creating Python virtual environment...
python -m venv venv
if errorlevel 1 goto :error

call venv\Scripts\activate.bat

:: Install Python dependencies
echo [2/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 goto :error

:: Install Node dependencies
echo [3/3] Installing Node.js dependencies...
pushd frontend
call npm install
if errorlevel 1 (
    popd
    goto :error
)
popd

echo.
echo --------------------------------------------------------
echo Setup complete!
echo Run the application using:
echo     run.bat
echo --------------------------------------------------------
pause
exit /b 0

:error
echo.
echo Setup failed.
echo Check the error messages above.
pause
exit /b 1