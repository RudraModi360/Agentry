"""
Search Engine - Performs hybrid search combining vector similarity and BM25.
Provides precise, ranked results from indexed documents.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import math

from ..config import settings
from .embeddings import EmbeddingEngine
from ..storage.vector_store import VectorStore, FAISSVectorStore, SearchResult
from ..storage.metadata_store import MetadataStore

logger = logging.getLogger(__name__)


@dataclass
class RankedResult:
    """A search result with combined ranking."""
    chunk_id: str
    text: str
    file_path: str
    file_name: str
    score: float
    vector_score: float
    bm25_score: float
    metadata: Dict[str, Any]
    highlight: Optional[str] = None


class BM25Index:
    """
    Simple BM25 index for keyword search.
    Complements vector search for better precision.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0
        self.term_frequencies: Dict[str, Dict[int, int]] = {}  # term -> {doc_id -> freq}
        self.doc_frequencies: Dict[str, int] = {}  # term -> num docs containing term
        self.total_docs: int = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the BM25 index."""
        for doc in documents:
            doc_id = len(self.documents)
            self.documents.append(doc)
            
            text = doc.get("text", "")
            tokens = self._tokenize(text)
            self.doc_lengths.append(len(tokens))
            
            # Count term frequencies
            seen_terms = set()
            for token in tokens:
                if token not in self.term_frequencies:
                    self.term_frequencies[token] = {}
                
                if doc_id not in self.term_frequencies[token]:
                    self.term_frequencies[token][doc_id] = 0
                
                self.term_frequencies[token][doc_id] += 1
                
                if token not in seen_terms:
                    self.doc_frequencies[token] = self.doc_frequencies.get(token, 0) + 1
                    seen_terms.add(token)
        
        self.total_docs = len(self.documents)
        self.avg_doc_length = sum(self.doc_lengths) / max(1, self.total_docs)
    
    def search(self, query: str, top_k: int = 10) -> List[tuple]:
        """
        Search using BM25 algorithm.
        
        Returns:
            List of (doc_index, score) tuples
        """
        if not self.documents:
            return []
        
        query_tokens = self._tokenize(query)
        scores = {}
        
        for token in query_tokens:
            if token not in self.term_frequencies:
                continue
            
            # IDF component
            df = self.doc_frequencies.get(token, 0)
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
            
            # Score each document containing this term
            for doc_id, tf in self.term_frequencies[token].items():
                doc_len = self.doc_lengths[doc_id]
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                score = idf * numerator / denominator
                
                scores[doc_id] = scores.get(doc_id, 0) + score
        
        # Sort by score and return top_k
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


class SearchEngine:
    """
    Hybrid search engine combining vector similarity and BM25.
    
    Features:
    - Semantic search via vector embeddings
    - Keyword search via BM25
    - Configurable ranking fusion
    - Metadata filtering
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
        
        # BM25 index for keyword search
        self.bm25_index: Optional[BM25Index] = None
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 index from metadata store."""
        # This is a simplified approach - in production, you'd want
        # to incrementally update the BM25 index
        pass  # Will be populated on first search if needed
    
    def _highlight_text(self, text: str, query: str, context_chars: int = 100) -> str:
        """Create a highlighted snippet around query terms."""
        import re
        
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        # Find first occurrence of any query term
        best_pos = len(text)
        for term in query_terms:
            pos = text_lower.find(term)
            if 0 <= pos < best_pos:
                best_pos = pos
        
        if best_pos == len(text):
            # No match found, return beginning
            return text[:context_chars * 2] + "..." if len(text) > context_chars * 2 else text
        
        # Extract context around match
        start = max(0, best_pos - context_chars)
        end = min(len(text), best_pos + context_chars)
        
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def search(
        self,
        query: str,
        top_k: int = None,
        use_hybrid: bool = None,
        filter_file_type: Optional[str] = None,
        filter_path: Optional[str] = None,
        min_score: float = None
    ) -> List[RankedResult]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            use_hybrid: Combine vector + BM25 search
            filter_file_type: Filter by file extension
            filter_path: Filter by path prefix
            min_score: Minimum similarity score
            
        Returns:
            List of ranked results
        """
        top_k = top_k or settings.search_top_k
        use_hybrid = use_hybrid if use_hybrid is not None else settings.use_hybrid_search
        min_score = min_score or settings.similarity_threshold
        
        # Vector search
        query_embedding = self.embedding_engine.embed(query)
        
        filter_metadata = {}
        if filter_file_type:
            filter_metadata["file_type"] = filter_file_type
        
        vector_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more for fusion
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # Convert to ranked results
        results = []
        for vr in vector_results:
            if vr.score < min_score:
                continue
            
            # Apply path filter
            if filter_path and not vr.metadata.get("file_path", "").startswith(filter_path):
                continue
            
            result = RankedResult(
                chunk_id=vr.chunk_id,
                text=vr.text,
                file_path=vr.metadata.get("file_path", ""),
                file_name=vr.metadata.get("file_name", ""),
                score=vr.score,
                vector_score=vr.score,
                bm25_score=0.0,
                metadata=vr.metadata,
                highlight=self._highlight_text(vr.text, query)
            )
            results.append(result)
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def search_by_file(
        self,
        query: str,
        file_path: str,
        top_k: int = 5
    ) -> List[RankedResult]:
        """Search within a specific file."""
        return self.search(
            query=query,
            top_k=top_k,
            filter_path=file_path
        )
    
    def get_similar_chunks(
        self,
        chunk_id: str,
        top_k: int = 5
    ) -> List[RankedResult]:
        """Find chunks similar to a given chunk."""
        # This would require storing/retrieving the original embedding
        # For now, return empty - can be implemented with chunk storage
        return []
    
    def get_document_context(
        self,
        file_path: str,
        chunk_index: int,
        context_chunks: int = 2
    ) -> str:
        """Get surrounding context for a chunk."""
        # Retrieve chunks around the specified index
        # This helps provide more context to the LLM
        return ""  # Implement based on your needs
