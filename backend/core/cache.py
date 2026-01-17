"""
In-Memory Caching Layer for Agentry Backend

Provides fast, thread-safe caching with TTL support for:
- User settings (provider, model, etc.)
- Model capabilities
- Session metadata
- API response data

This significantly reduces database queries and improves response times.
"""

import time
import threading
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps


@dataclass
class CacheEntry:
    """A single cache entry with value and expiration."""
    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.time)
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class TTLCache:
    """
    Thread-safe in-memory cache with TTL (Time To Live) support.
    
    Usage:
        cache = TTLCache(default_ttl=300)  # 5 minutes default
        cache.set("key", value, ttl=60)    # 1 minute TTL
        value = cache.get("key")           # Returns None if expired
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (300 = 5 minutes)
            max_size: Maximum number of entries before cleanup
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache. Returns None if not found or expired."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL override."""
        with self._lock:
            # Cleanup if too many entries
            if len(self._cache) >= self.max_size:
                self._cleanup_expired()
            
            ttl = ttl if ttl is not None else self.default_ttl
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.time() + ttl
            )
    
    def delete(self, key: str) -> bool:
        """Delete a specific key. Returns True if key existed."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern (simple prefix match). Returns count deleted."""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
    
    def _cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0,
                "max_size": self.max_size
            }


# === Global Cache Instances ===

# User settings cache (TTL: 10 minutes)
# Keys: f"user_settings:{user_id}"
user_settings_cache = TTLCache(default_ttl=600, max_size=500)

# Capabilities cache (TTL: 1 hour - capabilities rarely change)
# Keys: f"capabilities:{provider}:{model}"
capabilities_cache = TTLCache(default_ttl=3600, max_size=200)

# Session list cache (TTL: 30 seconds - frequently updated)
# Keys: f"sessions:{user_id}"
sessions_cache = TTLCache(default_ttl=30, max_size=500)

# Provider list cache (TTL: 5 minutes - static data)
# Keys: "providers"
providers_cache = TTLCache(default_ttl=300, max_size=10)

# Tools cache (TTL: 2 minutes)
# Keys: f"tools:{user_id}"
tools_cache = TTLCache(default_ttl=120, max_size=500)


# === Cache Decorators ===

def cached(cache: TTLCache, key_func: Callable[..., str], ttl: Optional[int] = None):
    """
    Decorator to cache function results.
    
    Usage:
        @cached(user_settings_cache, lambda user_id: f"settings:{user_id}")
        def get_user_settings(user_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs)
            
            # Try cache first
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            
            return result
        
        # Add cache invalidation method
        wrapper.invalidate = lambda *args, **kwargs: cache.delete(key_func(*args, **kwargs))
        wrapper.cache = cache
        
        return wrapper
    return decorator


def async_cached(cache: TTLCache, key_func: Callable[..., str], ttl: Optional[int] = None):
    """
    Async version of cached decorator.
    
    Usage:
        @async_cached(sessions_cache, lambda user_id: f"sessions:{user_id}")
        async def get_sessions(user_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs)
            
            # Try cache first
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call async function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            
            return result
        
        # Add cache invalidation method
        wrapper.invalidate = lambda *args, **kwargs: cache.delete(key_func(*args, **kwargs))
        wrapper.cache = cache
        
        return wrapper
    return decorator


# === Helper Functions ===

def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all caches for a specific user."""
    user_settings_cache.delete(f"user_settings:{user_id}")
    sessions_cache.delete(f"sessions:{user_id}")
    tools_cache.delete(f"tools:{user_id}")


def get_all_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all caches."""
    return {
        "user_settings": user_settings_cache.stats,
        "capabilities": capabilities_cache.stats,
        "sessions": sessions_cache.stats,
        "providers": providers_cache.stats,
        "tools": tools_cache.stats,
    }


def clear_all_caches() -> None:
    """Clear all caches (useful for testing/debugging)."""
    user_settings_cache.clear()
    capabilities_cache.clear()
    sessions_cache.clear()
    providers_cache.clear()
    tools_cache.clear()
