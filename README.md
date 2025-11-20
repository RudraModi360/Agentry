# Agentry

**A modular AI agent framework built from scratch in Python, designed to evolve into a real-time voice-driven assistant for task automation.**

[![CI/CD Pipeline](src/artifacts/image-removebg-preview%20(1).png)](https://github.com/RudraModi360/Agentry/actions)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Features

- 🔌 **Multi-Provider Support** - Seamlessly switch between Ollama, Groq, and Google Gemini
- 🛠️ **Extensible Tool System** - Built-in tools for web search, file operations, and code execution
- 🔒 **Safety Controls** - Approval workflows for dangerous operations
- 🐳 **Docker Ready** - Optimized containerization with Python 3.11-slim
- ⚡ **Fast Development** - Powered by `uv` for lightning-fast dependency management
- 🎯 **Production Architecture** - Clean, modular design with provider abstraction
- 🚀 **CI/CD Ready** - Automated testing and deployment to multiple cloud platforms

---

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [API Setup Guide](docs/API_SETUP.md) - **Detailed provider configuration**
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Available Tools](#-available-tools)
- [Configuration](#-configuration)
- [Docker Deployment](#-docker-deployment)
- [Development](#-development)
- [Architecture](#-architecture)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔧 Prerequisites

### Required

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **uv** - Fast Python package installer
  ```bash
  # Windows (PowerShell)
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Provider Setup (Choose One or More)

#### 🌟 Option 1: Ollama Cloud Models (Recommended - FREE!)

**Ollama now offers FREE cloud-hosted models** - no local installation required! This is the easiest way to get started.

**✨ Tested & Verified Cloud Models:**
- `gpt-oss:20b-cloud` - 20B parameter model (fast & capable)
- `gpt-oss:120b-cloud` - 120B parameter model (most powerful)
- `glm-4.6:cloud` - GLM-4.6 cloud model
- `minimax-m2:cloud` - MiniMax M2 cloud model

**Setup Steps:**

1. **Install Ollama** (just the client, no models needed!)
   - **Windows**: Download from [ollama.com/download](https://ollama.com/download)
   - **macOS**: 
     ```bash
     brew install ollama
     ```
   - **Linux**:
     ```bash
     curl -fsSL https://ollama.com/install.sh | sh
     ```

2. **No API Key Required!** Just run the agent and select Ollama
   ```bash
   python src/main.py
   # Select: 1. Ollama
   # Enter model: gpt-oss:20b-cloud  (or any cloud model)
   ```

3. **That's it!** Cloud models work immediately without downloading anything.

**💡 Pro Tip:** Cloud models (ending in `:cloud`) don't need to be pulled first - they run instantly!

---

#### 🏠 Option 2: Ollama Local Models (Free, Runs Offline)

For running models locally on your machine (requires download):

1. **Install Ollama** (same as above)

2. **Pull a Local Model** (Required before first use)
   ```bash
   # Recommended models with tool-calling support:
   ollama pull llama3.1        # 8B model (4.7GB download)
   ollama pull llama3.2        # Latest version (4.7GB)
   ollama pull mistral-nemo    # Alternative (7.1GB)
   ollama pull qwen2.5         # Another great option (4.7GB)
   ```

3. **Verify Installation**
   ```bash
   ollama list  # Should show your downloaded models
   ```

**⚠️ Important:** Only models with tool-calling support will work properly!

---

#### ⚡ Option 3: Groq (Cloud API - Fast Inference)

Groq provides blazing-fast inference with generous free tier.

**Setup Steps:**

1. **Get API Key**
   - Visit [console.groq.com](https://console.groq.com)
   - Sign up for free account
   - Navigate to **API Keys** section
   - Click **Create API Key**
   - Copy your key (starts with `gsk_...`)

2. **Configure Environment**
   ```bash
   # Option A: Using .env file (recommended)
   cp .env.example .env
   # Edit .env and add:
   GROQ_API_KEY=gsk_your_actual_key_here
   
   # Option B: Set environment variable directly
   # Windows (PowerShell)
   $env:GROQ_API_KEY="gsk_your_actual_key_here"
   
   # macOS/Linux
   export GROQ_API_KEY="gsk_your_actual_key_here"
   ```

3. **Available Models:**
   - `llama-3.3-70b-versatile` (recommended)
   - `llama-3.1-70b-versatile`
   - `mixtral-8x7b-32768`
   - `gemma2-9b-it`

---

#### 🧠 Option 4: Google Gemini (Cloud API - Multimodal)

Google's Gemini offers powerful multimodal capabilities.

**Setup Steps:**

1. **Get API Key**
   - Visit [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - Sign in with Google account
   - Click **Create API Key**
   - Copy your key

2. **Configure Environment**
   ```bash
   # Option A: Using .env file (recommended)
   cp .env.example .env
   # Edit .env and add:
   GEMINI_API_KEY=your_actual_key_here
   
   # Option B: Set environment variable directly
   # Windows (PowerShell)
   $env:GEMINI_API_KEY="your_actual_key_here"
   
   # macOS/Linux
   export GEMINI_API_KEY="your_actual_key_here"
   ```

3. **Available Models:**
   - `gemini-pro` (recommended)
   - `gemini-1.5-pro`
   - `gemini-1.5-flash`

---

### 🎯 Quick Comparison

| Provider | Cost | Speed | Setup Difficulty | Best For |
|----------|------|-------|------------------|----------|
| **Ollama Cloud** | 🆓 Free | ⚡ Fast | ⭐ Easiest | Getting started quickly |
| **Ollama Local** | 🆓 Free | 🐢 Depends on hardware | ⭐⭐ Easy | Privacy, offline use |
| **Groq** | 🆓 Free tier | ⚡⚡⚡ Fastest | ⭐⭐ Moderate | Speed-critical apps |
| **Gemini** | 🆓 Free tier | ⚡⚡ Fast | ⭐⭐ Moderate | Multimodal tasks |

**💡 Recommendation:** Start with **Ollama Cloud models** (`gpt-oss:20b-cloud`) - they're free, fast, and require zero configuration!

📖 **For detailed setup instructions, troubleshooting, and best practices, see [API_SETUP.md](docs/API_SETUP.md)**

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry
```

### 2. Install Dependencies

```bash
# Create virtual environment and install dependencies
uv venv .venv
uv sync
```

### 3. Configure Environment (Optional - Only for Groq/Gemini)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# For Ollama cloud models, you can skip this step entirely!
```

### 4. Run the Agent

```bash
# Activate virtual environment (optional with uv)
# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Run the application
python src/main.py
```

### 5. Select Your Provider

**🌟 Recommended for First-Time Users (Ollama Cloud):**

```
Welcome to the Modular AI Agent!
Select a provider:
1. Ollama (FREE cloud models available!)
2. Groq (requires API key)
3. Gemini (requires API key)
Enter choice (1-3): 1

Enter Ollama model (default: gpt-oss:20b-cloud): gpt-oss:20b-cloud
```

**That's it!** The cloud model will start immediately - no downloads, no API keys needed! 🎉

**Alternative Options:**
- For local models: `ollama pull llama3.1` first, then use `llama3.1` as model name
- For Groq: Set `GROQ_API_KEY` in `.env` and select option 2
- For Gemini: Set `GEMINI_API_KEY` in `.env` and select option 3

---

## 📦 Installation

### Method 1: Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and setup
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry
uv venv .venv
uv sync

# Run
uv run python src/main.py
```

### Method 2: Using pip

```bash
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt  # You'll need to generate this from pyproject.toml
python src/main.py
```

### Method 3: Using Docker

```bash
# Build the image
docker build -t agentry:latest .

# Run interactively
docker run -it --rm agentry:latest

# With API keys
docker run -it --rm \
  -e GROQ_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  agentry:latest

# With Ollama (requires Ollama running on host)
docker run -it --rm --network host agentry:latest
```

See [DOCKER.md](docs/DOCKER.md) for detailed Docker usage.

---

## 💻 Usage

### Interactive Mode

```bash
python src/main.py
```

The agent will prompt you to:
1. Select a provider (Ollama, Groq, or Gemini)
2. Choose a model
3. Start chatting!

### Example Conversation

```
You: Search the web for the latest Python 3.12 features

[Tool Start] web_search with args: {'user_input': 'Python 3.12 features', 'search_type': 'general'}
[Tool End] web_search result: {...}

[Assistant]: Python 3.12 introduces several exciting features including:
1. Improved error messages with better tracebacks
2. Per-interpreter GIL for better multi-threading
3. Type parameter syntax for generics
...

You: Create a file called test.py with a hello world function

[Approval] Allow create_file with {'path': 'test.py', 'content': '...'}? (y/n): y
[Tool Start] create_file with args: {...}
[Tool End] create_file result: {'success': True}

[Assistant]: I've created test.py with a hello world function!
```

---

## 🛠️ Available Tools

### Web Tools
- **`web_search`** - Search the internet using DuckDuckGo
  - `general` mode: Quick searches
  - `critical` mode: Deep research with LLM analysis
- **`url_fetch`** - Fetch content from any URL

### File System Tools
- **`read_file`** - Read file contents
- **`create_file`** - Create new files (requires approval)
- **`edit_file`** - Edit existing files (requires approval)
- **`delete_file`** - Delete files (requires approval - dangerous)
- **`list_files`** - List directory contents
- **`search_files`** - Search for files by name/pattern
- **`fast_grep`** - Fast text search in files

### Execution Tools
- **`execute_command`** - Run shell commands (requires approval - dangerous)
- **`code_execute`** - Execute Python code safely

### Tool Safety Levels

| Category | Tools | Approval Required |
|----------|-------|-------------------|
| **Safe** | `read_file`, `list_files`, `search_files`, `url_fetch`, `web_search` | ❌ No |
| **Moderate** | `create_file`, `edit_file`, `code_execute` | ⚠️ Yes |
| **Dangerous** | `delete_file`, `execute_command` | 🔴 Yes |

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys (only needed for cloud providers)
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Ollama Configuration (optional)
OLLAMA_HOST=http://localhost:11434

# Application Settings (optional)
LOG_LEVEL=INFO
MAX_ITERATIONS=20
```

### Provider Configuration

Edit `src/config/settings.py` to customize default models and settings.

### Adding Custom Tools

1. Create a new tool in `src/tools/`:

```python
from .base import BaseTool, ToolResult
from pydantic import BaseModel, Field

class MyToolParams(BaseModel):
    param: str = Field(..., description='Parameter description')

class MyTool(BaseTool):
    name = "my_tool"
    description = "What my tool does"
    args_schema = MyToolParams

    def run(self, param: str) -> ToolResult:
        # Your tool logic here
        return ToolResult(success=True, content="Result")
```

2. Register it in `src/tools/registry.py`:

```python
from .my_tool import MyTool

class ToolRegistry:
    def _register_defaults(self):
        # ... existing tools ...
        self.register_tool(MyTool())
```

---

## 🐳 Docker Deployment

### Quick Docker Commands

```bash
# Build
docker build -t agentry:latest .

# Run with environment file
docker run -it --rm --env-file .env agentry:latest

# Run with Ollama on host network
docker run -it --rm --network host agentry:latest

# Run with volume mount for persistence
docker run -it --rm -v $(pwd)/data:/app/data agentry:latest
```

See [DOCKER.md](docs/DOCKER.md) for comprehensive Docker documentation.

---

## 🔄 CI/CD

This project includes automated CI/CD pipelines for:
- ✅ Automated testing and linting
- 🐳 Docker image building
- ☁️ Deployment to Google Cloud Run, AWS ECS, or Azure
- 🔒 Security scanning with Trivy

See [CICD.md](docs/CICD.md) for complete setup instructions.

---

## 👨‍💻 Development

### Project Structure

```
Agentry/
├── src/
│   ├── agents/          # Agent orchestration logic
│   │   └── agent.py     # Main agent class
│   ├── providers/       # LLM provider implementations
│   │   ├── base.py      # Provider interface
│   │   ├── ollama_provider.py
│   │   ├── groq_provider.py
│   │   └── gemini_provider.py
│   ├── tools/           # Tool implementations
│   │   ├── base.py      # Tool interface
│   │   ├── registry.py  # Tool registration
│   │   ├── web.py       # Web tools
│   │   ├── filesystem.py # File tools
│   │   └── execution.py # Execution tools
│   ├── config/          # Configuration
│   │   └── settings.py
│   └── main.py          # Entry point
├── .github/
│   └── workflows/       # CI/CD pipelines
├── tests/               # Test suite (coming soon)
├── Dockerfile           # Container definition
├── pyproject.toml       # Project metadata & dependencies
├── uv.lock             # Locked dependencies
└── README.md           # This file
```

### Running Tests

```bash
# Install dev dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff black

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src tests/

# Lint code
uv run ruff check src/
uv run black --check src/
```
---

## 🏗️ Architecture

### Design Principles

1. **Provider Abstraction** - Easily swap between LLM providers
2. **Tool Modularity** - Add/remove tools without touching core logic
3. **Safety First** - Approval workflows for dangerous operations
4. **Async-Ready** - Built with async/await for future scalability
5. **Clean Separation** - Clear boundaries between agents, providers, and tools

### Key Components

```
┌─────────────┐
│   main.py   │  ← Entry point
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Agent    │  ← Orchestrates conversation & tool calls
└──────┬──────┘
       │
       ├─────────────┐
       ▼             ▼
┌─────────────┐  ┌──────────┐
│  Providers  │  │  Tools   │
│  (Ollama,   │  │ (Web,    │
│   Groq,     │  │  File,   │
│   Gemini)   │  │  Exec)   │
└─────────────┘  └──────────┘
```

---

## 🗺️ Roadmap

### Current Status: v0.1.0 (Foundation)
- ✅ Multi-provider LLM support
- ✅ Extensible tool system
- ✅ Docker containerization
- ✅ CI/CD pipelines

### Upcoming Features

#### v0.2.0 - Enhanced Capabilities
- [ ] Memory/context management
- [ ] Conversation history persistence
- [ ] Streaming responses
- [ ] Better error handling
- [ ] Comprehensive test suite

#### v0.3.0 - Voice Integration
- [ ] Speech-to-text (STT) integration
- [ ] Text-to-speech (TTS) integration
- [ ] Real-time audio processing
- [ ] Wake word detection

#### v0.4.0 - Advanced Agent Features
- [ ] Multi-agent collaboration
- [ ] Task planning and decomposition
- [ ] Long-term memory with vector DB
- [ ] Plugin system for third-party tools

#### v1.0.0 - Voice Assistant
- [ ] Full voice-driven interaction
- [ ] Real-time task automation
- [ ] Natural conversation flow
- [ ] Production-ready voice assistant

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests and linting**
   ```bash
   uv run pytest
   uv run ruff check src/
   uv run black src/
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- Write tests for new features
- Follow existing code style
- Update documentation
- Keep commits atomic and well-described

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ollama** - For making local LLM deployment easy
- **Groq** - For blazing-fast inference
- **Google Gemini** - For powerful multimodal capabilities
- **uv** - For lightning-fast Python package management
- **LangChain** - For tool abstractions and utilities

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RudraModi360/Agentry/discussions)
- **Email**: [Your Email] (rudramodi9560@gmail.com)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ by [Rudra Modi](https://github.com/RudraModi360)**

*Evolving towards the future of voice-driven AI assistants*
