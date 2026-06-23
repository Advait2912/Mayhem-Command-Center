#!/usr/bin/env bash
set -e

# Ensure we are in the repository root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=== Starting GridLock Command Center ==="

# 1️⃣ Start the FastAPI backend
echo "-> Starting backend on port 8000"
source venv/bin/activate
uvicorn backend.main:app --port 8000 --env-file .env &
BACKEND_PID=$!

# Helper: wait until the backend responds (simple health check)
wait_for_backend() {
    echo -n "⏳ Waiting for backend to become ready"
    while ! curl -s http://localhost:8000/docs > /dev/null; do
        printf "."
        sleep 1
    done
    echo " ✅"
}
wait_for_backend

# 2️⃣ Start the React frontend (Vite)
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

# Graceful shutdown: kill both background processes on exit
cleanup() {
    echo "\nStopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Wait for both processes to finish (will keep script alive until user aborts)
wait $BACKEND_PID $FRONTEND_PID

