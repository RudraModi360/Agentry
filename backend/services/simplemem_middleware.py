"""
SimpleMem middleware for WebSocket chat.
Provides context augmentation with detailed logging.
"""
import os
import time
from typing import Optional, List, Dict, Any

# Lazy import to avoid circular dependencies
_simplemem_instances: Dict[str, Any] = {}


def is_simplemem_enabled() -> bool:
    """Check if SimpleMem is enabled (requires LanceDB)."""
    try:
        import lancedb
        from agentry.config.settings import settings
        return settings.SIMPLEMEM_ENABLED
    except ImportError:
        print("[SimpleMem] LanceDB not installed - memory disabled")
        return False


async def get_simplemem_context(user_id: str, session_id: str, user_message: str) -> Optional[List[str]]:
    """
    Get relevant context from SimpleMem for the user's message.
    Returns list of context strings to augment the prompt, or None if disabled.
    """
    if not is_simplemem_enabled():
        return None
    
    start_time = time.time()
    
    try:
        from agentry.simplemem import AgentrySimpleMem
        
        cache_key = f"{user_id}:{session_id}"
        
        # Create or get SimpleMem instance
        if cache_key not in _simplemem_instances:
            from agentry.config.settings import settings
            print(f"[SimpleMem] Creating new instance for user {user_id}")
            _simplemem_instances[cache_key] = AgentrySimpleMem(
                user_id=str(user_id),
                session_id=session_id,
                debug=True  # Always enable debug for visibility
            )
        
        memory = _simplemem_instances[cache_key]
        
        # Get relevant context
        print(f"[SimpleMem] Retrieving context for: '{user_message[:80]}...'")
        contexts = await memory.on_user_message(user_message)
        
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        if contexts:
            print(f"[SimpleMem] ✓ Retrieved {len(contexts)} memories in {elapsed:.1f}ms:")
            for i, ctx in enumerate(contexts[:5]):  # Show first 5
                display_ctx = ctx[:150] + "..." if len(ctx) > 150 else ctx
                print(f"  [{i+1}] {display_ctx}")
        else:
            print(f"[SimpleMem] ○ No relevant memories found ({elapsed:.1f}ms)")
        
        return contexts if contexts else None
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"[SimpleMem] ✗ Context retrieval error ({elapsed:.1f}ms): {e}")
        import traceback
        traceback.print_exc()
        return None


async def store_response_in_simplemem(user_id: str, session_id: str, assistant_response: str):
    """
    Store the assistant's response in SimpleMem for future context.
    """
    if not is_simplemem_enabled():
        return
    
    try:
        cache_key = f"{user_id}:{session_id}"
        
        if cache_key in _simplemem_instances:
            memory = _simplemem_instances[cache_key]
            await memory.on_assistant_message(assistant_response)
            
            # Truncate for logging
            preview = assistant_response[:100] + "..." if len(assistant_response) > 100 else assistant_response
            print(f"[SimpleMem] Queued response for memory: {preview}")
            
    except Exception as e:
        print(f"[SimpleMem] Store response error: {e}")


async def process_pending_memories(user_id: str, session_id: str):
    """
    Process any queued dialogues into memory entries.
    Call this periodically or on session end.
    """
    if not is_simplemem_enabled():
        return
    
    try:
        cache_key = f"{user_id}:{session_id}"
        
        if cache_key in _simplemem_instances:
            memory = _simplemem_instances[cache_key]
            print(f"[SimpleMem] Processing pending dialogues for {user_id}...")
            await memory.process_pending()
            print(f"[SimpleMem] ✓ Pending dialogues processed")
            
    except Exception as e:
        print(f"[SimpleMem] Process pending error: {e}")


def augment_prompt_with_context(user_message: str, contexts: Optional[List[str]]) -> str:
    """
    Augment the user's message with relevant context from memory.
    """
    if not contexts:
        return user_message
    
    context_block = "\n".join(f"- {ctx}" for ctx in contexts[:5])
    
    augmented = f"""Relevant context from memory:
{context_block}

User: {user_message}"""
    
    return augmented


def get_memory_stats(user_id: str, session_id: str) -> Dict[str, Any]:
    """Get SimpleMem statistics for a user/session."""
    if not is_simplemem_enabled():
        return {"enabled": False, "reason": "LanceDB not installed or SimpleMem disabled"}
    
    try:
        cache_key = f"{user_id}:{session_id}"
        
        if cache_key in _simplemem_instances:
            memory = _simplemem_instances[cache_key]
            stats = memory.get_stats()
            print(f"[SimpleMem] Stats for {user_id}: {stats}")
            return {"enabled": True, **stats}
        
        return {"enabled": True, "initialized": False}
        
    except Exception as e:
        return {"enabled": True, "error": str(e)}


# --- SimpleMem-based Memory API for agents.py ---

async def search_memories_simplemem(user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search memories using SimpleMem's vector search."""
    if not is_simplemem_enabled():
        return []
    
    try:
        from agentry.simplemem import AgentrySimpleMem
        
        # Use a generic session for API queries
        cache_key = f"{user_id}:api"
        
        if cache_key not in _simplemem_instances:
            _simplemem_instances[cache_key] = AgentrySimpleMem(
                user_id=str(user_id),
                session_id="api",
                debug=False
            )
        
        memory = _simplemem_instances[cache_key]
        results = memory._fast_retrieve(query, limit=limit)
        
        # Convert to dict format
        return [{"content": r, "type": "memory"} for r in results]
        
    except Exception as e:
        print(f"[SimpleMem] Search error: {e}")
        return []


async def add_memory_simplemem(user_id: str, content: str, memory_type: str = "manual") -> bool:
    """Add a memory entry to SimpleMem."""
    if not is_simplemem_enabled():
        return False
    
    try:
        from agentry.simplemem import AgentrySimpleMem
        
        cache_key = f"{user_id}:api"
        
        if cache_key not in _simplemem_instances:
            _simplemem_instances[cache_key] = AgentrySimpleMem(
                user_id=str(user_id),
                session_id="api",
                debug=False
            )
        
        memory = _simplemem_instances[cache_key]
        memory._queue_dialogue("User", f"[{memory_type}] {content}")
        await memory.process_pending()
        
        print(f"[SimpleMem] Added memory for user {user_id}: {content[:50]}...")
        return True
        
    except Exception as e:
        print(f"[SimpleMem] Add memory error: {e}")
        return False
