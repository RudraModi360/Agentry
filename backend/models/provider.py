"""
Provider configuration and model lists.
"""
from typing import Optional
from pydantic import BaseModel

__all__ = [
    "ProviderConfig",
    "OLLAMA_CLOUD_MODELS",
    "OLLAMA_LOCAL_SUGGESTED_MODELS",
    "GROQ_MODELS",
    "GEMINI_MODELS",
]


class ProviderConfig(BaseModel):
    provider: str  # ollama, groq, gemini, azure
    api_key: Optional[str] = None
    endpoint: Optional[str] = None  # For Azure
    mode: Optional[str] = None  # For Ollama: 'local' or 'cloud'
    model: Optional[str] = None
    model_type: Optional[str] = None  # For Azure: 'openai' or 'anthropic'
    agent_type: Optional[str] = None  # 'default', 'copilot', 'smart'
    tools_enabled: bool = True


# ============== Ollama Models ==============
OLLAMA_CLOUD_MODELS = [
    {"id": "gpt-oss:20b-cloud", "name": "GPT-OSS 20B Cloud", "description": "Cloud-based GPT model"},
    {"id": "glm-4.6:cloud", "name": "GLM 4.6 Cloud", "description": "GLM 4.6 Cloud model"},
    {"id": "minimax-m2:cloud", "name": "MiniMax M2 Cloud", "description": "MiniMax M2 Cloud model"},
    {"id": "qwen3-vl:235b-cloud", "name": "Qwen3 VL 235B Cloud", "description": "Qwen3 Vision-Language 235B Cloud"},
]

OLLAMA_LOCAL_SUGGESTED_MODELS = [
    {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "description": "Fast and efficient local model"},
    {"id": "llama3.1:8b", "name": "Llama 3.1 8B", "description": "Balanced performance local model"},
    {"id": "mistral:7b", "name": "Mistral 7B", "description": "Excellent reasoning capabilities"},
    {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B", "description": "Strong multilingual support"},
    {"id": "deepseek-coder:6.7b", "name": "DeepSeek Coder 6.7B", "description": "Optimized for coding tasks"},
    {"id": "phi3:mini", "name": "Phi-3 Mini", "description": "Microsoft's compact powerhouse"},
]

# ============== Groq Models ==============
GROQ_MODELS = [
    # Production Models
    {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "description": "Production - Most capable Llama model"},
    {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "description": "Production - Fast responses"},
    {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B", "description": "Production - OpenAI's flagship open-weight model"},
    {"id": "openai/gpt-oss-20b", "name": "GPT-OSS 20B", "description": "Production - Efficient GPT model"},
    {"id": "meta-llama/llama-guard-4-12b", "name": "Llama Guard 4 12B", "description": "Production - Safety guardrail model"},
    {"id": "whisper-large-v3", "name": "Whisper Large V3", "description": "Production - Speech-to-text"},
    {"id": "whisper-large-v3-turbo", "name": "Whisper Large V3 Turbo", "description": "Production - Fast speech-to-text"},
    # Preview Models
    {"id": "meta-llama/llama-4-maverick-17b-128e-instruct", "name": "Llama 4 Maverick 17B", "description": "Preview - Latest Llama 4 Maverick"},
    {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "name": "Llama 4 Scout 17B", "description": "Preview - Llama 4 Scout"},
    {"id": "moonshotai/kimi-k2-instruct-0905", "name": "Kimi K2", "description": "Preview - Moonshot AI Kimi K2"},
    {"id": "qwen/qwen3-32b", "name": "Qwen3 32B", "description": "Preview - Alibaba Qwen3"},
    {"id": "playai-tts", "name": "PlayAI TTS", "description": "Preview - Text-to-speech"},
    # Compound Systems
    {"id": "compound", "name": "Compound", "description": "System - AI with web search & code execution"},
    {"id": "compound-mini", "name": "Compound Mini", "description": "System - Lightweight compound model"},
]

# ============== Gemini Models ==============
GEMINI_MODELS = [
    # Latest Models
    {"id": "gemini-3.0-pro-preview", "name": "Gemini 3 Pro (Preview)", "description": "Best multimodal understanding, most powerful agentic model"},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "State-of-the-art thinking model for code, math, STEM"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "Best price-performance, great for agentic tasks"},
    {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash-Lite", "description": "Lightweight, cost-effective model"},
    # Previous Generation
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "description": "Workhorse model with 1M token context"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash-Lite", "description": "Lightweight 2.0 model"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "description": "Previous gen pro with 1M context"},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "description": "Previous gen fast model"},
    # Specialized
    {"id": "gemini-2.5-flash-preview-tts", "name": "Gemini 2.5 Flash TTS", "description": "Text-to-speech capabilities"},
    {"id": "text-embedding-004", "name": "Text Embedding 004", "description": "Text embedding model"},
]
