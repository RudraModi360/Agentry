"""
MCP (Model Context Protocol) configuration routes.
"""
import json
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends

from backend.config import DB_PATH
from backend.core.dependencies import get_current_user
from backend.models.chat import MCPConfigRequest
from backend.services.agent_cache import agent_cache

router = APIRouter()


@router.get("/config")
async def get_mcp_config(user: Dict = Depends(get_current_user)):
    """Get MCP configuration for the user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT config_json FROM user_mcp_config WHERE user_id = ?", (user["id"],))
        row = cursor.fetchone()
        if row:
            return {"config": json.loads(row["config_json"])}
        return {"config": {"mcpServers": {}}}
    finally:
        conn.close()


@router.post("/config")
async def save_mcp_config(request: MCPConfigRequest, user: Dict = Depends(get_current_user)):
    """Save MCP configuration for the user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        config_json = json.dumps(request.config)
        cursor.execute("""
            INSERT INTO user_mcp_config (user_id, config_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                config_json = excluded.config_json,
                updated_at = excluded.updated_at
        """, (user["id"], config_json, datetime.now()))
        conn.commit()
    finally:
        conn.close()

    # Hot-reload agent if it exists
    user_id = user["id"]
    if user_id in agent_cache:
        try:
            agent = agent_cache[user_id]["agent"]
            # Hot-reload MCP servers for the active agent
            if hasattr(agent, 'clear_mcp_servers') and hasattr(agent, 'add_mcp_server'):
                print(f"[Server] Hot-reloading MCP config for user {user_id}")
                
                old_manager_count = len(agent.mcp_managers) if hasattr(agent, 'mcp_managers') else 0
                print(f"[Server]   Before clear: {old_manager_count} managers")
                
                await agent.clear_mcp_servers()
                
                print(f"[Server]   Adding MCP servers from config...")
                await agent.add_mcp_server(config=request.config)
                
                new_manager_count = len(agent.mcp_managers) if hasattr(agent, 'mcp_managers') else 0
                print(f"[Server]   After add: {new_manager_count} managers")
                
                for idx, manager in enumerate(agent.mcp_managers):
                    session_names = list(manager.sessions.keys()) if hasattr(manager, 'sessions') else []
                    tool_count = len(manager.server_tools_map) if hasattr(manager, 'server_tools_map') else 0
                    print(f"[Server]   Manager {idx}: sessions={session_names}, tools={tool_count}")
                
                print(f"[Server] MCP hot-reload complete.")
            else:
                print(f"[Server] Agent doesn't support hot-reload, invalidating cache for user {user_id}")
                del agent_cache[user_id]
        except Exception as e:
            import traceback
            print(f"[Server] Failed to hot-reload MCP config: {e}")
            traceback.print_exc()
            if user_id in agent_cache:
                del agent_cache[user_id]

    return {"message": "Configuration saved"}


@router.get("/status")
async def get_mcp_status(user: Dict = Depends(get_current_user)):
    """Check status of configured MCP servers."""
    user_id = user["id"]
    
    # Get real connection status from active agent if available
    connected_servers = set()
    agent_active = False
    
    if user_id in agent_cache:
        try:
            agent = agent_cache[user_id]["agent"]
            if hasattr(agent, 'mcp_managers'):
                for manager in agent.mcp_managers:
                    connected_servers.update(manager.sessions.keys())
            agent_active = True
        except Exception as e:
            print(f"[Server] Error checking agent status: {e}")

    # Get Config
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    config = {}
    try:
        cursor.execute("SELECT config_json FROM user_mcp_config WHERE user_id = ?", (user["id"],))
        row = cursor.fetchone()
        if row:
            config = json.loads(row["config_json"])
    finally:
        conn.close()

    statuses = {}
    mcp_servers = config.get("mcpServers", {})
    
    for name, server_config in mcp_servers.items():
        if agent_active:
            if name in connected_servers:
                statuses[name] = "connected"
            else:
                statuses[name] = "disconnected"
        else:
            command = server_config.get("command")
            if not command:
                statuses[name] = "disconnected"
                continue
                
            cmd_check = command
            if os.name == 'nt' and command in ['npx', 'npm']:
                cmd_check = f"{command}.cmd"
                
            if shutil.which(cmd_check) or shutil.which(command):
                statuses[name] = "connected"
            else:
                try:
                    if os.path.exists(command) and os.access(command, os.X_OK):
                        statuses[name] = "connected"
                    else:
                        statuses[name] = "disconnected"
                except:
                    statuses[name] = "disconnected"
                
    return {"statuses": statuses}
