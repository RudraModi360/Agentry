<div align="center">

# 🧠 Logicore

**A modular, multi-provider AI agent framework for Python**

[![PyPI version](https://img.shields.io/pypi/v/logicore?color=0066FF&logo=pypi&logoColor=white)](https://pypi.org/project/logicore/)
[![Python](https://img.shields.io/pypi/pyversions/logicore?logo=python&logoColor=white)](https://pypi.org/project/logicore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/logicore?color=0066FF)](https://pypi.org/project/logicore/)
[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white)](https://discord.gg/logicore)

Build intelligent, tool-using AI agents that work across **Gemini**, **Groq**, **Ollama**, **Azure OpenAI**, and **Anthropic** — with a single unified API.

[📖 Documentation](https://rudramodi360.github.io/Logicore/) · [🐛 Report Bug](https://github.com/RudraModi360/Logicore/issues) · [💡 Request Feature](https://github.com/RudraModi360/Logicore/issues)

</div>

---

## 🚀 What is Logicore?

Logicore is a **lightweight, production-ready** Python framework for building autonomous AI agents that can:

- **Understand** natural language and context across sessions
- **Decide** which tools to use and when to use them
- **Execute** tasks with memory persistence and safety checks
- **Integrate** with any major LLM provider without vendor lock-in

No more switching frameworks when you want to try a cheaper model, faster inference, or local deployment. **One framework. One API. Any LLM.**

---

## 🎯 Core Components

### 🤖 **Agent**
Single AI worker with tools and instructions
- Understands your domain
- Calls tools as needed
- Persists knowledge

### 👥 **Agent Team** (Coming Soon)
Multi-agent orchestration with sequential/hierarchical process
- Agents collaborate on complex tasks
- Each agent specializes in one role
- Automatic handoff and coordination

### 🔄 **Agent Flow** (Coming Soon)
Step-based pipelines with routing, parallel execution, and loops
- Define complex workflows
- Route to specialists
- Parallel processing of independent tasks

### ⚡ **Production Features**
Streaming, async execution, memory management, and telemetry
- Real-time token streaming
- Async-first design
- Production-grade safety and logging

---

## 💡 When to Use Logicore

| Use Case | Best Choice | Why? |
|----------|------------|------|
| Chat with one AI | `Agent` | Simple, single-turn interaction |
| Research → Analyze → Write | `Agent` (with memory) | Multi-step reasoning with context |
| Delegate to specialists | `Agent` (with tools) | Tools handle domain expertise |
| Parallel content creation | `Agent` (with async) | Multiple outputs simultaneously |
| Production API | `Agent` + FastAPI | Streaming + webhooks + monitoring |
| Cheaper inference | Any Provider | Swap one line: `provider="groq"` |
| Local-only deployment | `OllamaProvider` | No cloud, full privacy |

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Provider** | Gemini, Groq, Ollama, Azure OpenAI, Anthropic — pick one or swap anytime |
| **Built-in Tools** | File, web, git, PDF, Office, code execution — all ready to go |
| **MCP Support** | Model Context Protocol for dynamic tool discovery. Connect external MCPs seamlessly |
| **Persistent Memory** | Conversations auto-save and inform future interactions. Context across sessions |
| **Streaming** | Real-time token streaming with async callbacks. See responses as they generate |
| **Vision Support** | Multimodal image understanding across all supported models |
| **Skill Packs** | Modular, reusable domain-specific skills. Share and compose easily |
| **Telemetry** | Built-in execution tracing, token counting, and usage metrics |
| **Hot Reload** | Live code reloading during development. Edit → test instantly |
| **Production Ready** | Enterprise-grade safety, approval workflows, rate limiting, error recovery |

---

## 🎯 Why Logicore?

### ⚡ **Developer First**
- Intuitive, modern SDK designed for rapid development
- Clear abstractions: agents, tools, skills, memory
- Minimal boilerplate—get agents working in 30 seconds

### 🔄 **Multi-Provider from Day One**
- Stop being locked into one LLM
- Swap providers with one line of code
- Same agent code runs on OpenAI, Groq, Ollama, Gemini, Azure, Anthropic, custom endpoints
- Cost optimization: Route expensive queries to cheap models, latency-sensitive to local models

### 🧠 **Memory That Matters**
- Agents remember across conversations automatically
- Smart context injection: irrelevant memories ignored, relevant ones surface automatically
- Perfect for chatbots, assistants, research agents

### 🛠️ **Batteries Included**
- File operations, web search, git commands, PDF parsing, code execution
- 50+ tools ready out-of-the-box
- Extend with custom tools in one line

### 🔌 **MCP Ready**
- Use Model Context Protocol servers as tools
- Connect external services and databases dynamically
- No code changes—just add MCP config

### 📦 **Lightweight & Extensible**
- ~500 KB core framework
- No heavy dependencies forcing your hand
- Bring your own providers, tools, skills

### 🌍 **Open Source**
- MIT Licensed
- Active community on Discord
- Transparent development on GitHub

---

## 🚀 Quick Start

### Installation

```bash
# Core framework
pip install logicore

# With a specific provider
pip install logicore[gemini]      # Google Gemini
pip install logicore[groq]        # Groq (fast & cheap)
pip install logicore[ollama]      # Local models
pip install logicore[azure]       # Azure OpenAI
pip install logicore[anthropic]   # Claude

# Everything
pip install logicore[all]
```

### Your First Agent (30 Seconds)

```python
from logicore import BasicAgent

# Create an agent—that's it!
agent = BasicAgent()

# Chat with it
response = agent.chat("What's 15 times 4?")
print(response)
```

**Output:**
```
The result of 15 times 4 is 60.
```

---

### Give Your Agent Tools

```python
from logicore import Agent

# Define a tool (just a regular function)
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"It's sunny and 24°C in {city}!"

# Create agent with tools
agent = Agent(custom_tools=[get_weather])

# Agent uses the tool automatically
response = agent.chat("What's the weather in Tokyo?")
print(response)
```

**Output:**
```
In Tokyo, it's sunny with a pleasant temperature of 24°C. Great weather for sightseeing!
```

---

### Multi-Provider Flexibility

```python
from logicore import Agent
from logicore.providers import GroqProvider, GeminiProvider, OllamaProvider

# Same agent code, different providers—no code changes
providers = {
    "groq": GroqProvider(model="llama-3.3-70b-versatile"),
    "gemini": GeminiProvider(model="gemini-2.0-flash"),
    "local": OllamaProvider(model="llama3.2")
}

for name, provider in providers.items():
    agent = Agent(provider=provider)
    response = agent.chat("Explain quantum computing in 2 sentences")
    print(f"{name}: {response}\n")
```

---

### Memory Across Sessions

```python
from logicore import Agent

# Enable memory
agent = Agent(memory=True)

# First session
agent.chat("My name is Alice. I'm a researcher specializing in AI.")
agent.chat("What's my field of expertise?")

# Later... new Python process
agent2 = Agent(memory=True)
response = agent2.chat("What do you know about me?")
print(response)
# Output: "You're Alice, a researcher specializing in AI."
```

---

### Streaming Responses

```python
from logicore import Agent

agent = Agent()

# Stream tokens in real-time
async def stream_example():
    async for chunk in agent.stream_chat("Write a haiku about AI"):
        print(chunk, end="", flush=True)

import asyncio
asyncio.run(stream_example())
```

---

### Use Cases

#### **🤖 Customer Support Agent**
Automatically handle customer inquiries, resolve issues, and escalate complex problems
```python
agent = Agent(
    role="customer_support",
    tools=[search_database, send_email, create_ticket]
)
```

#### **📊 Data Analysis Agent**
Process datasets, run queries, generate visualizations, and provide insights
```python
agent = Agent(
    role="data_analyst",
    tools=[read_csv, run_sql, plot_chart]
)
```

#### **✍️ Content Creation Agent**
Generate, edit, optimize content across formats—blog posts, social media, video scripts
```python
agent = Agent(
    role="content_creator",
    tools=[web_search, write_article, optimize_seo]
)
```

#### **⚙️ Process Automation Agent**
Coordinate complex workflows: file processing, API calls, notifications, database updates
```python
agent = Agent(
    memory=True,
    tools=[file_reader, api_client, db_writer, notifier]
)
```

#### **🔬 Research Agent**
Autonomously investigate topics, aggregate findings, and produce reports
```python
agent = Agent(
    memory=True,  # Remember what's been researched
    tools=[web_search, pdf_reader, summarize]
)
```

---

## 📚 Built-in Tools (30+ and Growing)

### File Operations
- Read, write, edit, list, search files
- Safe file access with path restrictions

### Web & Search
- Web search (via multiple providers)
- Fetch URLs and parse content
- Image search

### Code & Execution
- Execute Python code safely
- Run shell commands
- Git operations

### Documents
- Parse PDFs, DOCX, XLSX, PPTX
- Extract text and tables
- Handle images

### Office Tools
- Create/edit Word documents
- Generate Excel spreadsheets
- Read presentations

### Custom Tools
Write your own in one line:
```python
@tool
def my_tool(param: str) -> str:
    """Do something useful."""
    return "Result"

agent.register_tool(my_tool)
```

---

## 🛠️ Agent Types at a Glance

| Agent | Use Case | Complexity |
|-------|----------|-----------|
| `BasicAgent` | Simple tool-calling | ⭐ (Beginner) |
| `Agent` | Full-featured production | ⭐⭐⭐ (Intermediate) |
| `SmartAgent` | Autonomous multi-step | ⭐⭐⭐⭐ (Advanced) |
| `MCPAgent` | Dynamic MCP tools | ⭐⭐⭐⭐ (Advanced) |

---

## 🔌 MCP Integration

Use Model Context Protocol servers as dynamic tools:

```python
from logicore import MCPAgent

agent = MCPAgent(
    mcp_config="mcp.json"  # Point to your MCP config
)

# All tools from MCP servers are now available
response = agent.chat("Query the database and summarize results")
```

---

## 📖 Full Documentation

**Get Started:**
- [Installation Guide](https://rudramodi360.github.io/Logicore/docs/installation) — Set up Logicore and your first provider
- [Quick Start](https://rudramodi360.github.io/Logicore/docs/quickstart) — From zero to agent in 5 minutes

**Learn:**
- [Core Concepts](https://rudramodi360.github.io/Logicore/docs/concepts/agents) — Agents, providers, tools, memory
- [How-To Guides](https://rudramodi360.github.io/Logicore/guides/) — Patterns for every use case
- [API Reference](https://rudramodi360.github.io/Logicore/api/) — Complete class and method documentation

**Advanced:**
- [Memory System](https://rudramodi360.github.io/Logicore/docs/memory-management) — Persistent context across sessions
- [Provider Architecture](https://rudramodi360.github.io/Logicore/docs/concepts/providers) — How multi-provider works
- [Custom Skills](https://rudramodi360.github.io/Logicore/guides/custom-skills) — Build reusable domain packages

---

## 🤝 Contributing

Contributions welcome! Whether it's new providers, tools, documentation, or examples:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 💬 Community

- **Discord**: [Join our community](https://discord.gg/logicore) — ask questions, share projects, get help
- **GitHub Issues**: [Report bugs or request features](https://github.com/RudraModi360/Logicore/issues)
- **Discussions**: [Share ideas and use cases](https://github.com/RudraModi360/Logicore/discussions)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🎉 Acknowledgments

- Inspired by frameworks like LangChain, CrewAI, and Ollama
- Built for developers who value flexibility and composability
- Special thanks to our open-source community

---

<div align="center">

**Built with ❤️ by [RudraModi360](https://github.com/RudraModi360) and contributors**

⭐ **Star this repo if you find Logicore useful!**

</div>
