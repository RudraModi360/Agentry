import asyncio
import json
import base64
import os
import sqlite3
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Header
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Add parent directory to path
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from existing scratchy modules
from scratchy import Agent
from scratchy.session_manager import SessionManager
from scratchy.providers.ollama_provider import OllamaProvider
from scratchy.providers.groq_provider import GroqProvider
from scratchy.providers.gemini_provider import GeminiProvider
from scratchy.memory.storage import PersistentMemoryStore

# ============== FastAPI App ==============
app = FastAPI(
    title="Scratchy AI Agent",
    description="A powerful AI agent with tool capabilities",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
assets_dir = os.path.join(current_dir, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# ============== Database Setup ==============
DB_PATH = os.path.join(current_dir, "scratchy_users.db")

def init_users_db():
    """Initialize the users database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # User tokens (sessions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Provider API Keys (Stored separately per provider)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_api_keys (
            user_id INTEGER,
            provider TEXT NOT NULL,
            api_key_encrypted TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, provider),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Active User Settings (Current selection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_active_settings (
            user_id INTEGER PRIMARY KEY,
            provider TEXT NOT NULL,
            mode TEXT,
            model TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize DB on startup
init_users_db()

# ============== Data Models ==============
class UserCredentials(BaseModel):
    username: str
    password: str

class ProviderConfig(BaseModel):
    provider: str  # ollama, groq, gemini
    api_key: Optional[str] = None
    mode: Optional[str] = None  # For Ollama: 'local' or 'cloud'
    model: Optional[str] = None

class ChatMessage(BaseModel):
    content: str
    session_id: Optional[str] = "default"

# ============== In-Memory Agent Cache ==============
# Cache agents per user to avoid recreating them
agent_cache: Dict[int, Dict[str, Any]] = {}  # user_id -> {"agent": Agent, "config": {...}}

# ============== Helper Functions ==============
def hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = "scratchy_salt_2024"  # In production, use per-user salts
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def generate_token() -> str:
    return str(uuid.uuid4())

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

def get_current_active_settings(user_id: int) -> Optional[Dict]:
    """Get the currently active provider settings for a user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM user_active_settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def get_api_key(user_id: int, provider: str) -> Optional[str]:
    """Retrieves the stored API key for a specific provider."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT api_key_encrypted FROM user_api_keys WHERE user_id = ? AND provider = ?", (user_id, provider))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def save_active_settings(user_id: int, config: ProviderConfig):
    """Save active provider selection and update API key if provided."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 1. Update active settings
        cursor.execute("""
            INSERT INTO user_active_settings (user_id, provider, mode, model, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                provider = excluded.provider,
                mode = excluded.mode,
                model = excluded.model,
                updated_at = excluded.updated_at
        """, (user_id, config.provider, config.mode, config.model, datetime.now()))

        # 2. Update API Key only if a new one is provided
        if config.api_key:
            cursor.execute("""
                INSERT INTO user_api_keys (user_id, provider, api_key_encrypted, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, provider) DO UPDATE SET
                    api_key_encrypted = excluded.api_key_encrypted,
                    updated_at = excluded.updated_at
            """, (user_id, config.provider, config.api_key, datetime.now()))
        
        conn.commit()
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

# ============== Ollama Models ==============
OLLAMA_CLOUD_MODELS = [
    {"id": "gpt-oss:20b-cloud", "name": "GPT-OSS 20B Cloud", "description": "Cloud-based GPT model"},
    {"id": "glm-4.6:cloud", "name": "GLM 4.6 Cloud", "description": "GLM 4.6 Cloud model"},
    {"id": "minimax-m2:cloud", "name": "MiniMax M2 Cloud", "description": "MiniMax M2 Cloud model"},
    {"id": "qwen3-vl:235b-cloud", "name": "Qwen3 VL 235B Cloud", "description": "Qwen3 Vision-Language 235B Cloud"},
]

OLLAMA_LOCAL_SUGGESTED_MODELS = [
    {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "description": "Fast and efficient local model"},
    {"id": "llama3.1:8b", "name": "Llama 3.1 8B", "description": "Balanced performance local model"},
    {"id": "mistral:7b", "name": "Mistral 7B", "description": "Excellent reasoning capabilities"},
    {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B", "description": "Strong multilingual support"},
    {"id": "deepseek-coder:6.7b", "name": "DeepSeek Coder 6.7B", "description": "Optimized for coding tasks"},
    {"id": "phi3:mini", "name": "Phi-3 Mini", "description": "Microsoft's compact powerhouse"},
]

# ============== Groq Models ==============
GROQ_MODELS = [
    # Production Models
    {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "description": "Production - Most capable Llama model"},
    {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "description": "Production - Fast responses"},
    {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B", "description": "Production - OpenAI's flagship open-weight model"},
    {"id": "openai/gpt-oss-20b", "name": "GPT-OSS 20B", "description": "Production - Efficient GPT model"},
    {"id": "meta-llama/llama-guard-4-12b", "name": "Llama Guard 4 12B", "description": "Production - Safety guardrail model"},
    {"id": "whisper-large-v3", "name": "Whisper Large V3", "description": "Production - Speech-to-text"},
    {"id": "whisper-large-v3-turbo", "name": "Whisper Large V3 Turbo", "description": "Production - Fast speech-to-text"},
    # Preview Models
    {"id": "meta-llama/llama-4-maverick-17b-128e-instruct", "name": "Llama 4 Maverick 17B", "description": "Preview - Latest Llama 4 Maverick"},
    {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "name": "Llama 4 Scout 17B", "description": "Preview - Llama 4 Scout"},
    {"id": "moonshotai/kimi-k2-instruct-0905", "name": "Kimi K2", "description": "Preview - Moonshot AI Kimi K2"},
    {"id": "qwen/qwen3-32b", "name": "Qwen3 32B", "description": "Preview - Alibaba Qwen3"},
    {"id": "playai-tts", "name": "PlayAI TTS", "description": "Preview - Text-to-speech"},
    # Compound Systems
    {"id": "compound", "name": "Compound", "description": "System - AI with web search & code execution"},
    {"id": "compound-mini", "name": "Compound Mini", "description": "System - Lightweight compound model"},
]


# ============== Gemini Models ==============
GEMINI_MODELS = [
    # Latest Models
    {"id": "gemini-3.0-pro-preview", "name": "Gemini 3 Pro (Preview)", "description": "Best multimodal understanding, most powerful agentic model"},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "State-of-the-art thinking model for code, math, STEM"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "Best price-performance, great for agentic tasks"},
    {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash-Lite", "description": "Lightweight, cost-effective model"},
    # Previous Generation
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "description": "Workhorse model with 1M token context"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash-Lite", "description": "Lightweight 2.0 model"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "description": "Previous gen pro with 1M context"},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "description": "Previous gen fast model"},
    # Specialized
    {"id": "gemini-2.5-flash-preview-tts", "name": "Gemini 2.5 Flash TTS", "description": "Text-to-speech capabilities"},
    {"id": "text-embedding-004", "name": "Text Embedding 004", "description": "Text embedding model"},
]


# ============== API Endpoints ==============

# --- Static Pages ---
def safe_file_response(filename: str):
    """Return file if exists, otherwise return JSON placeholder."""
    filepath = os.path.join(current_dir, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    return JSONResponse({"message": f"UI file '{filename}' not yet created. API is working.", "file": filename})

@app.get("/")
async def landing_page():
    return safe_file_response("index.html")

@app.get("/login")
async def login_page():
    return safe_file_response("login.html")

@app.get("/chat")
async def chat_page():
    return safe_file_response("chat.html")

@app.get("/setup")
async def setup_page():
    return safe_file_response("setup.html")

# --- Authentication ---
@app.post("/api/auth/register")
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

@app.post("/api/auth/login")
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
        config = get_current_active_settings(user_id)
        needs_setup = config is None
        
        return {"token": token, "message": "Login successful", "needs_setup": needs_setup}
    finally:
        conn.close()

@app.post("/api/auth/logout")
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

@app.get("/api/auth/me")
async def get_current_user_info(user: Dict = Depends(get_current_user)):
    """Get current user information."""
    config = get_current_active_settings(user["id"])
    
    # Check if keys exist for providers (to show "Configured" status in UI)
    stored_keys = {}
    for prov in ["groq", "gemini", "ollama"]:
        key = get_api_key(user["id"], prov)
        if key:
            stored_keys[prov] = True
            
    # Get active key if config exists
    active_key = None
    if config:
        active_key = get_api_key(user["id"], config["provider"])

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
            "api_key": active_key  # Return loaded key to frontend so it can pre-fill
        } if config else None,
        "stored_keys": stored_keys
    }

# --- Provider Configuration ---
@app.get("/api/providers")
async def get_providers():
    """Get list of available providers."""
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "Local-first AI with optional cloud models",
                "requires_key": False,
                "has_modes": True,
                "modes": [
                    {"id": "local", "name": "Local Models", "description": "Run models on your machine"},
                    {"id": "cloud", "name": "Cloud Models", "description": "Use Ollama cloud (requires API key)"}
                ]
            },
            {
                "id": "groq",
                "name": "Groq",
                "description": "Ultra-fast inference with LPU technology",
                "requires_key": True,
                "has_modes": False
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "description": "Google's most capable AI models",
                "requires_key": True,
                "has_modes": False
            }
        ]
    }

