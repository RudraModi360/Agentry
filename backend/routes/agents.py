"""
Agent configuration routes.
Uses SimpleMem (LanceDB) for per-user memory storage.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Optional, List

from fastapi import APIRouter, Depends

from backend.config import DB_PATH
from backend.core.dependencies import get_current_user
from backend.models.agent import AgentTypeConfig, ProjectConfig, MemoryEntry
from backend.services.agent_cache import agent_cache
from backend.services.simplemem_middleware import (
    search_memories_simplemem,
    add_memory_simplemem,
    get_memory_stats,
    is_simplemem_enabled
)

from agentry.agents import SmartAgent, SmartAgentMode

router = APIRouter()


@router.get("/agent-types")
async def get_agent_types():
    """Get available agent types."""
    return {
        "agent_types": [
            {
                "id": "default",
                "name": "Default Agent",
                "description": "Standard agent with configurable tools. Best for general-purpose tasks.",
                "features": ["Configurable tools", "Single-turn responses", "Direct API calls"]
            },
            {
                "id": "copilot", 
                "name": "Copilot Agent",
                "description": "Conversational assistant with context awareness. Great for pair programming.",
                "features": ["Conversation memory", "Code completion", "Documentation lookup"]
            },
            {
                "id": "smart",
                "name": "Smart Agent (Beta)",
                "description": "Autonomous goal-oriented agent with planning and self-debugging. Best for complex, multi-step tasks.",
                "features": [
                    "Autonomous planning",
                    "Self-debugging & retries", 
                    "Persistent memory",
                    "Multi-file operations",
                    "5 locked essential tools"
                ],
                "modes": [
                    {"id": "autonomous", "name": "Autonomous", "description": "Agent plans and executes independently"},
                    {"id": "interactive", "name": "Interactive", "description": "Agent asks for confirmation before major actions"},
                    {"id": "plan_only", "name": "Plan Only", "description": "Agent creates plan but waits for approval"}
                ],
                "locked_tools": True
            }
        ]
    }


@router.post("/agent-config")
async def configure_agent_type(config: AgentTypeConfig, user: Dict = Depends(get_current_user)):
    """Configure the agent type for a user."""
    user_id = user["id"]
    
    # Store in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_agent_config (
                user_id INTEGER PRIMARY KEY,
                agent_type TEXT DEFAULT 'default',
                mode TEXT,
                project_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            INSERT INTO user_agent_config (user_id, agent_type, mode, project_id, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                agent_type = excluded.agent_type,
                mode = excluded.mode,
                project_id = excluded.project_id,
                updated_at = excluded.updated_at
        """, (user_id, config.agent_type, config.mode, config.project_id, datetime.now()))
        conn.commit()
    finally:
        conn.close()
    
    # Invalidate agent cache to force recreation with new type
    if user_id in agent_cache:
        del agent_cache[user_id]
    
    return {"message": "Agent type configured", "agent_type": config.agent_type}


@router.get("/agent-config")
async def get_agent_config(user: Dict = Depends(get_current_user)):
    """Get current agent configuration."""
    user_id = user["id"]
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM user_agent_config WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                "agent_type": row["agent_type"],
                "mode": row["mode"],
                "project_id": row["project_id"]
            }
        return {"agent_type": "default", "mode": None, "project_id": None}
    except sqlite3.OperationalError:
        return {"agent_type": "default", "mode": None, "project_id": None}
    finally:
        conn.close()


# --- Project Management (SQLite-based for structure) ---

