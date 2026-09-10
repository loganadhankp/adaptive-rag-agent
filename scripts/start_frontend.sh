#!/usr/bin/env bash
# Start streamlit frontend in background and direct logs
mkdir -p logs
export TEST_MODE=${TEST_MODE:-true}
nohup .venv/bin/streamlit run frontend/app.py --server.port ${STREAMLIT_SERVER_PORT:-8501} > logs/frontend.log 2>&1 &
echo $! > logs/frontend.pid
