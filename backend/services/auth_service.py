"""
Authentication service.
Optimized with connection pooling and in-memory caching.
"""
import sqlite3
from datetime import datetime
from typing import Optional, Dict

from backend.config import DB_PATH
from backend.core.security import hash_password, verify_password, generate_token
from backend.core.db_pool import get_connection, connection_context
from backend.core.cache import user_settings_cache, invalidate_user_cache

__all__ = ["AuthService"]


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def get_current_active_settings(user_id: int) -> Optional[Dict]:
        """Get the currently active provider settings for a user (cached)."""
        cache_key = f"user_settings:{user_id}"
        
        # Try cache first
        cached = user_settings_cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Query database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_active_settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        result = dict(row) if row else None
        
        # Cache the result (even None to avoid repeated DB queries)
        if result:
            user_settings_cache.set(cache_key, result)
        
        return result

    @staticmethod
    def get_api_key(user_id: int, provider: str, model: Optional[str] = None) -> Optional[str]:
        """Retrieves the stored API key for a specific provider (cached)."""
        # Try specific model key first (e.g. "azure:claude-3-5-sonnet")
        if model and provider == "azure":
             specific_key = f"{provider}:{model}"
             cache_key = f"api_key:{user_id}:{specific_key}"
             cached = user_settings_cache.get(cache_key)
             if cached: return cached
             
             conn = get_connection()
             cursor = conn.cursor()
             cursor.execute("SELECT api_key_encrypted FROM user_api_keys WHERE user_id = ? AND provider = ?", (user_id, specific_key))
             row = cursor.fetchone()
             if row:
                 result = row[0]
                 user_settings_cache.set(cache_key, result, ttl=300)
                 return result

        # Fallback to generic provider key
        cache_key = f"api_key:{user_id}:{provider}"
        
        # Try cache first
        cached = user_settings_cache.get(cache_key)
        if cached is not None:
            return cached
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT api_key_encrypted FROM user_api_keys WHERE user_id = ? AND provider = ?", (user_id, provider))
        row = cursor.fetchone()
        result = row[0] if row else None
        
        # Cache for 5 minutes
        if result:
            user_settings_cache.set(cache_key, result, ttl=300)
        
        return result

    @staticmethod
    def get_provider_endpoint(user_id: int, provider: str, model: Optional[str] = None) -> Optional[str]:
        """Retrieves the stored Endpoint for a specific provider (cached)."""
        # Try specific model endpoint first
        if model and provider == "azure":
             specific_key = f"{provider}:{model}"
             cache_key = f"endpoint:{user_id}:{specific_key}"
             cached = user_settings_cache.get(cache_key)
             if cached: return cached
             
             conn = get_connection()
             cursor = conn.cursor()
             cursor.execute("SELECT endpoint FROM user_api_keys WHERE user_id = ? AND provider = ?", (user_id, specific_key))
             row = cursor.fetchone()
             if row:
                 result = row[0]
                 user_settings_cache.set(cache_key, result, ttl=300)
                 return result

        cache_key = f"endpoint:{user_id}:{provider}"
        
        # Try cache first
        cached = user_settings_cache.get(cache_key)
        if cached is not None:
            return cached
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT endpoint FROM user_api_keys WHERE user_id = ? AND provider = ?", (user_id, provider))
        row = cursor.fetchone()
        result = row[0] if row else None
        
        # Cache for 5 minutes
        if result:
            user_settings_cache.set(cache_key, result, ttl=300)
        
        return result

    @staticmethod
    def save_active_settings(user_id: int, config) -> None:
        """Save active provider selection and update API key if provided."""
        with connection_context() as conn:
            cursor = conn.cursor()
            # 1. Update active settings
            cursor.execute("""
                INSERT INTO user_active_settings (user_id, provider, mode, model, model_type, tools_enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    provider = excluded.provider,
                    mode = excluded.mode,
                    model = excluded.model,
                    model_type = excluded.model_type,
                    tools_enabled = excluded.tools_enabled,
                    updated_at = excluded.updated_at
            """, (user_id, config.provider, config.mode, config.model, config.model_type, 1 if config.tools_enabled else 0, datetime.now()))

            # 2. Update API Key and Endpoint if provided
            if config.api_key or config.endpoint:
                cursor.execute("""
                    INSERT INTO user_api_keys (user_id, provider, api_key_encrypted, endpoint, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, provider) DO UPDATE SET
                        api_key_encrypted = CASE WHEN excluded.api_key_encrypted IS NOT NULL THEN excluded.api_key_encrypted ELSE user_api_keys.api_key_encrypted END,
                        endpoint = CASE WHEN excluded.endpoint IS NOT NULL THEN excluded.endpoint ELSE user_api_keys.endpoint END,
                        updated_at = excluded.updated_at
                """, (user_id, config.provider, config.api_key, config.endpoint, datetime.now()))
        
        # Invalidate cache for this user
        invalidate_user_cache(user_id)
        user_settings_cache.delete(f"api_key:{user_id}:{config.provider}")
        user_settings_cache.delete(f"endpoint:{user_id}:{config.provider}")

    @staticmethod
    def get_all_saved_configs(user_id: int):
        """Get all stored provider/model configurations for a user."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT provider, endpoint, updated_at 
            FROM user_api_keys 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        configs = []
        for row in rows:
            provider_full = row[0]
            endpoint = row[1]
            updated_at = row[2]
            
            # Split into parent provider and model name if applicable
            if ":" in provider_full:
                parent, model = provider_full.split(":", 1)
            else:
                parent = provider_full
                model = None
                
            configs.append({
                "provider_full": provider_full,
                "provider": parent,
                "model": model,
                "endpoint": endpoint,
                "updated_at": updated_at
            })
            
        return configs

    @staticmethod
    def delete_config(user_id: int, provider: str, model: Optional[str] = None):
        """Delete a stored provider/model configuration."""
        specific_key = f"{provider}:{model}" if model else provider
        
        with connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_api_keys WHERE user_id = ? AND provider = ?", (user_id, specific_key))
        
        # Invalidate cache
        user_settings_cache.delete(f"api_key:{user_id}:{specific_key}")
        user_settings_cache.delete(f"endpoint:{user_id}:{specific_key}")

