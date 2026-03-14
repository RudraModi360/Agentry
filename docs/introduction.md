# Introduction to Logicore

Welcome to **Logicore** — the multi-provider AI agent framework that puts you in control.

## The Problem We're Solving

You're building AI agents and hitting three walls:

### 🪵 The Lock-In Problem
You build with OpenAI, then find you need cheaper inference (Groq), or local deployment (Ollama), or a faster model (Gemini). But your code is tightly coupled to OpenAI's API. **Time to rewrite everything.**

### 🧠 The Memory Problem
Your agent forgets everything between conversations. You explain the context once, it helps, then next time it's clueless. Like hiring a consultant who shows up every day with zero memory of what you discussed.

### 🔧 The Tool Overload Problem
Adding more tools (file reader, web search, code execution, PDF parsing) should be simple. Instead, your agent gets confused, forgets which tool does what, and makes bad choices. **The more tools, the worse it gets.**

---

## What is Logicore?

**Logicore is the antidote.**

Logicore is a lightweight, production-ready Python framework for building autonomous AI agents that can:

- **Work with any LLM** — Gemini, Groq, Ollama, Azure OpenAI, Anthropic — without changing your code
- **Remember across sessions** — Conversations auto-save and inform future interactions
- **Handle tons of tools** — 50+ built-in tools plus custom tools, MCP servers, skills
- **Deploy to production** — Streaming, async, telemetry, approval workflows all built-in

**One framework. One API. Any LLM. Zero lock-in.**

---

## Three Pillars of Logicore

### **Pillar 1: Multi-Provider Architecture**

Write your agent code once. Deploy it anywhere.

```python
from logicore import Agent
from logicore.providers import GroqProvider, OllamaProvider, GeminiProvider

# Same agent code
agent_code = Agent(custom_tools=[my_tool])

# Different providers, zero code changes
groq_agent = Agent(provider=GroqProvider(), custom_tools=[my_tool])
local_agent = Agent(provider=OllamaProvider(), custom_tools=[my_tool])
cloud_agent = Agent(provider=GeminiProvider(), custom_tools=[my_tool])
```

**Why it matters:**
- Cost optimization: Route expensive queries to cheaper models
- Performance: Use fast local models for latency-sensitive tasks
- Resilience: Fail over between providers seamlessly
- Future-proof: New model? Just add a new provider

### **Pillar 2: Persistent Memory**

Agents that actually learn instead of starting from scratch.

```python
agent = Agent(memory=True)

# Session 1
agent.chat("My company uses Python and React")
agent.chat("What's our tech stack?")

# Session 2 (next day, different process)
agent2 = Agent(memory=True)
agent2.chat("What do you know about my tech stack?")
# Automatically answers: "Python and React"
```

**How it works:**
1. Agent searches its memory: "Seen this before?"
2. Pulls in relevant facts automatically
3. LLM makes better decisions with context
4. New information gets stored back

Automatic. Zero code needed.

### **Pillar 3: Scalable Tools & Skills**

Traditional frameworks break with 20-30 tools. Logicore handles hundreds.

**How?**
- **Group tools as skills** — Instead of "here are 100 tools," the agent sees "here are 8 skills"
- **Smart loading** — Load only the tools the agent needs for the current task
- **Built-in tools** — 50+ ready-to-go: file operations, web search, code execution, document parsing
- **Easy extension** — Write custom tools in one line of code
- **MCP support** — Connect external tools via Model Context Protocol

---

## When to Use Logicore

| Scenario | Solution |
|----------|----------|
| You want to try different LLMs | Use Logicore now! |
| You're building production agents | Perfect fit |
| You need persistent memory | Designed for this |
| You have tons of tools | Exactly what we solve |
| You want "write once, run everywhere" | This is it |
| You're locked into one API | Switch providers, keep your code |

---

## What You'll Learn

This documentation will teach you:

**Getting Started** → [Installation](installation.md) and [Quick Start](quickstart.md)
- Set up Logicore
- Create your first agent in 30 seconds
- Add tools and see them in action

**Core Concepts** → [Agents](concepts/agents.md), [Providers](concepts/providers.md), [Tools](concepts/tools.md)
- How agents work under the hood
- Provider architecture and switching
- Tool registration and execution
- Skills, memory, and streaming

**How-To Guides** → [Your First Agent](../guides/your-first-agent.md), [Multi-Provider Patterns](../guides/multi-provider-patterns.md)
- Build real-world agents
- Pattern for every use case
- Production deployment

**API Reference** → [Complete documentation](../api/agent-class.md)
- Every class and method
- Parameters and examples
- Error handling

---

## Key Differences from Other Frameworks

| Feature | Logicore | LangChain | CrewAI | Ollama |
|---------|----------|-----------|---------|---------|
| Multi-provider support | ✅ Built-in | ✅ Via wrappers | ❌ Limited | ❌ Ollama only |
| Persistent memory | ✅ Out-of-box | ❌ Manual setup | ✅ Project memory | ❌ No |
| Tool management at scale | ✅ Designed for 100+ | ⚠️ Starts breaking at 30 | ✅ Via roles | ❌ No |
| MCP support | ✅ Native | ❌ Recent addition | ❌ No | ❌ No |
| Zero dependencies | ❌ Optional | ❌ Heavy | ❌ Heavy | ✅ Yes |
| Production streaming | ✅ Built-in | ✅ Supported | ❌ No | ⚠️ Limited |
| Learning curve | ⭐⭐ (Easy) | ⭐⭐⭐ (Medium) | ⭐⭐ (Easy) | ⭐ (Very easy) |

---

## Next Steps

1. **[Install Logicore](installation.md)** — Set up with your first provider
2. **[Run Quick Start](quickstart.md)** — Build your first agent in 5 minutes
3. **[Learn Core Concepts](concepts/agents.md)** — Understand how everything works
4. **[Explore Guides](../guides/)** — Patterns for real-world use cases

---

## Get Help

- 📖 **Documentation** — You're reading it!
- 💬 **Discord** — [Join our community](https://discord.gg/logicore)
- 🐛 **Issues** — [Report bugs or request features](https://github.com/RudraModi360/Logicore/issues)
- 💡 **Discussions** — [Share ideas](https://github.com/RudraModi360/Logicore/discussions)
