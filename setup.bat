@echo off

echo ====================================
echo Setting up GridLock Backend
echo ====================================

cd backend

python -m venv venv

call venv\Scripts\activate

pip install -r requirements.txt

cd ..

echo ====================================
echo Setting up GridLock Frontend
echo ====================================

cd frontend

npm install

cd ..

echo ====================================
echo Setup Complete
echo ====================================

pause