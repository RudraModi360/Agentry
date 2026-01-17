"""
In-memory agent cache.
Shared across the application for caching agent instances per user.
"""
from typing import Dict, Any

# Cache agents per user to avoid recreating them
# user_id -> {"agent": Agent, "config": {...}, "provider": Provider, "capabilities": {...}}
agent_cache: Dict[int, Dict[str, Any]] = {}
