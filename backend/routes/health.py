"""
Backend health and system endpoints.
Provides /health, /ready, and /telemetry endpoints.
"""

from fastapi import APIRouter
from datetime import datetime
import os
import sys


router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint — returns 200 if the server is alive.
    Used by load balancers and monitoring systems.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.6"
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check — verifies that all required services are available.
    Returns 200 only when the server is ready to handle requests.
    """
    checks = {}
    all_ready = True

    # Check database
    try:
        from backend.core.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_ready = False

    # Check SimpleMem
    try:
        from backend.services.simplemem_middleware import is_simplemem_enabled
        checks["simplemem"] = "enabled" if is_simplemem_enabled() else "disabled"
    except Exception as e:
        checks["simplemem"] = f"error: {str(e)}"

    # Check Python version
    checks["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check environment
    checks["env"] = os.environ.get("AGENTRY_ENV", "development")

    return {
        "ready": all_ready,
        "timestamp": datetime.now().isoformat(),
        "checks": checks
    }


@router.get("/system/info")
async def system_info():
    """
    System information endpoint.
    Returns configuration and capability details.
    """
    try:
        from logicore.config.settings import get_settings
        settings = get_settings()
        return {
            "version": "1.0.6",
            "deployment_mode": settings.DEPLOYMENT_MODE,
            "default_provider": settings.DEFAULT_PROVIDER,
            "default_model": settings.DEFAULT_MODEL,
            "embedding_enabled": True,
            "simplemem_enabled": settings.SIMPLEMEM_ENABLED,
            "providers_available": _get_available_providers(),
        }
    except Exception:
        return {
            "version": "1.0.6",
            "providers_available": _get_available_providers(),
        }


def _get_available_providers() -> list:
    """Check which LLM providers are importable."""
    providers = []
    provider_checks = {
        "ollama": "logicore.providers.ollama_provider",
        "groq": "logicore.providers.groq_provider",
        "gemini": "logicore.providers.gemini_provider",
        "azure": "logicore.providers.azure_provider",
        "openai": "logicore.providers.openai_provider",
    }
    for name, module_path in provider_checks.items():
        try:
            __import__(module_path)
            providers.append(name)
        except ImportError:
            pass
    return providers
