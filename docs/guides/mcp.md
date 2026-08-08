---
title: MCP Guide
description: Model Context Protocol integration
---

# MCP Guide

Model Context Protocol (MCP) extends agent capabilities by connecting to external tool servers. This guide covers MCP configuration and usage.

## What is MCP?

MCP is a protocol that allows agents to discover and use tools from external servers. It enables:

- **Tool Discovery**: Automatically find available tools
- **Server Management**: Connect to multiple servers
- **Deferred Loading**: Load tools on-demand
- **Tool Search**: Find tools by query

## Configuration

### mcp.json

Create an `mcp.json` file:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}
```

### Using MCPAgent

```python
from logicore import MCPAgent

agent = MCPAgent(
    provider="ollama",
    model="qwen3.5:0.8b",
    mcp_config_path="mcp.json"
)

# Connect to servers
await agent.init_mcp_servers()

# Get all tools (including MCP)
tools = await agent.get_all_tools()
```

## MCPAgent Features

### Deferred Tool Loading

When many tools are available, load them on-demand:

```python
agent = MCPAgent(
    provider="ollama",
    deferred_tools=True,  # Enable deferred loading
    tool_threshold=15     # Auto-defer if tools exceed this
)

# Search for specific tools
results = await agent._search_tools("file")

# Pre-load specific tools
await agent.preload_tools(["read_file", "write_file"])
```

### Tool Search

```python
# Search tools by query
results = await agent._search_tools("database")

# Returns matching tools from all servers
```

### Registry Stats

```python
# Get statistics about registered tools
stats = agent.get_registry_stats()
print(f"Total tools: {stats['total']}")
print(f"MCP tools: {stats['mcp']}")
print(f"Deferred: {stats['deferred']}")
```

## MCP Server Management

### Adding Servers

```python
# Add server programmatically
agent.add_mcp_server({
    "name": "custom-server",
    "command": "python",
    "args": ["-m", "my_mcp_server"]
})
```

### Listing Servers

```python
# Get all connected servers
servers = agent.get_mcp_servers()

# Get tools for specific server
tools = agent.get_server_tools("filesystem")
```

### Cleanup

```python
# Cleanup all MCP connections
await agent.cleanup()
```

## Session Management

### Creating Sessions

```python
# Create session with callbacks
session = await agent.create_session(
    session_id="my-session",
    on_session_created=lambda s: print(f"Session created: {s.id}"),
    on_session_destroyed=lambda s: print(f"Session destroyed: {s.id}")
)
```

### Managing Sessions

```python
# List active sessions
sessions = agent.list_sessions()

# Cleanup stale sessions
await agent.cleanup_stale_sessions(timeout=3600)

# Destroy specific session
await agent.destroy_session("my-session")
```

## Exporting Configuration

```python
# Export MCP config to JSON
config = agent.export_mcp_config()
print(json.dumps(config, indent=2))
```

## Common MCP Servers

### Filesystem

```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
  }
}
```

### GitHub

```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "ghp_..."
    }
  }
}
```

### PostgreSQL

```json
{
  "postgres": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
  }
}
```

### Slack

```json
{
  "slack": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-slack"],
    "env": {
      "SLACK_TOKEN": "xoxb-..."
    }
  }
}
```

## Best Practices

1. **Use Deferred Loading**: For servers with many tools
2. **Search Before Loading**: Find specific tools first
3. **Cleanup Connections**: Always cleanup MCP connections
4. **Handle Failures**: MCP servers may be unavailable
5. **Cache Results**: Cache tool schemas for performance

## Next Steps

- [MCP API Reference](../api/mcp.md)
- [MCP Examples](../examples/mcp/)
- [Creating MCP Servers](../tutorials/mcp-server.md)
