"""
Singleton SessionManager for performance optimization.
Avoids creating new SessionManager instances on every API call.
"""
from functools import lru_cache
from typing import Optional
import threading

_session_manager_lock = threading.Lock()
_session_manager_instance = None


def get_session_manager():
    """
    Get the global SessionManager singleton instance.
    Thread-safe lazy initialization.
    """
    global _session_manager_instance
    
    if _session_manager_instance is None:
        with _session_manager_lock:
            # Double-check locking pattern
            if _session_manager_instance is None:
                from scratchy.session_manager import SessionManager
                _session_manager_instance = SessionManager()
    
    return _session_manager_instance


def reset_session_manager():
    """Reset the singleton (useful for testing)."""
    global _session_manager_instance
    with _session_manager_lock:
        _session_manager_instance = None
