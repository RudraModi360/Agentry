"""
Chat and messaging data models.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

__all__ = ["ChatMessage", "MCPConfigRequest", "AutoCorrectRequest", "DisabledToolsRequest"]


class ChatMessage(BaseModel):
    content: str
    session_id: Optional[str] = "default"


class MCPConfigRequest(BaseModel):
    config: Dict[str, Any]


class AutoCorrectRequest(BaseModel):
    text: str


class DisabledToolsRequest(BaseModel):
    disabled_tools: List[str]
