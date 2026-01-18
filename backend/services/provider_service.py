"""
Provider service for managing LLM providers.
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from backend.config import DB_PATH
from backend.models.provider import ProviderConfig

# Import from agentry modules
from agentry import Agent
from agentry.providers.ollama_provider import OllamaProvider
from agentry.providers.groq_provider import GroqProvider
from agentry.providers.gemini_provider import GeminiProvider
from agentry.providers.azure_provider import AzureProvider
from agentry.providers.capability_detector import detect_model_capabilities, ModelCapabilities

from .agent_cache import agent_cache
from .auth_service import AuthService

__all__ = ["ProviderService"]


class ProviderService:
    """Service for managing LLM providers."""
    
    @staticmethod
    def set_environment_vars(provider: str, api_key: str, mode: str = None) -> None:
        """Set environment variables for the provider."""
        if provider == "groq" and api_key:
            os.environ["GROQ_API_KEY"] = api_key
        elif provider == "gemini" and api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "ollama" and mode == "cloud" and api_key:
            os.environ["OLLAMA_API_KEY"] = api_key

    @staticmethod
    def create_provider(config: ProviderConfig, api_key: str, endpoint: str = None, model_type: str = None) -> Any:
        """Create a provider instance based on configuration."""
        if config.provider == "ollama":
            return OllamaProvider(model_name=config.model or "llama3.2:3b")
        elif config.provider == "groq":
            return GroqProvider(model_name=config.model or "llama-3.3-70b-versatile", api_key=api_key)
        elif config.provider == "gemini":
            return GeminiProvider(model_name=config.model or "gemini-2.0-flash", api_key=api_key)
        elif config.provider == "azure":
            return AzureProvider(
                model_name=config.model or "gpt-4",
                api_key=api_key,
                endpoint=endpoint,
                model_type=model_type
            )
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    @staticmethod
    async def detect_capabilities(provider_name: str, model_name: str, provider_instance: Any) -> ModelCapabilities:
        """Detect model capabilities (cached)."""
        from backend.core.cache import capabilities_cache
        
        cache_key = f"capabilities:{provider_name}:{model_name}"
        
        # Try cache first
        cached = capabilities_cache.get(cache_key)
        if cached is not None:
            # Reconstruct ModelCapabilities from cached dict
            return ModelCapabilities.from_dict(cached)
        
        try:
            print(f"[Server] Detecting capabilities for {provider_name}/{model_name}...")
            capabilities = await detect_model_capabilities(
                provider_name=provider_name,
                model_name=model_name,
                provider_instance=provider_instance
            )
            print(f"[Server] Capabilities detected: tools={capabilities.supports_tools}, vision={capabilities.supports_vision}, method={capabilities.detection_method}")
            
            # Cache the result
            capabilities_cache.set(cache_key, capabilities.to_dict())
            
            return capabilities
        except Exception as e:
            print(f"[Server] Capability detection failed: {e}")
            return ModelCapabilities(
                supports_tools=False,
                supports_vision=False,
                provider=provider_name,
                model_name=model_name,
                detection_method="error",
                error_message=str(e)
            )

    @staticmethod
    async def create_and_cache_agent(user_id: int, config: ProviderConfig, provider: Any, capabilities: ModelCapabilities) -> Agent:
        """Create an agent and cache it. Optimized for speed."""
        import time
        start = time.time()
        
        # Clear old agent from cache if exists
        if user_id in agent_cache:
            del agent_cache[user_id]
        
        agent = Agent(llm=provider, debug=True, capabilities=capabilities)
        
        # Only load tools if the model supports them
        if capabilities.supports_tools:
            t1 = time.time()
            agent.load_default_tools()
            print(f"[Server] Loaded default tools in {time.time()-t1:.2f}s")
            
            # Use pooled connection for both queries
            from backend.core.db_pool import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            # Load MCP Configuration
            t2 = time.time()
            try:
                cursor.execute("SELECT config_json FROM user_mcp_config WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    mcp_config = json.loads(row[0])
                    await agent.add_mcp_server(config=mcp_config)
                    print(f"[Server] Loaded MCP tools in {time.time()-t2:.2f}s")
            except Exception as e:
                print(f"[Server] Failed to load MCP config: {e}")
            
            # Load disabled tools from database (same connection)
            try:
                cursor.execute("SELECT disabled_tools_json FROM user_disabled_tools WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    disabled_list = json.loads(row[0])
                    agent.disabled_tools = set(disabled_list)
            except Exception as e:
                print(f"[Server] Failed to load disabled tools: {e}")
        else:
            print(f"[Server] Skipping tool loading - model {config.model} does not support tools")
        
        agent_cache[user_id] = {
            "agent": agent,
            "config": config.dict(),
            "provider": provider,
            "capabilities": capabilities.to_dict()
        }
        print(f"[Server] Agent cached in {time.time()-start:.2f}s for {config.model}")
        
        return agent
