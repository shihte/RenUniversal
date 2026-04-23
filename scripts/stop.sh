#!/bin/bash
# CTAR Agent Stop Script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_ROOT/.agent.pid"

echo "=== Stopping CTAR Agent Server ==="

if [ ! -f "$PID_FILE" ]; then
    echo "No PID file found. Is the agent running?"
    # Fallback to pgrep
    PID=$(pgrep -f "backend/stream_server.py")
    if [ -n "$PID" ]; then
        echo "Found matching process via pgrep: $PID"
    else
        echo "Could not find any running agent process."
        exit 1
    fi
else
    PID=$(cat "$PID_FILE")
fi

echo "Terminating process $PID..."
kill "$PID"

# Wait for process to stop
MAX_RETRIES=5
COUNT=0
while ps -p "$PID" > /dev/null && [ $COUNT -lt $MAX_RETRIES ]; do
    sleep 1
    ((COUNT++))
done

if ps -p "$PID" > /dev/null; then
    echo "Force killing process $PID..."
    kill -9 "$PID"
fi

rm -f "$PID_FILE"
echo "Agent stopped successfully."
