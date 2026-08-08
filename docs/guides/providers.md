---
title: Providers Guide
description: LLM provider configuration and management
---

# Providers Guide

Logicore supports multiple LLM providers. This guide covers provider configuration, selection, and failover.

## Supported Providers

| Provider | Type | Models | API Key Required |
|----------|------|--------|------------------|
| Ollama | Local | qwen, llama, mistral | No |
| OpenAI | Cloud | gpt-4o, gpt-4, gpt-3.5 | Yes |
| Gemini | Cloud | gemini-2.0, gemini-1.5 | Yes |
| Groq | Cloud | llama-3.3, mixtral | Yes |
| Azure | Enterprise | gpt-4o, gpt-4 | Yes |

## Provider Selection

### By Name

```python
agent = Agent(provider="ollama", model="qwen3.5:0.8b")
agent = Agent(provider="openai", model="gpt-4o")
agent = Agent(provider="gemini", model="gemini-2.0-flash")
agent = Agent(provider="groq", model="llama-3.3-70b-versatile")
```

### By Instance

```python
from logicore.providers import OllamaProvider, OpenAIProvider

ollama = OllamaProvider(model_name="qwen3.5:0.8b")
openai = OpenAIProvider(model_name="gpt-4o", api_key="...")

agent = Agent(provider=ollama)
```

## Provider Configuration

### Ollama

```python
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    endpoint="http://localhost:11434"  # Optional
)
```

**Environment Variables:**
```env
OLLAMA_BASE_URL=http://localhost:11434
```

### OpenAI

```python
agent = Agent(
    provider="openai",
    model="gpt-4o",
    api_key="sk-..."  # Or use env var
)
```

**Environment Variables:**
```env
OPENAI_API_KEY=sk-...
```

### Gemini

```python
agent = Agent(
    provider="gemini",
    model="gemini-2.0-flash",
    api_key="AI..."  # Or use env var
)
```

**Environment Variables:**
```env
GEMINI_API_KEY=AI...
```

### Groq

```python
agent = Agent(
    provider="groq",
    model="llama-3.3-70b-versatile",
    api_key="gsk_..."  # Or use env var
)
```

**Environment Variables:**
```env
GROQ_API_KEY=gsk_...
```

### Azure OpenAI

```python
agent = Agent(
    provider="azure",
    model="gpt-4o",
    api_key="...",
    endpoint="https://your-resource.openai.azure.com/"
)
```

**Environment Variables:**
```env
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
```

## Provider Failover

### ModelAvailabilityService

Automatic failover when a provider fails:

```python
from logicore.providers import ModelAvailabilityService, OpenAIProvider, GroqProvider

availability = ModelAvailabilityService()

# Register providers with priorities
availability.register_provider("openai", OpenAIProvider(model="gpt-4o"), priority=1)
availability.register_provider("groq", GroqProvider(model="llama-3.3-70b"), priority=2)

# Get available provider
provider = availability.get_available_provider()

agent = Agent(provider=provider)
```

### How Failover Works

1. **Health Tracking**: Monitor provider health
2. **Automatic Retry**: Retry on failure
3. **Priority-Based**: Use next provider in priority order
4. **Exponential Backoff**: Wait longer between retries

### Custom Failover Logic

```python
from logicore.providers.policies import ProviderPolicy

class CustomPolicy(ProviderPolicy):
    async def should_retry(self, error, attempt):
        # Custom retry logic
        return attempt < 3
    
    async def get_delay(self, attempt):
        # Custom delay
        return attempt * 2

availability = ModelAvailabilityService(policy=CustomPolicy())
```

## Provider Gateway

### ResilientGateway

Wraps providers with resilience:

```python
from logicore.gateway import ResilientGateway

gateway = ResilientGateway(
    provider=provider,
    availability=availability,
    max_retries=3,
    timeout=30
)

agent = Agent(provider=gateway)
```

### Features

- **Automatic Retries**: Retry failed requests
- **Timeout Handling**: configurable timeouts
- **Error Recovery**: Handle transient errors
- **Logging**: Detailed error logs

## Streaming Support

All providers support streaming:

```python
agent = Agent(provider="ollama", model="qwen3.5:0.8b")

async for event in agent.stream("Hello"):
    print(event.content, end="", flush=True)
```

### Reasoning Extraction

Some providers support hidden reasoning:

```python
# Ollama with Qwen/DeepSeek
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    reasoning_level="medium"
)

# Reasoning tokens are extracted automatically
```

## Provider Comparison

### Local vs Cloud

| Feature | Local (Ollama) | Cloud (OpenAI) |
|---------|----------------|----------------|
| Cost | Free | Per-token |
| Latency | Low | Network-dependent |
| Privacy | Full control | Data sent to provider |
| Quality | Varies by model | High quality |
| Availability | Depends on hardware | 99.9% uptime |

### Use Cases

- **Ollama**: Development, privacy-sensitive, cost-conscious
- **OpenAI**: Production, high quality, multi-modal
- **Gemini**: Speed, multi-modal, Google ecosystem
- **Groq**: Fast inference, low latency
- **Azure**: Enterprise, compliance, existing infrastructure

## Best Practices

1. **Start Local**: Use Ollama for development
2. **Test Cloud**: Verify with cloud providers
3. **Use Failover**: Configure multiple providers
4. **Monitor Health**: Track provider availability
5. **Cache Responses**: Reduce API calls

## Next Steps

- [Provider API Reference](../api/providers.md)
- [Failover Examples](../examples/failover/)
- [Custom Providers](../tutorials/custom-provider.md)
