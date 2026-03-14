# Multi-Provider Architecture

One of Logicore's superpowers: **write your agent once, deploy it anywhere.**

---

## The Provider Concept

A **Provider** is an adapter that translates Logicore commands to any LLM's API.

```
Your Logicore Agent
       ↓
   ┌───────────────────────────────────────────┐
   │         Provider Gateway                  │
   │  (Translation Layer)                      │
   ├───────────────────────────────────────────┤
   ↓            ↓            ↓            ↓
OpenAI        Groq        Ollama       Gemini
```

### Why It Matters

| Scenario | Solution |
|----------|----------|
| Model is too expensive | Switch from OpenAI to Groq (5x cheaper) |
| Need lower latency | Use local Ollama instead of cloud |
| Want better reasoning | Try Gemini or Claude |
| Need privacy | Use local deployment with Ollama |
| Want redundancy | Fail over between providers automatically |

---

## Supported Providers

### OpenAI 🔥
**Best for:** State-of-the-art models, production reliability

```python
from logicore import Agent
from logicore.providers import OpenAIProvider

agent = Agent(
    provider=OpenAIProvider(
        model="gpt-4",
        api_key="sk-..."  # Or set OPENAI_API_KEY env var
    )
)

response = agent.chat("Explain quantum computing")
```

**Models:** gpt-4, gpt-4-turbo, gpt-4o, gpt-3.5-turbo

**Cost:** $$ (most expensive)

**Speed:** ⭐⭐⭐⭐ (Fast)

**Quality:** ⭐⭐⭐⭐⭐ (Best-in-class)

---

### Groq ⚡
**Best for:** Speed and cost optimization

```python
from logicore import Agent
from logicore.providers import GroqProvider

agent = Agent(
    provider=GroqProvider(
        model="llama-3.3-70b-versatile",
        api_key="gsk_..."  # Or set GROQ_API_KEY env var
    )
)

response = agent.chat("Explain quantum computing")
```

**Models:** llama-3.3-70b, mixtral-8x7b, gemma-2-9b

**Cost:** $ (Very cheap)

**Speed:** ⭐⭐⭐⭐⭐ (Lightning fast)

**Quality:** ⭐⭐⭐⭐ (Excellent)

---

### Ollama 🏠
**Best for:** Privacy, no cloud, zero cost

```python
from logicore import Agent
from logicore.providers import OllamaProvider

agent = Agent(
    provider=OllamaProvider(
        model="llama3.2:3b",  # Download with: ollama pull llama3.2
        endpoint="http://localhost:11434"  # Optional, auto-detected
    )
)

response = agent.chat("Explain quantum computing")
```

**Models:** llama3.2, mistral, qwen:2b, neural-chat

**Cost:** Free

**Speed:** ⭐⭐⭐ (Depends on hardware)

**Quality:** ⭐⭐⭐ (Good for free)

**Setup:** Download Ollama from ollama.ai

---

### Google Gemini 🌟
**Best for:** Vision/multimodal, cutting-edge

```python
from logicore import Agent
from logicore.providers import GeminiProvider

agent = Agent(
    provider=GeminiProvider(
        model="gemini-2.0-flash",
        api_key="..."  # Or set GOOGLE_API_KEY env var
    )
)

response = agent.chat("Explain quantum computing")
```

**Models:** gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash

**Cost:** $ (cheap)

**Speed:** ⭐⭐⭐⭐ (Fast)

**Quality:** ⭐⭐⭐⭐⭐ (Excellent)

---

### Anthropic (Claude) 🧠
**Best for:** Reasoning, detailed responses

```python
from logicore import Agent
from logicore.providers import AnthropicProvider

agent = Agent(
    provider=AnthropicProvider(
        model="claude-3-5-sonnet-20241022",
        api_key="sk-ant-..."  # Or set ANTHROPIC_API_KEY env var
    )
)

response = agent.chat("Explain quantum computing")
```

**Models:** claude-3-opus, claude-3-sonnet, claude-3-haiku

**Cost:** $$ (moderate)

**Speed:** ⭐⭐⭐⭐ (Fast)

**Quality:** ⭐⭐⭐⭐⭐ (Excellent reasoning)

---

### Azure OpenAI ☁️
**Best for:** Enterprise, hybrid cloud

```python
from logicore import Agent
from logicore.providers import AzureOpenAIProvider

agent = Agent(
    provider=AzureOpenAIProvider(
        model="gpt-4",
        api_key="...",
        endpoint="https://<resource>.openai.azure.com/",
        api_version="2024-02-15-preview"
    )
)

response = agent.chat("Explain quantum computing")
```

