"""
FastAPI dependencies for authentication and common operations.
"""
import sqlite3
from typing import Dict, Optional
from fastapi import Header, HTTPException

from backend.config import DB_PATH

__all__ = ["get_current_user", "get_user_from_token"]


def get_user_from_token(token: str) -> Optional[Dict]:
    """Get user info from token."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.id, u.username, u.created_at 
            FROM users u
            JOIN user_tokens t ON u.id = t.user_id
            WHERE t.token = ?
        """, (token,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """Dependency to get current authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user
