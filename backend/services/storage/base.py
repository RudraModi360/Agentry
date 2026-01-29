"""
Abstract base classes for storage backends.
Defines the interface that both local and cloud implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, BinaryIO
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionData:
    """Represents a chat session."""
    id: str
    user_id: str
    title: str
    provider: Optional[str] = None
    model: Optional[str] = None
    model_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0


@dataclass
class MessageData:
    """Represents a chat message."""
    id: str
    session_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class MediaData:
    """Represents a media file."""
    id: str
    user_id: str
    filename: str
    url: str
    content_type: str
    created_at: Optional[datetime] = None


class ChatStorageBase(ABC):
    """Interface for chat/session storage."""
    
    @abstractmethod
    async def create_session(self, user_id: str, metadata: Dict[str, Any]) -> SessionData:
        """Create a new chat session."""
        pass
    
    @abstractmethod
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[SessionData]:
        """Get all sessions for a user."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a specific session by ID."""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session metadata."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages."""
        pass
    
    @abstractmethod
    async def save_message(self, session_id: str, role: str, content: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> MessageData:
        """Save a chat message."""
        pass
    
    @abstractmethod
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[MessageData]:
        """Get messages for a session."""
        pass
    
    @abstractmethod
    async def search_sessions(self, user_id: str, query: str, limit: int = 20) -> List[SessionData]:
        """Search sessions by title and content."""
        pass


class MediaStorageBase(ABC):
    """Interface for media file storage."""
    
    @abstractmethod
    async def upload(self, filename: str, file: BinaryIO, 
                    content_type: str, user_id: str) -> MediaData:
        """Upload a media file."""
        pass
    
    @abstractmethod
    async def delete(self, media_id: str, user_id: str) -> bool:
        """Delete a media file."""
        pass
    
    @abstractmethod
    async def get_user_media(self, user_id: str, limit: int = 50) -> List[MediaData]:
        """Get all media files for a user."""
        pass
    
    @abstractmethod
    async def get_media(self, media_id: str) -> Optional[MediaData]:
        """Get a specific media file by ID."""
        pass


class MetricsBase(ABC):
    """Interface for performance metrics."""
    
    @abstractmethod
    async def log_request(self, user_id: str, endpoint: str, method: str,
                         latency_ms: float, **kwargs) -> None:
        """Log a request metric."""
        pass
    
    @abstractmethod
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a user."""
        pass
    
    @abstractmethod
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide stats."""
        pass