**Models:** gpt-4, gpt-4-turbo, gpt-35-turbo

**Cost:** $$ (Same as OpenAI)

**Speed:** ⭐⭐⭐⭐ (Fast)

**Quality:** ⭐⭐⭐⭐⭐ (OpenAI models)

---

## Switching Providers

### Same Code, Different Providers

```python
from logicore import Agent
from logicore.providers import (
    OpenAIProvider,
    GroqProvider,
    OllamaProvider,
    GeminiProvider
)

def build_agent(provider_name: str):
    providers = {
        "openai": OpenAIProvider(model="gpt-4"),
        "groq": GroqProvider(model="llama-3.3-70b-versatile"),
        "ollama": OllamaProvider(model="llama3.2"),
        "gemini": GeminiProvider(model="gemini-2.0-flash"),
    }
    
    return Agent(provider=providers[provider_name])

# Use different providers
for name in ["openai", "groq", "ollama"]:
    agent = build_agent(name)
    response = agent.chat("Hello!")
    print(f"{name}: {response}")
```

**Your agent code never changes!**

---

## Dynamic Provider Selection

Choose provider based on task:

```python
from logicore import Agent
from logicore.providers import GroqProvider, OllamaProvider

def process_task(task_type: str, query: str):
    if task_type == "expensive":
        # Use expensive model for complex tasks
        provider = GroqProvider(model="llama-3.3-70b")
    else:
        # Use fast local model for simple tasks
        provider = OllamaProvider(model="llama3.2:3b")
    
    agent = Agent(provider=provider)
    return agent.chat(query)

# Simple task → Ollama (fast, free)
result = process_task("simple", "What's 2+2?")

# Complex task → Groq (slower, smarter)
result = process_task("expensive", "Design a ML system for X")
```

---

## Error Handling & Fallback

Gracefully handle provider failures:

```python
from logicore import Agent
from logicore.providers import GroqProvider, OllamaProvider

def chat_with_fallback(query: str):
    providers = [
        GroqProvider(model="llama-3.3-70b"),  # Try first (fast)
        OllamaProvider(model="ollama3.2"),     # Fallback
    ]
    
    for provider in providers:
        try:
            agent = Agent(provider=provider)
            response = agent.chat(query)
            print(f"Success with {provider}")
            return response
        except Exception as e:
            print(f"Failed: {e}, trying next...")
    
    return "All providers failed"
```

---

## Comparing Providers

### Cost Comparison (per 1M tokens)

| Provider | Input | Output | Notes |
|----------|-------|--------|-------|
| **Ollama** | Free | Free | Local only |
| **Groq** | Free | Free | (April 2024+) |
| **Gemini** | $0.075 | $0.30 | Cheap |
| **OpenAI GPT-3.5** | $0.50 | $1.50 | Affordable |
| **OpenAI GPT-4** | $30 | $60 | Expensive |
| **Claude 3 Haiku** | $0.25 | $1.25 | Cheap |
| **Claude 3 Sonnet** | $3 | $15 | Mid-range |
| **Azure** | Same as OpenAI | Same | Enterprise discount |

### Speed Comparison (latency)

| Provider | First Token | Full Response |
|----------|------------|---------------|
| **Groq** | ~50ms | Fastest |
| **OpenAI** | ~200ms | Very fast |
| **Gemini** | ~150ms | Fast |
| **Ollama** | 100-500ms | Depends on hardware |
| **Claude** | ~300ms | Fast |

### Quality Comparison (reasoning)

| Provider | Coding | Math | Analysis | Writing |
|----------|--------|------|----------|---------|
| **GPT-4** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Claude** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Gemini** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Groq/Llama** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Ollama** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

---

## Choosing Your Provider

### For Beginners
→ **Ollama** (free, local, no API key)

### For Production
→ **OpenAI GPT-4** (best quality)

### For Cost
→ **Groq** (free + fast)

### For Speed
→ **Groq** (fastest)

### For Privacy
→ **Ollama** (entirely local)

### For Enterprise
→ **Azure OpenAI** (VPC, compliance)

### For Vision/Multimodal
→ **Gemini** or **GPT-4o**

---

## Custom Providers

Build your own provider:

```python
from logicore.providers import BaseProvider

class MyCustomProvider(BaseProvider):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Implement your API call here
        response = await my_api.call(prompt)
        return response.text

# Use it
agent = Agent(provider=MyCustomProvider(model="custom", api_key="..."))
```

---

## Next Steps

- [Tools](tools.md) — Give agents capabilities
- [Memory](memory.md) — Persistent context
- [Guides: Multi-Provider Patterns](../../guides/multi-provider-patterns.md) — Real examples
