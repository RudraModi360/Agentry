"""
Business logic services.
"""
from .auth_service import AuthService
from .provider_service import ProviderService
from .agent_cache import agent_cache

# Storage services (auto-selects based on AGENTRY_MODE)
from .storage import get_chat_storage, get_media_storage, get_metrics_service, get_mode

# SimpleMem middleware
from .simplemem_middleware import (
    get_simplemem_context,
    store_response_in_simplemem,
    is_simplemem_enabled,
)

__all__ = [
    "AuthService",
    "ProviderService",
    "agent_cache",
    # Storage
    "get_chat_storage",
    "get_media_storage",
    "get_metrics_service",
    "get_mode",
    # SimpleMem
    "get_simplemem_context",
    "store_response_in_simplemem",
    "is_simplemem_enabled",
]

