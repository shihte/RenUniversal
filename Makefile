# CTAR Project Makefile
.PHONY: help check-python setup run start stop test clean

PROJECT_ROOT := $(shell pwd)
PID_FILE := $(PROJECT_ROOT)/.agent.pid
LOG_FILE := $(PROJECT_ROOT)/agent.log

# Find compatible python version (Python 3.8 to 3.11)
PYTHON_CANDIDATES := python3.10 python3.11 python3.9 python3.8 python3
COMPATIBLE_PYTHON := $(shell for py in $(PYTHON_CANDIDATES); do \
	if which $$py >/dev/null 2>&1; then \
		if $$py -c 'import sys; v = sys.version_info; exit(0 if (3, 8) <= (v.major, v.minor) <= (3, 11) else 1)' >/dev/null 2>&1; then \
			echo $$py; \
			break; \
		fi; \
	fi; \
done)

# Virtual environment path
VENV_DIR := $(PROJECT_ROOT)/.venv
VENV_PYTHON := $(VENV_DIR)/bin/python

help:
	@echo "CTAR Agent Commands:"
	@echo "  setup   - Validate Python version and initialize environment/dependencies"
	@echo "  run     - Run stream server in foreground"
	@echo "  start   - Run stream server in background (saved to .agent.pid)"
	@echo "  stop    - Stop background stream server process"
	@echo "  test    - Run architecture validation tests"
	@echo "  clean   - Remove temporary files, logs, and python caches"

check-python:
	@if [ -z "$(COMPATIBLE_PYTHON)" ]; then \
		echo "Error: No compatible Python (3.8 - 3.11) found on your system."; \
		if which python3 >/dev/null 2>&1; then \
			echo "Found default python3 version: $$(python3 --version)"; \
		fi; \
		echo "Please install Python 3.8, 3.9, 3.10, or 3.11 to run CTAR."; \
		exit 1; \
	fi
	@echo "Compatible python found: $(COMPATIBLE_PYTHON) ($$($(COMPATIBLE_PYTHON) --version))"

setup: check-python
	@echo "=== Initializing CTAR Agent Environment ==="
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment at $(VENV_DIR)..."; \
		$(COMPATIBLE_PYTHON) -m venv $(VENV_DIR); \
	fi
	@echo "Upgrading pip and installing dependencies..."
	@$(VENV_PYTHON) -m pip install --upgrade pip
	@$(VENV_PYTHON) -m pip install -r backend/requirements.txt
	@mkdir -p skills
	@mkdir -p backend/services
	@echo "=== Setup Complete! ==="

run:
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "Error: Virtual environment not found. Please run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Starting CTAR Stream Server in foreground..."
	@export PYTHONPATH=$(PROJECT_ROOT):$$PYTHONPATH && $(VENV_PYTHON) backend/stream_server.py

start:
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "Error: Virtual environment not found. Please run 'make setup' first."; \
		exit 1; \
	fi
	@if [ -f "$(PID_FILE)" ]; then \
		PID=$$((cat "$(PID_FILE)") 2>/dev/null || true); \
		if [ -n "$$PID" ] && ps -p "$$PID" > /dev/null 2>&1; then \
			echo "Agent is already running (PID: $$PID)"; \
			exit 1; \
		else \
			rm -f "$(PID_FILE)"; \
		fi; \
	fi
	@echo "=== Starting CTAR Agent Server ==="
	@export PYTHONPATH=$(PROJECT_ROOT):$$PYTHONPATH && nohup $(VENV_PYTHON) backend/stream_server.py > "$(LOG_FILE)" 2>&1 & echo $$! > "$(PID_FILE)"
	@sleep 2
	@PID=$$(cat "$(PID_FILE)" 2>/dev/null || true); \
	if [ -n "$$PID" ] && ps -p "$$PID" > /dev/null 2>&1; then \
		echo "Agent started with PID: $$PID"; \
		echo "Logs are being written to: $(LOG_FILE)"; \
		echo "Monitor at: http://localhost:8080"; \
	else \
		echo "Failed to start agent. Check $(LOG_FILE) for details."; \
		exit 1; \
	fi

stop:
	@echo "=== Stopping CTAR Agent Server ==="
	@PID=""; \
	if [ -f "$(PID_FILE)" ]; then \
		PID=$$(cat "$(PID_FILE)"); \
	else \
		PID=$$(pgrep -f "backend/stream_server.py" | head -n 1); \
	fi; \
	if [ -z "$$PID" ]; then \
		echo "No running agent process found."; \
	else \
		echo "Terminating process $$PID..."; \
		kill "$$PID" 2>/dev/null || true; \
		COUNT=0; \
		while ps -p "$$PID" > /dev/null 2>&1 && [ $$COUNT -lt 5 ]; do \
			sleep 1; \
			COUNT=$$((COUNT+1)); \
		done; \
		if ps -p "$$PID" > /dev/null 2>&1; then \
			echo "Force killing process $$PID..."; \
			kill -9 "$$PID" 2>/dev/null || true; \
		fi; \
		rm -f "$(PID_FILE)"; \
		echo "Agent stopped successfully."; \
	fi

test:
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "Error: Virtual environment not found. Please run 'make setup' first."; \
		exit 1; \
	fi
	@export PYTHONPATH=$(PROJECT_ROOT):$$PYTHONPATH && $(VENV_PYTHON) backend/test_architecture.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f preferences.json
	rm -f backend/core/.status.tmp
	rm -f $(PID_FILE)
	rm -f $(LOG_FILE)
	@echo "Clean completed."
