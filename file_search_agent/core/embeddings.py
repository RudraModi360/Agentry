"""
Embedding Engine - Converts text to vectors for semantic search.
Supports multiple embedding providers: sentence-transformers, OpenAI, etc.
"""

import numpy as np
from typing import List, Optional, Literal
from abc import ABC, abstractmethod


class BaseEmbedding(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts at once."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass


class SentenceTransformerEmbedding(BaseEmbedding):
    """Local embeddings using sentence-transformers (free, fast, private)."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    @property
    def dimension(self) -> int:
        return self._dimension


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI embeddings (requires API key)."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model
        # text-embedding-3-small: 1536, text-embedding-3-large: 3072
        self._dimension = 1536 if "small" in model else 3072
    
    def embed_text(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(input=text, model=self.model)
        return np.array(response.data[0].embedding)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        response = self.client.embeddings.create(input=texts, model=self.model)
        return np.array([item.embedding for item in response.data])
    
    @property
    def dimension(self) -> int:
        return self._dimension


class EmbeddingEngine:
    """
    Unified embedding engine that supports multiple providers.
    
    Usage:
        engine = EmbeddingEngine(provider="sentence-transformers")
        vector = engine.embed("Hello world")
        vectors = engine.embed_batch(["Hello", "World"])
    """
    
    def __init__(
        self,
        provider: Literal["sentence-transformers", "openai"] = "sentence-transformers",
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider = provider
        
        if provider == "sentence-transformers":
            model = model_name or "all-MiniLM-L6-v2"
            self._engine = SentenceTransformerEmbedding(model)
        elif provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required for OpenAI embeddings")
            model = model_name or "text-embedding-3-small"
            self._engine = OpenAIEmbedding(api_key, model)
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
    
    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        return self._engine.embed_text(text)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts efficiently."""
        return self._engine.embed_batch(texts)
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self._engine.dimension
