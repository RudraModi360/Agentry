# Quick Reference Guide

Quick commands and tips for working with Agentry.

## 🚀 Installation & Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and setup
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry
uv venv .venv
uv sync

# Setup environment (optional for cloud providers)
cp .env.example .env
# Edit .env with your API keys
```

## 🎮 Running the Agent

```bash
# Basic run
python src/main.py

# With uv (auto-manages environment)
uv run python src/main.py

# Activate venv first (optional)
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
python src/main.py
```

## 🦙 Ollama Commands

### Cloud Models (Recommended - No Download Required!)

```bash
# Install Ollama client (one-time setup)
# Windows: Download from ollama.com/download
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# Use cloud models immediately (no pull needed!)
# Just run the agent and enter one of these models:
# - gpt-oss:20b-cloud      (20B, fast & capable)
# - gpt-oss:120b-cloud     (120B, most powerful)
# - glm-4.6:cloud          (GLM-4.6)
# - minimax-m2:cloud       (MiniMax M2)

# Example usage:
python src/main.py
# Select: 1. Ollama
# Enter model: gpt-oss:20b-cloud
# Start chatting immediately! ✨
```

### Local Models (For Offline Use)

```bash
# Pull models (REQUIRED before first use)
ollama pull llama3.1        # Recommended (4.7GB)
ollama pull llama3.2        # Latest (4.7GB)
ollama pull mistral-nemo    # Alternative (7.1GB)
ollama pull qwen2.5         # Another option (4.7GB)

# List installed models
ollama list

# Remove a model
ollama rm model-name

# Check Ollama status
ollama --version

# Start Ollama service manually (if needed)
ollama serve
```

## 🐳 Docker Commands

```bash
# Build image
docker build -t agentry:latest .

# Run interactively
docker run -it --rm agentry:latest

# With API keys
docker run -it --rm \
  -e GROQ_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  agentry:latest

# With Ollama (host network)
docker run -it --rm --network host agentry:latest

# With environment file
docker run -it --rm --env-file .env agentry:latest

# With volume mount
docker run -it --rm -v $(pwd)/data:/app/data agentry:latest
```

## 📦 Dependency Management

```bash
# Add a package
uv add package-name

# Add dev dependency
uv add --dev package-name

# Remove a package
uv remove package-name

# Update all packages
uv update

# Sync environment with lock file
uv sync

# Show dependency tree
uv tree
```

## 🧪 Testing & Quality

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src tests/

# Run specific test
uv run pytest tests/tools/test_web.py

# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Fix linting issues
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/
```

## 🔧 Development

```bash
# Create new branch
git checkout -b feature/my-feature

# Install dev dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff black mypy

# Run in debug mode
python src/main.py --debug  # (if implemented)

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +  # macOS/Linux
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force  # Windows
```

## 🌐 Git Commands

```bash
# Initial setup
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/RudraModi360/Agentry.git
git push -u origin main

# Regular workflow
git add .
git commit -m "feat: add new feature"
git push

# Create PR
git checkout -b feature/my-feature
# Make changes
git add .
git commit -m "feat: implement feature"
git push origin feature/my-feature
# Then create PR on GitHub
```

## 🔑 Environment Variables

```bash
# Create .env file
cp .env.example .env

# Required for cloud providers
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=...

# Optional
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
MAX_ITERATIONS=20
```

## 📊 Monitoring & Logs

```bash
# View Docker logs
docker logs container-name

# Follow logs
docker logs -f container-name

# View last 100 lines
docker logs --tail 100 container-name

# Check running containers
docker ps

# Check all containers
docker ps -a
```

## 🚨 Troubleshooting

```bash
# Ollama not responding
ollama serve  # Start Ollama service manually

# Model not found
ollama pull model-name  # Download the model

# Port already in use (Ollama)
lsof -i :11434  # macOS/Linux - find process
netstat -ano | findstr :11434  # Windows - find process

# Clear Docker cache
docker system prune -a

# Reinstall dependencies
rm -rf .venv
uv venv .venv
uv sync

# Check Python version
python --version  # Should be 3.11+
```

## 🎯 Common Workflows

### First Time Setup
```bash
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry
uv venv .venv
uv sync
python src/main.py
# Select: 1. Ollama
# Enter model: gpt-oss:20b-cloud
# Start chatting! No downloads needed! 🎉
```

### Daily Development
```bash
git pull origin main
uv sync  # Update dependencies if needed
python src/main.py
```

### Adding a New Tool
```bash
# 1. Create tool file
touch src/tools/my_tool.py

# 2. Implement tool (see CONTRIBUTING.md)

# 3. Register in registry.py

# 4. Write tests
touch tests/tools/test_my_tool.py

# 5. Run tests
uv run pytest tests/tools/test_my_tool.py

# 6. Commit
git add .
git commit -m "feat(tools): add my_tool"
git push
```

### Deploying to Cloud
```bash
# 1. Setup secrets in GitHub
# Settings → Secrets → Actions → New secret

# 2. Push to main
git push origin main

# 3. Check Actions tab for deployment status

# 4. View logs in cloud console
```

## 📱 Useful Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
# Agentry shortcuts
alias ag='uv run python src/main.py'
alias agtest='uv run pytest'
alias aglint='uv run ruff check src/ && uv run black --check src/'
alias agfix='uv run ruff check --fix src/ && uv run black src/'
```

## 🔗 Quick Links

- **Documentation**: [README.md](README.md)
- **Docker Guide**: [DOCKER.md](DOCKER.md)
- **CI/CD Guide**: [CICD.md](CICD.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Issues**: https://github.com/RudraModi360/Agentry/issues
- **Discussions**: https://github.com/RudraModi360/Agentry/discussions

## 💡 Pro Tips

1. **Use `uv run`** for one-off commands without activating venv
2. **Pull Ollama models in advance** to avoid waiting during first use
3. **Use `--help` flag** on most commands for more options
4. **Check Actions tab** on GitHub to see CI/CD status
5. **Use Docker** for consistent environments across machines
6. **Enable GitHub Copilot** for faster development
7. **Star the repo** to stay updated with releases

---

**Need more help?** Check the full [README.md](README.md) or open an [issue](https://github.com/RudraModi360/Agentry/issues).
