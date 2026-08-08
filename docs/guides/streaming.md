---
title: Streaming Guide
description: Real-time token streaming and event handling
---

# Streaming Guide

Logicore provides native streaming support for real-time token delivery. This guide covers streaming configuration and usage.

## Basic Streaming

### Callback-Based Streaming

```python
async def on_token(token: str):
    print(token, end="", flush=True)

response = await agent.chat(
    "Tell me a story",
    callbacks={"on_token": on_token},
    stream=True
)
```

### Async Generator Streaming

```python
async for event in agent.stream("Tell me a story"):
    if event.type == "token":
        print(event.content, end="", flush=True)
    elif event.type == "tool_call":
        print(f"\nUsing tool: {event.tool_name}")
    elif event.type == "tool_result":
        print(f"\nTool result: {event.content[:100]}...")
```

### Sync Streaming

```python
# For non-async contexts
for event in agent.stream_sync("Tell me a story"):
    print(event.content, end="", flush=True)
```

## Stream Events

### Event Types

| Event | Description |
|-------|-------------|
| `token` | Single token from LLM |
| `tool_call` | Agent is calling a tool |
| `tool_result` | Tool execution result |
| `reasoning` | Hidden reasoning tokens |
| `error` | Error occurred |
| `done` | Stream complete |

### Event Structure

```python
@dataclass
class StreamEvent:
    type: str           # Event type
    content: str        # Token/content
    tool_name: str      # Tool name (if tool_call)
    tool_args: dict     # Tool arguments (if tool_call)
    metadata: dict      # Additional metadata
```

## Reasoning Extraction

### Hidden Reasoning Tokens

Some models (like Qwen, DeepSeek) output hidden reasoning:

```python
async for event in agent.stream("Explain quantum computing"):
    if event.type == "reasoning":
        # Hidden reasoning tokens
        print(f"[Reasoning] {event.content}")
    elif event.type == "token":
        # Visible response tokens
        print(event.content, end="", flush=True)

# Output:
# [Reasoning] This is a complex topic about quantum mechanics...
# Quantum computing uses qubits that can be in superposition...
```

### Enabling Reasoning Extraction

```python
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    reasoning_level="medium"  # low, medium, high
)

# Reasoning tokens are automatically extracted
```

## Streaming with Tools

### Tool Call Events

```python
async for event in agent.stream("What's the weather in Seattle?"):
    if event.type == "tool_call":
        print(f"\nCalling tool: {event.tool_name}")
        print(f"Arguments: {event.tool_args}")
    elif event.type == "tool_result":
        print(f"Result: {event.content}")
    elif event.type == "token":
        print(event.content, end="", flush=True)
```

### Complete Example

```python
import asyncio
from logicore import Agent

def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Sunny, 72°F in {city}"

async def main():
    agent = Agent(
        provider="ollama",
        model="qwen3.5:0.8b",
        tools=[get_weather]
    )
    
    async for event in agent.stream("What's the weather in Seattle?"):
        if event.type == "tool_call":
            print(f"\n[Tool] {event.tool_name}({event.tool_args})")
        elif event.type == "tool_result":
            print(f"[Result] {event.content}")
        elif event.type == "token":
            print(event.content, end="", flush=True)
    
    print()  # Newline after stream

asyncio.run(main())
```

## WebSocket Integration

### FastAPI Example

```python
from fastapi import FastAPI, WebSocket
from logicore import Agent

app = FastAPI()
agent = Agent(provider="ollama", model="qwen3.5:0.8b")

@app.websocket("/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    
    data = await websocket.receive_json()
    message = data["message"]
    
    async def on_token(token):
        await websocket.send_json({"type": "token", "content": token})
    
    response = await agent.chat(
        message,
        callbacks={"on_token": on_token},
        stream=True
    )
    
    await websocket.send_json({"type": "done", "content": response["content"]})
    await websocket.close()
```

## SSE (Server-Sent Events)

### Generating SSE

```python
from logicore.stream.sse import format_sse

async for event in agent.stream("Tell me a story"):
    sse_data = format_sse(event)
    # Send to client
```

### Consuming SSE

```javascript
const eventSource = new EventSource('/chat');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'token') {
        document.getElementById('response').textContent += data.content;
    }
};
```

## Stream Configuration

### Disabling Streaming

```python
# Non-streaming response
response = await agent.chat("Hello", stream=False)
```

### Controlling Flow

```python
# Pause/resume streaming
async for event in agent.stream("Tell me a story"):
    print(event.content, end="", flush=True)
    
    # Slow down for UI
    await asyncio.sleep(0.05)
```

## Best Practices

1. **Use Streaming**: Better UX for long responses
2. **Handle Events**: Process different event types
3. **Buffer Tokens**: Don't update UI on every token
4. **Error Handling**: Handle stream errors gracefully
5. **Cleanup**: Close streams properly

## Next Steps

- [Streaming API Reference](../api/streaming.md)
- [WebSocket Examples](../examples/websocket/)
- [SSE Examples](../examples/sse/)
