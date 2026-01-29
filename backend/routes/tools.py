"""
Tools management routes.
"""
import json
import sqlite3
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from backend.config import DB_PATH
from backend.core.dependencies import get_current_user
from backend.models.chat import DisabledToolsRequest
from backend.services.agent_cache import agent_cache

router = APIRouter()


@router.get("")
async def get_available_tools(user: Dict = Depends(get_current_user)):
    """Get all available tools (built-in and MCP) for the user (cached)."""
    from backend.routes.agents import get_agent_config
    from backend.core.cache import tools_cache
    
    user_id = user["id"]
    cache_key = f"tools:{user_id}"
    
    # Try cache first
    cached = tools_cache.get(cache_key)
    if cached is not None:
        return cached
    
    builtin_tools = []
    mcp_tools = {}
    
    # Get tools from agent if cached
    if user_id in agent_cache:
        agent = agent_cache[user_id].get("agent")
        
        if agent and hasattr(agent, 'internal_tools'):
            mcp_tool_names = set()
            
            # First, get MCP tool names to exclude from built-in
            if hasattr(agent, 'mcp_managers'):
                for manager in agent.mcp_managers:
                    if hasattr(manager, 'server_tools_map'):
                        mcp_tool_names.update(manager.server_tools_map.keys())
            
            # Now iterate internal_tools
            for tool_schema in agent.internal_tools:
                if isinstance(tool_schema, dict) and 'function' in tool_schema:
                    func_info = tool_schema['function']
                    tool_name = func_info.get('name', 'unknown')
                    
                    if tool_name in mcp_tool_names:
                        continue
                    
                    description = func_info.get('description', '')
                    builtin_tools.append({
                        "name": tool_name,
                        "description": description[:100] if description else "No description"
                    })
                    
            # Get MCP tools
            if hasattr(agent, 'mcp_managers'):
                for manager in agent.mcp_managers:
                    if hasattr(manager, 'server_tools_cache') and manager.server_tools_cache:
                        for server_name, tools in manager.server_tools_cache.items():
                            if server_name not in mcp_tools:
                                mcp_tools[server_name] = []
                            for tool in tools:
                                if not any(t["name"] == tool["name"] for t in mcp_tools[server_name]):
                                    description = tool.get('description', 'No description')
                                    mcp_tools[server_name].append({
                                        "name": tool["name"],
                                        "description": description[:100] if description else "No description"
                                    })
                    
                    elif hasattr(manager, 'server_tools_map'):
                        for tool_name, server_name in manager.server_tools_map.items():
                            if server_name not in mcp_tools:
                                mcp_tools[server_name] = []
                            if not any(t["name"] == tool_name for t in mcp_tools[server_name]):
                                mcp_tools[server_name].append({
                                    "name": tool_name,
                                    "description": "Consolidating tool info..."
                                })
    
    # If no agent cached, return all available default tools from registry
    if not builtin_tools:
        from agentry.tools import ALL_TOOL_SCHEMAS
        for schema in ALL_TOOL_SCHEMAS:
            if isinstance(schema, dict) and 'function' in schema:
                func = schema['function']
                builtin_tools.append({
                    "name": func.get("name"),
                    "description": func.get("description", "No description")[:100]
                })
    
    # Get MCP server names from config if no tools loaded yet
    if not mcp_tools:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT config_json FROM user_mcp_config WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                config = json.loads(row["config_json"])
                for server_name in config.get("mcpServers", {}).keys():
                    mcp_tools[server_name] = []
        finally:
            conn.close()
    
    # Determine if tools are locked
    tools_locked = False
    if user_id in agent_cache:
        tools_locked = agent_cache[user_id].get("agent_type") == "smart"
    else:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT agent_type FROM user_agent_config WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0] == "smart":
                tools_locked = True
            conn.close()
        except:
            pass

    result = {
        "builtin": builtin_tools,
        "mcp": mcp_tools,
        "tools_locked": tools_locked
    }
    
    # Cache result
    tools_cache.set(cache_key, result)
    
    return result


@router.post("/disabled")
async def save_disabled_tools(request: DisabledToolsRequest, user: Dict = Depends(get_current_user)):
    """Save the list of disabled tools for the user."""
    from backend.routes.agents import get_agent_config
    from backend.core.cache import tools_cache
    import time
    
    start = time.time()
    user_id = user["id"]
    disabled_tools = request.disabled_tools

    # Check if user is using a Smart Agent (fast - check cache first)
    current_agent_type = "default"
    if user_id in agent_cache:
        current_agent_type = agent_cache[user_id].get("agent_type", "default")
    else:
        # Only hit DB if not cached
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT agent_type FROM user_agent_config WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                current_agent_type = row[0]
            conn.close()
        except:
            pass

    if current_agent_type == "smart":
        raise HTTPException(
            status_code=400, 
            detail="Granular tool disabling is not available for Smart Agent. All 5 essential tools are locked."
        )
    
    # Store in database with pooled connection
    from backend.core.db_pool import connection_context
    try:
        with connection_context() as conn:
            cursor = conn.cursor()
            disabled_json = json.dumps(disabled_tools)
            cursor.execute("""
                INSERT INTO user_disabled_tools (user_id, disabled_tools_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    disabled_tools_json = excluded.disabled_tools_json,
                    updated_at = excluded.updated_at
            """, (user_id, disabled_json, datetime.now()))
    except sqlite3.OperationalError:
        # Table doesn't exist, create it
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_disabled_tools (
                user_id INTEGER PRIMARY KEY,
                disabled_tools_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        disabled_json = json.dumps(disabled_tools)
        cursor.execute("""
            INSERT INTO user_disabled_tools (user_id, disabled_tools_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                disabled_tools_json = excluded.disabled_tools_json,
                updated_at = excluded.updated_at
        """, (user_id, disabled_json, datetime.now()))
        conn.commit()
        conn.close()
    
    # Update agent if cached
    if user_id in agent_cache:
        agent = agent_cache[user_id].get("agent")
        if agent:
            agent.disabled_tools = set(disabled_tools)
            print(f"[Server] Updated disabled tools for user {user_id}: {disabled_tools}")
    
    # Invalidate tools cache
    tools_cache.delete(f"tools:{user_id}")
    
    elapsed = time.time() - start
    if elapsed > 0.5:
        print(f"[Server] Warning: save_disabled_tools took {elapsed:.2f}s")
    
    return {"message": "Disabled tools saved", "count": len(disabled_tools)}


@router.get("/disabled")
async def get_disabled_tools(user: Dict = Depends(get_current_user)):
    """Get the list of disabled tools for the user."""
    user_id = user["id"]
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT disabled_tools_json FROM user_disabled_tools WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {"disabled_tools": json.loads(row["disabled_tools_json"])}
        return {"disabled_tools": []}
    finally:
        conn.close()
