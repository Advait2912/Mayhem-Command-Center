#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=== Starting Mayhem Command Center ==="

source venv/bin/activate

echo "-> Starting backend on port 8000"

if [ -f ".env" ]; then
    echo "Using .env file"
    uvicorn backend.main:app --port 8000 --env-file .env &
else
    echo "No .env found, starting without it"
    uvicorn backend.main:app --port 8000 &
fi

BACKEND_PID=$!

echo -n "Waiting for backend"

while ! curl -sf http://localhost:8000/docs >/dev/null 2>&1; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo
        echo "Backend failed to start."
        exit 1
    fi

    printf "."
    sleep 1
done

echo " ✓"

echo "-> Starting frontend on port 5173"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo
echo "========================================="
echo "Mayhem is running!"
echo "Frontend: http://localhost:5173"
echo "Backend : http://localhost:8000/docs"
echo "========================================="

cleanup() {
    printf "\nStopping servers...\n"

    kill -TERM "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup SIGINT SIGTERM EXIT

wait "$BACKEND_PID" "$FRONTEND_PID"