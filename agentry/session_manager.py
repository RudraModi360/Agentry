import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from .memory.storage import PersistentMemoryStore

class SessionManager:
    """
    Manages chat sessions using PersistentMemoryStore (SQLite).
    Replaces legacy .toon file storage.
    """
    
    def __init__(self, storage: PersistentMemoryStore = None):
        if storage is None:
            self.storage = PersistentMemoryStore()
        else:
            self.storage = storage
            
    def save_session(self, session_id: str, messages: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Save session messages to persistent storage."""
        # Validation: Only store sessions that contain messages
        if not messages:
            return

        # Ensure session exists in registry
        if not self.storage.load_state(session_id, "messages"):
             # If it's the first time saving, create the session entry
             self.storage.create_session(session_id, metadata=metadata or {"source": "agentry_cli"})
             
        # Update activity timestamp
        self.storage.update_session_activity(session_id)
        
        # Update metadata if provided (includes provider, model, model_type)
        if metadata:
            self.storage.update_session_metadata(session_id, metadata)
        
        # Save messages as state
        # We store the full message list. For massive histories, we might want to optimize later.
        self.storage.save_state(session_id, "messages", messages)

    def load_session(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load session messages from persistent storage."""
        messages = self.storage.load_state(session_id, "messages")
        if messages is None:
            return []
        return messages
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions from the DB."""
        sessions = self.storage.list_sessions()
        
        # Parse metadata to extract title, provider, model
        for s in sessions:
            if s.get('metadata'):
                try:
                    meta = json.loads(s['metadata'])
                    s['title'] = meta.get('title')
                    s['provider'] = meta.get('provider')
                    s['model'] = meta.get('model')
                    s['model_type'] = meta.get('model_type')
                except:
                    pass
        
        # Filter out sessions with no messages
        return [s for s in sessions if s.get('message_count', 0) > 0]

    def update_session_title(self, session_id: str, title: str):
        """Update the title of a session."""
        self.storage.update_session_metadata(session_id, {"title": title})
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        # This would require deleting from sessions, agent_state, memories tables.
        # For now, let's just clear the messages state.
        self.storage.save_state(session_id, "messages", [])
        return True # Soft delete
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        # Check if messages state exists
        return self.storage.load_state(session_id, "messages") is not None
