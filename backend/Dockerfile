# Backend-only Dockerfile for separate deployment
# Use Python 3.11 slim image for minimal footprint
FROM python:3.11-slim

# Build arguments for configuration
ARG PORT=8000
ARG ENV=production

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PORT=${PORT} \
    ENVIRONMENT=${ENV}

# Install system dependencies (if needed for certain Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (for better layer caching)
# Note: When building from project root, use context path
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv sync --frozen --no-cache

# Copy core packages needed by backend
COPY scratchy/ ./scratchy/
COPY agentry/ ./agentry/

# Copy the backend module
COPY backend/ ./backend/

# Copy UI assets needed for static file serving (optional)
# Comment out if UI is served separately
COPY ui/assets/ ./ui/assets/
COPY ui/css/ ./ui/css/
COPY ui/js/ ./ui/js/

# Create media directory for uploads
RUN mkdir -p ./ui/media

# Create a non-root user for security
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /app

# Switch to non-root user
USER agent

# Expose the port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Set the entrypoint - run the modular backend with configurable port
ENTRYPOINT ["sh", "-c", "uv run uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
