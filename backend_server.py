#!/usr/bin/env python
"""
Backend Server (FastAPI)
========================
Dedicated backend server for the Agentry application.
Handles API endpoints, WebSocket connections, and agent interactions.

Usage:
    python backend_server.py                    # Run on default port 8000
    python backend_server.py --port 8000        # Run on custom port
    python backend_server.py --host 0.0.0.0     # Bind to all interfaces
"""

import os
import sys
import asyncio
import argparse

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# ============================================================
# Configuration
# ============================================================
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def run_backend_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reload: bool = True):
    """Run the FastAPI backend server with uvicorn."""
    
    try:
        import uvicorn
        
        # Set Windows event loop policy
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        print(f"""
========================================
  AGENTRY BACKEND SERVER
========================================
  Server:   http://{host}:{port}
  API Docs: http://{host}:{port}/docs
  Status:   Starting...
========================================
        """)
        
        reload_dirs = [
            os.path.join(current_dir, "backend"),
            os.path.join(current_dir, "logicore")
        ]
        
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=reload_dirs if reload else None,
            log_level="info"
        )
    except ImportError:
        print("[Backend] Error: uvicorn not installed. Run: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"[Backend] Error: {e}")
        sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Agentry Backend Server - FastAPI with WebSocket support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend_server.py                    # Run with defaults
  python backend_server.py --port 8080        # Custom port
  python backend_server.py --host 0.0.0.0     # Bind to all interfaces
  python backend_server.py --no-reload        # Disable auto-reload
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
    
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='Disable auto-reload (useful for production)'
    )
    
    args = parser.parse_args()
    
    run_backend_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )


if __name__ == "__main__":
    main()
