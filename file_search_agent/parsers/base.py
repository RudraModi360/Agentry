"""
Base classes for document parsing.
All parsers inherit from BaseParser and return ParsedDocument objects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import hashlib


@dataclass
class DocumentChunk:
    """A chunk of text from a document with metadata."""
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Optional: page number, section, etc.
    page_number: Optional[int] = None
    section: Optional[str] = None
    
    def __len__(self) -> int:
        return len(self.text)


@dataclass
class ParsedDocument:
    """A parsed document with its content and metadata."""
    file_path: Path
    file_name: str
    file_type: str
    content: str
    chunks: List[DocumentChunk]
    
    # Metadata
    file_size: int
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: Optional[int] = None
    
    # Hash for deduplication
    content_hash: str = ""
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    # File extensions this parser handles
    supported_extensions: List[str] = []
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize parser with chunking parameters.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a document and return its content.
        
        Args:
            file_path: Path to the document
            
        Returns:
            ParsedDocument with content and metadata
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks.
        
        Uses sentence-aware chunking to avoid cutting mid-sentence.
        """
        if not text.strip():
            return []
        
        chunks = []
        metadata = metadata or {}
        
        # Split into sentences (simple approach)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        char_position = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=current_start + len(current_chunk),
                        metadata=metadata.copy()
                    ))
                    chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_start = char_position - len(overlap_text)
                current_chunk = overlap_text + sentence + " "
            
            char_position += len(sentence) + 1
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                text=current_chunk.strip(),
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                metadata=metadata.copy()
            ))
        
        return chunks
    
    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file metadata."""
        stat = file_path.stat()
        return {
            "file_size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
        }
