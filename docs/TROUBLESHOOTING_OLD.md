# Troubleshooting Guide

## Common Errors and Solutions

### 1. "model output must contain either output text or tool calls"

**Cause**: The LLM (usually Gemini) returned an empty response. This can happen due to:
- Content filtering/safety blocks
- Model limitations
- Invalid or problematic input
- API issues

**Solutions**:
1. **Try a different model**:
   ```bash
   # For Gemini, try different versions
   python run_agent.py --provider gemini --model gemini-1.5-flash
   python run_agent.py --provider gemini --model gemini-1.5-pro
   
   # Or switch to a different provider
   python run_agent.py --provider ollama
   python run_agent.py --provider groq
   ```

2. **Rephrase your question**: Some inputs may trigger content filters
   
3. **Check API status**: Ensure your API key is valid and the service is operational

4. **Use Ollama for local/offline work**:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3.2
   python run_agent.py --provider ollama --model llama3.2
   ```

### 2. "Ollama returned empty message"

**Cause**: Ollama model returned no content

**Solutions**:
1. **Check if Ollama is running**:
   ```bash
   ollama list  # Should show installed models
   ollama ps    # Should show running models
   ```

2. **Pull a different model**:
   ```bash
   ollama pull llama3.2
   ollama pull mistral
   ollama pull qwen2.5
   ```

3. **Restart Ollama service**:
   - Windows: Restart from system tray
   - Linux/Mac: `systemctl restart ollama` or restart the app

### 3. Connection/MCP Errors

**Cause**: Issues connecting to MCP servers

**Solutions**:
1. **Run without MCP** (standard mode):
   ```bash
   python run_agent.py --mode standard
   ```

2. **Check mcp.json configuration**:
   - Ensure file paths are correct
   - Verify Python environment paths
   - Check server scripts exist

3. **Test MCP servers separately**:
   ```bash
   # Test the MCP server directly
   python -m Agentry.mcp_client
   ```

### 4. API Key Issues

**Cause**: Missing or invalid API keys

**Solutions**:
1. **Set environment variables**:
   ```bash
   # Windows (PowerShell)
   $env:GROQ_API_KEY="your-key-here"
   $env:GEMINI_API_KEY="your-key-here"
   
   # Linux/Mac
   export GROQ_API_KEY="your-key-here"
   export GEMINI_API_KEY="your-key-here"
   ```

2. **Or provide when prompted**: The script will ask for keys if not found

### 5. Session/History Errors

**Cause**: Corrupted session files or permission issues

**Solutions**:
1. **Clear session history**:
   ```bash
   # Delete session_history folder
   rm -rf Agentry/session_history/*
   ```

2. **Start fresh session**:
   ```bash
   python run_agent.py --session new-session-name
   ```

## Best Practices

### 1. Choose the Right Provider

- **Ollama**: Best for local/offline, privacy, no API costs
- **Groq**: Fast inference, good for production, requires API key
- **Gemini**: Advanced capabilities, good for complex tasks, requires API key

### 2. Model Selection

**For Ollama**:
- `llama3.2`: Good balance of speed and quality
- `qwen2.5`: Excellent for coding tasks
- `mistral`: Fast and efficient

**For Groq**:
- `llama-3.3-70b-versatile`: Best quality
- `mixtral-8x7b-32768`: Good for long context

**For Gemini**:
- `gemini-1.5-flash`: Fast and cost-effective
- `gemini-1.5-pro`: Best quality

### 3. Agent Modes

- **Standard**: General purpose, session persistence
- **MCP**: Multi-session, advanced tool integration
- **Copilot**: Specialized for coding tasks

## Getting Help

If you continue to experience issues:

1. **Enable debug mode**: Already enabled by default in `run_agent.py`
2. **Check logs**: Look for detailed error messages in console
3. **Test with simple queries**: Start with "Hello" to verify basic functionality
4. **Try different combinations**: Different provider + model + mode

## Quick Start (Recommended)

For the most reliable experience:

```bash
# 1. Install and start Ollama
ollama pull llama3.2

# 2. Run in standard mode
python run_agent.py --mode standard --provider ollama --model llama3.2

# 3. Test with a simple query
You: Hello, can you help me?
```

This avoids API issues and provides a consistent local experience.
