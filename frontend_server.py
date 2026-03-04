#!/usr/bin/env python
"""
Frontend Server (Static File Server)
====================================
Dedicated frontend server for the Agentry application.
Serves static files (HTML, CSS, JS, assets) with CORS support.

Usage:
    python frontend_server.py                   # Run on default port 3000
    python frontend_server.py --port 3000       # Run on custom port
    python frontend_server.py --host 0.0.0.0    # Bind to all interfaces
"""

import os
import sys
import time
import subprocess
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial


# ============================================================
# Configuration
# ============================================================
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3000

current_dir = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(current_dir, "ui")


# ============================================================
# Custom Static File Server with CORS
# ============================================================
class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers for local development."""

    def __init__(self, *args, directory=None, **kwargs):
        self.serve_directory = directory or os.getcwd()
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        """Handle GET requests - redirect API/WebSocket routes to backend."""
        # Check if this is a backend route that shouldn't be served by frontend
        path = self.path.split('?')[0]
        if path.startswith('/ws/') or path.startswith('/api/'):
            # These routes should go to the backend (port 8000)
            self.send_error(
                502, 
                f"This route ({path}) should be handled by the backend server on port 8000. "
                "Make sure the backend is running."
            )
            return
        
        # Serve static files normally
        super().do_GET()

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        # Smart caching for development - cache static assets briefly
        path = getattr(self, 'path', '').split('?')[0]
        if path.endswith(('.css', '.js', '.woff2', '.woff', '.ttf', '.png', '.jpg', '.svg', '.ico')):
            self.send_header('Cache-Control', 'public, max-age=5')
        else:
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Custom log format - handle variable number of args safely
        if len(args) >= 3:
            print(f"[Frontend] {args[0]} - {args[1]} {args[2]}")
        elif len(args) >= 2:
            print(f"[Frontend] {args[0]} - {args[1]}")
        elif len(args) >= 1:
            print(f"[Frontend] {args[0]}")
        else:
            print(f"[Frontend] {format}")


def kill_process_on_port(port: int) -> bool:
    """Kill any process running on the specified port (Windows/Unix)."""
    try:
        if sys.platform == 'win32':
            # Windows: use netstat + taskkill
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                pids_killed = set()
                
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit() and pid not in pids_killed:
                            try:
                                subprocess.run(
                                    f'taskkill /F /PID {pid}',
                                    shell=True,
                                    capture_output=True
                                )
                                pids_killed.add(pid)
                                print(f"[Cleanup] Killed process {pid} on port {port}")
                            except Exception:
                                pass
                
                return len(pids_killed) > 0
        else:
            # Unix-like: use lsof + kill
            result = subprocess.run(
                f'lsof -ti:{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.isdigit():
                        try:
                            subprocess.run(f'kill -9 {pid}', shell=True, capture_output=True)
                            print(f"[Cleanup] Killed process {pid} on port {port}")
                        except Exception:
                            pass
                return True
    except Exception as e:
        print(f"[Cleanup] Could not check port {port}: {e}")
    
    return False


def run_frontend_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Run the static file server for the frontend."""
    
    if not os.path.exists(UI_DIR):
        print(f"[Frontend] Error: UI directory not found at {UI_DIR}")
        sys.exit(1)
    
    # Change to UI directory for serving
    os.chdir(UI_DIR)
    
    handler = partial(CORSRequestHandler, directory=UI_DIR)
    
    print(f"""
========================================
  AGENTRY FRONTEND SERVER
========================================
  Server:  http://{host}:{port}
  Serving: {UI_DIR}
  Status:  Starting...
========================================
    """)
    
    try:
        httpd = HTTPServer((host, port), handler)
        print(f"[Frontend] Static server running at http://{host}:{port}")
        print(f"[Frontend] Serving files from: {UI_DIR}")
        print(f"[Frontend] Press Ctrl+C to stop")
        httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print(f"[Frontend] Port {port} is in use. Attempting cleanup...")
            kill_process_on_port(port)
            time.sleep(1)
            try:
                httpd = HTTPServer((host, port), handler)
                print(f"[Frontend] Static server running at http://{host}:{port}")
                httpd.serve_forever()
            except Exception as e2:
                print(f"[Frontend] Failed to start: {e2}")
                sys.exit(1)
        else:
            print(f"[Frontend] Error: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[Frontend] Shutting down...")
    except Exception as e:
        print(f"[Frontend] Error: {e}")
        sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Agentry Frontend Server - Static file server with CORS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python frontend_server.py                    # Run with defaults
  python frontend_server.py --port 3001        # Custom port
  python frontend_server.py --host 0.0.0.0     # Bind to all interfaces
"""
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=DEFAULT_HOST,
        help=f'Host to bind to (default: {DEFAULT_HOST})'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=DEFAULT_PORT,
        help=f'Port to bind to (default: {DEFAULT_PORT})'
    )
    
    args = parser.parse_args()
    
    run_frontend_server(
        host=args.host,
        port=args.port
    )


if __name__ == "__main__":
    main()
