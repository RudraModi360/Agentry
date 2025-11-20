# API Setup Guide

Complete guide for setting up API keys and configuring different LLM providers for Agentry.

---

## 🌟 Ollama Cloud Models (Recommended - FREE!)

**Best for:** Getting started quickly, no configuration needed

### ✨ Tested Cloud Models

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| `gpt-oss:20b-cloud` | 20B | ⚡⚡⚡ Fast | General use, quick responses |
| `gpt-oss:120b-cloud` | 120B | ⚡⚡ Moderate | Complex tasks, better reasoning |
| `glm-4.6:cloud` | - | ⚡⚡ Moderate | Alternative option |
| `minimax-m2:cloud` | - | ⚡⚡ Moderate | Another alternative |

### Setup Steps

1. **Install Ollama Client**
   ```bash
   # Windows
   # Download from: https://ollama.com/download
   
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Run the Agent**
   ```bash
   python src/main.py
   ```

3. **Select Ollama and Enter Cloud Model**
   ```
   Select a provider:
   1. Ollama
   Enter choice (1-3): 1
   
   Enter Ollama model (default: gpt-oss:20b-cloud): gpt-oss:20b-cloud
   ```

4. **Start Chatting!**
   - No API key needed
   - No model download required
   - Works immediately

### 💡 Pro Tips

- Cloud models end with `:cloud` suffix
- No need to run `ollama pull` for cloud models
- Switch between cloud models anytime
- Free to use (as of now)

---

## 🏠 Ollama Local Models

**Best for:** Privacy, offline use, full control

### Recommended Local Models

| Model | Size | Download | Tool Calling |
|-------|------|----------|--------------|
| `llama3.1` | 8B | 4.7GB | ✅ Yes |
| `llama3.2` | 8B | 4.7GB | ✅ Yes |
| `mistral-nemo` | 12B | 7.1GB | ✅ Yes |
| `qwen2.5` | 7B | 4.7GB | ✅ Yes |

### Setup Steps

1. **Install Ollama** (same as above)

2. **Pull a Model**
   ```bash
   # Choose one:
   ollama pull llama3.1        # Recommended
   ollama pull llama3.2        # Latest
   ollama pull mistral-nemo    # Larger, more capable
   ollama pull qwen2.5         # Fast alternative
   ```

3. **Verify Installation**
   ```bash
   ollama list
   ```
   You should see your downloaded model listed.

4. **Run the Agent**
   ```bash
   python src/main.py
   # Select: 1. Ollama
   # Enter model: llama3.1  (or whichever you pulled)
   ```

### ⚠️ Important Notes

- **Tool calling support required** - Not all models work!
- Models without tool calling will fail or give generic responses
- Local models require significant disk space
- Performance depends on your hardware (CPU/GPU)

### Troubleshooting

**Model not found:**
```bash
ollama pull model-name  # Download the model first
```

**Ollama not responding:**
```bash
ollama serve  # Start Ollama service manually
```

**Check running models:**
```bash
ollama ps  # See currently loaded models
```

---

## ⚡ Groq API Setup

**Best for:** Blazing-fast inference, production use

### Features
- ⚡ Extremely fast inference
- 🆓 Generous free tier
- 🔒 Secure API access
- 📊 Usage dashboard

### Setup Steps

#### 1. Get API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for a free account (GitHub/Google login available)
3. Navigate to **API Keys** in the left sidebar
4. Click **Create API Key**
5. Give it a name (e.g., "Agentry")
6. Copy the key (starts with `gsk_...`)
   - ⚠️ **Save it now** - you won't see it again!

#### 2. Configure Environment

**Option A: Using .env file (Recommended)**

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your key
GROQ_API_KEY=gsk_your_actual_key_here_replace_this
```

**Option B: Environment Variable**

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY="gsk_your_actual_key_here"

# macOS/Linux (add to ~/.bashrc or ~/.zshrc for persistence)
export GROQ_API_KEY="gsk_your_actual_key_here"
```

#### 3. Run the Agent

```bash
python src/main.py
# Select: 2. Groq
# Enter model: llama-3.3-70b-versatile  (or press Enter for default)
```

### Available Models

| Model | Size | Context | Speed | Best For |
|-------|------|---------|-------|----------|
| `llama-3.3-70b-versatile` | 70B | 32K | ⚡⚡⚡ | Recommended, balanced |
| `llama-3.1-70b-versatile` | 70B | 128K | ⚡⚡⚡ | Long context |
| `mixtral-8x7b-32768` | 47B | 32K | ⚡⚡⚡ | Fast, efficient |
| `gemma2-9b-it` | 9B | 8K | ⚡⚡⚡ | Lightweight |

### Free Tier Limits

- **Requests:** Generous rate limits
- **Tokens:** Check dashboard for current limits
- **Models:** Access to all models
- **Usage:** Monitor at [console.groq.com](https://console.groq.com)

### Troubleshooting

**API key not found:**
```bash
# Check if .env file exists and has the key
cat .env  # macOS/Linux
type .env  # Windows

