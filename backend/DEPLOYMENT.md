# Backend Deployment Guide

This directory contains the modular backend for Agentry AI Agent. It can be deployed separately from the frontend.

## Quick Start

### Local Development

```bash
# From project root
cd backend
python -m uvicorn backend.main:app --reload --port 8000
```

### Docker Deployment (Standalone Backend)

#### Build the Docker Image

```bash
# From the project root directory
docker build -f backend/Dockerfile -t agentry-backend:latest .
```

#### Run the Container

```bash
docker run -d \
  --name agentry-backend \
  -p 8000:8000 \
  -e PORT=8000 \
  -e CORS_ORIGINS="http://localhost:3000,https://your-frontend-domain.com" \
  -e OPENAI_API_KEY="your-key" \
  -e ANTHROPIC_API_KEY="your-key" \
  agentry-backend:latest
```

### Docker Compose Deployment

```bash
# From backend directory
cd backend

# Create .env file with your settings
cat > .env << EOF
PORT=8000
ENVIRONMENT=production
CORS_ORIGINS=http://localhost:3000
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
GOOGLE_API_KEY=your-google-key
EOF

# Start the backend
docker-compose up -d

# View logs
docker-compose logs -f
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port to run the server on | `8000` |
| `ENVIRONMENT` | Environment mode (development/production) | `production` |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:3000` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GROQ_API_KEY` | Groq API key | - |
| `GOOGLE_API_KEY` | Google AI API key | - |

## API Endpoints

### Health Check
- `GET /health` - Returns backend health status

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Chat & Sessions
- `GET /api/sessions` - List chat sessions
- `POST /api/sessions` - Create new session
- `WS /ws/chat` - WebSocket for real-time chat

### Providers
- `GET /api/providers` - List available providers
- `POST /api/provider/switch` - Switch active provider

## Architecture

```
backend/
├── Dockerfile           # Docker build file for standalone deployment
├── docker-compose.yml   # Docker Compose for easy local deployment
├── main.py              # FastAPI application entry point
├── config.py            # Configuration and settings
├── core/                # Core utilities
│   ├── database.py      # Database initialization and management
│   ├── dependencies.py  # FastAPI dependencies
│   └── security.py      # Security utilities
├── models/              # Pydantic models
├── routes/              # API route handlers
│   ├── auth.py          # Authentication routes
│   ├── providers.py     # Provider management
│   ├── sessions.py      # Chat session management
│   ├── websocket.py     # WebSocket handlers
│   └── ...
└── services/            # Business logic services
    ├── auth_service.py  # Authentication logic
    └── provider_service.py  # Provider operations
```

## Cloud Deployment

### Google Cloud Run

```bash
# Build and push to Google Container Registry
docker build -f backend/Dockerfile -t gcr.io/YOUR_PROJECT/agentry-backend:latest .
docker push gcr.io/YOUR_PROJECT/agentry-backend:latest

# Deploy to Cloud Run
gcloud run deploy agentry-backend \
  --image gcr.io/YOUR_PROJECT/agentry-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "CORS_ORIGINS=https://your-frontend.com"
```

### AWS ECS/Fargate

Build the image and push to ECR, then deploy using ECS task definitions.

### Azure Container Apps

Build and push to Azure Container Registry, then deploy as a Container App.

## Notes

- The backend requires the `scratchy` and `agentry` packages to be available
- Static files (CSS, JS, assets) can optionally be served from the backend or separately via a CDN
- The SQLite database is persisted in the `/app/ui` directory - use a volume mount for persistence
