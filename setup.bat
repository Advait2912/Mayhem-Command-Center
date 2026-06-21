@echo off
echo Setting up GridLock Command Center (Windows)...

echo 1. Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo 2. Installing Python dependencies...
pip install -r requirements.txt

echo 3. Installing Node.js dependencies...
cd frontend
call npm install
cd ..

echo --------------------------------------------------------
echo [OK] Setup complete! You can now run the app with run.bat
echo --------------------------------------------------------
pause
