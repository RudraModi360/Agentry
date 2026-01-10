# Agentry Backend API Documentation
## Complete Route Reference

**Base URL:** `http://localhost:8000`

---

## 📄 HTML Pages (Browser Only)

These routes return HTML pages for the web UI. **Do NOT use for API testing.**

| Route | Method | Description |
|-------|--------|-------------|
| `http://localhost:8000/` | GET | Landing/Home page |
| `http://localhost:8000/login` | GET | Login page |
| `http://localhost:8000/chat` | GET | Chat interface |
| `http://localhost:8000/setup` | GET | Provider setup page |
| `http://localhost:8000/orb` | GET | Orb visualization page |

---

## 🔐 Authentication (`/api/auth/`)

### Register New User
```
POST http://localhost:8000/api/auth/register
Content-Type: application/json

{
    "username": "NewUser",
    "password": "password123"
}
```

**Response (201):**
```json
{
    "token": "abc123-def456-...",
    "message": "Registration successful",
    "needs_setup": true
}
```

---

### Login
```
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
    "username": "Rudra",
    "password": "123456"
}
```

**Response (200):**
```json
{
    "token": "f0d16155-2c2c-49bd-8db7-de07db0d6b1c",
    "message": "Login successful",
    "needs_setup": false
}
```

**Error (401):**
```json
{
    "detail": "Invalid credentials"
}
```

---

### Logout
```
POST http://localhost:8000/api/auth/logout
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "message": "Logged out successfully"
}
```

---

### Get Current User Info
```
GET http://localhost:8000/api/auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "user": {
        "id": 1,
        "username": "Rudra",
        "created_at": "2024-01-01T00:00:00"
    },
    "provider_configured": true,
    "provider_config": {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "tools_enabled": true
    }
}
```

---

## 🔌 Provider Configuration (`/api/`)

### List Available Providers
```
GET http://localhost:8000/api/providers
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "providers": [
        {"id": "groq", "name": "Groq", "modes": ["cloud"]},
        {"id": "gemini", "name": "Google Gemini", "modes": ["cloud"]},
        {"id": "ollama", "name": "Ollama", "modes": ["local"]},
        {"id": "azure", "name": "Azure OpenAI", "modes": ["cloud"]}
    ]
}
```

---

### Get Models for a Provider
```
GET http://localhost:8000/api/providers/{provider}/models
Authorization: Bearer <token>
```

**Example:**
```
GET http://localhost:8000/api/providers/groq/models
```

---

### Configure Provider
```
POST http://localhost:8000/api/provider/configure
Authorization: Bearer <token>
Content-Type: application/json

{
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "api_key": "gsk_...",
    "mode": "cloud"
}
```

---

### Get Current Provider
```
GET http://localhost:8000/api/provider/current
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "mode": "cloud",
    "tools_enabled": true,
    "capabilities": {
        "tools": true,
        "vision": false,
        "streaming": true
    }
}
```

---

### Toggle Tools
```
POST http://localhost:8000/api/provider/tools?enabled=true
Authorization: Bearer <token>
```

---

### Get Model Capabilities
```
GET http://localhost:8000/api/capabilities/{provider}/{model}
Authorization: Bearer <token>
```

**Example:**
```
GET http://localhost:8000/api/capabilities/groq/llama-3.3-70b-versatile
```

---

## 💬 Sessions (`/api/sessions/`)

### List All Sessions
```
GET http://localhost:8000/api/sessions
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "sessions": [
        {
            "id": "user_1_abc123",
            "title": "Chat about AI",
            "created_at": "2024-01-01T00:00:00",
            "message_count": 5
        }
    ]
}
```

---

### Create New Session
```
POST http://localhost:8000/api/sessions
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "session": {
        "id": "user_1_def456",
        "title": "New Chat",
        "messages": []
    }
}
```

---

### Get Session Details
```
GET http://localhost:8000/api/sessions/{session_id}
Authorization: Bearer <token>
```

---

### Search Sessions
```
GET http://localhost:8000/api/sessions/search?q=AI
Authorization: Bearer <token>
```

---

### Delete Session
```
DELETE http://localhost:8000/api/sessions/{session_id}
Authorization: Bearer <token>
```

---

