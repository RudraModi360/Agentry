"""
Entry point for the Agentry GUI (Web Interface).
Launches the FastAPI server with uvicorn.
"""
import os
import sys


def main():
    """Launch the Agentry web GUI."""
    import uvicorn
    
    # Get the directory where this module is located
    ui_dir = os.path.join(os.path.dirname(__file__), "ui")
    
    # Change to ui directory so relative paths work
    original_cwd = os.getcwd()
    os.chdir(ui_dir)
    
    try:
        # Import and run the server from the ui module
        from scratchy.ui.server import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
