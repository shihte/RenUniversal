#!/usr/bin/env python3
"""
Simple HTTP server for serving the Game.html file on port 3000.
Usage: python game_server.py
"""

import http.server
import socketserver
import os
import sys

PORT = 3001
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        # Redirect root to Game.html
        if self.path == '/' or self.path == '':
            self.send_response(302)
            self.send_header('Location', '/Game.html')
            self.end_headers()
            return
        return super().do_GET()
    
    def end_headers(self):
        # Enable CORS for API requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    # Check if Game.html exists
    game_file = os.path.join(DIRECTORY, "Game.html")
    if not os.path.exists(game_file):
        print(f"Error: Game.html not found in {DIRECTORY}")
        sys.exit(1)
    
    print(f"\n{'='*50}")
    print("CTAR Game Server")
    print(f"{'='*50}")
    print(f"Serving Game.html at: http://localhost:{PORT}/Game.html")
    print(f"Directory: {DIRECTORY}")
    print(f"{'='*50}\n")
    print("Make sure the posture detection backend is running on port 5001!")
    print("Press Ctrl+C to stop.\n")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
