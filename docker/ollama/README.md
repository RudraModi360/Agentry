# Ollama Embedding Service for Agentry

This container runs Ollama with the `qwen3-embedding:0.6b` model pre-loaded for SimpleMem context engineering.

## Build

```bash
docker build -t agentry-ollama:latest .
```

## Run Locally

```bash
# Run with persistent model storage
docker run -d \
  --name agentry-ollama \
  -p 11434:11434 \
  -v ollama-models:/root/.ollama \
  agentry-ollama:latest
```

## Verify

```bash
# Check if running
curl http://localhost:11434/api/tags

# Test embedding
curl http://localhost:11434/api/embeddings \
  -d '{"model": "qwen3-embedding:0.6b", "prompt": "Hello world"}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `0.0.0.0:11434` | Ollama server bind address |
| `OLLAMA_MODELS` | `/root/.ollama/models` | Model storage path |

## Kubernetes

The Kubernetes deployment is in `kubernetes/base/ollama-deployment.yaml`.

For AKS deployment, the backend connects to Ollama via:
```
OLLAMA_URL=http://ollama-service:11434
```

## Adding More Models

To add additional models, modify the Dockerfile:

```dockerfile
RUN echo '...\n\
ollama pull qwen3-embedding:0.6b\n\
ollama pull llama3.2:3b\n\  # Add more models
...' > /start.sh
```

## CPU vs GPU

This container runs in CPU mode by default. For GPU support:

```bash
# NVIDIA GPU
docker run -d \
  --gpus all \
  -p 11434:11434 \
  -v ollama-models:/root/.ollama \
  agentry-ollama:latest
```

For Kubernetes GPU, add to the deployment:
```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```
