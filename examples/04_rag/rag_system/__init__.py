"""
rag_system — Multimodal RAG with local Jina CLIP v2 embeddings.

Components:
- jina_embedder: JinaClipEmbedder (local CPU, text+images unified, no API key)
- embedder: Cohere/Gemini/Ollama fallbacks (API-based)
- parser: PDF content extractor (text + images)
- chunker: Hybrid chunker (structural + semantic + size)
- md_chunker: Topic-aware markdown chunker (section-based, image-aware)
- vector_store: FAISS cosine store for text chunks
- image_store: LanceDB store for image embeddings
- kb_manager: Dual Knowledge Base facade
- reranker: MMR-based reranking
- logging_setup: Unified logging configuration

Embedding priority: Jina CLIP v2 → Cohere → Gemini → Ollama

Usage:
    from rag_system.kb_manager import RAGKnowledgeBase
    from rag_system.jina_embedder import JinaClipEmbedder
    from rag_system.chunker import ChunkRecord
    from rag_system.md_chunker import MarkdownTopicChunker
    from rag_system.image_store import ImageRecord
    from rag_system.logging_setup import setup_rag_logging
"""

import os as _os
_os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from .chunker import ChunkRecord, HybridChunker
from .image_store import ImageRecord, LanceImageStore
from .jina_embedder import JinaClipEmbedder
from .kb_manager import HybridResult, RAGKnowledgeBase
from .logging_setup import get_logger, setup_rag_logging
from .md_chunker import MarkdownTopicChunker
from .parser import ContentBlock, PDFParser
from .reranker import deduplicate_chunks, mmr_rerank
from .vector_store import FaissTextStore

__all__ = [
    "ChunkRecord",
    "HybridChunker",
    "ImageRecord",
    "LanceImageStore",
    "JinaClipEmbedder",
    "RAGKnowledgeBase",
    "HybridResult",
    "MarkdownTopicChunker",
    "ContentBlock",
    "PDFParser",
    "deduplicate_chunks",
    "mmr_rerank",
    "FaissTextStore",
    "setup_rag_logging",
    "get_logger",
]
