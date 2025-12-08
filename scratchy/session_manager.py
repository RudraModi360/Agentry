import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from py_toon_format import encode, decode

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
        
        # Sanitize messages to ensure JSON serialization
        clean_messages = self._sanitize_messages(messages)
        
        # Convert messages to TOON format
        toon_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": clean_messages
        }
        
        # Encode to TOON string
        toon_content = encode(toon_data)
        
        with open(session_path, 'w', encoding='utf-8') as f:
            f.write(toon_content)

    def _sanitize_messages(self, data: Any) -> Any:
        """Recursively convert objects to dicts/lists for serialization."""
        if isinstance(data, dict):
            return {k: self._sanitize_messages(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_messages(item) for item in data]
        elif hasattr(data, "model_dump"): # Pydantic V2
            return self._sanitize_messages(data.model_dump())
        elif hasattr(data, "dict"): # Pydantic V1
            return self._sanitize_messages(data.dict())
        elif hasattr(data, "__dict__"): # Generic Object
            try:
                # Try to use vars() or __dict__
                return self._sanitize_messages(vars(data))
            except:
                # Fallback to string representation if we can't get vars
                return str(data)
        elif hasattr(data, "to_dict"): # Some SDKs
            return self._sanitize_messages(data.to_dict())
        else:
            return data
    
    def load_session(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load session messages from .toon file."""
        session_path = self._get_session_path(session_id)
        
        if not os.path.exists(session_path):
            return None
        
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it's legacy JSON
            if content.strip().startswith("{") and '"messages":' in content:
                 try:
                    toon_data = json.loads(content)
                    return toon_data.get("messages", [])
                 except:
                    pass # Fallback to TOON decode
            
            # Decode TOON
            toon_data = decode(content)
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
                        content = f.read()
                    
                    if content.strip().startswith("{") and '"messages":' in content:
                         try:
                            data = json.loads(content)
                         except:
                            data = decode(content)
                    else:
                        data = decode(content)
                    
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
