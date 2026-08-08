"""
FAISS Vector Store with cosine similarity for text chunks.

Uses IndexFlatIP with L2-normalized vectors for cosine similarity.
Stores ChunkRecord metadata alongside embeddings.
Supports hybrid retrieval: vector score + keyword TF-IDF score fusion.
"""

from __future__ import annotations

import json
from .logging_setup import get_logger
import os
import time
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

from .chunker import ChunkRecord

log = get_logger("vector_store")


class FaissTextStore:
    """FAISS-based vector store for text chunks with cosine similarity."""

    def __init__(
        self,
        embedding_fn=None,
        index_dir: str = "rag_index",
        embedding_dim: int = 1024,
    ):
        self.embedding_fn = embedding_fn
        self.index_dir = index_dir
        self.embedding_dim = embedding_dim
        self.index: Optional[faiss.IndexFlatIP] = None
        self.chunks: List[ChunkRecord] = []
        self._indexed_ids: set = set()

        os.makedirs(index_dir, exist_ok=True)

    def _ensure_index(self):
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.embedding_dim)

    def add_chunks(self, chunks: List[ChunkRecord]) -> int:
        """
        Add chunks to the index. Returns number of chunks added.
        Deduplicates by chunk_id — same content is never indexed twice.
        """
        if not chunks:
            return 0

        self._ensure_index()

        # Deduplicate
        new_chunks = []
        for c in chunks:
            if c.chunk_id not in self._indexed_ids:
                new_chunks.append(c)
                self._indexed_ids.add(c.chunk_id)

        if not new_chunks:
            print(f"    All {len(chunks)} chunks already indexed. Skipping.")
            return 0

        print(f"    Embedding {len(new_chunks)} new chunks for FAISS ...", flush=True)
        t0 = time.time()

        texts = [c.text for c in new_chunks]
        embeddings = self._embed_texts(texts)

        if embeddings is None or len(embeddings) == 0:
            print(f"    WARNING: Embedding failed — no vectors produced.")
            return 0

        # L2-normalize for cosine similarity via inner product
        faiss.normalize_L2(embeddings)

        self.index.add(embeddings)
        self.chunks.extend(new_chunks)

        elapsed = time.time() - t0
        print(f"    FAISS updated: +{len(new_chunks)} chunks | total: {self.index.ntotal} vectors | {elapsed:.1f}s")

        self.save()
        return len(new_chunks)

    def query(
        self,
        query_text: str,
        k: int = 5,
        min_score: float = 0.0,
    ) -> List[Tuple[ChunkRecord, float]]:
        """
        Query the store with a text string.
        """
        self._ensure_index()

        if self.index.ntotal == 0:
            log.debug("Query on empty index, returning nothing.")
            return []

        log.info("FAISS query: '%s' (k=%d) ...", query_text[:60], k)
        t0 = time.time()

        q_emb = self.embedding_fn(query_text)
        if q_emb is None:
            return []

        q_emb = np.array([q_emb], dtype=np.float32)
        faiss.normalize_L2(q_emb)

        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(q_emb, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if score < min_score:
                continue
            if idx < len(self.chunks):
                results.append((self.chunks[idx], float(score)))

        elapsed = (time.time() - t0) * 1000
        log.info(
            "FAISS query complete: %d results (top score=%.3f) in %.0fms",
            len(results), results[0][1] if results else 0, elapsed,
        )
        return results

    def query_batch(
        self,
        query_texts: List[str],
        k: int = 5,
    ) -> List[List[Tuple[ChunkRecord, float]]]:
        """Batch query multiple texts."""
        return [self.query(q, k) for q in query_texts]

    def save(self):
        """Persist index and metadata to disk."""
        if self.index is None or self.index.ntotal == 0:
            return

        index_path = os.path.join(self.index_dir, "text_index.faiss")
        meta_path = os.path.join(self.index_dir, "text_metadata.json")

        t0 = time.time()
        faiss.write_index(self.index, index_path)

        metadata = []
        for chunk in self.chunks:
            metadata.append({
                "text": chunk.text,
                "chunk_id": chunk.chunk_id,
                "section_path": chunk.section_path,
                "page_number": chunk.page_number,
                "source_file": chunk.source_file,
                "chunk_index": chunk.chunk_index,
                "chunk_type": chunk.chunk_type,
                "image_paths": chunk.image_paths,
                "image_ids": chunk.image_ids,
            })

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        elapsed = (time.time() - t0) * 1000
        log.info("FAISS index saved to disk in %.0fms", elapsed)

    def load(self) -> bool:
        """Load persisted index and metadata. Returns True if successful."""
        index_path = os.path.join(self.index_dir, "text_index.faiss")
        meta_path = os.path.join(self.index_dir, "text_metadata.json")

        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            log.info("No existing FAISS index found at %s", self.index_dir)
            return False

        log.info("Loading FAISS index from %s ...", self.index_dir)
        t0 = time.time()

        try:
            self.index = faiss.read_index(index_path)

            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            self.chunks = [
                ChunkRecord(
                    text=item["text"],
                    chunk_id=item["chunk_id"],
                    section_path=item.get("section_path", ""),
                    page_number=item.get("page_number", 0),
                    source_file=item.get("source_file", ""),
                    chunk_index=item.get("chunk_index", 0),
                    chunk_type=item.get("chunk_type", "topic"),
                    image_paths=item.get("image_paths", []),
                    image_ids=item.get("image_ids", []),
                )
                for item in metadata
            ]

            self._indexed_ids = {c.chunk_id for c in self.chunks}

            elapsed = time.time() - t0
            log.info(
                "FAISS index loaded: %d vectors, %d chunks in %.1fs",
                self.index.ntotal, len(self.chunks), elapsed,
            )
            return True
        except Exception as e:
            log.error("FAISS index load failed: %s", e)
            return False

    def clear(self):
        """Clear the index and metadata."""
        self.index = None
        self.chunks = []
        self._indexed_ids = set()

        for fname in ["text_index.faiss", "text_metadata.json"]:
            fpath = os.path.join(self.index_dir, fname)
            if os.path.exists(fpath):
                os.remove(fpath)

        log.info("FAISS index cleared.")

    def _embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """Embed a list of texts using the embedding function."""
        if self.embedding_fn is None:
            return None

        try:
            t0 = time.time()
            embeddings = [self.embedding_fn(t) for t in texts]
            embeddings = [e for e in embeddings if e is not None and len(e) > 0]
            if not embeddings:
                return None
            elapsed = time.time() - t0
            log.debug("Embedded %d texts in %.2fs", len(embeddings), elapsed)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            log.error("Embedding failed: %s", e)
            return None

    def keyword_search(
        self,
        query: str,
        k: int = 5,
    ) -> List[Tuple[ChunkRecord, float]]:
        """
        Simple keyword-based search using TF-IDF-like scoring.
        """
        if not self.chunks:
            return []

        query_terms = set(query.lower().split())
        scores = []

        for chunk in self.chunks:
            chunk_terms = set(chunk.text.lower().split())
            overlap = query_terms & chunk_terms
            score = len(overlap) / max(len(query_terms | chunk_terms), 1)
            scores.append((chunk, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def hybrid_query(
        self,
        query_text: str,
        k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[Tuple[ChunkRecord, float]]:
        """
        Hybrid retrieval combining vector similarity and keyword search.
        """
        log.info("Hybrid query: '%s' (k=%d, vw=%.1f, kw=%.1f)", query_text[:60], k, vector_weight, keyword_weight)
        t0 = time.time()

        vector_results = self.query(query_text, k=k * 2)
        keyword_results = self.keyword_search(query_text, k=k * 2)

        # Normalize scores
        max_vs = max((s for _, s in vector_results), default=1.0)
        max_ks = max((s for _, s in keyword_results), default=1.0)

        combined: Dict[str, Tuple[ChunkRecord, float]] = {}

        for chunk, score in vector_results:
            key = chunk.chunk_id
            norm_score = score / max_vs if max_vs > 0 else 0
            combined[key] = (chunk, vector_weight * norm_score)

        for chunk, score in keyword_results:
            key = chunk.chunk_id
            norm_score = score / max_ks if max_ks > 0 else 0
            if key in combined:
                combined[key] = (
                    combined[key][0],
                    combined[key][1] + keyword_weight * norm_score,
                )
            else:
                combined[key] = (chunk, keyword_weight * norm_score)

        results = sorted(combined.values(), key=lambda x: x[1], reverse=True)
        final = results[:k]

        elapsed = (time.time() - t0) * 1000
        log.info(
            "Hybrid query complete: %d results (top=%.3f) in %.0fms",
            len(final), final[0][1] if final else 0, elapsed,
        )
        return final

    @property
    def size(self) -> int:
        return self.index.ntotal if self.index else 0
