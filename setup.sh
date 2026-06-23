#!/usr/bin/env bash

set -e

echo "=== Mayhem Command Center Fresh Setup ==="
echo

echo "[1/5] Removing old Python environment..."
if [ -d "venv" ]; then
    chmod -R u+w venv 2>/dev/null || true
    rm -rf venv || true
fi

echo "[2/5] Removing old Node.js dependencies..."
if [ -d "frontend/node_modules" ]; then
    chmod -R u+w frontend/node_modules 2>/dev/null || true
    rm -rf frontend/node_modules || true
fi

rm -f frontend/package-lock.json

echo "[3/5] Creating fresh Python environment..."
python3 -m venv venv

echo "[4/5] Activating environment..."
source venv/bin/activate

echo "[5/5] Installing Python dependencies..."
python -m pip install -r requirements.txt

echo
echo "[6/6] Installing Node.js dependencies..."
cd frontend
npm install
cd ..

echo
echo "✓ Setup complete!"
echo "Run with:"
echo "    ./run.sh"