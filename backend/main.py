"""
Main FastAPI application entry point.
Run with: uvicorn backend.main:app --reload
"""
import os
import sys

# Add parent directory to path for agentry imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from backend.config import (
    CORS_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    ASSETS_DIR,
    MEDIA_DIR,
    CSS_DIR,
    JS_DIR,
)
from backend.core.database import init_db
from backend.routes import router


# ============== Logging Setup ==============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("backend.server")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Agentry AI Agent",
        description="A powerful AI agent with tool capabilities",
        version="1.0.0"
    )
    
    # ============== Middleware ==============
    class RequestLoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.time()
            
            # Log Request
            logger.info(f"Incoming Request: {request.method} {request.url.path}")
            
            try:
                response = await call_next(request)
                
                # Log Response
                process_time = time.time() - start_time
                logger.info(
                    f"Completed Request: {request.method} {request.url.path} "
                    f"- Status: {response.status_code} "
                    f"- Duration: {process_time:.4f}s"
                )
                
                return response
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(
                    f"Request Failed: {request.method} {request.url.path} "
                    f"- Error: {str(e)} "
                    f"- Duration: {process_time:.4f}s"
                )
                raise

    app.add_middleware(RequestLoggingMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )
    
    # Initialize database
    init_db()
    
    # Mount static files
    if os.path.exists(ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    
    if os.path.exists(MEDIA_DIR):
        app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
    
    if os.path.exists(CSS_DIR):
        app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
    
    if os.path.exists(JS_DIR):
        app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
    
    # Include all routes
    app.include_router(router)
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
