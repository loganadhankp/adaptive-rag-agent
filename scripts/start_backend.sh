#!/usr/bin/env bash
# Start backend in background and direct logs
mkdir -p logs
export TEST_MODE=${TEST_MODE:-true}
nohup .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
echo $! > logs/backend.pid
