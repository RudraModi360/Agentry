"""
SQLite-based storage for LOCAL MODE.
Wraps existing database with the unified storage interface.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from .base import (
    ChatStorageBase, SessionData, MessageData,
)
from backend.config import DB_PATH


class SQLiteChatStorage(ChatStorageBase):
    """
    SQLite implementation for local development.
    Uses the existing scratchy_users.db schema.
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._ensure_tables()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _ensure_tables(self):
        """Ensure required tables exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP,
                    last_activity TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Agent state (for messages)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    session_id TEXT,
                    key TEXT,
                    value TEXT,
                    updated_at TIMESTAMP,
                    PRIMARY KEY (session_id, key)
                )
            """)
            
            conn.commit()
    
    async def create_session(self, user_id: str, metadata: Dict[str, Any]) -> SessionData:
        """Create a new chat session."""
        session_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
        now = datetime.now()
        
        full_metadata = {
            "title": metadata.get("title", "New Chat"),
            "user_id": user_id,
            "provider": metadata.get("provider"),
            "model": metadata.get("model"),
            "model_type": metadata.get("model_type"),
            **metadata
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (session_id, created_at, last_activity, metadata) VALUES (?, ?, ?, ?)",
                (session_id, now, now, json.dumps(full_metadata))
            )
            conn.commit()
        
        return SessionData(
            id=session_id,
            user_id=user_id,
            title=full_metadata.get("title", "New Chat"),
            provider=full_metadata.get("provider"),
            model=full_metadata.get("model"),
            model_type=full_metadata.get("model_type"),
            created_at=now,
            updated_at=now,
            message_count=0
        )
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[SessionData]:
        """Get all sessions for a user."""
        user_prefix = f"user_{user_id}_"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT session_id, created_at, last_activity, metadata 
                   FROM sessions 
                   WHERE session_id LIKE ? 
                   ORDER BY last_activity DESC 
                   LIMIT ?""",
                (f"{user_prefix}%", limit)
            )
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                metadata = json.loads(row["metadata"] or "{}")
                
                # Get message count
                msg_cursor = cursor.execute(
                    "SELECT value FROM agent_state WHERE session_id = ? AND key = 'messages'",
                    (row["session_id"],)
                )
                msg_row = msg_cursor.fetchone()
                msg_count = 0
                if msg_row:
                    try:
                        msgs = json.loads(msg_row[0])
                        msg_count = sum(1 for m in msgs if m.get("role") == "user")
                    except:
                        pass
                
                sessions.append(SessionData(
                    id=row["session_id"],
                    user_id=user_id,
                    title=metadata.get("title", "New Chat"),
                    provider=metadata.get("provider"),
                    model=metadata.get("model"),
                    model_type=metadata.get("model_type"),
                    created_at=row["created_at"],
                    updated_at=row["last_activity"],
                    message_count=msg_count
                ))
            
            return sessions
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a specific session by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT session_id, created_at, last_activity, metadata FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            metadata = json.loads(row["metadata"] or "{}")
            user_id = metadata.get("user_id", "")
            
            return SessionData(
                id=row["session_id"],
                user_id=user_id,
                title=metadata.get("title", "New Chat"),
                provider=metadata.get("provider"),
                model=metadata.get("model"),
                model_type=metadata.get("model_type"),
                created_at=row["created_at"],
                updated_at=row["last_activity"]
            )
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current metadata
            cursor.execute("SELECT metadata FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            current_metadata = json.loads(row["metadata"] or "{}")
            current_metadata.update(updates)
            
            cursor.execute(
                "UPDATE sessions SET metadata = ?, last_activity = ? WHERE session_id = ?",
                (json.dumps(current_metadata), datetime.now(), session_id)
            )
            conn.commit()
            return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM agent_state WHERE session_id = ?", (session_id,))
            conn.commit()
            return True
    
    async def save_message(self, session_id: str, role: str, content: str,
                          metadata: Optional[Dict[str, Any]] = None) -> MessageData:
        """Save a chat message (append to messages array in agent_state)."""
        message_id = str(uuid.uuid4())
        now = datetime.now()
        
        message = {
            "id": message_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": now.isoformat()
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get existing messages
            cursor.execute(
                "SELECT value FROM agent_state WHERE session_id = ? AND key = 'messages'",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                messages = json.loads(row[0])
                messages.append(message)
                cursor.execute(
                    "UPDATE agent_state SET value = ?, updated_at = ? WHERE session_id = ? AND key = 'messages'",
                    (json.dumps(messages), now, session_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO agent_state (session_id, key, value, updated_at) VALUES (?, ?, ?, ?)",
                    (session_id, "messages", json.dumps([message]), now)
                )
            
            # Update session last_activity
            cursor.execute(
                "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
                (now, session_id)
            )
            
            conn.commit()
        
        return MessageData(
            id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
            created_at=now
        )
    
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[MessageData]:
        """Get messages for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM agent_state WHERE session_id = ? AND key = 'messages'",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return []
            
            messages_raw = json.loads(row[0])
            messages = []
            
            for msg in messages_raw[-limit:]:
                messages.append(MessageData(
                    id=msg.get("id", str(uuid.uuid4())),
                    session_id=session_id,
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    metadata=msg.get("metadata"),
                    created_at=datetime.fromisoformat(msg["created_at"]) if msg.get("created_at") else None
                ))
            
            return messages
    
    async def search_sessions(self, user_id: str, query: str, limit: int = 20) -> List[SessionData]:
        """Search sessions by title and content."""
        user_prefix = f"user_{user_id}_"
        query_lower = query.lower()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT session_id, created_at, last_activity, metadata 
                   FROM sessions 
                   WHERE session_id LIKE ? 
                   ORDER BY last_activity DESC""",
                (f"{user_prefix}%",)
            )
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                metadata = json.loads(row["metadata"] or "{}")
                title = metadata.get("title", "").lower()
                
                # Check title match
                if query_lower in title:
                    results.append(SessionData(
                        id=row["session_id"],
                        user_id=user_id,
                        title=metadata.get("title", "New Chat"),
                        created_at=row["created_at"],
                        updated_at=row["last_activity"]
                    ))
                    continue
                
                # Check message content (simplified)
                msg_cursor = cursor.execute(
                    "SELECT value FROM agent_state WHERE session_id = ? AND key = 'messages'",
                    (row["session_id"],)
                )
                msg_row = msg_cursor.fetchone()
                if msg_row:
                    content = msg_row[0].lower()
                    if query_lower in content:
                        results.append(SessionData(
                            id=row["session_id"],
                            user_id=user_id,
                            title=metadata.get("title", "New Chat"),
                            created_at=row["created_at"],
                            updated_at=row["last_activity"]
                        ))
                
                if len(results) >= limit:
                    break
            
            return results[:limit]
