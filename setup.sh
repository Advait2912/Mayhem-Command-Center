#!/bin/bash

set -e

echo "===================================="
echo "Setting up GridLock Backend"
echo "===================================="

cd backend

python3 -m venv venv

source venv/bin/activate

pip install --upgrade pip

pip install -r requirements.txt

deactivate

cd ..

echo ""
echo "===================================="
echo "Setting up GridLock Frontend"
echo "===================================="

cd frontend

npm install

cd ..

echo ""
echo "===================================="
echo "Setup Complete"
echo "===================================="
echo ""
echo "Run the project using:"
echo "./run.sh"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "Swagger:  http://localhost:8000/docs"