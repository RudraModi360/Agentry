# Understanding Agents

An **Agent** is a single autonomous AI worker that can understand tasks, make decisions, and execute actions using tools.

---

## Agent Anatomy

Every agent has three parts:

```
┌─────────────────────────────────────────────────┐
│                    AGENT                        │
├──────────────┬────────────┬──────────────────────┤
│              │            │                      │
│   BRAIN      │  HANDS     │    MEMORY            │
│              │            │                      │
│ • LLM        │ • Tools    │ • Sessions           │
│ • Reasoning  │ • Skills   │ • Context            │
│ • Streaming  │ • Workflows│ • Learned Facts      │
│              │            │                      │
└──────────────┴────────────┴──────────────────────┘
```

### Part 1: Brain 🧠
The Language Model (LLM) that understands and reasons
- Powered by your chosen provider (OpenAI, Groq, Ollama, Gemini, etc.)
- Makes decisions about what to do next
- Streams responses in real-time

### Part 2: Hands 🙌
Tools, skills, and workflows that take action
- Built-in tools (file ops, web search, code execution)
- Custom tools you define
- Skills (domain-specific tool collections)
- Workflows (multi-step processes)

### Part 3: Memory 🧠💾
Persistent context across conversations
- Session data from previous chats
- Learned facts and patterns
- User preferences and history

---

## Agent Types

### **BasicAgent** — Get Started Fast
Simplest agent for quick prototypes.

```python
from logicore import BasicAgent

agent = BasicAgent()
response = agent.chat("Hello!")
```

**Best for:** Testing, learning, simple one-off tasks

**What it includes:**
- LLM inference
- Basic streaming
- Default tools

---

### **Agent** — Production-Grade
Full-featured agent with all options.

```python
from logicore import Agent

agent = Agent(
    provider="groq",
    model="llama-3.3-70b-versatile",
    memory=True,
    custom_tools=[my_tool],
    streaming=True,
    telemetry=True
)
response = agent.chat("Complex task")
```

**Best for:** Production applications, complex workflows

**What it includes:**
- Multi-provider support
- Persistent memory
- Tool management
- Streaming + async
- Telemetry & debugging
- Approval workflows
- Context compression

---

### **SmartAgent** — Autonomous Reasoning
Multi-step, self-correcting agent.

```python
from logicore import SmartAgent

agent = SmartAgent(memory=True)
response = agent.chat("Analyze this dataset and generate a report")
```

**Best for:** Complex reasoning tasks, autonomous workflows

**What it includes:**
- Everything in Agent
- Multi-step reasoning
- Self-correction
- Reflection
- Plan generation

---

### **MCPAgent** — Dynamic Tool Discovery
Agent with Model Context Protocol servers.

```python
from logicore import MCPAgent

agent = MCPAgent(mcp_config="mcp.json")
response = agent.chat("Query the database")
```

**Best for:** Integration with external services

**What it includes:**
- Everything in Agent
- MCP server connections
- Dynamic tool discovery
- External tool execution

---

## How Agents Work

### The Execution Loop

Every time you call `agent.chat()`:

```
1. User Input
   └─> "What's the weather in Tokyo?"

2. Memory Check
   └─> Search: "Have I answered weather questions before?"
   
3. Tool Discovery
   └─> "I have: web_search, weather_api, calculator"
   
4. LLM Decision
   └─> "I'll use weather_api for Tokyo"
   
5. Tool Execution
   └─> Run weather_api("Tokyo")
   └─> Result: "Sunny, 24°C"
   
6. Response Generation
   └─> "It's sunny in Tokyo with 24°C"
   
7. Memory Storage
   └─> Save: "User asked about Tokyo weather"
   └─> Save: "I have weather_api tool"
```

### Code Level

```python
from logicore import Agent

agent = Agent(memory=True, custom_tools=[weather_api])

# Step 1-3: Agent prepares
# Step 4-5: LLM decides and runs tools
response = agent.chat("Weather in Tokyo?")

# Step 6: Returns response
# Step 7: Saves to memory automatically
print(response)
```

