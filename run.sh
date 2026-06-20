#!/bin/bash

# Exit script if any command fails
set -e

# Make sure we are in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting GridLock Command Center..."

# 1. Start the FastAPI backend
echo "-> Starting backend on port 8000"
source venv/bin/activate
# Run from root directory so Python finds the 'backend' module
uvicorn backend.main:app --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to initialize (models loading takes time)
sleep 2

# 2. Start the React frontend
echo "-> Starting frontend on port 5173"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================="
echo "✅ GridLock is running!"
echo "   Frontend UI: http://localhost:5173"
echo "   Backend API: http://localhost:8000/docs"
echo "========================================="
echo "Press Ctrl+C to stop both servers."

# Trap SIGINT (Ctrl+C) and SIGTERM to kill both background processes
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM EXIT

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
