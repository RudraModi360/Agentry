#!/usr/bin/env python
"""
Agentry Full Stack Runner
=========================
A single script to run both the backend (FastAPI) and frontend (static file server)
concurrently. This eliminates the need for multiple terminal windows during development.

Usage:
    python agentry_runner.py                  # Run both backend and frontend
    python agentry_runner.py --backend-only   # Run only backend (port 8000)
    python agentry_runner.py --frontend-only  # Run only frontend (port 3000)
    python agentry_runner.py --help           # Show help

Commands after package install:
    agentry_run                    # Run full stack (backend + frontend)
    agentry_ui / agentry-ui        # Alias for GUI (full stack)
    agentry_tui / agentry-tui      # Run TUI client (CLI interface)
"""

import os
import sys
import signal
import argparse
import asyncio
import threading
import subprocess
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# ============================================================
# Configuration
# ============================================================
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 3000

# Paths
UI_DIR = os.path.join(current_dir, "ui")
BACKEND_DIR = os.path.join(current_dir, "backend")


# ============================================================
# Custom Static File Server with CORS
# ============================================================
class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers for local development."""

    def __init__(self, *args, directory=None, **kwargs):
        self.serve_directory = directory or os.getcwd()
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Custom log format for frontend
        print(f"[Frontend] {args[0]} - {args[1]} {args[2]}")


# ============================================================
# Server Functions
# ============================================================
def kill_process_on_port(port: int) -> bool:
    """Kill any process running on the specified port (Windows)."""
    try:
        # Find the PID using netstat
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
    except Exception as e:
        print(f"[Cleanup] Could not check port {port}: {e}")
    
    return False


def run_frontend_server(host: str = FRONTEND_HOST, port: int = FRONTEND_PORT):
    """Run the static file server for the frontend."""
    
    if not os.path.exists(UI_DIR):
        print(f"[Frontend] Error: UI directory not found at {UI_DIR}")
        return
    
    # Change to UI directory for serving
    os.chdir(UI_DIR)
    
    handler = partial(CORSRequestHandler, directory=UI_DIR)
    
    try:
        httpd = HTTPServer((host, port), handler)
        print(f"[Frontend] Static server running at http://{host}:{port}")
        print(f"[Frontend] Serving files from: {UI_DIR}")
        httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print(f"[Frontend] Port {port} is in use. Attempting cleanup...")
            kill_process_on_port(port)
            time.sleep(1)
            try:
                httpd = HTTPServer((host, port), handler)
                httpd.serve_forever()
            except Exception as e2:
                print(f"[Frontend] Failed to start: {e2}")
        else:
            print(f"[Frontend] Error: {e}")
    except Exception as e:
        print(f"[Frontend] Error: {e}")


def run_backend_server(host: str = BACKEND_HOST, port: int = BACKEND_PORT):
    """Run the FastAPI backend server with uvicorn."""
    
    try:
        import uvicorn
        
        # Set Windows event loop policy
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        print(f"[Backend] Starting FastAPI server at http://{host}:{port}")
        print(f"[Backend] API Docs: http://{host}:{port}/docs")
        
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("[Backend] Error: uvicorn not installed. Run: pip install uvicorn")
    except Exception as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print(f"[Backend] Port {port} is in use. Attempting cleanup...")
            kill_process_on_port(port)
            time.sleep(1)
            run_backend_server(host, port)  # Retry once
        else:
            print(f"[Backend] Error: {e}")


# ============================================================
# Main Functions
# ============================================================
def print_banner():
    """Print the startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     █████╗  ██████╗ ███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗     ║
║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝     ║
║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝ ╚████╔╝      ║
║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝       ║
║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║  ██║   ██║        ║
║    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝        ║
║                                                                      ║
║                    🚀 Full Stack Development Server                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  Frontend:  http://localhost:3000  (Static File Server)             ║
║  Backend:   http://localhost:8000  (FastAPI Server)                 ║
║  API Docs:  http://localhost:8000/docs                               ║
╠══════════════════════════════════════════════════════════════════════╣
║  Press Ctrl+C to stop all servers                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_fullstack(backend_only: bool = False, frontend_only: bool = False):
    """Run the full stack application."""
    
    print_banner()
    
    # Kill any existing processes on the ports
    if not frontend_only:
        kill_process_on_port(BACKEND_PORT)
    if not backend_only:
        kill_process_on_port(FRONTEND_PORT)
    
    time.sleep(0.5)  # Brief pause after cleanup
    
    threads = []
    
    try:
        if not backend_only:
            # Start frontend in a separate thread
            frontend_thread = threading.Thread(
                target=run_frontend_server,
                daemon=True,
                name="Frontend"
            )
            frontend_thread.start()
            threads.append(frontend_thread)
            print("[Startup] Frontend server thread started")
        
        if not frontend_only:
            # Run backend in main thread (for uvicorn reload support)
            print("[Startup] Starting backend server...")
            run_backend_server()
        else:
            # Keep main thread alive for frontend-only mode
            print("[Startup] Frontend-only mode. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping servers...")
    except Exception as e:
        print(f"[Error] {e}")
    finally:
        print("[Shutdown] Cleanup complete. Goodbye!")


def main():
    """Main entry point with argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Agentry Full Stack Runner - Run backend and frontend together",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agentry_runner.py                  # Run both backend and frontend
  python agentry_runner.py --backend-only   # Run only backend (port 8000)
  python agentry_runner.py --frontend-only  # Run only frontend (port 3000)
  
After package install:
  agentry_run                    # Run full stack
  agentry_ui                     # Alias for full stack GUI
  agentry_tui                    # Run TUI client
"""
    )
    
    parser.add_argument(
        '--backend-only', '-b',
        action='store_true',
        help='Run only the backend server (port 8000)'
    )
    
    parser.add_argument(
        '--frontend-only', '-f',
        action='store_true',
        help='Run only the frontend server (port 3000)'
    )
    
    parser.add_argument(
        '--backend-port',
        type=int,
        default=8000,
        help='Backend port (default: 8000)'
    )
    
    parser.add_argument(
        '--frontend-port',
        type=int,
        default=3000,
        help='Frontend port (default: 3000)'
    )
    
    args = parser.parse_args()
    
    # Update ports if specified
    global BACKEND_PORT, FRONTEND_PORT
    BACKEND_PORT = args.backend_port
    FRONTEND_PORT = args.frontend_port
    
    # Handle mutually exclusive options
    if args.backend_only and args.frontend_only:
        print("Error: Cannot specify both --backend-only and --frontend-only")
        sys.exit(1)
    
    run_fullstack(
        backend_only=args.backend_only,
        frontend_only=args.frontend_only
    )


# ============================================================
# Entry Points for Package Commands
# ============================================================
def agentry_run():
    """Entry point for 'agentry_run' command - runs full stack."""
    main()


def agentry_ui():
    """Entry point for 'agentry_ui' command - runs GUI (full stack)."""
    print("[Agentry UI] Starting full stack GUI...")
    run_fullstack()


def agentry_tui():
    """Entry point for 'agentry_tui' command - runs TUI client."""
    # Import and run the CLI TUI
    from agentry.cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
