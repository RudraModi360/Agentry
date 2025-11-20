# Docker Usage Guide

## Building the Image

```bash
docker build -t agentry:latest .
```

## Running the Container

### Interactive Mode (Recommended)
```bash
docker run -it --rm agentry:latest
```

### With Environment Variables
```bash
docker run -it --rm \
  -e GROQ_API_KEY=your_key_here \
  -e GEMINI_API_KEY=your_key_here \
  agentry:latest
```

### With .env File
```bash
docker run -it --rm \
  --env-file .env \
  agentry:latest
```

### With Ollama (Host Network)
If you're running Ollama on your host machine:
```bash
docker run -it --rm \
  --network host \
  agentry:latest
```

### With Volume Mount (for persistence)
```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  agentry:latest
```

## Docker Compose (Optional)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  agentry:
    build: .
    stdin_open: true
    tty: true
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    # Uncomment if using Ollama on host
    # network_mode: host
```

Run with:
```bash
docker-compose up
```

## Image Size Optimization

The Dockerfile uses:
- **Python 3.11-slim** base image (~120MB vs ~1GB for full Python)
- **uv** for fast dependency installation
- **Multi-layer caching** for faster rebuilds
- **Non-root user** for security

Expected final image size: ~400-500MB
