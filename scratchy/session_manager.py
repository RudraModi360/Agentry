import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class SessionManager:
    """
    Manages chat sessions with .toon format persistence.
    Stores session history in scratchy/session_history/ folder.
    """
    
    def __init__(self, history_dir: str = None, uuid_in_session_ids: bool = False):
        if history_dir is None:
            # Default to scratchy/session_history
            script_dir = os.path.dirname(os.path.abspath(__file__))
            history_dir = os.path.join(script_dir, "session_history")
        self.history_dir = history_dir
        self.uuid_in_session_ids = uuid_in_session_ids
        os.makedirs(self.history_dir, exist_ok=True)
    
    def _get_session_path(self, session_id: str) -> str:
        """Get the file path for a session."""
        return os.path.join(self.history_dir, f"{session_id}_chat.toon")
    
    def save_session(self, session_id: str, messages: List[Dict[str, Any]]):
        """Save session messages to .toon file."""
        session_path = self._get_session_path(session_id)
        
        # Convert messages to TOON format
        toon_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": messages
        }
        
        # For now, we'll use JSON format with .toon extension
        # A full TOON encoder would be more compact, but JSON is readable and compatible
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(toon_data, f, indent=2)
    
    def load_session(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load session messages from .toon file."""
        session_path = self._get_session_path(session_id)
        
        if not os.path.exists(session_path):
            return None
        
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                toon_data = json.load(f)
            return toon_data.get("messages", [])
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def list_sessions(self) -> List[Dict[str, str]]:
        """List all available sessions."""
        sessions = []
        
        for filename in os.listdir(self.history_dir):
            if filename.endswith("_chat.toon"):
                session_id = filename.replace("_chat.toon", "")
                session_path = os.path.join(self.history_dir, filename)
                
                try:
                    with open(session_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        "id": session_id,
                        "created_at": data.get("created_at", "Unknown"),
                        "message_count": len(data.get("messages", []))
                    })
                except:
                    continue
        
        return sorted(sessions, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        session_path = self._get_session_path(session_id)
        
        if os.path.exists(session_path):
            os.remove(session_path)
            return True
        return False
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return os.path.exists(self._get_session_path(session_id))
