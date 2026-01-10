# Agentry Backend API Reference
# ==============================

## Base URL
http://localhost:8000

## Authentication Endpoints (/api/auth/)

### Login
POST /api/auth/login
Content-Type: application/json

Body:
{
    "username": "Rudra",
    "password": "123456"
}

Response:
{
    "token": "abc123...",
    "message": "Login successful",
    "needs_setup": false
}

---

### Register
POST /api/auth/register
Content-Type: application/json

Body:
{
    "username": "NewUser",
    "password": "password123"
}

Response:
{
    "token": "abc123...",
    "message": "Registration successful",
    "needs_setup": true
}

---

### Logout
POST /api/auth/logout
Authorization: Bearer <token>

Response:
{
    "message": "Logged out successfully"
}

---

### Get Current User
GET /api/auth/me
Authorization: Bearer <token>

Response:
{
    "user": {...},
    "provider_configured": true,
    "provider_config": {...}
}

---

## Provider Endpoints (/api/provider/)

### Get Current Provider
GET /api/provider/current
Authorization: Bearer <token>

---

## Session Endpoints (/api/sessions/)

### List Sessions
GET /api/sessions
Authorization: Bearer <token>

### Create Session
POST /api/sessions
Authorization: Bearer <token>

### Get Session
GET /api/sessions/{session_id}
Authorization: Bearer <token>

### Delete Session
DELETE /api/sessions/{session_id}
Authorization: Bearer <token>

---

## Tool Endpoints (/api/tools/)

### List Tools
GET /api/tools
Authorization: Bearer <token>

### Get Disabled Tools
GET /api/tools/disabled
Authorization: Bearer <token>

---

## WebSocket Endpoint

### Chat WebSocket
WS ws://localhost:8000/ws/chat

Message format:
{
    "type": "auth",
    "token": "<bearer_token>"
}

{
    "type": "message", 
    "content": "Hi"
}

---

## HTML Pages (Browser Only - NOT for API testing)

- GET /           → Landing page
- GET /login      → Login HTML page
- GET /chat       → Chat HTML page  
- GET /setup      → Setup HTML page

NOTE: These return HTML, not JSON!
