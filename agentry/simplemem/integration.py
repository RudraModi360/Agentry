"""
SimpleMem integration for Agentry.

Provides high-performance context engineering:
- Fast embedding-based retrieval (10-50ms target)
- Background memory processing (non-blocking)
- Per-user memory isolation

Based on SimpleMem: https://github.com/aiming-lab/SimpleMem
"""
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import threading
import queue

from . import config


@dataclass
class MemoryEntry:
    """Atomic memory entry."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lossless_restatement: str = ""
    keywords: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    location: Optional[str] = None
    persons: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    topic: Optional[str] = None


@dataclass  
class Dialogue:
    """A single dialogue turn."""
    dialogue_id: int
    speaker: str
    content: str
    timestamp: Optional[str] = None
    
    def __str__(self):
        ts = f"[{self.timestamp}] " if self.timestamp else ""
        return f"{ts}{self.speaker}: {self.content}"


class AgentrySimpleMem:
    """
    SimpleMem integration for Agentry.
    
    Features:
    - Per-user memory isolation (separate LanceDB tables)
    - Async-compatible operations
    - Background memory processing
    - Fast embedding-only retrieval
    
    Usage:
        memory = AgentrySimpleMem(user_id="123", session_id="abc")
        
        # On user message - returns relevant context
        contexts = await memory.on_user_message("What did we discuss?")
        
        # On assistant response - queues for processing
        await memory.on_assistant_message("We discussed...")
        
        # Process queued dialogues (call periodically or on session end)
        await memory.process_pending()
    """
    
    def __init__(
        self,
        user_id: str,
        session_id: str = "default",
        max_context_entries: int = 5,
        enable_background_processing: bool = True,
        debug: bool = False
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.max_context_entries = max_context_entries
        self.enable_background = enable_background_processing
        self.debug = debug
        
        # Per-user table name
        self.table_name = config.get_memory_table_name(user_id)
        
        # Components (lazy initialized)
        self._vector_store = None
        self._embedding_model = None
        self._initialized = False
        
        # Dialogue queue for batch processing
        self._dialogue_queue: List[Dialogue] = []
        self._dialogue_counter = 0
        
        # Background processing
        self._processing_lock = threading.Lock()
    
    def _lazy_init(self):
        """Lazy initialization of vector store and embedding model."""
        if self._initialized:
            return
        
        try:
            from .embedding import EmbeddingModel
            from .vector_store import VectorStore
            
            if self.debug:
                print(f"[SimpleMem] Initializing for user {self.user_id}...")
            
            # Initialize embedding model
            embed_config = config.get_embedding_config()
            self._embedding_model = EmbeddingModel(
                ollama_base_url=embed_config["ollama_url"]
            )
            
            # Initialize vector store with per-user table
            self._vector_store = VectorStore(
                db_path=config.get_lancedb_path(),
                embedding_model=self._embedding_model,
                table_name=self.table_name
            )
            
            self._initialized = True
            
            if self.debug:
                print(f"[SimpleMem] Ready! Table: {self.table_name}")
                
        except Exception as e:
            print(f"[SimpleMem] Init error: {e}")
            self._initialized = True  # Mark as tried to avoid repeated errors
    
    async def on_user_message(self, content: str) -> List[str]:
        """
        Called when user sends a message.
        
        Returns relevant context for LLM augmentation.
        Queues the message for memory processing.
        """
        # Queue dialogue for processing
        self._queue_dialogue("User", content)
        
        # Fast retrieval (embedding-only, no LLM)
        contexts = self._fast_retrieve(content)
        
        if self.debug and contexts:
            print(f"[SimpleMem] Retrieved {len(contexts)} memories")
        
        return contexts
    
    async def on_assistant_message(self, content: str):
        """
        Called when assistant responds.
        Queues the response for memory processing.
        """
        self._queue_dialogue("Assistant", content)
    
    def _queue_dialogue(self, speaker: str, content: str):
        """Add dialogue to processing queue."""
        self._dialogue_counter += 1
        dialogue = Dialogue(
            dialogue_id=self._dialogue_counter,
            speaker=speaker,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        self._dialogue_queue.append(dialogue)
        
        if self.debug:
            print(f"[SimpleMem] Queued: [{speaker}] {content[:50]}...")
    
    def _fast_retrieve(self, query: str, limit: int = None) -> List[str]:
        """
        Pure embedding retrieval - NO LLM calls.
        Target latency: 10-50ms
        """
        self._lazy_init()
        
        if not self._vector_store:
            return []
        
        limit = limit or self.max_context_entries
        
        try:
            results = self._vector_store.semantic_search(query, top_k=limit)
            return [r.lossless_restatement for r in results if r.lossless_restatement]
        except Exception as e:
            if self.debug:
                print(f"[SimpleMem] Retrieval error: {e}")
            return []
    
    async def process_pending(self):
        """
        Process pending dialogues and store as memories.
        
        For now, stores dialogues directly (simplified approach).
        Full SimpleMem uses LLM-based atomic extraction.
        """
        if not self._dialogue_queue:
            return
        
        self._lazy_init()
        
        if not self._vector_store:
            self._dialogue_queue = []
            return
        
        with self._processing_lock:
            dialogues = self._dialogue_queue.copy()
            self._dialogue_queue = []
        
        try:
            if self.debug:
                print(f"[SimpleMem] Processing {len(dialogues)} dialogues...")
            
            # Convert dialogues to memory entries (simplified)
            entries = []
            for dialogue in dialogues:
                entry = MemoryEntry(
                    lossless_restatement=f"[{dialogue.speaker}]: {dialogue.content}",
                    keywords=self._extract_keywords(dialogue.content),
                    timestamp=dialogue.timestamp,
                    persons=[dialogue.speaker] if dialogue.speaker else [],
                )
                entries.append(entry)
            
            # Store to vector store
            if entries:
                self._vector_store.add_entries(entries)
            
            if self.debug:
                print(f"[SimpleMem] Stored {len(entries)} memories")
                
        except Exception as e:
            if self.debug:
                print(f"[SimpleMem] Processing error: {e}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction (no LLM)."""
        import re
        
        # Common stop words
        stop_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
            'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
            'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
            'which', 'go', 'me', 'is', 'are', 'was', 'were', 'been', 'being',
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:10]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        self._lazy_init()
        
        stats = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "table_name": self.table_name,
            "initialized": self._initialized,
            "pending_dialogues": len(self._dialogue_queue),
        }
        
        if self._vector_store:
            try:
                all_entries = self._vector_store.get_all_entries()
                stats["total_memories"] = len(all_entries)
            except:
                stats["total_memories"] = "unknown"
        
        return stats
    
    def clear_memories(self):
        """Clear all memories for this user."""
        self._lazy_init()
        
        if self._vector_store:
            self._vector_store.clear()
            if self.debug:
                print(f"[SimpleMem] Cleared memories for {self.user_id}")
