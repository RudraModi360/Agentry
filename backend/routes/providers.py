"""
Provider configuration routes.
"""
import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException

from backend.config import DB_PATH
from backend.core.dependencies import get_current_user
from backend.models.provider import (
    ProviderConfig,
    OLLAMA_CLOUD_MODELS,
    OLLAMA_LOCAL_SUGGESTED_MODELS,
    GROQ_MODELS,
    GEMINI_MODELS,
)
from backend.services.auth_service import AuthService
from backend.services.agent_cache import agent_cache
from backend.services.provider_service import ProviderService

from agentry.providers.ollama_provider import OllamaProvider
from agentry.providers.groq_provider import GroqProvider
from agentry.providers.gemini_provider import GeminiProvider
from agentry.providers.azure_provider import AzureProvider
from agentry.providers.capability_detector import detect_model_capabilities, get_known_capability

router = APIRouter()


@router.get("/providers")
async def get_providers():
    """Get list of available providers."""
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "Local-first AI with optional cloud models",
                "requires_key": False,
                "has_modes": True,
                "modes": [
                    {"id": "local", "name": "Local Models", "description": "Run models on your machine"},
                    {"id": "cloud", "name": "Cloud Models", "description": "Use Ollama cloud (requires API key)"}
                ]
            },
            {
                "id": "groq",
                "name": "Groq",
                "description": "Ultra-fast inference with LPU technology",
                "requires_key": True,
                "has_modes": False
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "description": "Google's most capable AI models",
                "requires_key": True,
                "has_modes": False
            },
            {
                "id": "azure",
                "name": "Azure OpenAI",
                "description": "Enterprise-grade AI with your own deployments. Supports GPT-4, Claude (via Foundry), etc.",
                "requires_key": True,
                "requires_endpoint": True,
                "has_modes": False
            }
        ]
    }


