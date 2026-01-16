---
layout: page
title: Deployment Guide
nav_order: 11
description: "Guide for deploying Agentry in production environments"
---

# Deployment Guide

Guide for deploying Agentry in production environments.

## Table of Contents

1. [Overview](#overview)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Environment Variables](#environment-variables)
5. [Process Management](#process-management)
6. [Database Configuration](#database-configuration)
7. [Security Considerations](#security-considerations)
8. [Monitoring](#monitoring)
9. [Scaling](#scaling)
10. [Backup](#backup)
11. [Troubleshooting Deployment](#troubleshooting-deployment)

---

## Overview

Agentry can be deployed in several configurations:

| Deployment Type | Use Case | Complexity |
|:----------------|:---------|:-----------|
| Local Development | Testing and development | Low |
| Docker Container | Isolated deployment | Medium |
| Production Server | Full production deployment | High |

---

## Local Development

### Backend Server

```bash
# Navigate to project directory
cd Agentry

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Start backend
python -m backend.main
```

The backend will be available at `http://localhost:8000`.

### Frontend Server (Optional)

For development with hot reload:

```bash
cd ui
npm install
npm run dev
```

Frontend available at `http://localhost:3000`.

---

## Docker Deployment

### Building the Docker Image

```bash
# Build the image
docker build -t agentry:latest .

# Run the container
docker run -p 8000:8000 agentry:latest
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  agentry:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
```

Run with:

```bash
docker-compose up -d
```

---

## Environment Variables

| Variable | Description | Required |
|:---------|:------------|:---------|
| `GROQ_API_KEY` | Groq API key | For Groq provider |
| `GEMINI_API_KEY` | Gemini API key | For Gemini provider |
| `AZURE_API_KEY` | Azure OpenAI API key | For Azure provider |
| `AZURE_ENDPOINT` | Azure OpenAI endpoint | For Azure provider |
| `OLLAMA_HOST` | Ollama server URL | Optional (default: localhost:11434) |

---

## Production Configuration

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL Configuration

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Process Management

### Using systemd (Linux)

Create `/etc/systemd/system/agentry.service`:

```ini
[Unit]
Description=Agentry AI Agent Framework
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Agentry
Environment="PATH=/path/to/Agentry/.venv/bin"
ExecStart=/path/to/Agentry/.venv/bin/python -m backend.main
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable agentry
sudo systemctl start agentry
```

### Using PM2 (Node.js)

```bash
pm2 start "python -m backend.main" --name agentry
pm2 save
pm2 startup
```

---

## Database Configuration

Agentry uses SQLite by default. For production:

### SQLite (Default)

```bash
# Database location
./agentry_users.db
./agentry_sessions.db
```

### PostgreSQL (Production)

Update configuration in `backend/config.py`:

```python
DATABASE_URL = "postgresql://user:password@localhost/agentry"
```

---

## Security Considerations

| Area | Recommendation |
|:-----|:---------------|
| **API Keys** | Store in environment variables, never in code |
| **CORS** | Configure allowed origins for production |
| **Authentication** | Enable user authentication for production |
| **HTTPS** | Always use SSL/TLS in production |
| **Rate Limiting** | Implement rate limiting for API endpoints |

---

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

### Logging

Configure logging in `backend/config.py`:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/agentry/app.log',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file'],
    },
}
```

---

## Scaling

### Horizontal Scaling

Use a load balancer with multiple instances:

```yaml
# docker-compose.yml
version: '3.8'

services:
  agentry:
    build: .
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"

  nginx:
    image: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Caching

Implement Redis for session caching:

```python
CACHE_URL = "redis://localhost:6379/0"
```

---

## Backup

### Database Backup

```bash
# SQLite backup
sqlite3 agentry_users.db ".backup '/backups/agentry_users_$(date +%Y%m%d).db'"

# PostgreSQL backup
pg_dump agentry > /backups/agentry_$(date +%Y%m%d).sql
```

### Session Data Backup

```bash
tar -czf /backups/sessions_$(date +%Y%m%d).tar.gz ./agentry/session_history/
```

---

## Troubleshooting Deployment

### Common Issues

| Issue | Solution |
|:------|:---------|
| Port already in use | Change port or stop conflicting service |
| Permission denied | Check file permissions and user ownership |
| Database locked | Ensure only one process accesses SQLite |
| WebSocket not connecting | Check proxy configuration for upgrades |

### Debug Mode

Enable debug mode for troubleshooting:

```bash
export DEBUG=true
python -m backend.main
```

---

## Next Steps

| Topic | Description |
|:------|:------------|
| [Getting Started](getting-started) | Basic setup |
| [API Reference](api-reference) | API documentation |
| [Troubleshooting](troubleshooting) | Common issues |
