"""
Streaming Session Manager
=========================
Manages active streaming sessions to prevent interruptions when:
- User reloads the page
- User switches between sessions
- User opens new chat sessions

Key features:
- Each session has isolated streaming state
- Page reload doesn't interrupt ongoing streams
- Session switching preserves active streams
- Proper cleanup when streams complete
"""

import asyncio
from typing import Dict, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ActiveStream:
    """Represents an active streaming session."""
    session_id: str
    user_id: int
    started_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    is_cancelled: bool = False
    accumulated_response: str = ""
    media_state: Dict[str, Any] = field(default_factory=dict)
    
    def cancel(self):
        """Mark the stream as cancelled."""
        self.is_cancelled = True
        self.is_active = False
    
    def complete(self):
        """Mark the stream as completed."""
        self.is_active = False


class StreamingManager:
    """
    Manages active streaming sessions across all users.
    
    This ensures that:
    1. Each session has its own isolated streaming state
    2. Page reloads don't interrupt ongoing streams  
    3. Switching sessions doesn't affect other active sessions
    4. New sessions can be started while others are streaming
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Map: session_id -> ActiveStream
        self.active_streams: Dict[str, ActiveStream] = {}
        
        # Map: user_id -> set of session_ids with active streams
        self.user_streams: Dict[int, Set[str]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        self._initialized = True
        logger.info("[StreamingManager] Initialized")
    
    async def start_stream(self, session_id: str, user_id: int) -> ActiveStream:
        """
        Start a new streaming session.
        Returns the ActiveStream object for tracking.
        """
        async with self._lock:
            # Create new stream
            stream = ActiveStream(
                session_id=session_id,
                user_id=user_id,
                media_state={"committed": False, "data": {}}
            )
            
            self.active_streams[session_id] = stream
            
            # Track user's streams
            if user_id not in self.user_streams:
                self.user_streams[user_id] = set()
            self.user_streams[user_id].add(session_id)
            
            logger.info(f"[StreamingManager] Started stream for session {session_id}")
            return stream
    
    async def get_stream(self, session_id: str) -> Optional[ActiveStream]:
        """Get an active stream by session ID."""
        return self.active_streams.get(session_id)
    
    async def is_streaming(self, session_id: str) -> bool:
        """Check if a session is currently streaming."""
        stream = self.active_streams.get(session_id)
        return stream is not None and stream.is_active
    
    async def complete_stream(self, session_id: str):
        """Mark a stream as completed and clean up."""
        async with self._lock:
            stream = self.active_streams.get(session_id)
            if stream:
                stream.complete()
                
                # Clean up
                if session_id in self.active_streams:
                    del self.active_streams[session_id]
                
                user_id = stream.user_id
                if user_id in self.user_streams:
                    self.user_streams[user_id].discard(session_id)
                    if not self.user_streams[user_id]:
                        del self.user_streams[user_id]
                
                logger.info(f"[StreamingManager] Completed stream for session {session_id}")
    
    async def cancel_stream(self, session_id: str):
        """Cancel an active stream."""
        async with self._lock:
            stream = self.active_streams.get(session_id)
            if stream:
                stream.cancel()
                logger.info(f"[StreamingManager] Cancelled stream for session {session_id}")
    
    async def get_user_active_sessions(self, user_id: int) -> Set[str]:
        """Get all active streaming sessions for a user."""
        return self.user_streams.get(user_id, set()).copy()
    
    async def cleanup_user_streams(self, user_id: int):
        """Clean up all streams for a user (e.g., on logout)."""
        async with self._lock:
            session_ids = self.user_streams.get(user_id, set()).copy()
            for session_id in session_ids:
                if session_id in self.active_streams:
                    self.active_streams[session_id].cancel()
                    del self.active_streams[session_id]
            
            if user_id in self.user_streams:
                del self.user_streams[user_id]
            
            logger.info(f"[StreamingManager] Cleaned up {len(session_ids)} streams for user {user_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        return {
            "total_active_streams": len(self.active_streams),
            "users_with_streams": len(self.user_streams),
            "streams_by_user": {
                user_id: len(sessions) 
                for user_id, sessions in self.user_streams.items()
            }
        }


# Global singleton instance
streaming_manager = StreamingManager()


def get_streaming_manager() -> StreamingManager:
    """Get the streaming manager singleton."""
    return streaming_manager