@router.get("/models/{provider}")
async def get_models(provider: str, mode: Optional[str] = None, api_key: Optional[str] = None, endpoint: Optional[str] = None, user: Dict = Depends(get_current_user)):
    """Get available models for a provider."""
    
    # Try to get stored API key if not provided
    if not api_key:
        api_key = AuthService.get_api_key(user["id"], provider)
    
    if provider == "ollama":
        if mode == "cloud":
            return {"models": OLLAMA_CLOUD_MODELS, "requires_key": True}
        else:
            # Try to fetch local models from Ollama
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        local_models = []
                        for m in data.get("models", []):
                            size_bytes = m.get("size", 0)
                            size_str = f"{size_bytes / (1024**3):.1f}GB" if size_bytes > 0 else "N/A"
                            local_models.append({
                                "id": m["name"],
                                "name": m["name"],
                                "description": f"Size: {size_str}"
                            })
                        if local_models:
                            return {"models": local_models, "requires_key": False}
            except Exception as e:
                print(f"Could not fetch local Ollama models: {e}")
            
            # Fallback to suggested models
            return {"models": OLLAMA_LOCAL_SUGGESTED_MODELS, "requires_key": False}
    
    elif provider == "groq":
        if not api_key:
            return {
                "models": GROQ_MODELS, 
                "requires_key": True, 
                "message": "Showing suggested models. API key required to configure."
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [
                        {"id": m["id"], "name": m["id"], "description": m.get("owned_by", "Groq")}
                        for m in data.get("data", [])
                        if m.get("active", True)
                    ]
                    return {"models": models, "requires_key": True, "fetched": True}
                else:
                    return {"models": GROQ_MODELS, "requires_key": True, "message": "Could not verify key, showing default models"}
        except httpx.RequestError as e:
            return {"models": GROQ_MODELS, "requires_key": True, "message": f"Network error: {str(e)}"}
    
    elif provider == "gemini":
        if not api_key:
            return {
                "models": GEMINI_MODELS, 
                "requires_key": True, 
                "message": "Showing suggested models. API key required to configure."
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [
                        {
                            "id": m["name"].replace("models/", ""),
                            "name": m.get("displayName", m["name"]),
                            "description": m.get("description", "")[:100]
                        }
                        for m in data.get("models", [])
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    return {"models": models, "requires_key": True, "fetched": True}
                else:
                    return {"models": GEMINI_MODELS, "requires_key": True, "message": "Could not verify key, showing default models"}
        except httpx.RequestError as e:
            return {"models": GEMINI_MODELS, "requires_key": True, "message": f"Network error: {str(e)}"}
            
    elif provider == "azure":
        # Get endpoint
        if not endpoint:
            endpoint = AuthService.get_provider_endpoint(user["id"], provider)
        
        if not api_key or not endpoint:
            return {
                "models": [{"id": "gpt-4", "name": "Example: gpt-4", "description": "Please configure Url/Key"}], 
                "requires_key": True, 
                "requires_endpoint": True,
                "message": "API Key and Endpoint required."
            }
        
        # Cleanup endpoint
        base_url = endpoint.strip().rstrip('/')
        if not base_url.startswith('http'):
            base_url = f"https://{base_url}"
             
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/openai/deployments?api-version=2024-02-15-preview",
                    headers={"api-key": api_key},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for item in data.get("data", []):
                        models.append({
                            "id": item["id"],
                            "name": item["id"],
                            "description": f"Model: {item.get('model', 'Unknown')}"
                        })
                    return {"models": models, "requires_key": True, "requires_endpoint": True, "fetched": True}
        except:
            pass
        
        return {
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o", "description": "Vision + Fast (Enter Deployment Name)"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo with Vision", "description": "Vision + Capable"},
                {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet", "description": "Vision + Smart (Azure Anthropic)"},
                {"id": "claude-3-opus", "name": "Claude 3 Opus", "description": "Intelligence (Azure Anthropic)"},
                {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "description": "Fast + Vision"}
            ],
            "requires_key": True,
            "requires_endpoint": True,
            "message": "Deployment names vary. If using Azure Anthropic, deployment name might be 'claude-3-5-sonnet' etc."
        }
    
    raise HTTPException(status_code=400, detail="Unknown provider")


@router.post("/provider/configure")
async def configure_provider(config: ProviderConfig, user: Dict = Depends(get_current_user)):
    """Configure provider for a user. Optimized for speed."""
    import time
    start_time = time.time()
    user_id = user["id"]
    
    # 1. Resolve API Key
    final_api_key = config.api_key
    if not final_api_key:
        final_api_key = AuthService.get_api_key(user_id, config.provider)
    
    config.api_key = final_api_key

    # Set environment variables
    ProviderService.set_environment_vars(config.provider, final_api_key, config.mode)
    
    # Validate by creating a provider instance
    provider = None
    try:
        if config.provider == "ollama":
            if config.mode == "cloud" and not final_api_key:
                raise ValueError("Ollama Cloud requires an API Key.")
            
            provider = OllamaProvider(model_name=config.model or "llama3.2:3b")
            
            # Skip pull_model during setup - it's too slow (defer to first use)
            # if config.mode == "local" or not config.mode:
            #     provider.pull_model()
            
        elif config.provider == "groq":
            if not final_api_key:
                raise ValueError("Groq requires an API Key.")
            provider = GroqProvider(model_name=config.model or "llama-3.3-70b-versatile", api_key=final_api_key)
            
        elif config.provider == "gemini":
            if not final_api_key:
                raise ValueError("Gemini requires an API Key.")
            provider = GeminiProvider(model_name=config.model or "gemini-2.0-flash", api_key=final_api_key)
            
        elif config.provider == "azure":
            endpoint = config.endpoint
            if not endpoint:
                endpoint = AuthService.get_provider_endpoint(user_id, "azure")
            
            if not final_api_key:
                raise ValueError("Azure requires an API Key.")
            if not endpoint:
                raise ValueError("Azure requires an Endpoint.")
                 
            # Infer model_type from model name if not provided
            final_model_type = config.model_type
            if not final_model_type and config.model:
                model_name_lower = config.model.lower()
                if "claude" in model_name_lower:
                    final_model_type = "anthropic"
                else:
                    final_model_type = "openai"
            
            config.model_type = final_model_type

            provider = AzureProvider(
                model_name=config.model or "gpt-4", 
                api_key=final_api_key, 
                endpoint=endpoint,
                model_type=final_model_type
            )
            
            # Save endpoint to DB if provided in config (use pooled connection)
            if config.endpoint:
                from backend.core.db_pool import connection_context
                with connection_context() as conn:
                    c = conn.cursor()
                    c.execute("""
                        UPDATE user_api_keys 
                        SET endpoint = ?, updated_at = ?
                        WHERE user_id = ? AND provider = ?
                    """, (config.endpoint, datetime.now(), user_id, "azure"))
                    if c.rowcount == 0:
                        c.execute("""
                            INSERT INTO user_api_keys (user_id, provider, api_key_encrypted, endpoint, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (user_id, "azure", final_api_key, config.endpoint, datetime.now()))

        else:
            raise HTTPException(status_code=400, detail="Unknown provider")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to initialize provider: {str(e)}")
    
    # 2. Get capabilities using hardcoded lookup (instant) or provider defaults
    from agentry.providers.capability_detector import get_known_capability, ModelCapabilities
    
    known_caps = get_known_capability(config.model)
    if known_caps:
        capabilities = ModelCapabilities(
            supports_tools=known_caps.get("supports_tools", True),
            supports_vision=known_caps.get("supports_vision", False),
            supports_streaming=True,
            provider=config.provider,
            model_name=config.model,
            detection_method="hardcoded"
        )
    else:
        # Use provider defaults (instant, no probing)
        provider_defaults = {
            "ollama": {"tools": False, "vision": False},
            "groq": {"tools": True, "vision": False},
            "gemini": {"tools": True, "vision": True},
            "azure": {"tools": True, "vision": True},
        }
        defaults = provider_defaults.get(config.provider, {"tools": True, "vision": False})
        capabilities = ModelCapabilities(
            supports_tools=defaults["tools"],
            supports_vision=defaults["vision"],
            supports_streaming=True,
            provider=config.provider,
            model_name=config.model,
            detection_method="provider_default"
        )
    
    # 3. Save configuration to database (fast with pooled connection)
    AuthService.save_active_settings(user_id, config)
    
    # 4. LAZY AGENT CREATION: Just cache the provider and config
    # Agent will be fully initialized on first WebSocket connection
    # This makes "Finish Setup" instant!
    if user_id in agent_cache:
        del agent_cache[user_id]
    
    agent_cache[user_id] = {
        "agent": None,  # Will be created lazily
        "config": config.dict(),
        "provider": provider,
        "capabilities": capabilities.to_dict(),
        "needs_init": True  # Flag for lazy initialization
    }
    
    elapsed = time.time() - start_time
    print(f"[Server] configure_provider completed in {elapsed:.2f}s (lazy agent)")
    
    return {
        "message": "Provider configured successfully", 
        "model": config.model,
        "capabilities": capabilities.to_dict()
    }


@router.post("/provider/toggle-tools")
async def toggle_tools(enabled: bool, user: dict = Depends(get_current_user)):
    """Toggle tools enabled/disabled for the user."""
    from backend.routes.agents import get_agent_config
    
    user_id = user["id"]
    
    # Check if user is using a Smart Agent
    current_agent_type = "default"
    if user_id in agent_cache:
        current_agent_type = agent_cache[user_id].get("agent_type", "default")
    else:
        config = await get_agent_config(user)
        current_agent_type = config.get("agent_type", "default")

    if current_agent_type == "smart":
        raise HTTPException(
            status_code=400, 
            detail="Tools cannot be disabled for Smart Agent as they are essential for its operation."
        )

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_active_settings 
            SET tools_enabled = ?, updated_at = ?
            WHERE user_id = ?
        """, (1 if enabled else 0, datetime.now(), user_id))
        conn.commit()
        
        # Invalidate agent cache so it reloads with new setting
        if user_id in agent_cache:
            del agent_cache[user_id]
            
        return {"status": "success", "tools_enabled": enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/provider/current")
async def get_current_provider(user: Dict = Depends(get_current_user)):
    """Get current provider configuration with capabilities."""
    user_id = user["id"]
    config = AuthService.get_current_active_settings(user_id)
    if not config:
        return {"config": None, "capabilities": None}
    
    # Get capabilities from cache if available
    capabilities = None
    if user_id in agent_cache:
        capabilities = agent_cache[user_id].get("capabilities")
    
    return {
        "config": {
            "provider": config["provider"],
            "mode": config.get("mode"),
            "model": config["model"],
            "model_type": config.get("model_type")
        },
        "capabilities": capabilities
    }


@router.put("/provider/switch")
async def switch_provider(config: ProviderConfig, user: Dict = Depends(get_current_user)):
    """Switch to a different provider/model."""
    return await configure_provider(config, user)


@router.put("/provider/switch-quick")
async def switch_provider_quick(config: ProviderConfig, user: Dict = Depends(get_current_user)):
    """
    FAST switch to a previously used provider/model using cached credentials.
    Optimized for speed - skips full validation and uses hardcoded capabilities.
    """
    user_id = user["id"]
    
    # 1. Get stored credentials (fast DB lookup with pooled connection)
    if not config.api_key:
        config.api_key = AuthService.get_api_key(user_id, config.provider)
    
    if not config.endpoint and config.provider == "azure":
        config.endpoint = AuthService.get_provider_endpoint(user_id, config.provider)
    
    # 2. Validate credentials exist
    if not config.api_key and config.provider not in ["ollama"]:
        raise HTTPException(
            status_code=400, 
            detail=f"No saved API key for {config.provider}. Please configure it in Settings first."
        )
    
    if config.provider == "azure" and not config.endpoint:
        raise HTTPException(
            status_code=400,
            detail="No saved endpoint for Azure. Please configure it in Settings first."
        )
    
    # 3. Set environment variables (fast)
    ProviderService.set_environment_vars(config.provider, config.api_key, config.mode)
    
    # 4. Create provider instance (fast - no validation call)
    try:
        if config.provider == "ollama":
            provider = OllamaProvider(model_name=config.model or "llama3.2:3b")
        elif config.provider == "groq":
            provider = GroqProvider(model_name=config.model, api_key=config.api_key)
        elif config.provider == "gemini":
            provider = GeminiProvider(model_name=config.model, api_key=config.api_key)
        elif config.provider == "azure":
            # Infer model_type if not provided
            model_type = config.model_type
            if not model_type and config.model:
                model_type = "anthropic" if "claude" in config.model.lower() else "openai"
            config.model_type = model_type
            
            provider = AzureProvider(
                model_name=config.model,
                api_key=config.api_key,
                endpoint=config.endpoint,
                model_type=model_type
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create provider: {str(e)}")
    
    # 5. Get capabilities FAST using hardcoded lookup (no async detection)
    from agentry.providers.capability_detector import get_known_capability, ModelCapabilities
    
    known_caps = get_known_capability(config.model)
    if known_caps:
        capabilities = ModelCapabilities(
            supports_tools=known_caps.get("supports_tools", True),
            supports_vision=known_caps.get("supports_vision", False),
            supports_streaming=True,
            provider=config.provider,
            model_name=config.model,
            detection_method="hardcoded_quick"
        )
    else:
        # Fallback to provider defaults (still fast, no API call)
        provider_defaults = {
            "ollama": {"tools": False, "vision": False},
            "groq": {"tools": True, "vision": False},
            "gemini": {"tools": True, "vision": True},
            "azure": {"tools": True, "vision": True},
        }
        defaults = provider_defaults.get(config.provider, {"tools": True, "vision": False})
        capabilities = ModelCapabilities(
            supports_tools=defaults["tools"],
            supports_vision=defaults["vision"],
            supports_streaming=True,
            provider=config.provider,
            model_name=config.model,
            detection_method="provider_default_quick"
        )
    
    # 6. Save settings to database (fast with pooled connection)
    AuthService.save_active_settings(user_id, config)
    
    # 7. Create agent and cache it (simplified - skip MCP for speed)
    if user_id in agent_cache:
        del agent_cache[user_id]
    
    from agentry import Agent
    agent = Agent(llm=provider, debug=True, capabilities=capabilities)
    
    # Load default tools if supported (fast - no DB or MCP)
    if capabilities.supports_tools:
        agent.load_default_tools()
        
        # Load disabled tools from DB (fast query)
        try:
            from backend.core.db_pool import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT disabled_tools_json FROM user_disabled_tools WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                import json
                disabled_list = json.loads(row[0])
                agent.disabled_tools = set(disabled_list)
        except Exception:
            pass  # Non-critical, continue
    
    # Cache the agent (MCP will be loaded lazily on first WS connection)
    agent_cache[user_id] = {
        "agent": agent,
        "config": config.dict(),
        "provider": provider,
        "capabilities": capabilities.to_dict(),
        "mcp_loaded": False  # Flag to load MCP lazily
    }
    
    return {
        "message": "Provider switched successfully (quick)", 
        "model": config.model,
        "capabilities": capabilities.to_dict()
    }


@router.get("/capabilities")
async def get_capabilities(provider: str, model: str, user: Dict = Depends(get_current_user)):
    """Get capabilities for a specific model."""
    user_id = user["id"]
    
    # First check if we have cached capabilities for this user's active model
    if user_id in agent_cache:
        cached_caps = agent_cache[user_id].get("capabilities", {})
        cached_provider = agent_cache[user_id].get("config", {}).get("provider")
        cached_model = agent_cache[user_id].get("config", {}).get("model")
        
        if cached_provider == provider and cached_model == model and cached_caps:
            return {
                "capabilities": {
                    "tools": cached_caps.get("supports_tools", False),
                    "vision": cached_caps.get("supports_vision", False)
                }
            }
    
    # Fall back to detecting capabilities
    try:
        api_key = AuthService.get_api_key(user_id, provider)
        
        temp_provider = None
        if provider == "ollama":
            temp_provider = OllamaProvider(model_name=model)
        elif provider == "groq" and api_key:
            temp_provider = GroqProvider(model_name=model, api_key=api_key)
        elif provider == "gemini" and api_key:
            temp_provider = GeminiProvider(model_name=model, api_key=api_key)
        elif provider == "azure" and api_key:
            endpoint = AuthService.get_provider_endpoint(user_id, provider)
            if endpoint:
                temp_provider = AzureProvider(model_name=model, api_key=api_key, endpoint=endpoint)
        
        if temp_provider:
            capabilities = await detect_model_capabilities(
                provider_name=provider,
                model_name=model,
                provider_instance=temp_provider
            )
            return {
                "capabilities": {
                    "tools": capabilities.supports_tools,
                    "vision": capabilities.supports_vision
                }
            }
    except Exception as e:
        print(f"[Server] Capability detection error: {e}")
    
    return {
        "capabilities": {
            "tools": False,
            "vision": False
        }
    }


@router.get("/provider/saved/{provider}")
async def get_saved_provider_config(provider: str, user: Dict = Depends(get_current_user)):
    """Get stored configuration for a specific provider (API key and endpoint)."""
    user_id = user["id"]
    api_key = AuthService.get_api_key(user_id, provider)
    endpoint = AuthService.get_provider_endpoint(user_id, provider)
    
    return {
        "provider": provider,
        "api_key": api_key,
        "endpoint": endpoint
    }


@router.get("/model/capabilities/{provider}/{model:path}")
async def get_model_capabilities(provider: str, model: str, user: Dict = Depends(get_current_user)):
    """Get capabilities for a specific model."""
    # First try quick hardcoded lookup
    known = get_known_capability(model)
    if known:
        return {
            "model": model,
            "provider": provider,
            "capabilities": {
                "supports_tools": known.get("supports_tools", False),
                "supports_vision": known.get("supports_vision", False),
                "supports_streaming": True,
                "detection_method": "hardcoded"
            }
        }
    
    # For unknown models, try to detect dynamically
    try:
        user_id = user["id"]
        api_key = AuthService.get_api_key(user_id, provider)
        
        temp_provider = None
        if provider == "ollama":
            temp_provider = OllamaProvider(model_name=model)
        elif provider == "groq" and api_key:
            temp_provider = GroqProvider(model_name=model, api_key=api_key)
        elif provider == "gemini" and api_key:
            temp_provider = GeminiProvider(model_name=model, api_key=api_key)
        
        if temp_provider:
            capabilities = await detect_model_capabilities(
                provider_name=provider,
                model_name=model,
                provider_instance=temp_provider
            )
            return {
                "model": model,
                "provider": provider,
                "capabilities": capabilities.to_dict()
            }
    except Exception as e:
        print(f"[Server] Dynamic capability detection failed: {e}")
    
    # Fallback to conservative defaults
    return {
        "model": model,
        "provider": provider,
        "capabilities": {
            "supports_tools": provider in ["groq", "gemini"],
            "supports_vision": provider == "gemini",
            "supports_streaming": True,
            "detection_method": "default"
        }
    }