@app.get("/api/models/{provider}")
async def get_models(provider: str, mode: Optional[str] = None, api_key: Optional[str] = None, user: Dict = Depends(get_current_user)):
    """Get available models for a provider."""
    
    # Try to get stored API key if not provided
    if not api_key:
        api_key = get_api_key(user["id"], provider)
    
    if provider == "ollama":
        if mode == "cloud":
            return {"models": OLLAMA_CLOUD_MODELS, "requires_key": True}
        else:
            # Try to fetch local models from Ollama
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        local_models = []
                        for m in data.get("models", []):
                            size_bytes = m.get("size", 0)
                            size_str = f"{size_bytes / (1024**3):.1f}GB" if size_bytes > 0 else "N/A"
                            local_models.append({
                                "id": m["name"],
                                "name": m["name"],
                                "description": f"Size: {size_str}"
                            })
                        if local_models:
                            return {"models": local_models, "requires_key": False}
            except Exception as e:
                print(f"Could not fetch local Ollama models: {e}")
            
            # Fallback to suggested models
            return {"models": OLLAMA_LOCAL_SUGGESTED_MODELS, "requires_key": False}
    
    elif provider == "groq":
        if not api_key:
            # Return predefined models list (user can still select, key required at configure time)
            return {
                "models": GROQ_MODELS, 
                "requires_key": True, 
                "message": "Showing suggested models. API key required to configure."
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [
                        {"id": m["id"], "name": m["id"], "description": m.get("owned_by", "Groq")}
                        for m in data.get("data", [])
                        if m.get("active", True)  # Only active models
                    ]
                    return {"models": models, "requires_key": True, "fetched": True}
                else:
                    # Return predefined on API error
                    return {"models": GROQ_MODELS, "requires_key": True, "message": "Could not verify key, showing default models"}
        except httpx.RequestError as e:
            # Return predefined on network error
            return {"models": GROQ_MODELS, "requires_key": True, "message": f"Network error: {str(e)}"}
    
    elif provider == "gemini":
        if not api_key:
            # Return predefined models list
            return {
                "models": GEMINI_MODELS, 
                "requires_key": True, 
                "message": "Showing suggested models. API key required to configure."
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [
                        {
                            "id": m["name"].replace("models/", ""),
                            "name": m.get("displayName", m["name"]),
                            "description": m.get("description", "")[:100]
                        }
                        for m in data.get("models", [])
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    return {"models": models, "requires_key": True, "fetched": True}
                else:
                    # Return predefined on API error
                    return {"models": GEMINI_MODELS, "requires_key": True, "message": "Could not verify key, showing default models"}
        except httpx.RequestError as e:
            # Return predefined on network error
            return {"models": GEMINI_MODELS, "requires_key": True, "message": f"Network error: {str(e)}"}
    
    raise HTTPException(status_code=400, detail="Unknown provider")

@app.post("/api/provider/configure")
async def configure_provider(config: ProviderConfig, user: Dict = Depends(get_current_user)):
    """Configure provider for a user."""
    user_id = user["id"]
    
    # 1. Resolve API Key
    # If not provided in request, try to load from storage
    final_api_key = config.api_key
    if not final_api_key:
        final_api_key = get_api_key(user_id, config.provider)
    
    # Update config object with resolved key (so it's saved correctly in cache)
    config.api_key = final_api_key

    # Set environment variables for the current process
    if config.provider == "groq" and final_api_key:
        os.environ["GROQ_API_KEY"] = final_api_key
    elif config.provider == "gemini" and final_api_key:
        os.environ["GOOGLE_API_KEY"] = final_api_key
        os.environ["GEMINI_API_KEY"] = final_api_key
    elif config.provider == "ollama" and config.mode == "cloud" and final_api_key:
        os.environ["OLLAMA_API_KEY"] = final_api_key
    
    # Validate by creating a provider instance
    try:
        if config.provider == "ollama":
            # Check requirements
            if config.mode == "cloud" and not final_api_key:
                 raise ValueError("Ollama Cloud requires an API Key.")
            provider = OllamaProvider(model_name=config.model or "llama3.2:3b")
            
        elif config.provider == "groq":
            if not final_api_key:
                raise ValueError("Groq requires an API Key.")
            provider = GroqProvider(model_name=config.model or "llama-3.3-70b-versatile", api_key=final_api_key)
            
        elif config.provider == "gemini":
            if not final_api_key:
                raise ValueError("Gemini requires an API Key.")
            provider = GeminiProvider(model_name=config.model or "gemini-2.0-flash", api_key=final_api_key)
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to initialize provider: {str(e)}")
    
    # Save configuration to database (Active settings + Key)
    save_active_settings(user_id, config)
    
    # Clear old agent from cache if exists
    if user_id in agent_cache:
        print(f"[Server] Clearing old agent cache for user {user_id}")
        del agent_cache[user_id]
    
    # Create agent and cache it
    try:
        agent = Agent(llm=provider, debug=True)
        agent.load_default_tools()
        
        agent_cache[user_id] = {
            "agent": agent,
            "config": config.dict(),
            "provider": provider
        }
        print(f"[Server] Agent cached for user {user_id} with model {config.model}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")
    
    return {"message": "Provider configured successfully", "model": config.model}

@app.get("/api/provider/current")
async def get_current_provider(user: Dict = Depends(get_current_user)):
    """Get current provider configuration."""
    config = get_user_provider_config(user["id"])
    if not config:
        return {"config": None}
    
    return {
        "config": {
            "provider": config["provider"],
            "mode": config["mode"],
            "model": config["model"]
        }
    }

@app.put("/api/provider/switch")
async def switch_provider(config: ProviderConfig, user: Dict = Depends(get_current_user)):
    """Switch to a different provider/model."""
    # Just reuse configure_provider
    return await configure_provider(config, user)

# --- Sessions ---
@app.get("/api/sessions")
async def get_sessions(user: Dict = Depends(get_current_user)):
    """Get all chat sessions for the user."""
    session_manager = SessionManager()
    sessions = session_manager.list_sessions()
    
    # Filter sessions by user (using session_id prefix)
    user_prefix = f"user_{user['id']}_"
    user_sessions = [
        {
            "id": s["session_id"],
            "title": s.get("title") or "New Chat",
            "created_at": s.get("created_at"),
            "updated_at": s.get("last_activity"),
            "message_count": s.get("message_count", 0)
        }
        for s in sessions
        if s["session_id"].startswith(user_prefix)
    ]
    
    return {"sessions": user_sessions}

@app.post("/api/sessions")
async def create_session(user: Dict = Depends(get_current_user)):
    """Create a new chat session."""
    session_id = f"user_{user['id']}_{uuid.uuid4().hex[:8]}"
    
    session_manager = SessionManager()
    session_manager.storage.create_session(session_id, metadata={"title": "New Chat", "user_id": user["id"]})
    
    return {
        "session": {
            "id": session_id,
            "title": "New Chat",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
    }

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, user: Dict = Depends(get_current_user)):
    """Get a specific session with messages."""
    # Verify session belongs to user
    user_prefix = f"user_{user['id']}_"
    if not session_id.startswith(user_prefix):
        raise HTTPException(status_code=403, detail="Access denied")
    
    session_manager = SessionManager()
    messages = session_manager.load_session(session_id)
    
    return {
        "session": {
            "id": session_id,
            "messages": messages or []
        }
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, user: Dict = Depends(get_current_user)):
    """Delete a chat session."""
    user_prefix = f"user_{user['id']}_"
    if not session_id.startswith(user_prefix):
        raise HTTPException(status_code=403, detail="Access denied")
    
    session_manager = SessionManager()
    session_manager.delete_session(session_id)
    
    return {"message": "Session deleted"}

async def generate_title(session_id: str, messages: List[Dict], provider: Any, session_manager: SessionManager):
    """Generate and save 3-5 word title for the session."""
    try:
        # User message is usually at index 1 (0 is system)
        if len(messages) < 2: 
            return
            
        # Get first user message content
        user_msg = messages[1].get("content", "")
        if isinstance(user_msg, list): # Multimodal
             for part in user_msg:
                 if isinstance(part, dict) and part.get("type") == "text":
                     user_msg = part.get("text", "")
                     break
        
        prompt = [
            {"role": "system", "content": "You are a helpful assistant. Generate a short, concise title (3-5 words) for the following conversation. Do not use quotes."},
            {"role": "user", "content": f"Summarize this query into a title:\n\n{user_msg}"}
        ]
        
        # Call provider directly
        # Note: Provider interfaces differ. Agent usually wraps this. 
        # But we pass simple text messages which all providers support.
        response = await provider.chat(prompt)
        
        title = "Untitled Chat"
        if isinstance(response, dict):
            title = response.get("content", "").strip('" ')
        else: # Object with content attribute (Groq/Gemini sometimes)
            title = getattr(response, "content", str(response)).strip('" ')
            
        if title:
             session_manager.update_session_title(session_id, title)
             
    except Exception as e:
        print(f"[Server] Title generation failed: {e}")

# --- WebSocket Chat ---
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    user = None
    agent = None
    
    try:
        # Wait for authentication message
        auth_data = await websocket.receive_json()
        token = auth_data.get("token")
        
        if not token:
            await websocket.send_json({"type": "error", "message": "Token required"})
            await websocket.close()
            return
        
        user = get_user_from_token(token)
        if not user:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close()
            return
        
        user_id = user["id"]
        
        # Get or create agent from cache
        if user_id in agent_cache:
            agent = agent_cache[user_id]["agent"]
        else:
            # Load config and create agent
            config = get_current_active_settings(user_id)
            if not config:
                await websocket.send_json({"type": "error", "message": "Provider not configured. Please complete setup."})
                await websocket.close()
                return
            
            try:
                # Retrieve API Key for the active provider
                provider_name = config["provider"]
                api_key = get_api_key(user_id, provider_name)
                
                # Restore API keys to environment (for process-level tools if any)
                if api_key:
                    if provider_name == "groq":
                        os.environ["GROQ_API_KEY"] = api_key
                    elif provider_name == "gemini":
                        os.environ["GOOGLE_API_KEY"] = api_key
                        os.environ["GEMINI_API_KEY"] = api_key
                    elif provider_name == "ollama":
                        os.environ["OLLAMA_API_KEY"] = api_key
                
                # Create provider
                if provider_name == "ollama":
                    provider = OllamaProvider(model_name=config["model"] or "llama3.2:3b")
                elif provider_name == "groq":
                    provider = GroqProvider(model_name=config["model"], api_key=api_key)
                elif provider_name == "gemini":
                    provider = GeminiProvider(model_name=config["model"], api_key=api_key)
                else:
                    raise ValueError(f"Unknown provider: {provider_name}")
                
                agent = Agent(llm=provider, debug=True)
                agent.load_default_tools()
                
                agent_cache[user_id] = {
                    "agent": agent,
                    "config": config,
                    "provider": provider
                }
            
            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"Failed to initialize agent: {str(e)}"})
                await websocket.close()
                return
        
        await websocket.send_json({"type": "connected", "message": "Connected to Scratchy"})
        
        session_manager = SessionManager()
        
        # Chat loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "message":
                content = data.get("content", "")
                session_id = data.get("session_id", f"user_{user_id}_default")
                is_edit = data.get("is_edit", False)
                edit_index = data.get("edit_index") # 0-based index of message to replace
                
                # Ensure session_id has user prefix
                if not session_id.startswith(f"user_{user_id}_"):
                    session_id = f"user_{user_id}_{session_id}"

                # Handle Editing Logic
                if is_edit and edit_index is not None:
                    session = agent.get_session(session_id)
                    # Safety check
                    if 0 <= edit_index < len(session.messages):
                         # Truncate history up to edit_index (exclusive of the message being replaced)
                         # Actually, we want to replace the user message at edit_index.
                         # So we keep everything BEFORE it.
                         session.messages = session.messages[:edit_index]
                         # The new content will be added by agent.chat() as a new user message
                         # This effectively "restarts" from that point.

                
                # Track connection state
                ws_connected = True
                
                # Define callbacks for streaming
                async def on_token(token_text: str):
                    nonlocal ws_connected
                    if not ws_connected:
                        return
                    try:
                        await websocket.send_json({
                            "type": "token",
                            "content": token_text
                        })
                    except Exception:
                        ws_connected = False
                
                async def on_tool_start(sess, name: str, args: dict):
                    nonlocal ws_connected
                    if not ws_connected:
                        return
                    try:
                        await websocket.send_json({
                            "type": "tool_start",
                            "tool_name": name,
                            "args": args
                        })
                    except Exception:
                        ws_connected = False
                
                async def on_tool_end(sess, name: str, result):
                    nonlocal ws_connected
                    if not ws_connected:
                        return
                    try:
                        await websocket.send_json({
                            "type": "tool_end",
                            "tool_name": name,
                            "result": str(result)[:500] if result else ""
                        })
                    except Exception:
                        ws_connected = False
                
                # Auto-approve tools for now (TODO: implement proper UI approval)
                async def on_tool_approval(sess, name: str, args: dict):
                    # For now, auto-approve all tools
                    # Later we can implement a WebSocket-based approval flow
                    return True
                
                # Set callbacks
                agent.set_callbacks(
                    on_token=on_token,
                    on_tool_start=on_tool_start,
                    on_tool_end=on_tool_end,
                    on_tool_approval=on_tool_approval
                )
                
                try:
                    # Run agent
                    response = await agent.chat(content, session_id=session_id)
                    
                    # Get updated messages and save
                    session = agent.get_session(session_id)
                    session_manager.save_session(session_id, session.messages)
                    
                    if ws_connected:
                        await websocket.send_json({
                            "type": "complete",
                            "content": response
                        })

                    # Check for Auto-Title Generation (in background)
                    if len(session.messages) >= 2 and len(session.messages) <= 5: 
                         asyncio.create_task(generate_title(session_id, session.messages, agent.provider, session_manager))


                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    if ws_connected:
                        try:
                            await websocket.send_json({
                                "type": "error",
                                "message": str(e)
                            })
                        except:
                            pass
            
            elif msg_type == "load_session":
                session_id = data.get("session_id")
                
                messages = session_manager.load_session(session_id)
                await websocket.send_json({
                        "type": "session_loaded",
                        "session_id": session_id,
                        "messages": messages or []
                    })
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"Client disconnected: {user['username'] if user else 'unknown'}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()

# --- Health Check ---
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============== Run Server ==============
if __name__ == "__main__":
    import uvicorn
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    Scratchy AI Agent                         ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:8000                    ║
║  API Docs: http://localhost:8000/docs                        ║
║  Landing Page: http://localhost:8000/                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
