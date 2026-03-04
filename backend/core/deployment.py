"""
Deployment Mode Configuration
=============================
Handles local vs cloud deployment modes with proper isolation.

Local Mode:
- All 3 agent types available (Default, Copilot, Smart)
- Full tool access including filesystem
- SQLite storage
- Local filesystem for media

Cloud Mode:
- Single Cloud Agent (no switching)
- Cloud-safe tools only (no filesystem)
- Supabase storage
- Vercel Blob for media
"""

import os
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class DeploymentMode(Enum):
    """Deployment modes for the application."""
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class DeploymentConfig:
    """Configuration for current deployment mode."""
    mode: DeploymentMode
    environment: str  # dev, staging, prod
    
    # Feature flags
    allow_agent_switching: bool = True
    allow_filesystem_tools: bool = True
    allow_execution_tools: bool = True
    mcp_enabled: bool = True
    
    # Available agent types
    available_agents: List[str] = field(default_factory=list)
    
    # Tool restrictions
    disabled_tools: List[str] = field(default_factory=list)
    
    # UI configuration
    ui_variant: str = "local"  # "local" or "cloud"
    
    @classmethod
    def from_environment(cls) -> "DeploymentConfig":
        """Create configuration from environment variables."""
        mode_str = os.environ.get("AGENTRY_MODE", "local").lower()
        mode = DeploymentMode.CLOUD if mode_str == "cloud" else DeploymentMode.LOCAL
        environment = os.environ.get("ENVIRONMENT", "dev")
        
        if mode == DeploymentMode.CLOUD:
            return cls(
                mode=mode,
                environment=environment,
                allow_agent_switching=False,
                allow_filesystem_tools=False,
                allow_execution_tools=False,
                mcp_enabled=True,
                available_agents=["cloud"],
                disabled_tools=[
                    "read_file", "create_file", "edit_file", "delete_file",
                    "list_files", "search_files", "fast_grep",
                    "execute_command", "git_command", "code_execute"
                ],
                ui_variant="cloud"
            )
        else:
            return cls(
                mode=mode,
                environment=environment,
                allow_agent_switching=True,
                allow_filesystem_tools=True,
                allow_execution_tools=True,
                mcp_enabled=True,
                available_agents=["default", "copilot", "smart"],
                disabled_tools=[],
                ui_variant="local"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "mode": self.mode.value,
            "environment": self.environment,
            "allow_agent_switching": self.allow_agent_switching,
            "allow_filesystem_tools": self.allow_filesystem_tools,
            "allow_execution_tools": self.allow_execution_tools,
            "mcp_enabled": self.mcp_enabled,
            "available_agents": self.available_agents,
            "disabled_tools": self.disabled_tools,
            "ui_variant": self.ui_variant,
        }
    
    def is_cloud(self) -> bool:
        """Check if running in cloud mode."""
        return self.mode == DeploymentMode.CLOUD
    
    def is_local(self) -> bool:
        """Check if running in local mode."""
        return self.mode == DeploymentMode.LOCAL
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed in current mode."""
        return tool_name not in self.disabled_tools


# Global deployment configuration instance
_deployment_config: Optional[DeploymentConfig] = None


def get_deployment_config() -> DeploymentConfig:
    """Get the current deployment configuration."""
    global _deployment_config
    if _deployment_config is None:
        _deployment_config = DeploymentConfig.from_environment()
    return _deployment_config


def reload_deployment_config() -> DeploymentConfig:
    """Reload deployment configuration from environment."""
    global _deployment_config
    _deployment_config = DeploymentConfig.from_environment()
    return _deployment_config


def is_cloud_mode() -> bool:
    """Quick check if running in cloud mode."""
    return get_deployment_config().is_cloud()


def is_local_mode() -> bool:
    """Quick check if running in local mode."""
    return get_deployment_config().is_local()


# Agent type info for different modes
AGENT_INFO = {
    "local": {
        "default": {
            "id": "default",
            "name": "Default Agent",
            "description": "Standard agent with configurable tools. Best for general-purpose tasks.",
            "features": ["Configurable tools", "MCP servers", "File operations"],
            "icon": "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
        },
        "copilot": {
            "id": "copilot", 
            "name": "Copilot Agent",
            "description": "Coding assistant with context awareness. Great for pair programming.",
            "features": ["Conversation memory", "Code completion", "Documentation lookup"],
            "icon": "M16 18l6-6-6-6M8 6l-6 6 6 6"
        },
        "smart": {
            "id": "smart",
            "name": "Smart Agent (Beta)",
            "description": "Autonomous goal-oriented agent with planning and self-debugging.",
            "features": ["Autonomous planning", "Self-debugging", "Persistent memory"],
            "icon": "M9 18h6M10 22h4M12 2a7 7 0 017 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 01-1 1H9a1 1 0 01-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 017-7z"
        }
    },
    "cloud": {
        "cloud": {
            "id": "cloud",
            "name": "Cloud Agent",
            "description": "Powerful cloud agent with web tools, MCP servers, and plugin support.",
            "features": ["Web search", "URL fetching", "MCP plugins", "Document analysis"],
            "icon": "M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z",
            "is_default": True,
            "switchable": False
        }
    }
}


def get_available_agents() -> List[Dict[str, Any]]:
    """Get list of available agents for current deployment mode."""
    config = get_deployment_config()
    mode_key = "cloud" if config.is_cloud() else "local"
    
    agents = []
    for agent_id in config.available_agents:
        if agent_id in AGENT_INFO[mode_key]:
            agents.append(AGENT_INFO[mode_key][agent_id])
    
    return agents


# ============================================================================
# Agent Factory Functions
# ============================================================================

def create_agent_for_mode(
    user_id: str,
    agent_type: str = None,
    provider: str = None,
    model: str = None,
    api_key: str = None,
    user_mcp_configs: List[Dict[str, Any]] = None,
    debug: bool = False
):
    """
    Factory function to create the appropriate agent based on deployment mode.
    
    In CLOUD mode: Always returns CloudAgent (ignores agent_type)
    In LOCAL mode: Returns the specified agent type (default, copilot, smart)
    
    Args:
        user_id: User identifier
        agent_type: Agent type (only used in local mode)
        provider: LLM provider name
        model: Model name
        api_key: API key
        user_mcp_configs: User's custom MCP configurations (cloud mode only)
        debug: Enable debug logging
    
    Returns:
        Configured agent instance
    """
    config = get_deployment_config()
    
    if config.is_cloud():
        # Cloud mode: Always use CloudAgent
        from logicore.agents.agent_cloud import CloudAgent, create_cloud_agent
        return create_cloud_agent(
            user_id=user_id,
            provider=provider,
            model=model,
            api_key=api_key,
            user_mcp_configs=user_mcp_configs,
            debug=debug
        )
    else:
        # Local mode: Use the specified agent type
        agent_type = agent_type or "default"
        
        if agent_type == "smart":
            from logicore.agents.agent_smart import SmartAgent
            return SmartAgent(
                llm=provider or "ollama",
                model=model,
                api_key=api_key,
                debug=debug
            )
        elif agent_type == "copilot":
            from logicore.agents.agent_mcp import MCPAgent
            from logicore.providers.ollama_provider import OllamaProvider
            from logicore.providers.groq_provider import GroqProvider
            
            if provider == "groq":
                llm = GroqProvider(model_name=model, api_key=api_key)
            else:
                llm = OllamaProvider(model_name=model or "gpt-oss:20b-cloud")
            
            return MCPAgent(
                provider=llm,
                debug=debug
            )
        else:
            # Default agent
            from logicore.agents.agent import Agent
            agent = Agent(
                llm=provider or "ollama",
                model=model,
                api_key=api_key,
                debug=debug
            )
            agent.load_default_tools()
            return agent


def get_agent_for_user(user_id: str, session_config: Dict[str, Any] = None) -> Any:
    """
    Get or create an agent for a specific user.
    Uses caching for efficiency.
    
    Args:
        user_id: User identifier
        session_config: Optional session-specific configuration
    
    Returns:
        Agent instance
    """
    from backend.services.agent_cache import agent_cache
    
    config = get_deployment_config()
    
    # Build cache key
    cache_key = f"{user_id}"
    if session_config:
        cache_key += f":{session_config.get('provider', '')}:{session_config.get('model', '')}"
    
    # Check cache
    if cache_key in agent_cache:
        return agent_cache[cache_key]
    
    # Create new agent
    agent = create_agent_for_mode(
        user_id=user_id,
        agent_type=session_config.get("agent_type") if session_config else None,
        provider=session_config.get("provider") if session_config else None,
        model=session_config.get("model") if session_config else None,
        api_key=session_config.get("api_key") if session_config else None,
        debug=os.environ.get("DEBUG", "false").lower() == "true"
    )
    
    # Cache the agent
    agent_cache[cache_key] = agent
    
    return agent
