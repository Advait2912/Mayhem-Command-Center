@echo off
setlocal enabledelayedexpansion

echo === Setting up GridLock Command Center (Windows) ===

:: 1️⃣ Create Python virtual environment
echo 1️⃣ Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo ✅

:: 2️⃣ Install Python dependencies
echo 2️⃣ Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1
echo ✅

:: 3️⃣ Install Node.js dependencies
echo 3️⃣ Installing Node.js dependencies...
pushd frontend
call npm install >nul 2>&1
popd
echo ✅

echo --------------------------------------------------------
echo ✅ Setup complete! You can now run the app with run.bat
echo --------------------------------------------------------
pause

