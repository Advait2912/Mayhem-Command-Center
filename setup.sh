#!/bin/bash
set -e
echo "Setting up GridLock Command Center (Linux/macOS)..."

echo "1. Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "2. Installing Python dependencies..."
pip install -r requirements.txt

echo "3. Installing Node.js dependencies..."
cd frontend
npm install
cd ..

echo "--------------------------------------------------------"
echo "✅ Setup complete! You can now run the app with ./run.sh"
echo "--------------------------------------------------------"
