"""
Media library routes.
"""
import os
import sqlite3
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from backend.config import DB_PATH, UI_DIR
from backend.core.dependencies import get_current_user

router = APIRouter()


@router.get("")
async def get_user_media(user: Dict = Depends(get_current_user)):
    """Retrieve all media files uploaded by the user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, filename, filepath, content_type, created_at 
        FROM user_media 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    
    media = []
    for row in rows:
        media.append({
            "id": row[0],
            "filename": row[1],
            "url": row[2],
            "content_type": row[3],
            "created_at": row[4]
        })
    
    return {"media": media}


@router.delete("/{media_id}")
async def delete_user_media(media_id: int, user: Dict = Depends(get_current_user)):
    """Delete a media file by ID (only if owned by the user)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # First, get the media info to verify ownership and get file path
        cursor.execute("""
            SELECT id, filename, filepath, user_id 
            FROM user_media 
            WHERE id = ?
        """, (media_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Media not found")
        
        # Verify ownership
        if row[3] != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to delete this media")
        
        filename = row[1]
        filepath = os.path.join(UI_DIR, "media", filename)
        
        # Delete from database
        cursor.execute("DELETE FROM user_media WHERE id = ?", (media_id,))
        conn.commit()
        
        # Delete from disk
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"[Server] Deleted media file: {filepath}")
            except Exception as e:
                print(f"[Server] Warning: Could not delete file from disk: {e}")
        
        return {"success": True, "message": "Media deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Server] Error deleting media: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete media: {str(e)}")
    finally:
        conn.close()
