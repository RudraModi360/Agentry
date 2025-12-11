import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class PersistentMemoryStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to scratchy/user_data/memory.db
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "user_data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "memory.db")
        else:
            self.db_path = db_path
            
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
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

        # Memories table (Long-term memory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                type TEXT,
                content TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
        """)

        # Agent State table (Checkpointing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_state (
                session_id TEXT,
                key TEXT,
                value TEXT,
                updated_at TIMESTAMP,
                PRIMARY KEY (session_id, key),
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
        """)
        
        conn.commit()
        conn.close()

    def create_session(self, session_id: str, metadata: Dict[str, Any] = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO sessions (session_id, created_at, last_activity, metadata) VALUES (?, ?, ?, ?)",
                (session_id, datetime.now(), datetime.now(), json.dumps(metadata or {}))
            )
            conn.commit()
        finally:
            conn.close()

    def update_session_activity(self, session_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
                (datetime.now(), session_id)
            )
            conn.commit()
        finally:
            conn.close()

    def add_memory(self, session_id: str, memory_type: str, content: str):
        """
        Add a memory. 
        session_id can be a specific session ID or 'global' for cross-session memories.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO memories (session_id, type, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, memory_type, content, datetime.now())
            )
            conn.commit()
        finally:
            conn.close()

    def get_memories(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get memories for a specific session AND global memories."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT * FROM memories 
                WHERE session_id = ? OR session_id = 'global'
                ORDER BY timestamp DESC LIMIT ?
                """,
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def save_state(self, session_id: str, key: str, value: Any):
        """Save arbitrary state (checkpointing)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO agent_state (session_id, key, value, updated_at) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id, key) DO UPDATE SET 
                value=excluded.value, updated_at=excluded.updated_at
                """,
                (session_id, key, json.dumps(value), datetime.now())
            )
            conn.commit()
        finally:
            conn.close()

    def load_state(self, session_id: str, key: str) -> Optional[Any]:
        """Load arbitrary state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT value FROM agent_state WHERE session_id = ? AND key = ?",
                (session_id, key)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
        finally:
            conn.close()

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions ordered by last activity."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # Join with agent_state to roughly estimate message count if stored there
            # Since we store messages as a JSON blob in agent_state, we can't easily count them without parsing.
            # But we can just return the metadata.
            cursor.execute("SELECT * FROM sessions ORDER BY last_activity DESC")
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                data = dict(row)
                data['id'] = data['session_id']  # Map session_id to id for compatibility
                # Try to get message count from agent_state
                msg_row = cursor.execute("SELECT value FROM agent_state WHERE session_id = ? AND key = 'messages'", (data['session_id'],)).fetchone()
                msg_count = 0
                if msg_row:
                    try:
                        msgs = json.loads(msg_row[0])
                        msg_count = len(msgs)
                    except: pass
                
                data['message_count'] = msg_count
                results.append(data)
                
            return results
        finally:
            conn.close()
