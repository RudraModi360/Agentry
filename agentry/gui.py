"""
Entry point for the Agentry GUI (Web Interface).
Launches the FastAPI server with uvicorn.
"""
import os
import sys

# Add parent directory to sys.path to allow running as a script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def main():
    """Launch the Agentry web GUI."""
    import uvicorn
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import agentry
        
        # Check if it's a namespace package (no __file__) and reload if needed
        if not hasattr(agentry, '__file__') or agentry.__file__ is None:
            import importlib
            # Ensure our local path is definitely in sys.path and AT THE FRONT
            current_dir_abs = os.path.dirname(os.path.abspath(__file__))
            parent_dir_abs = os.path.dirname(current_dir_abs)
            
            # Remove from sys.path if present elsewhere to avoid conflicts, then insert at 0
            if parent_dir_abs in sys.path:
                sys.path.remove(parent_dir_abs)
            sys.path.insert(0, parent_dir_abs)
            
            # Force reload
            importlib.reload(agentry)

        import agentry.ui
    except Exception as e:
        print(f"DEBUG IMPORT ERROR: {e}")


    # Ensure agentry.ui.server is importable
    try:
        from agentry.ui.server import app
    except ImportError:
        print("Import failed, attempting to add package root explicitly")
        # Only needed if something is very broken with the environment
        pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if pkg_root not in sys.path:
            sys.path.insert(0, pkg_root)
        from agentry.ui.server import app

    # Get the directory where this module is located
    ui_dir = os.path.join(os.path.dirname(__file__), "ui")
    
    # Change to ui directory so relative paths work - REMOVED
    # original_cwd = os.getcwd()
    # os.chdir(ui_dir)
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    Agentry AI Agent - GUI                    ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:8000                    ║
║  API Docs: http://localhost:8000/docs                        ║
║  Landing Page: http://localhost:8000/                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Import and run the server from the ui module
        # Import and run the server from the ui module (already imported above)
        # from agentry.ui.server import app (Already imported)
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        pass # os.chdir(original_cwd)


if __name__ == "__main__":
    main()
