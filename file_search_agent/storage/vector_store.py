"""
Vector Store - Manages vector embeddings for similarity search.
Supports FAISS (fast, local) and ChromaDB (feature-rich).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Result from a vector search."""
    chunk_id: str
    score: float
    text: str
    metadata: Dict[str, Any]


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def add(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add vectors with metadata to the store."""
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        pass
    
    @abstractmethod
    def save(self) -> None:
        """Persist the store to disk."""
        pass
    
    @abstractmethod
    def load(self) -> None:
        """Load the store from disk."""
        pass
    
    @property
    @abstractmethod
    def count(self) -> int:
        """Return number of vectors in store."""
        pass


class FAISSVectorStore(VectorStore):
    """FAISS-based vector store for fast similarity search."""
    
    def __init__(
        self,
        dimension: int,
        store_path: Path,
        index_type: str = "flat"  # flat, ivf, hnsw
    ):
        import faiss
        
        self.dimension = dimension
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Create index based on type
        if index_type == "flat":
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine after normalization)
        elif index_type == "ivf":
            quantizer = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        elif index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(dimension, 32)
        
        # Store texts and metadata separately (FAISS only stores vectors)
        self._texts: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._ids: List[str] = []
        
        # Try to load existing index
        if (self.store_path / "index.faiss").exists():
            self.load()
    
    def add(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add vectors to FAISS index."""
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # Normalize embeddings for cosine similarity
        embeddings = embeddings.astype(np.float32)
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        self._texts.extend(texts)
        self._metadatas.extend(metadatas)
        self._ids.extend(ids)
        
        return ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        import faiss
        
        # Normalize query
        query = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query)
        
        # Search (get more results if filtering)
        search_k = top_k * 3 if filter_metadata else top_k
        scores, indices = self.index.search(query, min(search_k, self.count))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            metadata = self._metadatas[idx]
            
            # Apply metadata filter
            if filter_metadata:
                match = all(
                    metadata.get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue
            
            results.append(SearchResult(
                chunk_id=self._ids[idx],
                score=float(score),
                text=self._texts[idx],
                metadata=metadata
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID (rebuilds index)."""
        # FAISS doesn't support deletion, so we rebuild
        indices_to_keep = [
            i for i, id_ in enumerate(self._ids)
            if id_ not in ids
        ]
        
        if len(indices_to_keep) == len(self._ids):
            return  # Nothing to delete
        
        # Get vectors to keep
        import faiss
        vectors = faiss.rev_swig_ptr(
            self.index.get_xb(), self.count * self.dimension
        ).reshape(self.count, self.dimension)
        
        kept_vectors = vectors[indices_to_keep]
        
        # Rebuild index
        self.index.reset()
        if len(kept_vectors) > 0:
            self.index.add(kept_vectors)
        
        # Update metadata
        self._texts = [self._texts[i] for i in indices_to_keep]
        self._metadatas = [self._metadatas[i] for i in indices_to_keep]
        self._ids = [self._ids[i] for i in indices_to_keep]
    
    def save(self) -> None:
        """Save index and metadata to disk."""
        import faiss
        import json
        
        faiss.write_index(self.index, str(self.store_path / "index.faiss"))
        
        with open(self.store_path / "metadata.json", "w") as f:
            json.dump({
                "texts": self._texts,
                "metadatas": self._metadatas,
                "ids": self._ids
            }, f)
    
    def load(self) -> None:
        """Load index and metadata from disk."""
        import faiss
        import json
        
        index_path = self.store_path / "index.faiss"
        meta_path = self.store_path / "metadata.json"
        
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
        
        if meta_path.exists():
            with open(meta_path) as f:
                data = json.load(f)
                self._texts = data.get("texts", [])
                self._metadatas = data.get("metadatas", [])
                self._ids = data.get("ids", [])
    
    @property
    def count(self) -> int:
        return self.index.ntotal


class ChromaVectorStore(VectorStore):
    """ChromaDB-based vector store with rich metadata filtering."""
    
    def __init__(self, store_path: Path, collection_name: str = "documents"):
        import chromadb
        from chromadb.config import Settings
        
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.store_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add vectors to ChromaDB."""
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # ChromaDB expects lists
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search with optional metadata filtering."""
        where_filter = None
        if filter_metadata:
            where_filter = {
                "$and": [
                    {k: {"$eq": v}}
                    for k, v in filter_metadata.items()
                ]
            }
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        search_results = []
        for i, id_ in enumerate(results["ids"][0]):
            search_results.append(SearchResult(
                chunk_id=id_,
                score=1 - results["distances"][0][i],  # Convert distance to similarity
                text=results["documents"][0][i],
                metadata=results["metadatas"][0][i]
            ))
        
        return search_results
    
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        self.collection.delete(ids=ids)
    
    def save(self) -> None:
        """ChromaDB auto-persists, but we can force it."""
        pass  # Auto-persisted
    
    def load(self) -> None:
        """ChromaDB auto-loads from persistent storage."""
        pass  # Auto-loaded
    
    @property
    def count(self) -> int:
        return self.collection.count()
