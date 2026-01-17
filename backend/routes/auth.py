"""
Authentication routes.
"""
import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks

from backend.config import DB_PATH
from backend.core.security import hash_password, verify_password, generate_token
from backend.core.dependencies import get_current_user
from backend.models.auth import (
    UserCredentials, UserRegistration, UserProfileUpdate, 
    PasswordChange, ForgotPasswordRequest, ResetPasswordRequest, SmtpConfig
)
from backend.services.auth_service import AuthService
from backend.services.email_service import EmailService

router = APIRouter()


@router.post("/register")
async def register(credentials: UserRegistration, background_tasks: BackgroundTasks):
    """Register a new user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (credentials.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email exists (if provided)
        if credentials.email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (credentials.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        password_hash = hash_password(credentials.password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)",
            (credentials.username, password_hash, credentials.email, datetime.now())
        )
        user_id = cursor.lastrowid
        
        # Create token
        token = generate_token()
        cursor.execute(
            "INSERT INTO user_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, datetime.now())
        )
        
        conn.commit()
        
        # Send Welcome Email
        if credentials.email:
            # We run this in background to not block the response
            background_tasks.add_task(EmailService.send_welcome_email, credentials.username, credentials.email)
        
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
        # Allow login by username OR email (if we wanted, but sticking to username for now based on request flow logic)
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
            "email": user.get("email"),  # Added email
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


# === User Profile Management ===

@router.post("/profile")
async def update_profile(data: UserProfileUpdate, user: Dict = Depends(get_current_user)):
    """Update user profile (email essentially)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check if email is taken by another user
        cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (data.email, user["id"]))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already in use")
        
        cursor.execute("UPDATE users SET email = ? WHERE id = ?", (data.email, user["id"]))
        conn.commit()
        return {"message": "Profile updated successfully"}
    finally:
        conn.close()


@router.post("/change-password")
async def change_password(data: PasswordChange, user: Dict = Depends(get_current_user)):
    """Change current user's password."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Verify current password
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        row = cursor.fetchone()
        if not verify_password(data.current_password, row[0]):
            raise HTTPException(status_code=400, detail="Incorrect current password")
        
        # Update password
        new_hash = hash_password(data.new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user["id"]))
        conn.commit()
        return {"message": "Password updated successfully"}
    finally:
        conn.close()


# === SMTP & Password Reset ===

@router.get("/smtp")
async def get_smtp_config(user: Dict = Depends(get_current_user)):
    """Get SMTP configuration."""
    config = EmailService.get_smtp_config()
    if not config:
        return {} # Return empty to indicate not set
    # Do not return real password for security? Or return it because it's the owner?
    # For now, we return it but frontend should mask it. 
    # Or better: return empty password and only update if user sends new one.
    # But for "edit" functionality users usually expect to see it or see "******".
    # We'll return it as is for simplicity in this MVP.
    return config


@router.post("/smtp")
async def save_smtp_config(config: SmtpConfig, user: Dict = Depends(get_current_user)):
    """Save SMTP configuration."""
    EmailService.save_smtp_config(config.dict())
    return {"message": "SMTP configuration saved"}


@router.post("/smtp/test")
async def test_smtp(data: Dict, user: Dict = Depends(get_current_user)):
    """Test SMTP configuration by sending an email."""
    to_email = data.get("to_email")
    if notto_email:
        raise HTTPException(status_code=400, detail="Target email required")
    
    success = EmailService.send_email(to_email, "SMTP Test", "This is a test email from Agentry.")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check server logs.")
    return {"message": "Test email sent"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Initiate password reset flow."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (data.email,))
        row = cursor.fetchone()
        if not row:
            # Don't reveal if user exists
             return {"message": "If the email is registered, you will receive a reset instructions."}
        
        # Generate generic token (6 digit code for simplicity?) 
        # Or a secure UUID. The requirement says "password reset code".
        # Let's use a 6-digit code for ease of typing if not clicking link.
        token = secrets.token_hex(3).upper() # 6 chars
        expires_at = datetime.now() + timedelta(minutes=15)
        
        cursor.execute(
            "INSERT OR REPLACE INTO password_resets (email, token, expires_at) VALUES (?, ?, ?)",
            (data.email, token, expires_at)
        )
        conn.commit()
        
        # Send Email
        background_tasks.add_task(EmailService.send_password_reset_email, data.email, token)
        
        return {"message": "If the email is registered, you will receive a reset instructions."}
    finally:
        conn.close()


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, background_tasks: BackgroundTasks):
    """Reset password using token."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Verify token
        cursor.execute(
            "SELECT email FROM password_resets WHERE email = ? AND token = ? AND expires_at > ?",
            (data.email, data.token, datetime.now())
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Get user
        cursor.execute("SELECT id, username FROM users WHERE email = ?", (data.email,))
        user_row = cursor.fetchone()
        if not user_row:
             raise HTTPException(status_code=400, detail="User not found")
        
        # Update Password
        new_hash = hash_password(data.new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_row[0]))
        
        # Delete token
        cursor.execute("DELETE FROM password_resets WHERE email = ?", (data.email,))
        
        conn.commit()
        
        # Send Confirmation Email
        background_tasks.add_task(EmailService.send_password_changed_email, user_row[1], data.email)
        
        return {"message": "Password successfully reset"}
    finally:
        conn.close()
