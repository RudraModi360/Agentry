# MCP Server Configuration Guide

This guide explains how to configure Agentry as an MCP (Model Context Protocol) server that can be used by MCP clients like Claude Desktop, VS Code extensions, and other compatible applications.

---

## 📋 Table of Contents

- [What is MCP?](#what-is-mcp)
- [Quick Setup](#quick-setup)
- [Configuration Files](#configuration-files)
- [Integration with MCP Clients](#integration-with-mcp-clients)
- [Available Configurations](#available-configurations)
- [Troubleshooting](#troubleshooting)

---

## What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol that allows AI applications to:
- Discover and use external tools
- Access resources and data sources
- Maintain consistent interfaces across different AI systems
- Enable interoperability between AI agents and applications

Agentry implements MCP to expose its tools and capabilities to any MCP-compatible client.

---

## Quick Setup

### For Claude Desktop

1. **Locate Claude Desktop Config**
   
   The configuration file is located at:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add Agentry Server**
   
   Open the config file and add:
   
   ```json
   {
     "mcpServers": {
       "agentry": {
         "command": "python",
         "args": ["D:\\Scratchy\\src\\main.py", "--mcp-mode"],
         "env": {
           "AGENTRY_MODE": "mcp"
         }
       }
     }
   }
   ```
   
   **Important**: Replace `D:\\Scratchy` with your actual Agentry installation path.

3. **Restart Claude Desktop**
   
   Close and reopen Claude Desktop to load the new MCP server.

4. **Verify Connection**
   
   In Claude Desktop, you should now see Agentry's tools available in the tool picker.

---

## Configuration Files

Agentry provides two MCP configuration files:

### 1. `mcp_simple.json` - Minimal Configuration

**Use this for**: Quick setup with Claude Desktop or simple integrations

```json
{
  "mcpServers": {
    "agentry": {
      "command": "python",
      "args": ["D:\\Scratchy\\src\\main.py", "--mcp-mode"],
      "env": {
        "AGENTRY_MODE": "mcp"
      }
    }
  }
}
```

**Features:**
- ✅ Minimal setup
- ✅ Auto-detects provider
- ✅ Uses default settings

---

### 2. `mcp.json` - Full Configuration

**Use this for**: Advanced setups with multiple providers and custom configurations

```json
{
  "mcpServers": {
    "agentry-ollama": {
      "command": "python",
      "args": [
        "src/main.py",
        "--mcp-mode",
        "--provider", "ollama",
        "--model", "gpt-oss:20b-cloud"
      ],
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "AGENTRY_MODE": "mcp"
      }
    },
    "agentry-groq": {
      "command": "python",
      "args": [
        "src/main.py",
        "--mcp-mode",
        "--provider", "groq",
        "--model", "llama-3.3-70b-versatile"
      ],
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "AGENTRY_MODE": "mcp",
        "GROQ_API_KEY": "${GROQ_API_KEY}"
      }
    }
  }
}
```

**Features:**
- ✅ Multiple server configurations
- ✅ Provider-specific setups
- ✅ Custom models
- ✅ Environment variable support

---

## Integration with MCP Clients

### Claude Desktop

**Setup:**
1. Copy the contents of `mcp_simple.json`
2. Paste into `claude_desktop_config.json`
3. Update the path to match your installation
4. Restart Claude Desktop

**Usage:**
- Agentry tools will appear in Claude's tool picker
- Claude can now use web search, file operations, and code execution
- All tool approvals will be handled through Claude's interface

---

### VS Code MCP Extension

**Setup:**
1. Install an MCP extension for VS Code
2. Add Agentry to the extension's configuration
3. Use the full `mcp.json` configuration for best results

**Configuration:**
```json
{
  "mcp.servers": {
    "agentry": {
      "command": "python",
      "args": ["${workspaceFolder}/src/main.py", "--mcp-mode"]
    }
  }
}
```

---

### Custom MCP Client

**Setup:**
1. Use the MCP SDK for your language
2. Point to Agentry's MCP server
3. Configure according to your client's requirements

**Example (Python MCP Client):**
```python
from mcp import Client

client = Client()
client.connect_to_server(
    command="python",
    args=["src/main.py", "--mcp-mode"]
)

# List available tools
tools = client.list_tools()
print(tools)

# Call a tool
result = client.call_tool("web_search", {
    "user_input": "Python tutorials",
    "search_type": "general"
})
```

---

## Available Configurations

### Server Variants

The `mcp.json` file includes several pre-configured server variants:

| Server Name | Provider | Model | Use Case |
|-------------|----------|-------|----------|
| `agentry` | Auto-detect | Default | General purpose |
| `agentry-ollama` | Ollama | gpt-oss:20b-cloud | Free, local/cloud |
| `agentry-groq` | Groq | llama-3.3-70b-versatile | Fast inference |
| `agentry-gemini` | Gemini | gemini-pro | Multimodal tasks |

### Environment Variables

Configure these in your MCP client or `.env` file:

```bash
# Required for Groq
GROQ_API_KEY=your_groq_api_key

# Required for Gemini
GEMINI_API_KEY=your_gemini_api_key

# Optional for Ollama
OLLAMA_HOST=http://localhost:11434

# Agentry settings
AGENTRY_MODE=mcp
AGENTRY_DEBUG=false
AGENTRY_MAX_ITERATIONS=20
```

---

## Tool Categories

Agentry exposes the following tool categories via MCP:

### 🌐 Web Tools
- `web_search` - DuckDuckGo search (safe, no approval)
- `url_fetch` - Fetch URL content (safe, no approval)

### 📁 File System Tools
- `read_file` - Read files (safe, no approval)
- `list_files` - List directory contents (safe, no approval)
- `search_files` - Search for files (safe, no approval)
- `fast_grep` - Text search in files (safe, no approval)
- `create_file` - Create new files (requires approval)
- `edit_file` - Edit existing files (requires approval)
- `delete_file` - Delete files (dangerous, requires approval)

### 💻 Execution Tools
- `code_execute` - Execute Python code (requires approval)
- `execute_command` - Run shell commands (dangerous, requires approval)

---

## Prompts

Agentry provides pre-configured system prompts via MCP:

| Prompt Name | Description |
|-------------|-------------|
| `system_default` | General-purpose assistant |
| `coding_assistant` | Software engineering help |
| `research_assistant` | Research and information gathering |
| `file_manager` | File organization and management |

**Using prompts in Claude Desktop:**
```
Use the "coding_assistant" prompt from Agentry
```

---

## Troubleshooting

### Server Not Appearing in Claude Desktop

**Check:**
1. ✅ Config file path is correct
2. ✅ Python is in your PATH
3. ✅ Agentry path is absolute and correct
4. ✅ Claude Desktop was restarted

**Fix:**
```bash
# Test if server starts manually
python D:\Scratchy\src\main.py --mcp-mode

# Check Python path
python --version
```

---

### Tools Not Working

**Check:**
1. ✅ API keys are set (for Groq/Gemini)
2. ✅ Ollama is running (for Ollama provider)
3. ✅ Dependencies are installed

**Fix:**
```bash
# Install dependencies
cd D:\Scratchy
uv sync

# Test tools manually
python src/main.py
# Select mode 2 (MCP Agent)
```

---

### Permission Errors

**Issue:** Tools requiring approval fail silently

**Fix:**
- In Claude Desktop, approval prompts should appear automatically
- For custom clients, implement approval callbacks
- Set `autoApprove: true` in config (use with caution!)

---

### Path Issues on Windows

**Issue:** Backslashes in paths cause errors

**Fix:**
Use double backslashes or forward slashes:
```json
// Good
"args": ["D:\\Scratchy\\src\\main.py"]
"args": ["D:/Scratchy/src/main.py"]

// Bad
"args": ["D:\Scratchy\src\main.py"]
```

---

## Advanced Configuration

### Custom Tool Approval

Create a custom approval handler:

```json
{
  "mcpServers": {
    "agentry-auto": {
      "command": "python",
      "args": ["src/main.py", "--mcp-mode", "--auto-approve"],
      "env": {
        "AGENTRY_AUTO_APPROVE": "true"
      }
    }
  }
}
```

---

### Debug Mode

Enable detailed logging:

```json
{
  "mcpServers": {
    "agentry-debug": {
      "command": "python",
      "args": ["src/main.py", "--mcp-mode", "--debug"],
      "env": {
        "AGENTRY_DEBUG": "true"
      }
    }
  }
}
```

---

### Session Timeout

Configure session timeout (in seconds):

```json
{
  "configuration": {
    "sessionTimeout": 1800  // 30 minutes
  }
}
```

---

## Testing Your Setup

### 1. Manual Test

```bash
# Start Agentry in MCP mode
python src/main.py --mcp-mode

# Should see:
# "MCP Server started on stdio"
```

### 2. Test with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Inspect Agentry
mcp-inspector python src/main.py --mcp-mode
```

### 3. Test in Claude Desktop

1. Open Claude Desktop
2. Start a new conversation
3. Look for Agentry tools in the tool picker
4. Try a simple command:
   ```
   Use the web_search tool to find information about Python
   ```

---

## Example Configurations

### For Development

```json
{
  "mcpServers": {
    "agentry-dev": {
      "command": "python",
      "args": [
        "${workspaceFolder}/src/main.py",
        "--mcp-mode",
        "--debug"
      ],
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "AGENTRY_MODE": "mcp",
        "AGENTRY_DEBUG": "true"
      }
    }
  }
}
```

### For Production

```json
{
  "mcpServers": {
    "agentry-prod": {
      "command": "python",
      "args": [
        "/opt/agentry/src/main.py",
        "--mcp-mode",
        "--provider", "groq"
      ],
      "env": {
        "AGENTRY_MODE": "mcp",
        "GROQ_API_KEY": "${GROQ_API_KEY}",
        "AGENTRY_MAX_ITERATIONS": "30"
      }
    }
  }
}
```

---

## Security Considerations

### Tool Approval

- ⚠️ **Never** set `autoApprove: true` in untrusted environments
- 🔒 Always review file deletion and command execution requests
- ✅ Safe tools (read_file, web_search) don't require approval

### API Keys

- 🔑 Store API keys in environment variables, not in config files
- 🔒 Use `.env` files and add them to `.gitignore`
- ✅ Rotate keys regularly

### File Access

- 📁 Agentry can only access files the Python process has permissions for
- 🔒 Consider running in a sandboxed environment for untrusted use
- ✅ Review file paths before approving operations

---

## Next Steps

1. ✅ Set up your MCP client with Agentry
2. ✅ Test basic tools (web_search, read_file)
3. ✅ Configure your preferred LLM provider
4. ✅ Explore advanced features in [MCP_AGENT.md](MCP_AGENT.md)
5. ✅ Build custom tools for your use case

---

## Resources

- **MCP Specification**: https://modelcontextprotocol.io
- **Claude Desktop**: https://claude.ai/desktop
- **Agentry Documentation**: [README.md](../README.md)
- **MCP Agent Guide**: [MCP_AGENT.md](MCP_AGENT.md)

---

**Questions or Issues?**
- Open an issue: https://github.com/RudraModi360/Agentry/issues
- Email: rudramodi9560@gmail.com

---

**Built with ❤️ for the Agentry Framework**
