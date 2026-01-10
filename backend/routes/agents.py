"""
Agent configuration routes.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends

from backend.config import DB_PATH
from backend.core.dependencies import get_current_user
from backend.models.agent import AgentTypeConfig, ProjectConfig, MemoryEntry
from backend.services.agent_cache import agent_cache

from scratchy.agents import SmartAgent, SmartAgentMode
from scratchy.memory.storage import PersistentMemoryStore

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
        agent_cache[user_id]["agent_type"] = config.agent_type
        if config.agent_type == "smart":
            # Smart agent requires fresh creation
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
        # Table doesn't exist yet
        return {"agent_type": "default", "mode": None, "project_id": None}
    finally:
        conn.close()


# --- Project Management ---

@router.get("/projects")
async def list_projects(user: Dict = Depends(get_current_user)):
    """List all projects for the user."""
    memory = PersistentMemoryStore()
    projects = memory.get_all_projects(user_id=user["id"])
    return {"projects": projects}


@router.post("/projects")
async def create_project(config: ProjectConfig, user: Dict = Depends(get_current_user)):
    """Create a new project."""
    memory = PersistentMemoryStore()
    project = memory.create_project(
        project_id=config.project_id,
        title=config.title,
        goal=config.goal,
        environment=config.environment,
        key_files=config.key_files,
        user_id=user["id"]
    )
    return {"project": project}


@router.get("/projects/{project_id}")
async def get_project(project_id: str, user: Dict = Depends(get_current_user)):
    """Get a specific project."""
    memory = PersistentMemoryStore()
    project = memory.get_project(project_id, user_id=user["id"])
    if not project:
        return {"error": "Project not found"}
    return {"project": project}


@router.post("/projects/{project_id}/focus")
async def update_project_focus(project_id: str, focus: str, user: Dict = Depends(get_current_user)):
    """Update the current focus of a project."""
    memory = PersistentMemoryStore()
    memory.update_project_focus(project_id, focus, user_id=user["id"])
    return {"message": "Focus updated"}


# --- Memory APIs ---

@router.get("/memories") 
async def get_memories(
    project_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 50,
    user: Dict = Depends(get_current_user)
):
    """Get memories with optional filters."""
    memory = PersistentMemoryStore()
    memories = memory.search(
        query="",  # Empty query returns all
        project_id=project_id,
        memory_type=memory_type,
        limit=limit,
        user_id=user["id"]
    )
    return {"memories": memories}


@router.post("/memories")
async def add_memory(entry: MemoryEntry, user: Dict = Depends(get_current_user)):
    """Add a new memory entry."""
    memory = PersistentMemoryStore()
    memory_id = memory.add(
        memory_type=entry.memory_type,
        title=entry.title,
        content=entry.content,
        tags=entry.tags,
        project_id=entry.project_id,
        user_id=user["id"]
    )
    return {"id": memory_id, "message": "Memory added"}


@router.get("/memories/search")
async def search_memories(
    q: str,
    project_id: Optional[str] = None,
    limit: int = 10,
    user: Dict = Depends(get_current_user)
):
    """Search memories."""
    memory = PersistentMemoryStore()
    results = memory.search(
        query=q,
        project_id=project_id,
        limit=limit,
        user_id=user["id"]
    )
    return {"memories": results}


@router.get("/memories/export")
async def export_memory(
    project_id: Optional[str] = None,
    format: str = "markdown",
    user: Dict = Depends(get_current_user)
):
    """Export memory in LLM-friendly format."""
    memory = PersistentMemoryStore()
    export = memory.export_for_llm(project_id=project_id, format=format, user_id=user["id"])
    return {"export": export}


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int, user: Dict = Depends(get_current_user)):
    """Delete a memory entry."""
    memory = PersistentMemoryStore()
    memory.delete(memory_id, user_id=user["id"])
    return {"message": "Memory deleted"}
