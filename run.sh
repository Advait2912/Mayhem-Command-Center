#!/bin/bash

echo "Starting backend..."
cd backend
source venv/bin/activate
uvicorn main:app --reload &
BACKEND_PID=$!

echo "Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

wait