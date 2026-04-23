#!/bin/bash
# CTAR Agent Setup Script
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Initializing CTAR Agent Environment ==="

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies from backend/requirements.txt..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Initialize skill directories if missing
mkdir -p skills/video_capture
mkdir -p skills/posture_reviewer
mkdir -p skills/calibration_wizard

echo "=== Setup Complete! ==="
echo "To activate the environment, run: source venv/bin/activate"
