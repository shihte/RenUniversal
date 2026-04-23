#!/bin/bash
# CTAR Agent Start Script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_ROOT/.agent.pid"

echo "=== Starting CTAR Agent Server ==="

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
        echo "Agent is already running (PID: $PID)"
        exit 1
    else
        rm "$PID_FILE"
    fi
fi

# Activate venv and run in background
source "$PROJECT_ROOT/venv/bin/activate"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
nohup python3 "$PROJECT_ROOT/backend/stream_server.py" > "$PROJECT_ROOT/agent.log" 2>&1 &
echo $! > "$PID_FILE"

echo "Agent started with PID: $(cat $PID_FILE)"
echo "Logs are being written to: $PROJECT_ROOT/agent.log"
echo "Monitor at: http://localhost:8080"
