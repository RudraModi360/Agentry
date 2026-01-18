"""
Supabase-based storage for CLOUD MODE.
Handles chat sessions, messages, and metrics.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import ChatStorageBase, MetricsBase, SessionData, MessageData

# Lazy import to avoid dependency issues in local mode
_supabase_client = None


def _get_client():
    """Get or create Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in CLOUD MODE")
        _supabase_client = create_client(url, key)
    return _supabase_client


class SupabaseChatStorage(ChatStorageBase):
    """
    Supabase implementation for cloud deployment.
    Uses PostgreSQL tables via Supabase client.
    """
    
    def __init__(self):
        self.client = _get_client()
    
    async def create_session(self, user_id: str, metadata: Dict[str, Any]) -> SessionData:
        """Create a new chat session."""
        data = {
            "user_id": user_id,
            "title": metadata.get("title", "New Chat"),
            "provider": metadata.get("provider"),
            "model": metadata.get("model"),
            "model_type": metadata.get("model_type"),
        }
        
        result = self.client.table("chat_sessions").insert(data).execute()
        row = result.data[0]
        
        return SessionData(
            id=row["id"],
            user_id=user_id,
            title=row.get("title", "New Chat"),
            provider=row.get("provider"),
            model=row.get("model"),
            model_type=row.get("model_type"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None,
            message_count=0
        )
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[SessionData]:
        """Get all sessions for a user."""
        result = self.client.table("chat_sessions") \
            .select("*, chat_messages(count)") \
            .eq("user_id", user_id) \
            .order("updated_at", desc=True) \
            .limit(limit) \
            .execute()
        
        sessions = []
        for row in result.data:
            # Get message count from aggregation
            msg_count = 0
            if row.get("chat_messages"):
                msg_count = row["chat_messages"][0].get("count", 0) if row["chat_messages"] else 0
            
            sessions.append(SessionData(
                id=row["id"],
                user_id=user_id,
                title=row.get("title", "New Chat"),
                provider=row.get("provider"),
                model=row.get("model"),
                model_type=row.get("model_type"),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None,
                message_count=msg_count
            ))
        
        return sessions
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a specific session by ID."""
        result = self.client.table("chat_sessions") \
            .select("*") \
            .eq("id", session_id) \
            .single() \
            .execute()
        
        if not result.data:
            return None
        
        row = result.data
        return SessionData(
            id=row["id"],
            user_id=row["user_id"],
            title=row.get("title", "New Chat"),
            provider=row.get("provider"),
            model=row.get("model"),
            model_type=row.get("model_type"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None
        )
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session metadata."""
        updates["updated_at"] = datetime.now().isoformat()
        
        result = self.client.table("chat_sessions") \
            .update(updates) \
            .eq("id", session_id) \
            .execute()
        
        return len(result.data) > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages (cascade)."""
        # Messages will be deleted by CASCADE in database
        result = self.client.table("chat_sessions") \
            .delete() \
            .eq("id", session_id) \
            .execute()
        
        return len(result.data) > 0
    
    async def save_message(self, session_id: str, role: str, content: str,
                          metadata: Optional[Dict[str, Any]] = None) -> MessageData:
        """Save a chat message."""
        data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        
        result = self.client.table("chat_messages").insert(data).execute()
        row = result.data[0]
        
        # Update session timestamp
        self.client.table("chat_sessions") \
            .update({"updated_at": datetime.now().isoformat()}) \
            .eq("id", session_id) \
            .execute()
        
        return MessageData(
            id=row["id"],
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None
        )
    
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[MessageData]:
        """Get messages for a session."""
        result = self.client.table("chat_messages") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("created_at", desc=False) \
            .limit(limit) \
            .execute()
        
        return [
            MessageData(
                id=row["id"],
                session_id=session_id,
                role=row["role"],
                content=row["content"],
                metadata=row.get("metadata"),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None
            )
            for row in result.data
        ]
    
    async def search_sessions(self, user_id: str, query: str, limit: int = 20) -> List[SessionData]:
        """Search sessions by title."""
        # Basic title search - Supabase supports full-text search for more advanced use
        result = self.client.table("chat_sessions") \
            .select("*") \
            .eq("user_id", user_id) \
            .ilike("title", f"%{query}%") \
            .order("updated_at", desc=True) \
            .limit(limit) \
            .execute()
        
        return [
            SessionData(
                id=row["id"],
                user_id=user_id,
                title=row.get("title", "New Chat"),
                provider=row.get("provider"),
                model=row.get("model"),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None
            )
            for row in result.data
        ]


class SupabaseMetrics(MetricsBase):
    """
    Supabase-based metrics for cloud deployment.
    Stores detailed request metrics for analytics.
    """
    
    def __init__(self):
        self.client = _get_client()
    
    async def log_request(self, user_id: str, endpoint: str, method: str,
                         latency_ms: float, **kwargs) -> None:
        """Log a request metric."""
        data = {
            "user_id": user_id,
            "endpoint": endpoint,
            "method": method,
            "latency_ms": latency_ms,
            "status_code": kwargs.get("status_code", 200),
            "tokens_input": kwargs.get("tokens_input"),
            "tokens_output": kwargs.get("tokens_output"),
            "memory_retrieval_ms": kwargs.get("memory_retrieval_ms"),
            "llm_latency_ms": kwargs.get("llm_latency_ms"),
            "session_id": kwargs.get("session_id"),
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        try:
            self.client.table("request_metrics").insert(data).execute()
        except Exception as e:
            # Don't fail the request if metrics logging fails
            print(f"[Metrics] Failed to log: {e}")
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a user."""
        try:
            result = self.client.rpc("get_user_stats", {"p_user_id": user_id}).execute()
            return result.data if result.data else {}
        except Exception as e:
            # Fallback to basic query if RPC not available
            result = self.client.table("request_metrics") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute()
            
            if not result.data:
                return {"total_requests": 0, "avg_latency_ms": 0}
            
            total = len(result.data)
            avg_latency = sum(r.get("latency_ms", 0) for r in result.data) / total if total > 0 else 0
            
            return {
                "total_requests": total,
                "avg_latency_ms": round(avg_latency, 2)
            }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide stats."""
        try:
            result = self.client.table("request_metrics") \
                .select("*", count="exact") \
                .execute()
            
            total = result.count or 0
            avg_latency = 0
            if result.data:
                avg_latency = sum(r.get("latency_ms", 0) for r in result.data) / len(result.data)
            
            return {
                "mode": "cloud",
                "total_requests": total,
                "avg_latency_ms": round(avg_latency, 2)
            }
        except Exception as e:
            return {"mode": "cloud", "error": str(e)}
