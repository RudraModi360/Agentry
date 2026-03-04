"""
MCP Server Configuration Routes (Cloud Mode)

Allows users to configure their own external MCP servers in cloud mode.
Pre-configured servers are loaded from mcp-cloud.json.
User-defined servers are stored in Supabase.
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.core.dependencies import get_current_user
from backend.core.deployment import get_deployment_config, is_cloud_mode

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class MCPServerConfig(BaseModel):
    """MCP Server configuration model."""
    server_name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    description: Optional[str] = None
    enabled: bool = True


class MCPServerResponse(BaseModel):
    """Response model for MCP server."""
    id: Optional[str] = None
    server_name: str
    server_type: str  # 'builtin' or 'custom'
    config: Dict[str, Any]
    enabled: bool
    created_at: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def _get_supabase_client():
    """Get Supabase client for MCP config storage."""
    if not is_cloud_mode():
        return None
    
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            return create_client(url, key)
    except ImportError:
        pass
    return None


def _load_builtin_servers() -> List[Dict[str, Any]]:
    """Load pre-configured MCP servers from mcp-cloud.json."""
    servers = []
    
    # Try multiple paths
    paths = [
        os.getenv("MCP_CONFIG_PATH", "/config/mcp-cloud.json"),
        "mcp-cloud.json",
        "/app/mcp-cloud.json",
        os.path.join(os.path.dirname(__file__), "..", "..", "mcp-cloud.json")
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    mcp_servers = data.get("mcpServers", {})
                    
                    for name, config in mcp_servers.items():
                        servers.append({
                            "server_name": name,
                            "server_type": "builtin",
                            "config": config,
                            "enabled": config.get("enabled", True),
                            "description": config.get("description", "")
                        })
                break
            except Exception as e:
                print(f"[MCPConfig] Error loading {path}: {e}")
    
    return servers


# ============================================================================
# Routes
# ============================================================================

@router.get("/mcp-servers")
async def list_mcp_servers(user: Dict = Depends(get_current_user)):
    """
    List all available MCP servers for the user.
    Returns both built-in and user-defined servers.
    """
    config = get_deployment_config()
    user_id = str(user["id"])
    
    servers = []
    
    # Add built-in servers
    builtin = _load_builtin_servers()
    servers.extend(builtin)
    
    # Add user-defined servers (cloud mode only)
    if config.is_cloud():
        client = _get_supabase_client()
        if client:
            try:
                result = client.table("user_mcp_configs") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .execute()
                
                for row in result.data:
                    servers.append({
                        "id": row["id"],
                        "server_name": row["server_name"],
                        "server_type": "custom",
                        "config": row["config"],
                        "enabled": row["enabled"],
                        "created_at": row.get("created_at")
                    })
            except Exception as e:
                print(f"[MCPConfig] Error fetching user configs: {e}")
    
    return {
        "servers": servers,
        "builtin_count": len(builtin),
        "custom_count": len(servers) - len(builtin),
        "cloud_mode": config.is_cloud()
    }


@router.post("/mcp-servers")
async def add_mcp_server(
    server: MCPServerConfig,
    user: Dict = Depends(get_current_user)
):
    """
    Add a new user-defined MCP server configuration.
    Only available in cloud mode.
    """
    config = get_deployment_config()
    
    if not config.is_cloud():
        raise HTTPException(
            status_code=400,
            detail="User MCP server configuration is only available in cloud mode. "
                   "For local mode, edit mcp.json directly."
        )
    
    user_id = str(user["id"])
    client = _get_supabase_client()
    
    if not client:
        raise HTTPException(
            status_code=500,
            detail="Storage not available"
        )
    
    # Build config object
    server_config = {
        "command": server.command,
        "args": server.args,
        "env": server.env,
        "description": server.description
    }
    
    try:
        # Upsert (update if exists, insert if not)
        result = client.table("user_mcp_configs").upsert({
            "user_id": user_id,
            "server_name": server.server_name,
            "server_type": "custom",
            "config": server_config,
            "enabled": server.enabled,
            "updated_at": datetime.now().isoformat()
        }, on_conflict="user_id,server_name").execute()
        
        if result.data:
            return {
                "message": "MCP server configuration saved",
                "server": result.data[0]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mcp-servers/{server_name}")
async def update_mcp_server(
    server_name: str,
    server: MCPServerConfig,
    user: Dict = Depends(get_current_user)
):
    """Update an existing user-defined MCP server configuration."""
    config = get_deployment_config()
    
    if not config.is_cloud():
        raise HTTPException(status_code=400, detail="Only available in cloud mode")
    
    user_id = str(user["id"])
    client = _get_supabase_client()
    
    if not client:
        raise HTTPException(status_code=500, detail="Storage not available")
    
    server_config = {
        "command": server.command,
        "args": server.args,
        "env": server.env,
        "description": server.description
    }
    
    try:
        result = client.table("user_mcp_configs") \
            .update({
                "config": server_config,
                "enabled": server.enabled,
                "updated_at": datetime.now().isoformat()
            }) \
            .eq("user_id", user_id) \
            .eq("server_name", server_name) \
            .execute()
        
        if result.data:
            return {"message": "Configuration updated", "server": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="Server not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mcp-servers/{server_name}")
async def delete_mcp_server(
    server_name: str,
    user: Dict = Depends(get_current_user)
):
    """Delete a user-defined MCP server configuration."""
    config = get_deployment_config()
    
    if not config.is_cloud():
        raise HTTPException(status_code=400, detail="Only available in cloud mode")
    
    user_id = str(user["id"])
    client = _get_supabase_client()
    
    if not client:
        raise HTTPException(status_code=500, detail="Storage not available")
    
    try:
        result = client.table("user_mcp_configs") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("server_name", server_name) \
            .execute()
        
        if result.data:
            return {"message": "Server configuration deleted"}
        else:
            raise HTTPException(status_code=404, detail="Server not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/mcp-servers/{server_name}/toggle")
async def toggle_mcp_server(
    server_name: str,
    user: Dict = Depends(get_current_user)
):
    """Toggle enabled/disabled state of a user-defined MCP server."""
    config = get_deployment_config()
    
    if not config.is_cloud():
        raise HTTPException(status_code=400, detail="Only available in cloud mode")
    
    user_id = str(user["id"])
    client = _get_supabase_client()
    
    if not client:
        raise HTTPException(status_code=500, detail="Storage not available")
    
    try:
        # Get current state
        result = client.table("user_mcp_configs") \
            .select("enabled") \
            .eq("user_id", user_id) \
            .eq("server_name", server_name) \
            .single() \
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Toggle
        new_state = not result.data["enabled"]
        
        update_result = client.table("user_mcp_configs") \
            .update({
                "enabled": new_state,
                "updated_at": datetime.now().isoformat()
            }) \
            .eq("user_id", user_id) \
            .eq("server_name", server_name) \
            .execute()
        
        return {
            "message": f"Server {'enabled' if new_state else 'disabled'}",
            "enabled": new_state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mcp-servers/user-configs")
async def get_user_mcp_configs_for_agent(user: Dict = Depends(get_current_user)):
    """
    Get user MCP configurations in format ready for CloudAgent.
    This is used internally when creating the agent.
    """
    config = get_deployment_config()
    
    if not config.is_cloud():
        return {"configs": []}
    
    user_id = str(user["id"])
    client = _get_supabase_client()
    
    if not client:
        return {"configs": []}
    
    try:
        result = client.table("user_mcp_configs") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("enabled", True) \
            .execute()
        
        configs = []
        for row in result.data:
            configs.append({
                "server_name": row["server_name"],
                "config": row["config"],
                "enabled": True
            })
        
        return {"configs": configs}
        
    except Exception as e:
        print(f"[MCPConfig] Error: {e}")
        return {"configs": []}
