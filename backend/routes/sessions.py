"""
Session management routes.
Optimized with singleton SessionManager and connection pooling.
"""
import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends

from backend.core.dependencies import get_current_user
from backend.core.session_singleton import get_session_manager

router = APIRouter()


@router.get("")
async def get_sessions(user: Dict = Depends(get_current_user)):
    """Get all chat sessions for the user (cached)."""
    from backend.core.cache import sessions_cache
    
    user_id = user['id']
    cache_key = f"sessions:{user_id}"
    
    # Try cache first
    cached = sessions_cache.get(cache_key)
    if cached is not None:
        return {"sessions": cached}
    
    session_manager = get_session_manager()
    sessions = session_manager.list_sessions()
    
    # Filter sessions by user (using session_id prefix)
    user_prefix = f"user_{user_id}_"
    user_sessions = [
        {
            "id": s["session_id"],
            "title": s.get("title") or "New Chat",
            "created_at": s.get("created_at"),
            "updated_at": s.get("last_activity"),
            "message_count": s.get("message_count", 0),
            "provider": s.get("provider"),
            "model": s.get("model"),
            "model_type": s.get("model_type")
        }
        for s in sessions
        if s["session_id"].startswith(user_prefix)
    ]
    
    # Cache for 10 seconds (short TTL to keep up with message updates)
    sessions_cache.set(cache_key, user_sessions, ttl=10)
    
    return {"sessions": user_sessions}


@router.post("")
async def create_session(user: Dict = Depends(get_current_user)):
    """Create a new chat session."""
    from backend.core.cache import sessions_cache
    
    session_id = f"user_{user['id']}_{uuid.uuid4().hex[:8]}"
    
    session_manager = get_session_manager()
    session_manager.storage.create_session(session_id, metadata={"title": "New Chat", "user_id": user["id"]})
    
    # Invalidate session list cache
    sessions_cache.delete(f"sessions:{user['id']}")
    
    return {
        "session": {
            "id": session_id,
            "title": "New Chat",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
    }


@router.get("/search")
async def search_sessions(q: str, user: Dict = Depends(get_current_user)):
    """Search chat sessions by title and message content."""
    # Search is not cached due to variable query
    # ... (rest of search logic remains same)
    if not q or len(q.strip()) < 1:
        return {"sessions": [], "query": q}
    
    query = q.strip().lower()
    query_words = query.split()
    
    session_manager = get_session_manager()
    all_sessions = session_manager.list_sessions()
    
    # Filter sessions by user
    user_prefix = f"user_{user['id']}_"
    user_sessions = [s for s in all_sessions if s["session_id"].startswith(user_prefix)]
    
    # ... (rest of search logic logic is complex and best left as is for now)
    
    # Returning original search implementation from this point...
    user_sessions.sort(key=lambda x: x.get("last_activity") or x.get("created_at") or "", reverse=True)
    
    results = []
    
    for session in user_sessions[0:100]:
        session_id = session["session_id"]
        title = (session.get("title") or "New Chat").lower()
        score = 0
        match_source = []
        snippet = ""
        
        # Title matching - high priority
        if query in title:
            score += 150
            match_source.append("title")
        else:
            for word in query_words:
                if len(word) > 2 and word in title:
                    score += 40
                    if "title" not in match_source:
                        match_source.append("title")
        
        # Message content matching
        try:
            messages = session_manager.load_session(session_id)
            if messages:
                for msg in reversed(messages):
                    content = ""
                    if isinstance(msg, dict):
                        content = str(msg.get("content", "")).lower()
                    else:
                        content = str(msg).lower()
                    
                    if query in content:
                        score += 80
                        if "messages" not in match_source:
                            match_source.append("messages")
                        
                        idx = content.find(query)
                        start = max(0, idx - 30)
                        end = min(len(content), idx + len(query) + 30)
                        snippet = "..." + content[start:end] + "..."
                        break
                    else:
                        for word in query_words:
                            if len(word) > 2 and word in content:
                                score += 20
                                if "messages" not in match_source:
                                    match_source.append("messages")
                                break
        except Exception as e:
            print(f"[Search] Error loading session {session_id}: {e}")
        
        if score > 0:
            results.append({
                "id": session_id,
                "title": session.get("title") or "New Chat",
                "created_at": session.get("created_at"),
                "updated_at": session.get("last_activity"),
                "score": score,
                "match_source": match_source,
                "snippet": snippet
            })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {"sessions": results[:20], "query": q}


@router.get("/{session_id}")
async def get_session(session_id: str, user: Dict = Depends(get_current_user)):
    """Get a specific session with messages."""
    # Verify session belongs to user
    user_prefix = f"user_{user['id']}_"
    if not session_id.startswith(user_prefix):
        return {"error": "Session not found"}
    
    session_manager = get_session_manager()
    messages = session_manager.load_session(session_id)
    
    return {
        "session": {
            "id": session_id,
            "messages": messages or []
        }
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str, user: Dict = Depends(get_current_user)):
    """Delete a chat session."""
    from backend.core.cache import sessions_cache
    
    # Verify session belongs to user
    user_prefix = f"user_{user['id']}_"
    if not session_id.startswith(user_prefix):
        return {"error": "Session not found"}
    
    session_manager = get_session_manager()
    session_manager.storage.delete_session(session_id)
    
    # Invalidate session list cache
    sessions_cache.delete(f"sessions:{user['id']}")
    
    return {"message": "Session deleted"}
