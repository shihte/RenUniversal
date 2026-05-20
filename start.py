import subprocess
import sys
import os
import signal
import time

def main():
    """
    One-click startup script for CTAR CTAR Posture Monitor.
    Handles starting the server and ensuring it shuts down when this script is closed.
    """
    # Define paths based on the script location
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Check for venv python or fallback to system python
    VENV_PYTHON = os.path.join(ROOT_DIR, "venv", "bin", "python")
    if not os.path.exists(VENV_PYTHON):
        print("Virtualenv not found, trying system 'python3'...")
        PYTHON_EXEC = "python3"
    else:
        PYTHON_EXEC = VENV_PYTHON

    SERVER_SCRIPT = os.path.join(ROOT_DIR, "backend", "stream_server.py")

    if not os.path.exists(SERVER_SCRIPT):
        print(f"Error: Server script not found at {SERVER_SCRIPT}")
        sys.exit(1)

    print(f"{'='*50}")
    print(f"CTAR Launcher")
    print(f"{'='*50}")
    print(f"Root:   {ROOT_DIR}")
    print(f"Python: {PYTHON_EXEC}")
    print(f"Script: {SERVER_SCRIPT}")
    print(f"{'='*50}")
    print("Starting server... Press Ctrl+C to stop.")
    print(f"{'='*50}\n")
    
    # Start process
    # We pass the environment to ensure it runs correctly
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    process = subprocess.Popen(
        [PYTHON_EXEC, SERVER_SCRIPT], 
        cwd=ROOT_DIR,
        env=env
    )

    try:
        # Wait for the process to complete
        # This allows capturing Ctrl+C (KeyboardInterrupt)
        return_code = process.wait()
        sys.exit(return_code)
        
    except KeyboardInterrupt:
        print("\n\nUser interrupted. Stopping server...")
        
        # Send SIGTERM to the child process
        process.terminate()
        
        try:
            # Wait up to 5 seconds for graceful shutdown
            process.wait(timeout=5)
            print("Server stopped cleanly.")
        except subprocess.TimeoutExpired:
            print("Server did not stop, forcing kill...")
            process.kill()
            print("Server killed.")
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if process.poll() is None:
            process.kill()

if __name__ == "__main__":
    main()
