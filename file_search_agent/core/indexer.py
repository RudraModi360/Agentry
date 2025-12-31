"""
Document Indexer - Crawls directories and indexes documents.
Handles incremental updates and file watching.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import hashlib

from ..config import settings
from ..parsers import get_parser
from ..parsers.base import ParsedDocument
from .embeddings import EmbeddingEngine
from ..storage.vector_store import VectorStore, FAISSVectorStore
from ..storage.metadata_store import MetadataStore

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    Crawls directories and indexes documents for semantic search.
    
    Features:
    - Multi-format document parsing
    - Incremental indexing (only new/changed files)
    - Parallel processing for speed
    - Content deduplication
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_engine: Optional[EmbeddingEngine] = None,
        metadata_store: Optional[MetadataStore] = None
    ):
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        
        self.vector_store = vector_store or FAISSVectorStore(
            dimension=self.embedding_engine.dimension,
            store_path=settings.vector_store_path
        )
        
        self.metadata_store = metadata_store or MetadataStore(
            db_path=settings.metadata_db_path
        )
        
        self._indexed_hashes: Set[str] = set()
        self._load_indexed_hashes()
    
    def _load_indexed_hashes(self):
        """Load hashes of already indexed documents."""
        docs = self.metadata_store.get_all_documents()
        self._indexed_hashes = {doc.get("content_hash") for doc in docs}
    
    def _should_skip_path(self, path: Path) -> bool:
        """Check if path matches ignore patterns."""
        import fnmatch
        name = path.name
        for pattern in settings.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
    
    def _get_files_to_index(self, directory: Path) -> List[Path]:
        """Get all indexable files from directory."""
        files = []
        
        for ext in settings.supported_extensions:
            for file_path in directory.rglob(f"*{ext}"):
                if not self._should_skip_path(file_path):
                    # Check file size
                    if file_path.stat().st_size <= settings.max_file_size_mb * 1024 * 1024:
                        files.append(file_path)
        
        return files
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute hash of file for change detection."""
        stat = file_path.stat()
        hash_input = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def index_file(self, file_path: Path) -> Optional[str]:
        """
        Index a single file.
        
        Returns:
            Document ID if successful, None otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        
        # Check if already indexed (by file hash)
        file_hash = self._compute_file_hash(file_path)
        if file_hash in self._indexed_hashes:
            logger.debug(f"Skipping already indexed: {file_path}")
            return None
        
        # Get parser for file type
        parser = get_parser(file_path)
        if not parser:
            logger.warning(f"No parser for: {file_path}")
            return None
        
        try:
            # Parse document
            doc = parser.parse(file_path)
            
            if not doc.chunks:
                logger.warning(f"No content extracted from: {file_path}")
                return None
            
            # Generate embeddings for chunks
            chunk_texts = [chunk.text for chunk in doc.chunks]
            embeddings = self.embedding_engine.embed_batch(chunk_texts)
            
            # Prepare metadata for each chunk
            metadatas = []
            for chunk in doc.chunks:
                meta = {
                    "file_path": str(doc.file_path),
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    **chunk.metadata
                }
                metadatas.append(meta)
            
            # Add to vector store
            chunk_ids = self.vector_store.add(
                embeddings=embeddings,
                texts=chunk_texts,
                metadatas=metadatas
            )
            
            # Store document metadata
            doc_id = self.metadata_store.add_document(
                file_path=str(doc.file_path),
                file_name=doc.file_name,
                file_type=doc.file_type,
                file_size=doc.file_size,
                content_hash=doc.content_hash,
                file_hash=file_hash,
                chunk_count=len(doc.chunks),
                title=doc.title,
                author=doc.author,
                page_count=doc.page_count,
                indexed_at=datetime.now()
            )
            
            self._indexed_hashes.add(file_hash)
            logger.info(f"Indexed: {file_path} ({len(doc.chunks)} chunks)")
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            return None
    
    def index_directory(
        self,
        directory: Path,
        parallel: bool = True,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Index all documents in a directory.
        
        Args:
            directory: Path to directory
            parallel: Use parallel processing
            max_workers: Number of parallel workers
            
        Returns:
            Statistics about the indexing operation
        """
        directory = Path(directory)
        
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        files = self._get_files_to_index(directory)
        logger.info(f"Found {len(files)} files to index in {directory}")
        
        stats = {
            "total_files": len(files),
            "indexed": 0,
            "skipped": 0,
            "failed": 0,
            "start_time": datetime.now()
        }
        
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.index_file, f): f
                    for f in files
                }
                
                for future in tqdm(as_completed(futures), total=len(files), desc="Indexing"):
                    result = future.result()
                    if result:
                        stats["indexed"] += 1
                    else:
                        stats["skipped"] += 1
        else:
            for file_path in tqdm(files, desc="Indexing"):
                result = self.index_file(file_path)
                if result:
                    stats["indexed"] += 1
                else:
                    stats["skipped"] += 1
        
        # Save indices
        self.vector_store.save()
        
        stats["end_time"] = datetime.now()
        stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        
        logger.info(
            f"Indexing complete: {stats['indexed']} indexed, "
            f"{stats['skipped']} skipped in {stats['duration']:.1f}s"
        )
        
        return stats
    
    def remove_document(self, file_path: str) -> bool:
        """Remove a document from the index."""
        # Get chunk IDs for this document
        chunk_ids = self.metadata_store.get_chunk_ids(file_path)
        
        if chunk_ids:
            self.vector_store.delete(chunk_ids)
        
        return self.metadata_store.remove_document(file_path)
    
    def clear_index(self):
        """Clear all indexed data."""
        self.metadata_store.clear_all()
        self._indexed_hashes.clear()
        logger.info("Index cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        return {
            "total_documents": self.metadata_store.document_count,
            "total_chunks": self.vector_store.count,
            "file_types": self.metadata_store.get_file_type_counts()
        }