---

## Creating Custom Agents

### Via Inheritance

```python
from logicore import Agent

class MyCustomAgent(Agent):
    def __init__(self, **kwargs):
        # Custom setup
        super().__init__(**kwargs)
        self.custom_field = "value"
    
    def preprocess_input(self, user_input: str) -> str:
        # Custom preprocessing
        return user_input.upper()
```

### Via Configuration

```python
from logicore import Agent

agent = Agent(
    custom_system_prompt="You are a security-focused agent",
    custom_tools=[security_check],
    max_tool_calls=5,
    temperature=0.1  # More deterministic
)
```

---

## Agent Configuration

### Basic Parameters

```python
agent = Agent(
    # LLM Provider
    provider="groq",                              # or custom provider
    model="llama-3.3-70b-versatile",             # model name
    
    # Behavior
    system_message="You are a helpful assistant", # custom prompt
    role="general",                               # "developer", "analyst", etc.
    temperature=0.7,                              # creativity (0-1)
    
    # Memory
    memory=True,                                  # persistent memory
    memory_provider="local",                      # or "pinecone", etc.
    
    # Tools
    custom_tools=[],                              # list of tools
    skills=[],                                    # list of skills
    max_tool_calls=40,                            # prevent infinite loops
    
    # Output
    streaming=True,                               # stream tokens
    telemetry=True,                               # track usage
    debug=False                                   # verbose logging
)
```

### Execution Mode

```python
# Single-turn (simple)
response = agent.chat("Question?")

# Multi-turn (conversational)
agent.chat("First question")
agent.chat("Follow-up question")  # Remembers context

# Streaming (real-time)
import asyncio
async def stream():
    async for chunk in agent.stream_chat("Long response"):
        print(chunk, end="")
asyncio.run(stream())

# Async (non-blocking)
import asyncio
response = await agent.async_chat("Question?")
```

---

## Agent Lifecycle

### 1. Initialization
```python
agent = Agent(
    provider=groq_provider,
    custom_tools=[my_tool],
    memory=True
)
```

### 2. First Chat
```python
response = agent.chat("First question")
# Memory: No history, nothing to retrieve
```

### 3. Subsequent Chats
```python
response = agent.chat("Second question")
# Memory: Retrieves relevant context from first chat
```

### 4. New Session (Different Process)
```python
agent2 = Agent(memory=True)
response = agent2.chat("Question?")
# Memory: Automatically loads from previous session
```

### 5. Serialization (Save/Load)
```python
# Save agent state
agent.save_state("agent_backup.pkl")

# Load later
agent_restored = Agent.load_state("agent_backup.pkl")
```

---

## Monitoring & Debugging

### View Tool Calls

```python
agent = Agent(debug=True)
response = agent.chat("What's 2+2?")

# Output shows:
# Tool called: calculator(expression="2+2")
# Tool result: 4
# LLM response: "The answer is 4"
```

### Track Token Usage

```python
agent = Agent(telemetry=True)
response = agent.chat("Question?")

# Access metrics
print(agent.telemetry.tokens_used)
print(agent.telemetry.cost_estimate)
print(agent.telemetry.latency_ms)
```

### Access Memory

```python
agent = Agent(memory=True)
agent.chat("My name is Alice")

# View what's in memory
memories = agent.memory.search("Alice")
print(memories)
```

---

## Best Practices

✅ **DO:**
- Use specific roles: `role="code_reviewer"` vs. generic
- Enable memory for multi-turn conversations
- Set appropriate `max_tool_calls` to prevent infinite loops
- Use streaming for better UX with long responses
- Monitor telemetry in production

❌ **DON'T:**
- Give agents too many similar tools (confuses the LLM)
- Forget to set API keys for cloud providers
- Use high temperature (>0.8) for deterministic tasks
- Leave debug=True in production
- Create a new agent for every chat (reuse!)

---

## Next Steps

- [Providers](providers.md) — Learn to swap LLMs
- [Tools](tools.md) — Give agents superpowers
- [Memory](memory.md) — Build context across sessions
