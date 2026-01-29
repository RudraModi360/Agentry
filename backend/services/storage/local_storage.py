"""
Local filesystem storage for media files (LOCAL MODE).
"""
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, BinaryIO

from .base import MediaStorageBase, MediaData
from backend.config import DB_PATH, MEDIA_DIR


class LocalMediaStorage(MediaStorageBase):
    """
    Local filesystem media storage.
    Files stored in ui/media/, metadata in SQLite.
    """
    
    def __init__(self, db_path: str = None, media_dir: str = None):
        self.db_path = db_path or DB_PATH
        self.media_dir = media_dir or MEDIA_DIR
        os.makedirs(self.media_dir, exist_ok=True)
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure user_media table exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                filepath TEXT,
                content_type TEXT,
                created_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    async def upload(self, filename: str, file: BinaryIO,
                    content_type: str, user_id: str) -> MediaData:
        """Upload a media file to local filesystem."""
        # Generate unique filename
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(self.media_dir, unique_name)
        
        # Save file
        content = file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        now = datetime.now()
        url = f"/media/{unique_name}"
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_media (user_id, filename, filepath, content_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, unique_name, url, content_type, now)
        )
        media_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return MediaData(
            id=str(media_id),
            user_id=user_id,
            filename=unique_name,
            url=url,
            content_type=content_type,
            created_at=now
        )
    
    async def delete(self, media_id: str, user_id: str) -> bool:
        """Delete a media file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get file info
            cursor.execute(
                "SELECT filename, user_id FROM user_media WHERE id = ?",
                (media_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            # Verify ownership
            if str(row[1]) != str(user_id):
                return False
            
            filename = row[0]
            filepath = os.path.join(self.media_dir, filename)
            
            # Delete from database
            cursor.execute("DELETE FROM user_media WHERE id = ?", (media_id,))
            conn.commit()
            
            # Delete from disk
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return True
        finally:
            conn.close()
    
    async def get_user_media(self, user_id: str, limit: int = 50) -> List[MediaData]:
        """Get all media files for a user."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, filename, filepath, content_type, created_at 
               FROM user_media 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [
            MediaData(
                id=str(row["id"]),
                user_id=user_id,
                filename=row["filename"],
                url=row["filepath"],
                content_type=row["content_type"],
                created_at=row["created_at"]
            )
            for row in rows
        ]
    
    async def get_media(self, media_id: str) -> Optional[MediaData]:
        """Get a specific media file by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, user_id, filename, filepath, content_type, created_at FROM user_media WHERE id = ?",
            (media_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return MediaData(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            filename=row["filename"],
            url=row["filepath"],
            content_type=row["content_type"],
            created_at=row["created_at"]
        )
