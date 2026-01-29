"""
Unified storage interface - automatically selects backend based on AGENTRY_MODE.

LOCAL MODE (AGENTRY_MODE=local):
  - SQLite for chat/sessions
  - Local filesystem for media
  - Local logging for metrics

CLOUD MODE (AGENTRY_MODE=cloud):
  - Supabase for chat/sessions/metrics
  - Vercel Blob for media
"""
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ChatStorageBase, MediaStorageBase, MetricsBase

# Singleton instances
_chat_storage = None
_media_storage = None
_metrics_service = None


def get_mode() -> str:
    """Get current deployment mode (local or cloud)."""
    return os.getenv("AGENTRY_MODE", "local").lower()


def get_chat_storage() -> "ChatStorageBase":
    """Get chat/session storage backend."""
    global _chat_storage
    if _chat_storage is None:
        if get_mode() == "cloud":
            from .supabase_storage import SupabaseChatStorage
            _chat_storage = SupabaseChatStorage()
        else:
            from .sqlite_storage import SQLiteChatStorage
            _chat_storage = SQLiteChatStorage()
    return _chat_storage


def get_media_storage() -> "MediaStorageBase":
    """Get media file storage backend."""
    global _media_storage
    if _media_storage is None:
        if get_mode() == "cloud":
            from .blob_storage import VercelBlobStorage
            _media_storage = VercelBlobStorage()
        else:
            from .local_storage import LocalMediaStorage
            _media_storage = LocalMediaStorage()
    return _media_storage


def get_metrics_service() -> "MetricsBase":
    """Get metrics service (detailed in cloud, logging in local)."""
    global _metrics_service
    if _metrics_service is None:
        if get_mode() == "cloud":
            from .supabase_storage import SupabaseMetrics
            _metrics_service = SupabaseMetrics()
        else:
            from .local_metrics import LocalMetrics
            _metrics_service = LocalMetrics()
    return _metrics_service


def reset_storage():
    """Reset storage singletons (useful for testing)."""
    global _chat_storage, _media_storage, _metrics_service
    _chat_storage = None
    _media_storage = None
    _metrics_service = None
