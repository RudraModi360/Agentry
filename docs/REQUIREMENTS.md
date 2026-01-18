# Agentry Requirements Guide

A comprehensive list of all credentials, user-side requirements, and developer requirements for running Agentry.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Credentials & API Keys](#credentials--api-keys)
3. [Local Mode Requirements](#local-mode-requirements)
4. [Cloud Mode Requirements](#cloud-mode-requirements)
5. [Developer Requirements](#developer-requirements)
6. [Optional Features](#optional-features)

---

## System Requirements

### Minimum Hardware
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 4GB | 8GB+ |
| **CPU** | 2 cores | 4+ cores |
| **Storage** | 2GB free | 10GB+ (for models) |
| **GPU** | Not required | CUDA-compatible (for local LLMs) |

### Software Requirements
| Software | Version | Notes |
|----------|---------|-------|
| **Python** | ≥3.11 | Required |
| **Node.js** | ≥18.x | For MCP servers & frontend dev |
| **npm/npx** | Latest | For MCP tool servers |
| **Ollama** | Latest | For local embeddings & LLMs |
| **Docker** | Latest | Optional, for containerized deployment |
| **uv** | Latest | Recommended for dependency management |

---

## Credentials & API Keys

### 🔑 LLM Provider API Keys

At least **ONE** of the following is required based on your chosen provider:

| Provider | Environment Variable | How to Get |
|----------|---------------------|------------|
| **Groq** | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| **Google Gemini** | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | [makersuite.google.com](https://makersuite.google.com/app/apikey) |
| **Azure OpenAI** | `AZURE_API_KEY` + `AZURE_ENDPOINT` | Azure Portal |
| **OpenAI** | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| **Ollama** | None required | Local installation, no API key needed |

### 🔍 Optional: Google Custom Search

For web and image search functionality:

| Variable | Description | How to Get |
|----------|-------------|------------|
| `GOOGLE_API_KEY` | Google Cloud API Key | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |
| `GOOGLE_CX` | Custom Search Engine ID | [Programmable Search Engine](https://programmablesearchengine.google.com/) |

---

## Local Mode Requirements

**Mode:** `AGENTRY_MODE=local` (default)

### Required

| Component | Details |
|-----------|---------|
| **Python 3.11+** | Core runtime |
| **Ollama** | For embeddings (or switch to HuggingFace) |
| **LLM Provider Key** | At least one provider configured |

### Ollama Setup

```bash
# Install Ollama (Windows/Mac/Linux)
# Download from: https://ollama.ai

# Pull the embedding model
ollama pull qwen3-embedding:0.6b

# (Optional) Pull an LLM for local inference
ollama pull llama3.2
ollama pull gpt-oss:20b-cloud  # Requires access
```

### Environment Variables (Local Mode)

```bash
# .env file
AGENTRY_MODE=local

# LLM Provider (at least one)
GROQ_API_KEY=your_key_here
# OR
GEMINI_API_KEY=your_key_here
# OR
# No key needed for Ollama

# Embedding Configuration
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:0.6b
OLLAMA_URL=http://localhost:11434

# Optional
DEBUG=false
```

### Storage (Auto-created)

| Path | Purpose |
|------|---------|
| `./agentry/user_data/lancedb_data` | LanceDB vector storage |
| `./ui/scratchy_users.db` | SQLite user database |
| `./ui/media/` | Uploaded media files |

---

## Cloud Mode Requirements

**Mode:** `AGENTRY_MODE=cloud`

### Required Services

| Service | Purpose | Sign Up |
|---------|---------|---------|
| **Supabase** | Database & Auth | [supabase.com](https://supabase.com) |
| **Vercel Blob** | Media Storage (optional) | [vercel.com](https://vercel.com/storage/blob) |
| **Azure AKS** | Kubernetes (production) | [portal.azure.com](https://portal.azure.com) |

### Supabase Setup

1. Create a new Supabase project
2. Navigate to **Settings > API**
3. Copy the **Project URL** and **anon public key**
4. Run the schema setup:

```sql
-- Execute in Supabase SQL Editor
-- See: supabase_schema.sql in project root
```

### Environment Variables (Cloud Mode)

```bash
# .env file
AGENTRY_MODE=cloud

# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Vercel Blob (for media storage)
BLOB_READ_WRITE_TOKEN=vercel_blob_rw_xxxxx

# LLM Provider (at least one)
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Embedding (can use cloud LanceDB or local Ollama)
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:0.6b
OLLAMA_URL=http://ollama-service:11434  # K8s internal
# LANCEDB_PATH=s3://bucket/lancedb  # For cloud storage
```

### Kubernetes (Azure AKS) Deployment

| Variable | Description |
|----------|-------------|
| `ACR_REGISTRY` | Azure Container Registry URL (e.g., `agentryacr.azurecr.io`) |
| `AKS_CLUSTER` | AKS Cluster Name (e.g., `agentry-aks`) |
| `AKS_RESOURCE_GROUP` | Azure Resource Group (e.g., `agentry-rg`) |

---

## Developer Requirements

### Installation

```bash
# Clone the repository
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Install using uv (recommended)
uv sync

# OR install using pip
pip install -e .
```

### Running the Application

```bash
# Full stack (backend + frontend)
python agentry_runner.py
# OR
agentry_run

# Backend only (API server)
agentry_gui
# OR
python -m backend.main

# CLI/TUI only
agentry_cli
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up -d

# With frontend included
docker-compose --profile with-frontend up -d

# View logs
docker-compose logs -f backend
```

### Development Dependencies

All dependencies are managed via `pyproject.toml`:

| Category | Key Packages |
|----------|--------------|
| **Core** | `fastapi`, `uvicorn`, `pydantic` |
| **LLM Providers** | `groq`, `google-generativeai`, `anthropic`, `ollama` |
| **Memory/Vectors** | `lancedb`, `sentence-transformers`, `pyarrow` |
| **MCP** | `mcp>=1.22.0` |
| **Documents** | `pypdf`, `python-docx`, `python-pptx`, `openpyxl` |
| **Cloud** | `supabase>=2.0.0`, `httpx` |
| **UI** | `textual` (TUI), `rich` (console) |

---

## Optional Features

### 📧 SMTP (Email Sending)

For email functionality from within agents:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # Use App Password, not regular password
SMTP_FROM_EMAIL=Agentry <notifications@agentry.ai>
SMTP_USE_TLS=true
```

**Gmail Users:** Enable 2FA and create an [App Password](https://support.google.com/accounts/answer/185833).

### 🔧 MCP Tool Servers

For extended tool capabilities:

| Server | Command | Purpose |
|--------|---------|---------|
| **Excel** | `uvx excel-mcp-server stdio` | Excel file operations |
| **Computer Use** | `npx -y computer-use-mcp` | Screen control, clicking |

Configure in `mcp.json`:

```json
{
   "mcpServers": {
      "excel": {
         "command": "uvx",
         "args": ["excel-mcp-server", "stdio"]
      },
      "computer-use": {
         "command": "npx",
         "args": ["-y", "computer-use-mcp"]
      }
   }
}
```

### 🧠 SimpleMem (Context Engineering)

Fine-tune memory retrieval:

```bash
# Enable/disable
SIMPLEMEM_ENABLED=true

# Dialogue window for context
SIMPLEMEM_WINDOW_SIZE=6

# Number of memories to retrieve
SIMPLEMEM_TOP_K=5

# Parallel processing
SIMPLEMEM_PARALLEL=true
SIMPLEMEM_MAX_WORKERS=4
```

---

## Quick Reference: Environment Variable Checklist

### ✅ Minimum Requirements (Local Mode)

```bash
# Required: At least ONE LLM provider
GROQ_API_KEY=...        # Option 1
GEMINI_API_KEY=...      # Option 2
# Ollama                # Option 3 (no key needed)

# Embedding (Ollama must be running)
OLLAMA_URL=http://localhost:11434
```

### ✅ Full Production Setup (Cloud Mode)

```bash
AGENTRY_MODE=cloud
ENVIRONMENT=production
DEBUG=false

# LLM Provider
GROQ_API_KEY=...

# Cloud Services
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
BLOB_READ_WRITE_TOKEN=vercel_blob_rw_xxx

# Embedding
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:0.6b
OLLAMA_URL=http://ollama-service:11434

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...

# Search (optional)
GOOGLE_API_KEY=...
GOOGLE_CX=...
```

---

## Configuration Files Reference

| File | Purpose |
|------|---------|
| `.env` | Environment variables (secrets) |
| `agentry.toml` | Application configuration |
| `mcp.json` | MCP server definitions |
| `pyproject.toml` | Python dependencies |
| `docker-compose.yml` | Docker services |

**Priority:** Environment Variables > `agentry.toml` > Defaults

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `OLLAMA_URL connection refused` | Start Ollama: `ollama serve` |
| `Embedding model not found` | Pull model: `ollama pull qwen3-embedding:0.6b` |
| `SUPABASE_URL required` | Switch to local mode or configure Supabase |
| `API key not working` | Verify key is correct and has proper permissions |
| `MCP server failed` | Ensure Node.js/npm is installed |

### Health Checks

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check Backend
curl http://localhost:8000/health

# Check Frontend
curl http://localhost:3000
```

---

*Last updated: January 2026*
