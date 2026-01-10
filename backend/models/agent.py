"""
Agent configuration data models.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel

__all__ = ["AgentTypeConfig", "ProjectConfig", "MemoryEntry"]


class AgentTypeConfig(BaseModel):
    """Configuration for agent type selection."""
    agent_type: str
    mode: Optional[str] = None
    project_id: Optional[str] = None


class ProjectConfig(BaseModel):
    """Configuration for creating a new project."""
    project_id: str
    title: str
    goal: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    key_files: Optional[List[str]] = None


class MemoryEntry(BaseModel):
    """A memory entry to store."""
    memory_type: str
    title: str
    content: str
    tags: Optional[List[str]] = None
    project_id: Optional[str] = None