@router.get("/projects")
async def list_projects(user: Dict = Depends(get_current_user)):
    """List all projects for the user."""
    user_id = user["id"]
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_projects (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                goal TEXT,
                environment TEXT,
                key_files TEXT,
                current_focus TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        cursor.execute("SELECT * FROM user_projects WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            import json
            projects.append({
                "id": row["id"],
                "title": row["title"],
                "goal": row["goal"],
                "environment": row["environment"],
                "key_files": json.loads(row["key_files"]) if row["key_files"] else [],
                "current_focus": row["current_focus"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return {"projects": projects}
    finally:
        conn.close()


@router.post("/projects")
async def create_project(config: ProjectConfig, user: Dict = Depends(get_current_user)):
    """Create a new project."""
    import json
    user_id = user["id"]
    now = datetime.now()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_projects (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                goal TEXT,
                environment TEXT,
                key_files TEXT,
                current_focus TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO user_projects (id, user_id, title, goal, environment, key_files, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (config.project_id, user_id, config.title, config.goal, 
              config.environment, json.dumps(config.key_files or []), now, now))
        conn.commit()
        
        return {"project": {
            "id": config.project_id,
            "title": config.title,
            "goal": config.goal,
            "created_at": now.isoformat()
        }}
    finally:
        conn.close()


@router.get("/projects/{project_id}")
async def get_project(project_id: str, user: Dict = Depends(get_current_user)):
    """Get a specific project."""
    import json
    user_id = user["id"]
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM user_projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        row = cursor.fetchone()
        
        if not row:
            return {"error": "Project not found"}
        
        return {"project": {
            "id": row["id"],
            "title": row["title"],
            "goal": row["goal"],
            "environment": row["environment"],
            "key_files": json.loads(row["key_files"]) if row["key_files"] else [],
            "current_focus": row["current_focus"]
        }}
    finally:
        conn.close()


@router.post("/projects/{project_id}/focus")
async def update_project_focus(project_id: str, focus: str, user: Dict = Depends(get_current_user)):
    """Update the current focus of a project."""
    user_id = user["id"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE user_projects SET current_focus = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (focus, datetime.now(), project_id, user_id)
        )
        conn.commit()
        return {"message": "Focus updated"}
    finally:
        conn.close()


# --- Memory APIs (SimpleMem/LanceDB-based) ---

@router.get("/memories") 
async def get_memories(
    project_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 50,
    user: Dict = Depends(get_current_user)
):
    """Get memories using SimpleMem vector search."""
    user_id = str(user["id"])
    
    if not is_simplemem_enabled():
        return {"memories": [], "message": "SimpleMem not enabled"}
    
    # Use empty query to get recent memories
    memories = await search_memories_simplemem(user_id, "", limit=limit)
    return {"memories": memories}


@router.post("/memories")
async def add_memory(entry: MemoryEntry, user: Dict = Depends(get_current_user)):
    """Add a new memory entry to SimpleMem."""
    user_id = str(user["id"])
    
    if not is_simplemem_enabled():
        return {"error": "SimpleMem not enabled"}
    
    content = f"{entry.title}: {entry.content}" if entry.title else entry.content
    success = await add_memory_simplemem(user_id, content, entry.memory_type or "manual")
    
    if success:
        return {"message": "Memory added"}
    return {"error": "Failed to add memory"}


@router.get("/memories/search")
async def search_memories(
    q: str,
    project_id: Optional[str] = None,
    limit: int = 10,
    user: Dict = Depends(get_current_user)
):
    """Search memories using SimpleMem's semantic search."""
    user_id = str(user["id"])
    
    if not is_simplemem_enabled():
        return {"memories": [], "message": "SimpleMem not enabled"}
    
    results = await search_memories_simplemem(user_id, q, limit=limit)
    return {"memories": results}


@router.get("/memories/stats")
async def memory_stats(user: Dict = Depends(get_current_user)):
    """Get SimpleMem statistics for the user."""
    user_id = str(user["id"])
    stats = get_memory_stats(user_id, "api")
    return {"stats": stats}


@router.get("/memories/export")
async def export_memory(
    project_id: Optional[str] = None,
    format: str = "markdown",
    user: Dict = Depends(get_current_user)
):
    """Export memory in LLM-friendly format."""
    user_id = str(user["id"])
    
    if not is_simplemem_enabled():
        return {"export": "SimpleMem not enabled"}
    
    memories = await search_memories_simplemem(user_id, "", limit=100)
    
    if format == "markdown":
        lines = ["# Memory Export\n"]
        for m in memories:
            lines.append(f"- {m.get('content', '')}")
        return {"export": "\n".join(lines)}
    else:
        import json
        return {"export": json.dumps(memories)}


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int, user: Dict = Depends(get_current_user)):
    """Delete a memory entry (not supported in SimpleMem)."""
    return {"message": "Memory deletion not available in vector storage", "note": "Use memory expiry instead"}
