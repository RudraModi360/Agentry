# 🚀 Deployment Guide: Frontend (Vercel) + Backend (Azure)

This guide explains how to deploy the Agentry application with the frontend on **Vercel** and the backend on **Azure**.

---

## 📋 Architecture Overview

```
┌─────────────────────┐          ┌─────────────────────────────┐
│   Vercel (Frontend) │  ─────►  │   Azure (Backend + API)     │
│   Static HTML/JS    │   HTTPS  │   FastAPI + WebSocket       │
│   ui/               │   WSS    │   backend/main.py           │
└─────────────────────┘          └─────────────────────────────┘
```

**Backend Module Structure:**
```
backend/
├── main.py              # Entry point
├── config.py            # Configuration
├── core/                # Database, security, dependencies
├── models/              # Pydantic schemas
├── services/            # Business logic
└── routes/              # API endpoints (modular)
```

---

## 🔧 Step 1: Prepare the Backend for Azure

### 1.1 Update CORS Settings

The backend already has CORS enabled (`allow_origins=["*"]`), but for production you should restrict it:

```python
# In backend/config.py, set the CORS_ORIGINS environment variable:
# Or modify the CORS_ORIGINS list directly:
CORS_ORIGINS = [
    "https://your-frontend.vercel.app",
    "https://your-custom-domain.com"
]
```

### 1.2 Build and Deploy to Azure

The existing `Dockerfile` is ready for Azure deployment:

```bash
# Build the Docker image
docker build -t agentry-backend:latest .

# Tag for Azure Container Registry (ACR)
docker tag agentry-backend:latest <your-acr>.azurecr.io/agentry-backend:latest

# Push to ACR
docker push <your-acr>.azurecr.io/agentry-backend:latest
```

Deploy to Azure Web App for Containers or Azure Container Apps.

---

## 🌐 Step 2: Deploy Frontend to Vercel

### 2.1 Frontend File Structure

The frontend is a static site located in the `ui/` directory:

```
ui/
├── index.html      # Landing page
├── login.html      # Login page
├── chat.html       # Main chat interface
├── setup.html      # Provider setup
├── css/            # Stylesheets
├── js/             # JavaScript modules
└── assets/         # Static assets
```

### 2.2 Configure the Backend URL

There are **two ways** to configure the backend URL:

#### Option A: Script Tag in HTML (Recommended for Static Hosting)

Add this script **before** loading `config.js` in your HTML files:

```html
<script>
    // Configure before loading the app
    window.AGENTRY_API_URL = 'https://your-backend.azurewebsites.net';
    // Optional: explicit WebSocket URL (auto-derived from API URL if not set)
    // window.AGENTRY_WS_URL = 'wss://your-backend.azurewebsites.net';
</script>
<script src="/js/config.js"></script>
```

#### Option B: Build-time Configuration

Create a build script that replaces the values:

```bash
# build.sh
sed -i "s|window.AGENTRY_API_URL || ''|'$BACKEND_URL'|g" ui/js/config.js
```

### 2.3 Vercel Project Setup

1. **Create a new Vercel project** pointing to your repository
2. **Set the Root Directory** to `ui/`
3. **Framework Preset**: Select "Other" (static HTML)
4. **Add Environment Variables** (if using build-time configuration):
   - `BACKEND_URL`: Your Azure backend URL

### 2.4 vercel.json Configuration

Create this file in the `ui/` directory:

```json
{
    "version": 2,
    "routes": [
        {
            "src": "/api/(.*)",
            "dest": "https://your-backend.azurewebsites.net/api/$1"
        },
        {
            "src": "/ws/(.*)",
            "dest": "https://your-backend.azurewebsites.net/ws/$1"
        },
        {
            "src": "/(.*)",
            "dest": "/$1"
        }
    ],
    "rewrites": [
        { "source": "/", "destination": "/index.html" },
        { "source": "/login", "destination": "/login.html" },
        { "source": "/chat", "destination": "/chat.html" },
        { "source": "/setup", "destination": "/setup.html" },
        { "source": "/orb", "destination": "/orb.html" }
    ]
}
```

---

## 📝 Step 3: Update HTML Files for Production

Add the configuration script to each HTML file that uses the API:

**Files to update:**
- `ui/chat.html`
- `ui/login.html`
- `ui/setup.html`
- `ui/orb.html`

Add this in the `<head>` section, **before** other scripts:

```html
<script>
    // PRODUCTION CONFIGURATION
    // Set your Azure backend URL here
    window.AGENTRY_API_URL = 'https://your-backend.azurewebsites.net';
</script>
```

---

## ✅ Step 4: Verification Checklist

After deployment, verify:

- [ ] Frontend loads at your Vercel URL
- [ ] Login/Register works and redirects properly
- [ ] WebSocket connects (check for "Connected" status)
- [ ] Chat messages are sent and received
- [ ] Provider setup saves correctly
- [ ] Images/media upload works

---

## 🔒 Security Considerations

1. **CORS**: Restrict `allow_origins` to your Vercel domain only
2. **HTTPS**: Ensure both frontend and backend use HTTPS
3. **WebSocket**: Use WSS (secure WebSockets)
4. **API Keys**: Never expose API keys in frontend code

---

## 🐛 Troubleshooting

### WebSocket Connection Fails
- Ensure Azure allows WebSocket connections
- Check that the WSS URL is correct
- Verify CORS allows WebSocket upgrades

### API Calls Fail with CORS Error
- Update `allow_origins` in `server.py`
- Ensure credentials are being handled correctly

### Static Files Not Found
- Verify `vercel.json` routing is correct
- Check that all paths are relative, not absolute

---

## 📚 Related Files

- `ui/js/config.js` - Central configuration
- `ui/js/utils/api.js` - API utilities
- `ui/js/components/websocket.js` - WebSocket handling
- `Dockerfile` - Backend container definition
- `.github/workflows/deploy.yml` - CI/CD pipeline
