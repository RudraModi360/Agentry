"""
Model Capability Detector

Detects LLM model capabilities (tool calling, vision, etc.) across different providers.
This module provides a unified interface to probe models and determine their feature support.
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class ModelCapabilities:
    """Represents the capabilities of an LLM model."""
    supports_tools: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    supports_json_mode: bool = False
    max_context_length: Optional[int] = None
    provider: str = "unknown"
    model_name: str = "unknown"
    detection_method: str = "default"  # 'probe', 'api', 'hardcoded', 'default'
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelCapabilities':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Known model capabilities (hardcoded for speed and reliability)
KNOWN_CAPABILITIES = {
    # === Ollama Models ===
    # Tool-capable models
    "llama3.2": {"supports_tools": True, "supports_vision": False},
    "llama3.2:3b": {"supports_tools": True, "supports_vision": False},
    "llama3.2:1b": {"supports_tools": True, "supports_vision": False},
    "llama3.1": {"supports_tools": True, "supports_vision": False},
    "llama3.1:8b": {"supports_tools": True, "supports_vision": False},
    "llama3.1:70b": {"supports_tools": True, "supports_vision": False},
    "llama3": {"supports_tools": True, "supports_vision": False},
    "llama3:8b": {"supports_tools": True, "supports_vision": False},
    "mistral": {"supports_tools": True, "supports_vision": False},
    "mistral:7b": {"supports_tools": True, "supports_vision": False},
    "mixtral": {"supports_tools": True, "supports_vision": False},
    "qwen2.5": {"supports_tools": True, "supports_vision": False},
    "qwen2.5:7b": {"supports_tools": True, "supports_vision": False},
    "qwen2.5:14b": {"supports_tools": True, "supports_vision": False},
    "qwen2.5:32b": {"supports_tools": True, "supports_vision": False},
    "qwen2.5:72b": {"supports_tools": True, "supports_vision": False},
    "qwen2": {"supports_tools": True, "supports_vision": False},
    "deepseek-coder": {"supports_tools": True, "supports_vision": False},
    "deepseek-coder:6.7b": {"supports_tools": True, "supports_vision": False},
    "codellama": {"supports_tools": True, "supports_vision": False},
    "command-r": {"supports_tools": True, "supports_vision": False},
    "command-r-plus": {"supports_tools": True, "supports_vision": False},
    "phi3": {"supports_tools": True, "supports_vision": False},
    "phi3:mini": {"supports_tools": True, "supports_vision": False},
    "phi3:medium": {"supports_tools": True, "supports_vision": False},
    
    # Vision + Tool capable models
    "llava": {"supports_tools": False, "supports_vision": True},  # Vision but no tools
    "llava:7b": {"supports_tools": False, "supports_vision": True},
    "llava:13b": {"supports_tools": False, "supports_vision": True},
    "llava:34b": {"supports_tools": False, "supports_vision": True},
    "llava-llama3": {"supports_tools": False, "supports_vision": True},
    "bakllava": {"supports_tools": False, "supports_vision": True},
    "moondream": {"supports_tools": False, "supports_vision": True},
    "minicpm-v": {"supports_tools": False, "supports_vision": True},
    "qwen3-vl": {"supports_tools": True, "supports_vision": True},
    "qwen3-vl:2b": {"supports_tools": True, "supports_vision": True},
    "qwen3-vl:235b-cloud": {"supports_tools": True, "supports_vision": True},
    
    # Models WITHOUT tool support
    "gemma": {"supports_tools": False, "supports_vision": False},
    "gemma:2b": {"supports_tools": False, "supports_vision": False},
    "gemma:7b": {"supports_tools": False, "supports_vision": False},
    "gemma2": {"supports_tools": False, "supports_vision": False},
    "gemma2:2b": {"supports_tools": False, "supports_vision": False},
    "gemma2:9b": {"supports_tools": False, "supports_vision": False},
    "gemma2:27b": {"supports_tools": False, "supports_vision": False},
    "gemma:1b": {"supports_tools": False, "supports_vision": False},
    "tinyllama": {"supports_tools": False, "supports_vision": False},
    "tinydolphin": {"supports_tools": False, "supports_vision": False},
    "phi": {"supports_tools": False, "supports_vision": False},
    "phi:2.7b": {"supports_tools": False, "supports_vision": False},
    "orca-mini": {"supports_tools": False, "supports_vision": False},
    "stablelm": {"supports_tools": False, "supports_vision": False},
    "neural-chat": {"supports_tools": False, "supports_vision": False},
    "starling": {"supports_tools": False, "supports_vision": False},
    "yi": {"supports_tools": False, "supports_vision": False},
    "falcon": {"supports_tools": False, "supports_vision": False},
    "wizardcoder": {"supports_tools": False, "supports_vision": False},
    "starcoder": {"supports_tools": False, "supports_vision": False},
    "starcoder2": {"supports_tools": False, "supports_vision": False},
    
    # Cloud models (gpt-oss, etc.)
    "gpt-oss:20b-cloud": {"supports_tools": True, "supports_vision": False},
    "gpt-oss:20b": {"supports_tools": True, "supports_vision": False},
    "glm-4.6:cloud": {"supports_tools": True, "supports_vision": False},
    "minimax-m2:cloud": {"supports_tools": True, "supports_vision": False},
    
    # === Groq Models (all typically support tools) ===
    "llama-3.3-70b-versatile": {"supports_tools": True, "supports_vision": False},
    "llama-3.1-8b-instant": {"supports_tools": True, "supports_vision": False},
    "llama-3.2-90b-vision-preview": {"supports_tools": True, "supports_vision": True},
    "llama-3.2-11b-vision-preview": {"supports_tools": True, "supports_vision": True},
    "mixtral-8x7b-32768": {"supports_tools": True, "supports_vision": False},
    "gemma-7b-it": {"supports_tools": False, "supports_vision": False},  # Groq's gemma
    "gemma2-9b-it": {"supports_tools": False, "supports_vision": False},
    
    # === Gemini Models (all support tools and vision) ===
    "gemini-pro": {"supports_tools": True, "supports_vision": False},
    "gemini-1.5-pro": {"supports_tools": True, "supports_vision": True},
    "gemini-1.5-flash": {"supports_tools": True, "supports_vision": True},
    "gemini-2.0-flash": {"supports_tools": True, "supports_vision": True},
    "gemini-2.0-flash-lite": {"supports_tools": True, "supports_vision": True},
    "gemini-2.5-pro": {"supports_tools": True, "supports_vision": True},
    "gemini-2.5-flash": {"supports_tools": True, "supports_vision": True},
    "gemini-2.5-flash-lite": {"supports_tools": True, "supports_vision": True},
    "gemini-3.0-pro-preview": {"supports_tools": True, "supports_vision": True},

    # === Azure / OpenAI Models ===
    "gpt-4o": {"supports_tools": True, "supports_vision": True},
    "gpt-4o-mini": {"supports_tools": True, "supports_vision": True},
    "gpt-4-turbo": {"supports_tools": True, "supports_vision": True},
    "gpt-4-vision-preview": {"supports_tools": True, "supports_vision": True},
    "gpt-4": {"supports_tools": True, "supports_vision": False},
    "gpt-3.5-turbo": {"supports_tools": True, "supports_vision": False},
    "o1-preview": {"supports_tools": True, "supports_vision": True},
    "o1-mini": {"supports_tools": True, "supports_vision": True},

    "claude-3-5-sonnet": {"supports_tools": True, "supports_vision": True},
    "claude-3-5-haiku": {"supports_tools": True, "supports_vision": True},
    "claude-3-opus": {"supports_tools": True, "supports_vision": True},
    "claude-3-sonnet": {"supports_tools": True, "supports_vision": True},
    "claude-3-haiku": {"supports_tools": True, "supports_vision": True},
    "claude-opus": {"supports_tools": True, "supports_vision": True},
    "claude-sonnet": {"supports_tools": True, "supports_vision": True}, 
    "claude-haiku": {"supports_tools": True, "supports_vision": True},
    "claude-opus-4": {"supports_tools": True, "supports_vision": True},
    "claude-opus-4-5": {"supports_tools": True, "supports_vision": True},
    "claude-sonnet-4": {"supports_tools": True, "supports_vision": True},
    "claude-4": {"supports_tools": True, "supports_vision": True},
    "claude-2.1": {"supports_tools": True, "supports_vision": False},
    "claude-2.0": {"supports_tools": True, "supports_vision": False},
    "claude-instant-1.2": {"supports_tools": True, "supports_vision": False},
    
    # Additional Groq models
    "llama3-70b": {"supports_tools": True, "supports_vision": False},
    "llama3-8b": {"supports_tools": True, "supports_vision": False},
}


class CapabilityDetector:
    """
    Detects model capabilities across different providers.
    Uses a multi-strategy approach:
    1. Check hardcoded known capabilities (fastest)
    2. Query provider API (if available)
    3. Probe model with test request (slowest, most accurate)
    """
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name.lower()
    
    async def detect(self, model_name: str, provider_instance=None) -> ModelCapabilities:
        """
        Detect capabilities for a given model.
        
        Args:
            model_name: The model identifier
            provider_instance: Optional provider instance for probing
            
        Returns:
            ModelCapabilities object with detected capabilities
        """
        # Normalize model name for lookup
        normalized_name = self._normalize_model_name(model_name)
        
        # Strategy 1: Check hardcoded capabilities
        if normalized_name in KNOWN_CAPABILITIES:
            caps = KNOWN_CAPABILITIES[normalized_name]
            return ModelCapabilities(
                supports_tools=caps.get("supports_tools", False),
                supports_vision=caps.get("supports_vision", False),
                supports_streaming=True,
                provider=self.provider_name,
                model_name=model_name,
                detection_method="hardcoded"
            )
        
        # Strategy 2: Check partial matches (e.g., "gemma:1b" matches "gemma")
        for known_model, caps in KNOWN_CAPABILITIES.items():
            if normalized_name.startswith(known_model) or known_model.startswith(normalized_name.split(":")[0]):
                return ModelCapabilities(
                    supports_tools=caps.get("supports_tools", False),
                    supports_vision=caps.get("supports_vision", False),
                    supports_streaming=True,
                    provider=self.provider_name,
                    model_name=model_name,
                    detection_method="partial_match"
                )
        
        # Strategy 2b: Keyword-based matching for common model families
        name_lower = normalized_name.lower()
        
        # Vision + Tools Keywords
        # Claude 3+ models always support vision. GPT-4o and o1 models too.
        vision_keywords = ["gpt-4o", "o1-", "claude-3", "sonnet", "haiku", "opus", "pixtral", "llava"]
        if any(kw in name_lower for kw in vision_keywords):
             if "agent" in name_lower: # Some wrapper model names might contain 'agent'
                 pass 
             print(f"[CapabilityDetector] Keyword match: '{name_lower}' contains vision keyword. Vision=True")
             return ModelCapabilities(
                 supports_tools=True, 
                 supports_vision=True, 
                 provider=self.provider_name, 
                 model_name=model_name, 
                 detection_method="keyword_match"
             )
             
        # Tools Only (non-vision) Keywords
        tool_keywords = ["gpt-4", "gpt-3.5", "claude-", "llama-3", "mistral", "mixtral", "qwen"]
        if any(kw in name_lower for kw in tool_keywords):
             print(f"[CapabilityDetector] Keyword match: '{name_lower}' contains tool keyword. Vision=False")
             return ModelCapabilities(
                 supports_tools=True, 
                 supports_vision=False, 
                 provider=self.provider_name, 
                 model_name=model_name, 
                 detection_method="keyword_match"
             )
        
        # Strategy 3: Provider-specific API query
        if self.provider_name == "ollama" and provider_instance:
            try:
                return await self._detect_ollama_capabilities(model_name, provider_instance)
            except Exception as e:
                print(f"[CapabilityDetector] Ollama API detection failed: {e}")
        
        # Strategy 4: Probe the model (most reliable but slow)
        if provider_instance:
            try:
                return await self._probe_model(model_name, provider_instance)
            except Exception as e:
                print(f"[CapabilityDetector] Probe detection failed: {e}")
        
        # Fallback: Conservative defaults based on provider
        return self._get_default_capabilities(model_name)
    
    def _normalize_model_name(self, model_name: str) -> str:
        """Normalize model name for consistent lookups."""
        return model_name.lower().strip()
    
    async def _detect_ollama_capabilities(self, model_name: str, provider) -> ModelCapabilities:
        """Detect capabilities using Ollama's model info API."""
        try:
            info = provider.client.show(model_name)
            details = info.get('details', {})
            
            # Check for vision capability
            families = details.get('families', []) or []
            if details.get('family'):
                families.append(details.get('family'))
            
            vision_families = ['clip', 'vision', 'momo', 'llava', 'multimodal', 'mllama']
            supports_vision = any(f.lower() in vision_families for f in families)
            
            name_lower = model_name.lower()
            vision_keywords = ['llava', 'vision', 'minicpm', 'vl', 'pixtral', 'moondream', 'bakllava']
            if any(k in name_lower for k in vision_keywords):
                supports_vision = True
            
            # Check for tool support via model family
            # Models that typically support tools
            tool_families = ['llama', 'mistral', 'mixtral', 'qwen', 'command-r', 'phi3', 'deepseek']
            no_tool_families = ['gemma', 'tinyllama', 'falcon', 'yi', 'orca', 'stablelm', 'starcoder']
            
            supports_tools = True  # Assume true by default
            
            base_name = name_lower.split(':')[0]
            for family in no_tool_families:
                if family in base_name:
                    supports_tools = False
                    break
            
            return ModelCapabilities(
                supports_tools=supports_tools,
                supports_vision=supports_vision,
                supports_streaming=True,
                provider=self.provider_name,
                model_name=model_name,
                detection_method="api"
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to query Ollama model info: {e}")
    
    async def _probe_model(self, model_name: str, provider) -> ModelCapabilities:
        """
        Probe the model with a test request to determine tool support.
        This is the most reliable but slowest method.
        """
        # Define a simple test tool
        test_tool = [{
            "type": "function",
            "function": {
                "name": "test_capability",
                "description": "A test function to check tool support",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test": {"type": "string", "description": "Test parameter"}
                    },
                    "required": ["test"]
                }
            }
        }]
        
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Use the test_capability tool with test='hello'"}
        ]
        
        supports_tools = False
        supports_vision = False
        error_message = None
        
        try:
            # Try a chat request with tools
            response = await provider.chat(test_messages, tools=test_tool)
            
            # If we get here without error, tools might be supported
            # Check if the response contains tool calls
            if isinstance(response, dict):
                if response.get('tool_calls'):
                    supports_tools = True
                elif response.get('content'):
                    # Model responded but didn't use tools - might not support them
                    # or just chose not to use them
                    supports_tools = True  # Conservative: assume support
            else:
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    supports_tools = True
                else:
                    supports_tools = True  # Conservative: assume support
                    
        except Exception as e:
            error_str = str(e).lower()
            if 'does not support tools' in error_str or 'tool' in error_str and 'not supported' in error_str:
                supports_tools = False
                error_message = str(e)
            elif 'empty' in error_str or 'invalid' in error_str:
                # Could be a transient error, assume tools are supported
                supports_tools = True
                error_message = f"Probe inconclusive: {str(e)}"
            else:
                # Unknown error, play it safe
                supports_tools = False
                error_message = str(e)
        
        # Check vision support using provider method if available
        if hasattr(provider, '_supports_vision'):
            supports_vision = provider._supports_vision()
        
        return ModelCapabilities(
            supports_tools=supports_tools,
            supports_vision=supports_vision,
            supports_streaming=True,
            provider=self.provider_name,
            model_name=model_name,
            detection_method="probe",
            error_message=error_message
        )
    
    def _get_default_capabilities(self, model_name: str) -> ModelCapabilities:
        """Return conservative default capabilities based on provider."""
        defaults = {
            "ollama": {"supports_tools": False, "supports_vision": False},
            "groq": {"supports_tools": True, "supports_vision": False},
            "gemini": {"supports_tools": True, "supports_vision": True},
            "azure": {"supports_tools": True, "supports_vision": True},
        }
        
        provider_defaults = defaults.get(self.provider_name, {"supports_tools": False, "supports_vision": False})
        
        return ModelCapabilities(
            supports_tools=provider_defaults["supports_tools"],
            supports_vision=provider_defaults["supports_vision"],
            supports_streaming=True,
            provider=self.provider_name,
            model_name=model_name,
            detection_method="default"
        )


async def detect_model_capabilities(
    provider_name: str, 
    model_name: str, 
    provider_instance=None
) -> ModelCapabilities:
    """
    Convenience function to detect model capabilities.
    
    Args:
        provider_name: Name of the provider ('ollama', 'groq', 'gemini')
        model_name: Model identifier
        provider_instance: Optional provider instance for probing
        
    Returns:
        ModelCapabilities object
    """
    detector = CapabilityDetector(provider_name)
    return await detector.detect(model_name, provider_instance)


def get_known_capability(model_name: str) -> Optional[Dict[str, bool]]:
    """
    Quick synchronous lookup for known capabilities.
    Returns None if model is not in the known list.
    """
    normalized = model_name.lower().strip()
    
    if normalized in KNOWN_CAPABILITIES:
        return KNOWN_CAPABILITIES[normalized]
    
    # Check partial match
    base_name = normalized.split(':')[0]
    if base_name in KNOWN_CAPABILITIES:
        return KNOWN_CAPABILITIES[base_name]
    
    return None
