# Quick Start: From Zero to Agent in 5 Minutes

No theory. Just code. Let's build your first agent right now.

---

## What You'll Build

A working AI agent that:
1. Understands natural language
2. Calls tools automatically
3. Returns results

**Time: 5 minutes. Setup: 1 minute.**

---

## 1. Install (1 Minute)

```bash
# Core + Ollama (local, free)
pip install logicore[ollama]

# OR with cloud provider
pip install logicore[groq]     # Fast & cheap
# pip install logicore[openai]  # GPT-4
# pip install logicore[gemini]  # Google Gemini
```

**For Ollama (free):**
```bash
# Download from https://ollama.ai and run:
ollama run qwen3.5:0.8b
```

---

## 2. Your First Agent (1 Minute)

Create `hello_agent.py`:

```python
from logicore import BasicAgent

# Create an agent
agent = BasicAgent()

# Chat with it
response = agent.chat("What's 2 + 2?")
print(response)
```

Run it:
```bash
python hello_agent.py
```

**Output:**
```
2 + 2 equals 4.
```

✅ **Done!** You have a working agent.

---

## 3. Add Tools (2 Minutes)

Let's give the agent superpowers. Update your code:

```python
from logicore import Agent

# Define a tool (just a Python function!)
def calculate(expression: str) -> str:
    """Calculate a mathematical expression. Example: 15 * 4 + 2"""
    try:
        result = eval(expression)
        return f"The result is: {result}"
    except Exception as e:
        return f"Error: {e}"

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"In {city}, it's sunny and 24°C"

# Create agent with tools
agent = Agent(custom_tools=[calculate, get_weather])

# Now ask it something that needs tools!
response = agent.chat("What's 1000 * 50 + 25? And what's the weather like in Tokyo?")
print(response)
```

**Output:**
```
The result of 1000 * 50 + 25 is 50,025, and in Tokyo, it's sunny and 24°C.
```

✅ **Your agent used tools automatically!**

---

## 4. Try Different Providers (1 Minute)

Same code, different LLMs — no changes needed:

```python
from logicore import Agent
from logicore.providers import GroqProvider, GeminiProvider, OllamaProvider

def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        return f"Result: {eval(expression)}"
    except:
        return "Error calculating"

# Define different providers
providers = {
    "groq": GroqProvider(model="llama-3.3-70b-versatile"),
    "gemini": GeminiProvider(model="gemini-2.0-flash"),
    "local": OllamaProvider(model="llama3.2")
}

# Same agent code works everywhere
question = "What's 15 * 4?"
for name, provider in providers.items():
    agent = Agent(provider=provider, custom_tools=[calculate])
    response = agent.chat(question)
    print(f"{name}: {response}")
```

---

## 5. Enable Memory (30 Seconds)

Agents that remember conversations:

```python
from logicore import Agent

# Enable memory
agent = Agent(memory=True)

# First session
agent.chat("My name is Alex")
agent.chat("What's my name?")  # Agent remembers!

# Later (different session)
agent2 = Agent(memory=True)
response = agent2.chat("Who am I?")
print(response)
# Output: "You're Alex"
```

---

## 6. Use Streaming (30 Seconds)

See responses generate in real-time:

```python
import asyncio
from logicore import Agent

async def stream_response():
    agent = Agent()
    
    # Stream output token-by-token
    async for chunk in agent.stream_chat("Write a 3-line poem about AI"):
        print(chunk, end="", flush=True)
    print()

asyncio.run(stream_response())
```

---

## Code Patterns You'll Use All the Time

### Pattern 1: Simple Chat
```python
agent = Agent()
response = agent.chat("Your question here")
print(response)
```

### Pattern 2: Chat with Tools
```python
def my_tool(param: str) -> str:
    """Do something."""
    return f"Result for {param}"

agent = Agent(custom_tools=[my_tool])
response = agent.chat("Use my_tool to do something")
```

### Pattern 3: Multi-Provider
```python
from logicore.providers import GroqProvider, OllamaProvider

groq = Agent(provider=GroqProvider())
local = Agent(provider=OllamaProvider())

# Use switch between them
response = groq.chat("Fast query")      # Expensive but quick
response = local.chat("Heavy lifting")  # Cheap but local
```

### Pattern 4: With Memory
```python
agent = Agent(memory=True)

# Session 1
agent.chat("Remember: I like Python programming")
agent.chat("What are my interests?")  # Answers based on memory

# Session 2
agent2 = Agent(memory=True)
agent2.chat("What do I like?")  # Still remembers!
```

### Pattern 5: Async (Multiple Agents in Parallel)
```python
import asyncio
from logicore import Agent

async def parallel_agents():
    agents = [Agent() for _ in range(3)]
    
    # Run in parallel
    tasks = [
        agent.async_chat(f"Task {i}") 
        for i, agent in enumerate(agents)
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# results = asyncio.run(parallel_agents())
```

---

## Real-World Examples

### Example 1: Code Reviewer Agent
```python
from logicore import Agent

def review_code(code: str) -> str:
    """Analyze code for issues."""
    # Your review logic here
    return "Review complete"

agent = Agent(
    role="code_reviewer",
    custom_tools=[review_code]
)

response = agent.chat("""
Review this code:
```python
x = 1
y = 2
print(x+y)
```
""")
print(response)
```

### Example 2: Research Agent
```python
from logicore import Agent

agent = Agent(
    role="researcher",
    memory=True,  # Remember what's been researched
)

# Multi-turn conversation
agent.chat("Research: What is quantum computing?")
agent.chat("Now summarize the key differences from classical computing")
agent.chat("What's the next step to mastering this topic?")
```

### Example 3: Customer Support Agent
```python
from logicore import Agent

def search_kb(query: str) -> str:
    """Search knowledge base."""
    return "Answer from KB..."

def create_ticket(issue: str) -> str:
    """Create support ticket."""
    return "Ticket #12345 created"

agent = Agent(
    role="customer_support",
    custom_tools=[search_kb, create_ticket],
    memory=True
)

agent.chat("Hi! My order isn't working")
agent.chat("Can you check my account?")
agent.chat("I need to escalate this")
```

---

## What to Do Next

1. **[Learn Core Concepts](concepts/agents.md)** — Understand agents, providers, tools deeper
2. **[Explore How-To Guides](../guides/your-first-agent.md)** — Real-world patterns
3. **[Check API Reference](../api/agent-class.md)** — All classes and methods

---

## Common Questions

**Q: Which provider should I use?**
A: Start with Ollama (free, local). Then:
- Need speed? Use Groq
- Like OpenAI? Use OpenAI provider
- Privacy-critical? Use Ollama
- Cheapest? Use Groq

**Q: Can I use multiple providers in the same project?**
A: Yes! Create multiple agents with different providers.

**Q: Does memory persist forever?**
A: Memory is stored locally in a vector database. You can clear it anytime.

**Q: Can I deploy Logicore to production?**
A: Yes! See [Production Deployment Guide](../guides/production-deployment.md).

**Q: Can I add my own tools?**
A: Absolutely! Any Python function can be a tool.

---

## Troubleshooting

**"No provider found"**
→ Install a provider: `pip install logicore[groq]` or `pip install logicore[ollama]`

**"Connection refused"**
→ Ollama isn't running. Start it: `ollama run qwen3.5:0.8b`

**"API key not found"**
→ Set your environment variable (see [Installation](installation.md))

---

## Get Help

- 💬 **Discord** — [Join community](https://discord.gg/logicore)
- 🐛 **Issues** — [GitHub](https://github.com/RudraModi360/Logicore/issues)
- 📚 **Full Docs** — [documentation](../guides/)
