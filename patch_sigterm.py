import re

with open('backend/stream_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add signal handlers before app.run
signal_code = """
import signal
import sys

def graceful_shutdown(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    if "pipeline" in service_context and service_context["pipeline"]:
        service_context["pipeline"].stop()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

"""

if "graceful_shutdown" not in content:
    content = content.replace("if __name__ == \"__main__\":", signal_code + "if __name__ == \"__main__\":")
    with open('backend/stream_server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched stream_server.py with graceful shutdown")
else:
    print("Already patched")
