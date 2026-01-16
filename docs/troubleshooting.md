---
layout: page
title: Troubleshooting
nav_order: 9
description: "Common issues and their solutions"
---

# Troubleshooting Guide

Common issues and their solutions when working with Agentry.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [LLM Provider Issues](#llm-provider-issues)
3. [Tool Execution Issues](#tool-execution-issues)
4. [Session Management Issues](#session-management-issues)
5. [MCP Integration Issues](#mcp-integration-issues)
6. [Performance Issues](#performance-issues)
7. [Common Error Messages](#common-error-messages)
8. [Diagnostic Commands](#diagnostic-commands)
9. [Getting Help](#getting-help)

---

## Installation Issues

### Import Error: No module named 'agentry'

**Problem:** Python cannot find the Agentry module.

**Solution:**

```bash
# Verify installation
pip show agentry-community

# If not installed
pip install agentry-community

# If installed from source, ensure you're in the correct directory
cd Agentry
pip install -e .
```

Or add to your Python path:

```python
import sys
sys.path.insert(0, '/path/to/Agentry')
from agentry import Agent
```

---

### Dependency Installation Fails

**Problem:** `pip install` fails with dependency errors.

**Solution:**

```bash
# Update pip
python -m pip install --upgrade pip

# Try installing from source
pip install -e .

# If specific package fails
pip install <package-name>

# Use virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -e .
```

---

### Python Version Issues

**Problem:** "Python 3.11+ required" error.

**Solution:**

```bash
# Check your Python version
python --version

# Install Python 3.11 or higher from python.org

# Use pyenv for multiple versions
pyenv install 3.11
pyenv local 3.11
```

---

## LLM Provider Issues

### Ollama: Connection Refused

**Problem:** `ConnectionError: [Errno 111] Connection refused`

**Solution:**

```bash
# Start Ollama server
ollama serve

# Check if running
ollama list

# On Windows, check system tray for Ollama icon
# On macOS/Linux, check with:
ps aux | grep ollama
```

---

### Ollama: Model Not Found

**Problem:** `Error: model 'llama3.2' not found`

**Solution:**

```bash
# List available models
ollama list

# Pull the required model
ollama pull llama3.2

# Or use a different model
ollama pull llama3.2:3b
```

Update your code:

```python
agent = Agent(llm="ollama", model="llama3.2")
```

---

### Groq: Authentication Error

**Problem:** `AuthenticationError: Invalid API key`

**Solution:**

```bash
# Set environment variable
export GROQ_API_KEY="your-api-key"

# On Windows PowerShell
$env:GROQ_API_KEY="your-api-key"
```

Or pass directly in code:

```python
agent = Agent(
    llm="groq",
    model="llama-3.3-70b-versatile",
    api_key="your-api-key"
)
```

Verify your key at [console.groq.com](https://console.groq.com/).

---

### Gemini: Permission Denied

**Problem:** `google.api_core.exceptions.PermissionDenied`

**Solution:**

```bash
# Set environment variable
export GEMINI_API_KEY="your-api-key"

# Get a key from https://ai.google.dev/
# Ensure the Gemini API is enabled
```

---

### Azure: Endpoint Issues

**Problem:** Connection errors with Azure OpenAI

**Solution:**

```python
agent = Agent(
    llm="azure",
    model="your-deployment-name",  # Not model name, deployment name
    api_key="your-azure-key",
    endpoint="https://your-resource.openai.azure.com"  # Include full URL
)
```

Verify:
- Endpoint URL is correct
- Deployment name matches Azure portal
- API key has correct permissions

---

### Empty Response Error

**Problem:** `model output must contain either output text or tool calls`

**Cause:** The LLM returned an empty response.

**Solutions:**

1. **Enable debug mode:**
   ```python
   agent = Agent(llm="ollama", debug=True)
   ```

2. **Try a different model:**
   ```python
   agent = Agent(llm="ollama", model="llama3.2:latest")
   ```

3. **Simplify your prompt:**
   ```python
   # Instead of complex multi-step requests
   await agent.chat("Do A, then B, then C")
   
   # Break it down
   await agent.chat("Do A")
   await agent.chat("Now do B")
   await agent.chat("Finally do C")
   ```

4. **Reduce tool count:**
   ```python
   agent = Agent(llm="ollama")
   # Only register specific tools needed
   agent.register_tool_from_function(my_tool)
   ```

---

### Rate Limiting

**Problem:** `RateLimitError: Too many requests`

**Solution:**

```python
import asyncio

# Add delays between requests
await agent.chat("First request")
await asyncio.sleep(1)
await agent.chat("Second request")

# Or use local provider (no rate limits)
agent = Agent(llm="ollama")
```

---

## Tool Execution Issues

### Tool Not Found

**Problem:** Agent says "I don't have a tool for that"

**Solution:**

```python
# Load default tools
agent.load_default_tools()

# Or register your custom tool
agent.register_tool_from_function(my_tool)

# Check available tools
tools = await agent.get_all_tools()
print([t['function']['name'] for t in tools])
```

---

### Tool Execution Fails

**Problem:** Tool returns an error

**Solutions:**

1. **Test the tool directly:**
   ```python
   from agentry.tools import execute_tool
   result = execute_tool("read_file", {"path": "test.txt"})
   print(result)
   ```

2. **Enable debug mode:**
   ```python
   agent = Agent(llm="ollama", debug=True)
   ```

3. **Handle errors in custom tools:**
   ```python
   def my_tool(arg: str) -> str:
       """My tool."""
       try:
           result = do_something(arg)
           return str(result)
       except Exception as e:
           return f"Error: {str(e)}"
   ```

---

### Permission Denied Errors

**Problem:** `PermissionError: [Errno 13] Permission denied`

**Solution:**

```bash
# Check file permissions (Linux/macOS)
ls -l filename
chmod +r filename

# On Windows, check file properties
# Ensure file is not open in another program
```

---

### File Not Found

**Problem:** `FileNotFoundError: [Errno 2] No such file or directory`

**Solution:**

```python
import os

# Use absolute paths
file_path = os.path.abspath("myfile.txt")

# Check current directory
print(os.getcwd())

# Verify file exists
if os.path.exists("myfile.txt"):
    await agent.chat("Read myfile.txt")
```

---

## Session Management Issues

### Session Not Persisting

**Problem:** Session data is lost between runs

**Solution:**

```python
from agentry.session_manager import SessionManager

sm = SessionManager(storage_dir="./sessions")

# Save after chatting
session = agent.get_session("my_session")
sm.save_session("my_session", session.messages)

# Load before chatting
messages = sm.load_session("my_session")
if messages:
    session.messages = messages
```

---

### Session File Corrupted

**Problem:** `JSONDecodeError` when loading session

**Solution:**

```bash
# Check the session file
cat sessions/my_session.toon

# If corrupted, delete and start fresh
rm sessions/my_session.toon
```

Or handle in code:

```python
try:
    messages = sm.load_session(session_id)
except Exception as e:
    print(f"Error loading session: {e}")
    sm.delete_session(session_id)
    agent.get_session(session_id)
```

---

### Memory Issues with Large Sessions

**Problem:** Session grows too large, causing slowdowns

**Solution:**

```python
session = agent.get_session(session_id)

# Clear old messages
if len(session.messages) > 100:
    session.messages = session.messages[-50:]

# Save trimmed session
sm.save_session(session_id, session.messages)
```

---

## MCP Integration Issues

### MCP Server Won't Start

**Problem:** `Failed to connect to MCP server`

**Solution:**

```bash
# Check if npx is installed
npx --version

# Install Node.js if needed (visit nodejs.org)

# Test the MCP server manually
npx -y @modelcontextprotocol/server-excel

# Validate mcp.json syntax
cat mcp.json | python -m json.tool
```

---

### MCP Tools Not Available

**Problem:** Agent cannot see MCP tools

**Solution:**

```python
# Verify connection
await agent.add_mcp_server("mcp.json")

# Check if tools were loaded
tools = await agent.get_all_tools()
print([t['function']['name'] for t in tools])

# Enable debug mode
agent = Agent(llm="ollama", debug=True)
await agent.add_mcp_server("mcp.json")
```

---

### MCP Server Crashes

**Problem:** MCP server stops responding

**Solution:**

```python
# Cleanup and reconnect
await agent.cleanup()

# Create new agent
agent = Agent(llm="ollama")
await agent.add_mcp_server("mcp.json")
```

---

## Performance Issues

### Slow Response Times

**Solutions:**

1. **Use a faster provider:**
   ```python
   # Groq is typically fastest
   agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="...")
   ```

2. **Reduce tool count:**
   ```python
   # Only load specific tools
   agent.register_tool_from_function(specific_tool)
   ```

3. **Use smaller models:**
   ```python
   agent = Agent(llm="ollama", model="llama3.2:3b")
   ```

4. **Limit max iterations:**
   ```python
   agent = Agent(llm="ollama", max_iterations=5)
   ```

---

### High Memory Usage

**Solutions:**

```python
# Clear sessions periodically
agent.clear_session("my_session")

# Limit conversation history
session = agent.get_session("my_session")
if len(session.messages) > 50:
    session.messages = session.messages[-30:]
```

---

## Common Error Messages

### "Max iterations reached"

**Cause:** Agent could not complete the task in 20 iterations.

**Solution:**

```python
# Increase max iterations
agent = Agent(llm="ollama", max_iterations=50)

# Or break down the task
await agent.chat("First, do step 1")
await agent.chat("Now do step 2")
```

---

### "Tool execution denied by user"

**Cause:** User rejected a dangerous tool call.

**Solution:**

```python
# Auto-approve if you trust the operation
async def auto_approve(session_id, tool_name, args):
    return True

agent.set_callbacks(on_tool_approval=auto_approve)
```

---

### "JSON decode error"

**Cause:** LLM returned invalid JSON for tool arguments.

**Solution:**

```python
# Try a more capable model
agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="...")

# Or use a different local model
agent = Agent(llm="ollama", model="llama3.2:latest")
```

---

## Diagnostic Commands

### Check Ollama Status

```bash
ollama list
ollama ps
curl http://localhost:11434/api/tags
```

### Check Python Environment

```bash
python --version
pip list | grep agentry
```

### Check MCP Configuration

```bash
cat mcp.json | python -m json.tool
npx --version
```

---

## Getting Help

If you are still experiencing issues:

1. **Enable debug mode:**
   ```python
   agent = Agent(llm="ollama", debug=True)
   ```

2. **Check the logs** for detailed error messages

3. **Search existing issues:** [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)

4. **Open a new issue** with:
   - Python version
   - Agentry version
   - LLM provider and model
   - Full error traceback
   - Minimal code to reproduce

5. **Join discussions:** [GitHub Discussions](https://github.com/RudraModi360/Agentry/discussions)

6. **Email:** rudramodi9560@gmail.com
