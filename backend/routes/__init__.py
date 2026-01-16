"""
API Routes for the backend.
All routers are aggregated here and included in the main app.
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .providers import router as providers_router
from .sessions import router as sessions_router
from .mcp_routes import router as mcp_router
from .tools import router as tools_router
from .agents import router as agents_router
from .media import router as media_router
from .pages import router as pages_router
from .websocket import router as websocket_router

# Main router that includes all sub-routers
router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker and load balancer health probes."""
    return {
        "status": "healthy",
        "service": "agentry-backend",
        "version": "1.0.0"
    }

# Include all routers
router.include_router(pages_router)
router.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
router.include_router(providers_router, prefix="/api", tags=["Providers"])
router.include_router(sessions_router, prefix="/api/sessions", tags=["Sessions"])
router.include_router(mcp_router, prefix="/api/mcp", tags=["MCP"])
router.include_router(tools_router, prefix="/api/tools", tags=["Tools"])
router.include_router(agents_router, prefix="/api", tags=["Agents"])
router.include_router(media_router, prefix="/api/media", tags=["Media"])
router.include_router(websocket_router, tags=["WebSocket"])

__all__ = ["router"]
