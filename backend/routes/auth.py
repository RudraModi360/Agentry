"""
Authentication routes.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.config import DB_PATH
from backend.core.security import hash_password, verify_password, generate_token
from backend.core.dependencies import get_current_user
from backend.models.auth import UserCredentials
from backend.services.auth_service import AuthService

router = APIRouter()


@router.post("/register")
async def register(credentials: UserCredentials):
    """Register a new user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (credentials.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user
        password_hash = hash_password(credentials.password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (credentials.username, password_hash, datetime.now())
        )
        user_id = cursor.lastrowid
        
        # Create token
        token = generate_token()
        cursor.execute(
            "INSERT INTO user_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, datetime.now())
        )
        
        conn.commit()
        return {"token": token, "message": "Registration successful", "needs_setup": True}
    finally:
        conn.close()


@router.post("/login")
async def login(credentials: UserCredentials):
    """Login an existing user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (credentials.username,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(credentials.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_id = row["id"]
        
        # Update last login
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user_id))
        
        # Create new token
        token = generate_token()
        cursor.execute(
            "INSERT INTO user_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, datetime.now())
        )
        
        conn.commit()
        
        # Check if provider is configured
        config = AuthService.get_current_active_settings(user_id)
        needs_setup = config is None
        
        return {"token": token, "message": "Login successful", "needs_setup": needs_setup}
    finally:
        conn.close()


@router.post("/logout")
async def logout(user: Dict = Depends(get_current_user), authorization: Optional[str] = Header(None)):
    """Logout the current user."""
    token = authorization.replace("Bearer ", "") if authorization else None
    if token:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_tokens WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(user: Dict = Depends(get_current_user)):
    """Get current user information."""
    from backend.routes.agents import get_agent_config
    
    config = AuthService.get_current_active_settings(user["id"])
    
    # Check if keys exist for providers (to show "Configured" status in UI)
    stored_keys = {}
    for prov in ["groq", "gemini", "ollama", "azure"]:
        key = AuthService.get_api_key(user["id"], prov)
        if key:
            stored_keys[prov] = key
            
    # Get active key/endpoint if config exists
    active_key = None
    active_endpoint = None
    if config:
        active_key = AuthService.get_api_key(user["id"], config["provider"])
        active_endpoint = AuthService.get_provider_endpoint(user["id"], config["provider"])

    # Get agent config
    agent_config = await get_agent_config(user)
    agent_type = agent_config.get("agent_type", "default")

    # Force tools_enabled to True for Smart Agent in the response
    tools_enabled = True
    if agent_type != "smart":
        tools_enabled = bool(config["tools_enabled"]) if (config and "tools_enabled" in config) else True

    return {
        "user": {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"]
        },
        "provider_configured": config is not None,
        "provider_config": {
            "provider": config["provider"] if config else None,
            "mode": config["mode"] if config else None,
            "model": config["model"] if config else None,
            "api_key": active_key,
            "endpoint": active_endpoint,
            "tools_enabled": tools_enabled,
            "agent_type": agent_type,
            "agent_mode": agent_config.get("mode"),
            "project_id": agent_config.get("project_id")
        } if config else None,
        "stored_keys": stored_keys
    }
