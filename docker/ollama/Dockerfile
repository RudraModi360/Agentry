# Ollama Container for Agentry Embedding Service
# Pre-loads the embedding model on startup

FROM ollama/ollama:latest

# Set environment variables
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_MODELS=/root/.ollama/models

# Create models directory
RUN mkdir -p /root/.ollama/models

# Create startup script that pulls the model
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Ollama server..."\n\
ollama serve &\n\
SERVER_PID=$!\n\
\n\
# Wait for server to be ready\n\
echo "Waiting for Ollama to be ready..."\n\
sleep 10\n\
\n\
# Pull embedding model\n\
echo "Pulling qwen3-embedding:0.6b model..."\n\
ollama pull qwen3-embedding:0.6b\n\
\n\
echo "Ollama ready with embedding model!"\n\
\n\
# Keep the server running\n\
wait $SERVER_PID\n\
' > /start.sh && chmod +x /start.sh

# Expose Ollama port
EXPOSE 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Run startup script
CMD ["/start.sh"]