## 🛠️ Tools (`/api/tools/`)

### Get Available Tools
```
GET http://localhost:8000/api/tools
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "tools": [
        {"name": "datetime", "description": "Get current date and time"},
        {"name": "web_search", "description": "Search the web"},
        {"name": "notes", "description": "Create and manage notes"}
    ]
}
```

---

### Get Disabled Tools
```
GET http://localhost:8000/api/tools/disabled
Authorization: Bearer <token>
```

---

### Save Disabled Tools
```
POST http://localhost:8000/api/tools/disabled
Authorization: Bearer <token>
Content-Type: application/json

{
    "disabled_tools": ["web_search", "bash"]
}
```

---

## 🤖 Agent Configuration (`/api/`)

### Get Agent Types
```
GET http://localhost:8000/api/agent/types
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "types": [
        {
            "id": "smart",
            "name": "Smart Agent",
            "description": "Autonomous agent with tool use"
        },
        {
            "id": "chat",
            "name": "Chat Agent", 
            "description": "Simple conversational agent"
        }
    ]
}
```

---

### Configure Agent Type
```
POST http://localhost:8000/api/agent/configure
Authorization: Bearer <token>
Content-Type: application/json

{
    "agent_type": "smart",
    "mode": "solo"
}
```

---

### Get Agent Config
```
GET http://localhost:8000/api/agent/config
Authorization: Bearer <token>
```

---

## 📁 Projects (`/api/`)

### List Projects
```
GET http://localhost:8000/api/projects
Authorization: Bearer <token>
```

### Create Project
```
POST http://localhost:8000/api/projects
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "My Project",
    "path": "/path/to/project"
}
```

---

## 🧠 Memory (`/api/`)

### Get Memories
```
GET http://localhost:8000/api/memory?limit=50
Authorization: Bearer <token>
```

### Add Memory
```
POST http://localhost:8000/api/memory
Authorization: Bearer <token>
Content-Type: application/json

{
    "content": "Remember this fact",
    "memory_type": "user_preference"
}
```

### Search Memories
```
GET http://localhost:8000/api/memory/search?q=fact
Authorization: Bearer <token>
```

---

## 🔗 MCP (Model Context Protocol) (`/api/mcp/`)

### Get MCP Config
```
GET http://localhost:8000/api/mcp/config
Authorization: Bearer <token>
```

### Save MCP Config
```
POST http://localhost:8000/api/mcp/config
Authorization: Bearer <token>
Content-Type: application/json

{
    "config": {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@anthropic/mcp-server-filesystem"]
            }
        }
    }
}
```

### Get MCP Status
```
GET http://localhost:8000/api/mcp/status
Authorization: Bearer <token>
```

---

## 🌐 WebSocket (`/ws/`)

### Chat WebSocket
```
WS ws://localhost:8000/ws/chat
```

**Authentication Message:**
```json
{
    "type": "auth",
    "token": "f0d16155-2c2c-49bd-8db7-de07db0d6b1c"
}
```

**Send Message:**
```json
{
    "type": "message",
    "content": "Hello, how are you?",
    "session_id": "user_1_abc123"
}
```

**Response Stream:**
```json
{"type": "chunk", "content": "Hello"}
{"type": "chunk", "content": "! I'm"}
{"type": "chunk", "content": " doing well."}
{"type": "stream_end"}
```

---

## 📎 Media (`/api/media/`)

### Upload File
```
POST http://localhost:8000/api/media/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
```

---

## 🧪 Quick Test with PowerShell

### Test Login
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"Rudra","password":"123456"}'
```

### Test with Token
```powershell
$token = "your-token-here"
Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method GET -Headers @{Authorization="Bearer $token"}
```

---

## ⚠️ Common Errors

| Status | Meaning | Solution |
|--------|---------|----------|
| 401 | Unauthorized | Check token or credentials |
| 404 | Not Found | Check URL path |
| 405 | Method Not Allowed | Use correct HTTP method (POST vs GET) |
| 422 | Validation Error | Check request body format |

---

## 📝 Notes

1. **All API endpoints** require `/api/` prefix
2. **HTML pages** (/, /login, /chat) are for browser only
3. **Authorization header** format: `Bearer <token>`
4. **Content-Type** for POST requests: `application/json`
