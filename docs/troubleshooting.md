# Troubleshooting Guide

Common issues and their solutions when working with Scratchy.

## Table of Contents

- [Installation Issues](#installation-issues)
- [LLM Provider Issues](#llm-provider-issues)
- [Tool Execution Issues](#tool-execution-issues)
- [Session Management Issues](#session-management-issues)
- [MCP Integration Issues](#mcp-integration-issues)
- [Performance Issues](#performance-issues)
- [Common Error Messages](#common-error-messages)

## Installation Issues

### Import Error: No module named 'scratchy'

**Problem:** Python can't find the Scratchy module.

**Solution:**
```bash
# Make sure you're in the Scratchy directory
cd Scratchy

# Verify the directory structure
ls  # Should see scratchy/ folder

# Run from the parent directory
python -c "import sys; sys.path.insert(0, '.'); from scratchy import Agent"
```

Or add to your Python path:
```python
import sys
sys.path.insert(0, '/path/to/Scratchy')
from scratchy import Agent
```

### Dependency Installation Fails

**Problem:** `uv sync` or `pip install` fails.

**Solution:**
```bash
# Try using pip directly
pip install -r requirements.txt

# If specific package fails, install it separately
pip install <package-name>

# Update pip
python -m pip install --upgrade pip

# Use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Python Version Issues

**Problem:** "Python 3.11+ required"

**Solution:**
```bash
# Check your Python version
python --version

# Install Python 3.11 or higher
# Visit https://www.python.org/downloads/

# Use pyenv to manage multiple versions
pyenv install 3.11
pyenv local 3.11
```

## LLM Provider Issues

### Ollama: Connection Refused

**Problem:** `ConnectionError: [Errno 111] Connection refused`

**Solution:**
```bash
# Start Ollama server
ollama serve

# Or check if it's running
ps aux | grep ollama

# On Windows, Ollama runs as a service
# Check system tray for Ollama icon
```

### Ollama: Model Not Found

**Problem:** `Error: model 'gpt-oss:20b' not found`

**Solution:**
```bash
# List available models
ollama list

# Pull the model
ollama pull gpt-oss:20b

# Or use a different model
ollama pull llama3.2
```

Then update your code:
```python
agent = Agent(llm="ollama", model="llama3.2")
```

### Groq: Authentication Error

**Problem:** `AuthenticationError: Invalid API key`

**Solution:**
```bash
# Set environment variable
export GROQ_API_KEY="your-actual-api-key"

# Or pass directly in code
agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="your-key")

# Verify the key is correct at https://console.groq.com/
```

### Gemini: API Key Issues

**Problem:** `google.api_core.exceptions.PermissionDenied`

**Solution:**
```bash
# Set environment variable
export GEMINI_API_KEY="your-actual-api-key"

# Get a key from https://ai.google.dev/

# Enable the Gemini API in Google Cloud Console
```

### Empty Response Error

**Problem:** `model output must contain either output text or tool calls`

**Cause:** The LLM returned an empty response (common with some models/prompts).

**Solution:**

Scratchy has built-in retry logic, but you can:

1. **Enable debug mode** to see what's happening:
```python
agent = Agent(llm="ollama", debug=True)
```

2. **Try a different model:**
```python
# If using Ollama
agent = Agent(llm="ollama", model="llama3.2:latest")

# If using Groq
agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="...")
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
# Don't load all tools if not needed
agent = Agent(llm="ollama")
# Only register specific tools you need
agent.register_tool_from_function(my_tool)
```

### Rate Limiting

**Problem:** `RateLimitError: Too many requests`

**Solution:**
```python
import asyncio

# Add delays between requests
await agent.chat("First request")
await asyncio.sleep(1)  # Wait 1 second
await agent.chat("Second request")

# Or use a different provider with higher limits
agent = Agent(llm="ollama")  # No rate limits for local
```

## Tool Execution Issues

### Tool Not Found

**Problem:** Agent says "I don't have a tool for that"

**Solution:**
```python
# Make sure you loaded the tools
agent.load_default_tools()

# Or register your custom tool
agent.register_tool_from_function(my_tool)

# Check what tools are available
tools = await agent.get_all_tools()
print([t['function']['name'] for t in tools])
```

### Tool Execution Fails

**Problem:** Tool returns an error

**Solution:**

1. **Test the tool directly:**
```python
from scratchy.tools import execute_tool

result = execute_tool("read_file", {"path": "test.txt"})
print(result)
```

2. **Check tool arguments:**
```python
# Enable debug mode to see what arguments the LLM is passing
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

### Permission Denied Errors

**Problem:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```bash
# Check file permissions
ls -l filename

# Make file readable
chmod +r filename

# Run with appropriate permissions
sudo python your_script.py  # Use cautiously!
```

### File Not Found

**Problem:** `FileNotFoundError: [Errno 2] No such file or directory`

**Solution:**
```python
# Use absolute paths
import os
file_path = os.path.abspath("myfile.txt")

# Or check current directory
print(os.getcwd())

# Verify file exists before using
if os.path.exists("myfile.txt"):
    await agent.chat("Read myfile.txt")
```

## Session Management Issues

### Session Not Persisting

**Problem:** Session data is lost between runs

**Solution:**
```python
from scratchy.session_manager import SessionManager

# Create session manager
manager = SessionManager(storage_dir="./sessions")

# Save after chatting
session = agent.get_session("my_session")
await manager.save_session(session)

# Load before chatting
loaded = await manager.load_session("my_session")
agent.sessions["my_session"] = loaded
```

### Session File Corrupted

**Problem:** `JSONDecodeError` when loading session

**Solution:**
```bash
# Check the session file
cat sessions/my_session.toon

# If corrupted, delete and start fresh
rm sessions/my_session.toon

# Or restore from backup if available
cp sessions/my_session.toon.backup sessions/my_session.toon
```

### Memory Issues with Large Sessions

**Problem:** Session grows too large, causing slowdowns

**Solution:**
```python
# Clear old messages
agent.clear_session("my_session")

# Or keep only recent messages
session = agent.get_session("my_session")
session.messages = session.messages[-20:]  # Keep last 20 messages

# Use separate sessions for different topics
await agent.chat("Topic A", session_id="session_a")
await agent.chat("Topic B", session_id="session_b")
```

## MCP Integration Issues

### MCP Server Won't Start

**Problem:** `Failed to connect to MCP server`

**Solution:**
```bash
# Check if npx is installed
npx --version

# Install Node.js if needed
# Visit https://nodejs.org/

# Test the MCP server manually
npx -y @modelcontextprotocol/server-excel

# Check mcp.json syntax
cat mcp.json | python -m json.tool
```

### MCP Tools Not Available

**Problem:** Agent can't see MCP tools

**Solution:**
```python
# Make sure you connected to the server
await agent.add_mcp_server("mcp.json")

# Check if tools were loaded
tools = await agent.get_all_tools()
mcp_tools = [t for t in tools if 'excel' in t['function']['name'].lower()]
print(mcp_tools)

# Enable debug mode
agent = Agent(llm="ollama", debug=True)
await agent.add_mcp_server("mcp.json")
```

### MCP Server Crashes

**Problem:** MCP server stops responding

**Solution:**
```python
# Cleanup and reconnect
await agent.cleanup()

# Restart the agent
agent = Agent(llm="ollama")
await agent.add_mcp_server("mcp.json")
```

## Performance Issues

### Slow Response Times

**Problem:** Agent takes too long to respond

**Solutions:**

1. **Use a faster provider:**
```python
# Groq is typically fastest
agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="...")
```

2. **Reduce tool count:**
```python
# Don't load all tools
# agent.load_default_tools()  # Skip this

# Only add what you need
agent.register_tool_from_function(specific_tool)
```

3. **Use smaller models:**
```python
# Instead of large models
agent = Agent(llm="ollama", model="llama3.2:3b")  # Smaller, faster
```

4. **Limit max iterations:**
```python
agent = Agent(llm="ollama", max_iterations=5)  # Default is 20
```

### High Memory Usage

**Problem:** Python process uses too much RAM

**Solution:**
```python
# Clear sessions periodically
agent.clear_session("my_session")

# Use separate processes for different tasks
# Instead of one long-running agent

# Limit conversation history
session = agent.get_session("my_session")
if len(session.messages) > 50:
    session.messages = session.messages[-30:]  # Keep last 30
```

## Common Error Messages

### "Max iterations reached"

**Cause:** Agent couldn't complete the task in 20 iterations.

**Solution:**
```python
# Increase max iterations
agent = Agent(llm="ollama", max_iterations=50)

# Or break down the task
await agent.chat("First, do step 1")
await agent.chat("Now do step 2")
```

### "Tool execution denied by user"

**Cause:** User rejected a dangerous tool call.

**Solution:**
```python
# Auto-approve if you trust the operation
async def auto_approve(session_id, tool_name, args):
    return True  # Always approve

agent.set_callbacks(on_tool_approval=auto_approve)

# Or remove from approval list (use cautiously!)
from scratchy.tools import APPROVAL_REQUIRED_TOOLS
APPROVAL_REQUIRED_TOOLS.discard("run_shell_command")
```

### "JSON decode error"

**Cause:** LLM returned invalid JSON for tool arguments.

**Solution:**
```python
# This is usually a model issue - try a different model
agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="...")

# Or use a more capable local model
agent = Agent(llm="ollama", model="llama3.2:latest")
```

## Getting Help

If you're still stuck:

1. **Enable debug mode:**
```python
agent = Agent(llm="ollama", debug=True)
```

2. **Check the logs** for detailed error messages

3. **Search existing issues:** [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)

4. **Open a new issue** with:
   - Your Python version
   - Scratchy version
   - LLM provider and model
   - Full error traceback
   - Minimal code to reproduce

5. **Join discussions:** [GitHub Discussions](https://github.com/RudraModi360/Agentry/discussions)

---

**Still need help?** Email: rudramodi9560@gmail.com
