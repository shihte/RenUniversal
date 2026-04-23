# CTAR Project Makefile

.PHONY: setup run test clean help

help:
	@echo "CTAR Agent Commands:"
	@echo "  setup   - Initialize environment and dependencies"
	@echo "  run     - Start the stream server"
	@echo "  test    - Run architecture validation tests"
	@echo "  clean   - Remove temporary files and caches"

setup:
	bash scripts/setup_agent.sh

run:
	@echo "Directly running for debugging..."
	export PYTHONPATH=$$PYTHONPATH:. && ./venv/bin/python3 backend/stream_server.py

start:
	@chmod +x scripts/start.sh
	@./scripts/start.sh

stop:
	@chmod +x scripts/stop.sh
	@./scripts/stop.sh

test:
	export PYTHONPATH=$$PYTHONPATH:. && ./venv/bin/python3 backend/test_architecture.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f preferences.json
	rm -f backend/core/.status.tmp