# Verify environment variable
echo $env:GROQ_API_KEY  # PowerShell
echo $GROQ_API_KEY      # macOS/Linux
```

**Rate limit errors:**
- Wait a few seconds and try again
- Check usage dashboard
- Consider upgrading plan if needed

---

## 🧠 Google Gemini API Setup

**Best for:** Multimodal tasks, Google ecosystem integration

### Features
- 🖼️ Multimodal capabilities (text + images)
- 🆓 Generous free tier
- 🚀 Fast inference
- 🔗 Google Cloud integration

### Setup Steps

#### 1. Get API Key

1. Visit [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Select a Google Cloud project (or create new one)
5. Copy the API key
   - ⚠️ **Save it securely**

#### 2. Configure Environment

**Option A: Using .env file (Recommended)**

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your key
GEMINI_API_KEY=your_actual_key_here_replace_this
```

**Option B: Environment Variable**

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your_actual_key_here"

# macOS/Linux (add to ~/.bashrc or ~/.zshrc for persistence)
export GEMINI_API_KEY="your_actual_key_here"
```

#### 3. Run the Agent

```bash
python src/main.py
# Select: 3. Gemini
# Enter model: gemini-pro  (or press Enter for default)
```

### Available Models

| Model | Context | Speed | Best For |
|-------|---------|-------|----------|
| `gemini-pro` | 32K | ⚡⚡ | General use (recommended) |
| `gemini-1.5-pro` | 1M | ⚡⚡ | Long context, complex tasks |
| `gemini-1.5-flash` | 1M | ⚡⚡⚡ | Fast, lightweight |

### Free Tier Limits

- **Requests per minute:** 60 RPM
- **Requests per day:** 1,500 RPD
- **Tokens:** Check current quotas
- **Usage:** Monitor in Google Cloud Console

### Troubleshooting

**API key not working:**
- Verify the key is correct
- Check if API is enabled in Google Cloud Console
- Ensure billing is set up (free tier still requires it)

**Quota exceeded:**
- Wait for quota reset (per minute/day)
- Check usage in Google Cloud Console
- Consider upgrading quota if needed

---

## 🔄 Switching Between Providers

You can easily switch providers without changing code:

### Method 1: Interactive Selection
```bash
python src/main.py
# Choose provider each time you run
```

### Method 2: Environment Variables
```bash
# Set multiple API keys in .env
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=...

# Switch by selecting different provider at runtime
```

### Method 3: Multiple Configurations
```bash
# Create different .env files
.env.groq    # Contains GROQ_API_KEY
.env.gemini  # Contains GEMINI_API_KEY

# Load specific config
cp .env.groq .env
python src/main.py
```

---

## 🎯 Provider Comparison

| Feature | Ollama Cloud | Ollama Local | Groq | Gemini |
|---------|--------------|--------------|------|--------|
| **Cost** | 🆓 Free | 🆓 Free | 🆓 Free tier | 🆓 Free tier |
| **Speed** | ⚡⚡ Fast | 🐢 Varies | ⚡⚡⚡ Fastest | ⚡⚡ Fast |
| **Setup** | ⭐ Easiest | ⭐⭐ Easy | ⭐⭐ Moderate | ⭐⭐ Moderate |
| **API Key** | ❌ Not needed | ❌ Not needed | ✅ Required | ✅ Required |
| **Download** | ❌ None | ✅ 4-7GB | ❌ None | ❌ None |
| **Offline** | ❌ No | ✅ Yes | ❌ No | ❌ No |
| **Privacy** | ⚠️ Cloud | ✅ Local | ⚠️ Cloud | ⚠️ Cloud |
| **Models** | 4+ cloud | 100+ local | 10+ | 3+ |
| **Multimodal** | ❌ No | Varies | ❌ No | ✅ Yes |

---

## 📝 Best Practices

### Security

1. **Never commit API keys to Git**
   ```bash
   # .env is already in .gitignore
   # Always use .env.example for templates
   ```

2. **Rotate keys regularly**
   - Generate new keys periodically
   - Revoke old keys from provider dashboards

3. **Use environment-specific keys**
   - Development keys for testing
   - Production keys for deployment

### Cost Management

1. **Monitor usage**
   - Check provider dashboards regularly
   - Set up usage alerts if available

2. **Use appropriate models**
   - Smaller models for simple tasks
   - Larger models only when needed

3. **Implement rate limiting**
   - Add delays between requests if needed
   - Cache responses when possible

### Performance

1. **Choose provider based on needs**
   - Groq for speed
   - Gemini for multimodal
   - Ollama Cloud for ease of use
   - Ollama Local for privacy

2. **Test different models**
   - Each model has different strengths
   - Benchmark for your specific use case

---

## 🆘 Getting Help

### Provider-Specific Support

- **Ollama**: [GitHub Issues](https://github.com/ollama/ollama/issues)
- **Groq**: [Documentation](https://console.groq.com/docs)
- **Gemini**: [Google AI Studio](https://ai.google.dev/)

### Agentry Support

- **Issues**: [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RudraModi360/Agentry/discussions)

---

## ✅ Quick Checklist

Before running the agent, ensure:

- [ ] Python 3.11+ installed
- [ ] `uv` installed
- [ ] Dependencies installed (`uv sync`)
- [ ] Provider selected:
  - [ ] Ollama client installed (for Ollama)
  - [ ] API key set in `.env` (for Groq/Gemini)
- [ ] Model chosen (cloud or local)

**Ready to go!** 🚀

```bash
python src/main.py
```
