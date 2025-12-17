# 🐱 Scratchy
### *A Professional, Modular AI Agent Framework*

Scratchy is a powerful, privacy-focused AI agent framework designed for flexibility and ease of use. Whether you prefer a terminal user interface (TUI), a modern web dashboard, or building custom python scripts, Scratchy has you covered.

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/RudraModi360/Agentry.git
cd Scratchy

# 2. Install dependencies (and register the 'agentry' command)
pip install -e .
```

## 🎮 How to Access

Scratchy provides three distinct ways to interact with the agent. Click the links below for detailed guides on each method.

### 1. [The Terminal Interface (CLI)](docs/cli-usage.md)
*Best for: Rapid interaction, coding, and keyboard-first workflows.*

```bash
agentry
```

### 2. [The Web Interface (UI)](docs/ui-usage.md)
*Best for: Visual users, dragging & dropping files, and a chat-like experience.*

```bash
python ui/server.py
```

### 3. [The Python Framework (Library)](docs/framework-usage.md)
*Best for: Developers building custom tools, automations, or apps.*

```python
from scratchy import Agent
response = await agent.chat("Hello!")
```

---

## 🛠️ Advanced Usage

For power users who need deep customization:

- **Session Management**: Sessions are auto-saved. converting chat history into `.toon` memory files.
- **Tools**: Scratchy comes with file system, web search, and execution tools out of the box.
- **MCP**: Connect to Model Context Protocol servers via `mcp.json`.

## 📚 Documentation

Detailed documentation is available in the `docs/` folder:
- [**Getting Started**](docs/getting-started.md)
- [**API Reference**](docs/api-reference.md)
- [**Custom Tools**](docs/custom-tools.md)
- [**Session Management**](docs/session-management.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING_OLD.md).
