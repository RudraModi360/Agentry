"""
Dual Knowledge Base Manager — orchestrates text and multimodal RAG.

Coordinates:
- PDFParser: extracts structured content from PDFs
- HybridChunker: splits text into semantic chunks
- FaissTextStore: stores text chunk embeddings
- LanceImageStore: stores image embeddings
- Reranker: MMR-based reranking for diversity

Embedding stack (split architecture):
    Text:  Jina CLIP v2 — local CPU, no API key, text↔text similarity
    Image: Gemini Embedding 2 — API, cross-modal text↔image similarity

Query flow:
    Text query → Jina → FAISS search → text results
    Text query → Gemini → LanceDB search → image results
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .chunker import ChunkRecord, HybridChunker
from .chunk_store import save_chunks, load_chunks, chunks_exist, chunk_report
from .image_store import ImageRecord, LanceImageStore
from .md_chunker import MarkdownTopicChunker
from .parser import ContentBlock, PDFParser
from .reranker import deduplicate_chunks, mmr_rerank
from .vector_store import FaissTextStore

from .logging_setup import get_logger

log = get_logger("kb")


@dataclass
class HybridResult:
    """Result from hybrid (text + image) retrieval."""

    text_results: List[Tuple[ChunkRecord, float]] = field(default_factory=list)
    image_results: List[Tuple[ImageRecord, float]] = field(default_factory=list)
    query: str = ""
    text_latency_ms: float = 0.0
    image_latency_ms: float = 0.0


class RAGKnowledgeBase:
    """
    High-level RAG knowledge base supporting both text-only and multimodal retrieval.
    """

    def __init__(
        self,
        index_dir: str = "rag_index",
        text_embedder=None,
        vision_embedder=None,
        embedding_model_name: str = "mxbai-embed-large:latest",
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        semantic_threshold: float = 0.60,
        embedding_dim: int = 1024,  # Cohere embed-v4.0 default
        use_gpu: bool = True,
        strategy: str = "default",  # "default" | "topic"
    ):
        log.info("Initializing RAGKnowledgeBase (index_dir=%s, dim=%d)", index_dir, embedding_dim)
        t0 = time.time()

        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)

        self.manifest_path = os.path.join(index_dir, "index_manifest.json")
        self.manifest = self._load_manifest()
        log.info("Manifest loaded: %d previously indexed files", len(self.manifest))

        # ── Embedding setup (split architecture) ─────────────────────
        # Text:  Jina CLIP v2 (local CPU, text↔text works)
        # Image: Cohere Embed v4 (API, cross-modal works)
        self._text_embedder = text_embedder
        self._vision_embedder = vision_embedder
        self._has_multimodal = False

        if self._text_embedder is None:
            # Text embedder: Jina CLIP v2 (local, free)
            try:
                from .jina_embedder import JinaClipEmbedder
                jina = JinaClipEmbedder(dimension=embedding_dim)
                jina._ensure_model()
                if not jina._load_failed:
                    self._text_embedder = jina
                    log.info("Text embedder: Jina CLIP v2 (dim=%d) — local CPU", embedding_dim)
            except Exception:
                pass

            # Fallback text embedder: Cohere
            if self._text_embedder is None:
                try:
                    from .embedder import CohereEmbedder
                    cohere_text = CohereEmbedder(dimension=embedding_dim)
                    cohere_text._ensure_client()
                    if not cohere_text._load_failed:
                        self._text_embedder = cohere_text
                        log.info("Text embedder: Cohere Embed v4 (dim=%d) — fallback", embedding_dim)
                except Exception:
                    pass

            # Fallback text embedder: Ollama
            if self._text_embedder is None:
                from .embedder import OllamaEmbeddingModel
                ollama = OllamaEmbeddingModel(model_name=embedding_model_name)
                self._text_embedder = ollama
                log.info("Text embedder: Ollama fallback: %s", embedding_model_name)

        self._embed_fn = self._text_embedder.embed_text

        if self._vision_embedder is None:
            # Image embedder: Gemini Embedding 2 (API, cross-modal, 1536 dim)
            try:
                from .embedder import GeminiEmbedder
                gemini = GeminiEmbedder(dimension=1536)
                gemini._ensure_client()
                if not gemini._load_failed:
                    self._vision_embedder = gemini
                    self._has_multimodal = True
                    log.info("Image embedder: Gemini Embedding 2 (dim=1536) — cross-modal")
            except Exception:
                pass

            # Fallback image embedder: Cohere
            if self._vision_embedder is None:
                try:
                    from .embedder import CohereEmbedder
                    cohere_img = CohereEmbedder(dimension=embedding_dim)
                    cohere_img._ensure_client()
                    if not cohere_img._load_failed:
                        self._vision_embedder = cohere_img
                        self._has_multimodal = True
                        log.info("Image embedder: Cohere Embed v4 (dim=%d) — fallback", embedding_dim)
                except Exception:
                    pass
        else:
            self._has_multimodal = True

        # Setup parser
        images_dir = os.path.join(index_dir, "extracted_images")
        self._parser = PDFParser(output_dir=images_dir)

        # Setup chunker
        batch_embed_fn = None
        if self._text_embedder is not None and hasattr(self._text_embedder, "embed_text_batch"):
            batch_embed_fn = self._text_embedder.embed_text_batch

        self._chunker = HybridChunker(
            embed_fn=self._embed_fn,
            batch_embed_fn=batch_embed_fn,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            semantic_threshold=semantic_threshold,
        )

        # Setup topic-aware markdown chunker (strategy="topic")
        self._strategy = strategy
        self._md_chunker = None
        if strategy == "topic":
            self._md_chunker = MarkdownTopicChunker(
                images_dir=images_dir,
                max_chunk_size=6000,
                min_chunk_size=200,
            )

        # Setup text vector store
        self._text_store = FaissTextStore(
            embedding_fn=self._embed_fn,
            index_dir=index_dir,
            embedding_dim=embedding_dim,
        )
        loaded = self._text_store.load()
        if loaded:
            log.info("Existing text index loaded: %d chunks", self._text_store.size)

        # Setup image store (uses vision_embedder for queries)
        self._image_store = None
        if self._has_multimodal and self._vision_embedder is not None:
            self._image_store = LanceImageStore(
                embedding_fn=self._vision_embedder.embed_text,
                db_dir=index_dir,
                table_name="rag_images",
            )
            self._image_store._rebuild_indexed_ids()

        elapsed = time.time() - t0
        log.info("RAGKnowledgeBase initialized in %.1fs", elapsed)

    def index_file(self, file_path: str, include_images: bool = True, mode: str = "full", strategy: str = None) -> bool:
        """
        Index a file (PDF, TXT, MD) into the knowledge base.

        Modes:
            "chunk" — parse + chunk only, save to chunks.json. No embedding.
            "embed" — load chunks.json, embed into FAISS/LanceDB. No re-chunking.
            "full"  — chunk + embed in one pass (default).

        Strategies:
            "default" — HybridChunker (structural + semantic + size)
            "topic"   — MarkdownTopicChunker (section-based, image-aware)
        """
        if not os.path.exists(file_path):
            print(f"  ERROR: File not found: {file_path}")
            return False

        # Use instance strategy if not overridden
        effective_strategy = strategy or self._strategy

        # Check manifest (skip only for full mode)
        abs_path = os.path.abspath(file_path)
        if mode == "full":
            mtime = os.path.getmtime(file_path)
            if file_path in self.manifest and self.manifest[file_path] == mtime:
                print(f"  Already indexed (unchanged): {os.path.basename(file_path)} — skipping")
                return True

        ext = os.path.splitext(file_path)[1].lower()

        print(f"INDEXING: {os.path.basename(file_path)} (type={ext}, mode={mode}, strategy={effective_strategy})")
        t0 = time.time()
        try:
            # Topic strategy only works on markdown files
            if effective_strategy == "topic" and ext in (".md", ".markdown"):
                if mode == "chunk":
                    success = self._chunk_md_file(abs_path)
                elif mode == "embed":
                    success = self._embed_text_file(abs_path)
                else:
                    success = self._chunk_md_file(abs_path) and self._embed_text_file(abs_path)
            elif ext == ".pdf":
                if mode == "chunk":
                    success = self._chunk_pdf(abs_path)
                elif mode == "embed":
                    success = self._embed_pdf(abs_path, include_images)
                else:
                    success = self._index_pdf(abs_path, include_images)
            elif ext in (".txt", ".md", ".markdown"):
                if mode == "chunk":
                    success = self._chunk_text_file(abs_path)
                elif mode == "embed":
                    success = self._embed_text_file(abs_path)
                else:
                    success = self._index_text_file(abs_path)
            else:
                print(f"  ERROR: Unsupported file type: {ext}")
                return False

            elapsed = time.time() - t0
            if success:
                status = self.status()
                print(f"  DONE: {status['text_chunks']} chunks, {status['image_count']} images, {status['indexed_files']} files ({elapsed:.1f}s)")
            return success
        except Exception as e:
            log.error("Indexing failed for %s: %s", file_path, e)
            return False

    def _index_pdf(self, file_path: str, include_images: bool) -> bool:
        """Index a PDF file."""
        fname = os.path.basename(file_path)
        print(f"  [1/3] Parsing PDF: {fname} ...", flush=True)
        t0 = time.time()

        blocks = self._parser.parse(file_path)
        if not blocks:
            print(f"  ERROR: No content extracted from {fname}")
            return False

        elapsed_parse = time.time() - t0
        text_count = sum(1 for b in blocks if b.type == "text")
        header_count = sum(1 for b in blocks if b.type == "section_header")
        image_count = sum(1 for b in blocks if b.type == "image")
        print(f"  [1/3] Parsed: {len(blocks)} blocks ({text_count} text, {header_count} headers, {image_count} images) in {elapsed_parse:.1f}s")

        # Separate text and image blocks
        text_blocks = [b for b in blocks if b.type in ("text", "section_header")]
        image_blocks = [b for b in blocks if b.type == "image"]

        # Phase 2: Chunk and embed text
        print(f"  [2/3] Chunking and embedding text ...", flush=True)
        t1 = time.time()

        print(f"    Structural splitting: {len(text_blocks)} blocks ...", flush=True)
        chunks = self._chunker.chunk_blocks(text_blocks, source_file=file_path)
        elapsed_chunk = time.time() - t1
        print(f"    Structural splitting done: {len(chunks)} chunks in {elapsed_chunk:.1f}s", flush=True)

        if chunks:
            print(f"    Embedding {len(chunks)} chunks into FAISS index ...", flush=True)
            t_emb = time.time()
            self._text_store.add_chunks(chunks)
            elapsed_emb = time.time() - t_emb
            print(f"    FAISS embedding done in {elapsed_emb:.1f}s", flush=True)

        elapsed_embed = time.time() - t1
        print(f"  [2/3] Embedded: {len(chunks)} chunks in {elapsed_embed:.1f}s")

        # Phase 3: Index images
        if include_images and image_blocks and self._image_store and self._has_multimodal:
            print(f"  [3/3] Indexing {len(image_blocks)} images ...", flush=True)
            t2 = time.time()
            self._index_images(image_blocks, file_path)
            elapsed_img = time.time() - t2
            print(f"  [3/3] Images indexed in {elapsed_img:.1f}s")
        else:
            print(f"  [3/3] Skipped (no images or multimodal disabled)")

        # Update manifest
        self.manifest[file_path] = os.path.getmtime(file_path)
        self._save_manifest()

        total_elapsed = time.time() - t0
        log.info("Total indexing time: %.1fs", total_elapsed)
        return True

    def _index_text_file(self, file_path: str) -> bool:
        """Index a text/markdown file."""
        fname = os.path.basename(file_path)
        print(f"  Parsing text file: {fname} ...", flush=True)
        t0 = time.time()

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            print(f"  ERROR: Empty file: {fname}")
            return False

        print(f"  File size: {len(text)} chars")

        from .parser import ContentBlock as CB

        blocks = [CB(type="text", content=text, page_number=1, metadata={"source": file_path})]
        chunks = self._chunker.chunk_blocks(blocks, source_file=file_path)

        if chunks:
            self._text_store.add_chunks(chunks)

        self.manifest[file_path] = os.path.getmtime(file_path)
        self._save_manifest()

        elapsed = time.time() - t0
        print(f"  DONE: {len(chunks)} chunks in {elapsed:.1f}s")
        return True

    # ── Chunk-only mode ─────────────────────────────────────────────────

    def _chunk_pdf(self, file_path: str) -> bool:
        """Parse PDF and chunk text only. No embedding. Saves chunks.json."""
        fname = os.path.basename(file_path)
        print(f"  [1/2] Parsing PDF: {fname} ...", flush=True)
        t0 = time.time()

        blocks = self._parser.parse(file_path)
        if not blocks:
            print(f"  ERROR: No content extracted from {fname}")
            return False

        elapsed_parse = time.time() - t0
        text_count = sum(1 for b in blocks if b.type == "text")
        header_count = sum(1 for b in blocks if b.type == "section_header")
        image_count = sum(1 for b in blocks if b.type == "image")
        print(f"  [1/2] Parsed: {len(blocks)} blocks ({text_count} text, {header_count} headers, {image_count} images) in {elapsed_parse:.1f}s")

        text_blocks = [b for b in blocks if b.type in ("text", "section_header")]
        image_blocks = [b for b in blocks if b.type == "image"]

        # Chunk only (no embedding)
        print(f"  [2/2] Chunking text (no embedding) ...", flush=True)
        t1 = time.time()
        chunks = self._chunker.chunk_blocks(text_blocks, source_file=file_path)
        elapsed_chunk = time.time() - t1
        print(f"  [2/2] Chunked: {len(chunks)} chunks in {elapsed_chunk:.1f}s", flush=True)

        # Save chunks to disk
        save_chunks(chunks, self.index_dir)

        # Save image paths for later embedding
        if image_blocks:
            image_paths = [b.content for b in image_blocks]
            img_manifest_path = os.path.join(self.index_dir, "pending_images.json")
            import json as _json
            with open(img_manifest_path, "w", encoding="utf-8") as f:
                _json.dump({
                    "source_file": file_path,
                    "image_paths": image_paths,
                    "image_blocks": [
                        {
                            "content": b.content,
                            "page_number": b.page_number,
                            "section_path": b.section_path,
                            "metadata": b.metadata,
                        }
                        for b in image_blocks
                    ],
                }, f, indent=1)
            print(f"  Saved {len(image_blocks)} pending image paths for later embedding")

        # Print chunk report
        print()
        print(chunk_report(chunks))

        return True

    def _chunk_text_file(self, file_path: str) -> bool:
        """Parse text file and chunk only. No embedding. Saves chunks.json."""
        fname = os.path.basename(file_path)
        print(f"  Parsing text file: {fname} ...", flush=True)
        t0 = time.time()

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            print(f"  ERROR: Empty file: {fname}")
            return False

        from .parser import ContentBlock as CB
        blocks = [CB(type="text", content=text, page_number=1, metadata={"source": file_path})]
        chunks = self._chunker.chunk_blocks(blocks, source_file=file_path)

        save_chunks(chunks, self.index_dir)
        print()
        print(chunk_report(chunks))

        elapsed = time.time() - t0
        print(f"  Chunked: {len(chunks)} chunks in {elapsed:.1f}s")
        return True

    def _chunk_md_file(self, file_path: str) -> bool:
        """Chunk a markdown file using topic-aware strategy with image association."""
        fname = os.path.basename(file_path)
        print(f"  [Topic chunking] Parsing markdown: {fname} ...", flush=True)
        t0 = time.time()

        if self._md_chunker is None:
            # Fallback: create md_chunker on the fly
            images_dir = os.path.join(self.index_dir, "extracted_images")
            self._md_chunker = MarkdownTopicChunker(
                images_dir=images_dir,
                max_chunk_size=6000,
                min_chunk_size=200,
            )

        chunks = self._md_chunker.chunk_markdown(file_path, source_file=file_path)
        if not chunks:
            print(f"  ERROR: No chunks produced from {fname}")
            return False

        elapsed = time.time() - t0
        print(f"  [Topic chunking] Produced {len(chunks)} chunks in {elapsed:.1f}s", flush=True)

        save_chunks(chunks, self.index_dir)
        print()
        print(chunk_report(chunks))

        return True

    # ── Embed-only mode ─────────────────────────────────────────────────

    def _embed_pdf(self, file_path: str, include_images: bool) -> bool:
        """Load saved chunks and embed into FAISS/LanceDB. No re-chunking."""
        fname = os.path.basename(file_path)

        if not chunks_exist(self.index_dir):
            print(f"  ERROR: No chunks.json found. Run --chunk-first on this file first.")
            return False

        print(f"  Loading chunks from {self.index_dir} ...", flush=True)
        chunks = load_chunks(self.index_dir)
        if not chunks:
            print(f"  ERROR: No chunks loaded")
            return False
        print(f"  Loaded {len(chunks)} chunks")

        # Embed text chunks into FAISS
        print(f"  Embedding {len(chunks)} chunks into FAISS index ...", flush=True)
        t0 = time.time()
        self._text_store.add_chunks(chunks)
        elapsed = time.time() - t0
        print(f"  FAISS embedding done in {elapsed:.1f}s")

        # Embed pending images if available
        if include_images and self._has_multimodal:
            import json as _json
            img_manifest_path = os.path.join(self.index_dir, "pending_images.json")
            if os.path.exists(img_manifest_path):
                with open(img_manifest_path, "r", encoding="utf-8") as f:
                    img_data = _json.load(f)

                image_blocks = []
                for ib in img_data.get("image_blocks", []):
                    from .parser import ContentBlock as CB
                    image_blocks.append(CB(
                        type="image",
                        content=ib["content"],
                        page_number=ib.get("page_number", 0),
                        section_path=ib.get("section_path", []),
                        metadata=ib.get("metadata", {}),
                    ))

                if image_blocks:
                    print(f"  Embedding {len(image_blocks)} images ...", flush=True)
                    t1 = time.time()
                    self._index_images(image_blocks, img_data.get("source_file", file_path))
                    print(f"  Images embedded in {time.time() - t1:.1f}s")

                # Clean up pending manifest
                os.remove(img_manifest_path)

        # Update manifest
        self.manifest[file_path] = os.path.getmtime(file_path)
        self._save_manifest()

        return True

    def _embed_text_file(self, file_path: str) -> bool:
        """Load saved chunks and embed into FAISS. No re-chunking."""
        if not chunks_exist(self.index_dir):
            print(f"  ERROR: No chunks.json found. Run --chunk-first on this file first.")
            return False

        chunks = load_chunks(self.index_dir)
        if not chunks:
            print(f"  ERROR: No chunks loaded")
            return False

        print(f"  Embedding {len(chunks)} chunks into FAISS index ...", flush=True)
        t0 = time.time()
        self._text_store.add_chunks(chunks)
        elapsed = time.time() - t0
        print(f"  FAISS embedding done in {elapsed:.1f}s")

        self.manifest[file_path] = os.path.getmtime(file_path)
        self._save_manifest()

        return True

    def _index_images(self, image_blocks: List[ContentBlock], source_file: str):
        """Index extracted images into the LanceDB image store."""
        if not self._image_store or not self._has_multimodal:
            return

        image_paths = [b.content for b in image_blocks]
        descriptions = []
        for b in image_blocks:
            w = b.metadata.get("width", "?")
            h = b.metadata.get("height", "?")
            page = b.page_number
            section = ".".join(b.section_path) if b.section_path else "unsectioned"
            desc = f"Image from page {page}, section {section} ({w}x{h})"
            descriptions.append(desc)

        # Embed images using the vision embedder (Cohere)
        print(f"    Embedding {len(image_paths)} images ...", flush=True)
        t0 = time.time()
        try:
            if self._vision_embedder is not None and hasattr(self._vision_embedder, "embed_image_batch"):
                image_embeddings = self._vision_embedder.embed_image_batch(image_paths)
            elif self._vision_embedder is not None and hasattr(self._vision_embedder, "embed_batch"):
                image_embeddings = self._vision_embedder.embed_batch(image_paths)
            else:
                print(f"    ERROR: No vision embedder available for images")
                return
        except Exception as e:
            print(f"    ERROR: Image embedding failed: {e}")
            return
        print(f"    Image embeddings computed in {time.time() - t0:.1f}s")

        self._image_store.add_images(
            image_paths=image_paths,
            descriptions=descriptions,
            image_embeddings=image_embeddings,
            page_numbers=[b.page_number for b in image_blocks],
            section_paths=[".".join(b.section_path) for b in image_blocks],
            source_files=[source_file] * len(image_blocks),
        )

    def retrieve_text(
        self,
        query: str,
        k: int = 5,
        use_hybrid: bool = True,
        min_score: float = 0.0,
    ) -> List[Tuple[ChunkRecord, float]]:
        """
        Retrieve relevant text chunks for a query.
        """
        log.info("TEXT RETRIEVAL: '%s' (k=%d, hybrid=%s)", query[:60], k, use_hybrid)
        t0 = time.time()

        if use_hybrid:
            results = self._text_store.hybrid_query(query, k=k)
        else:
            results = self._text_store.query(query, k=k, min_score=min_score)

        # Apply MMR reranking for diversity
        if len(results) > k:
            chunks = [r[0] for r in results]
            scores = [r[1] for r in results]
            try:
                q_emb = self._embed_fn(query)
                chunk_embs = np.array([self._embed_fn(c.text) for c in chunks], dtype=np.float32)
                results = mmr_rerank(q_emb, chunk_embs, chunks, top_k=k)
                log.info("MMR reranking applied: %d -> %d results", len(scores), len(results))
            except Exception:
                results = results[:k]

        elapsed = (time.time() - t0) * 1000
        log.info(
            "Text retrieval complete: %d results (top=%.3f) in %.0fms",
            len(results), results[0][1] if results else 0, elapsed,
        )
        return results

    def retrieve_images(
        self,
        query: str,
        k: int = 3,
    ) -> List[Tuple[ImageRecord, float]]:
        """
        Retrieve relevant images for a query.
        """
        if not self._image_store or not self._has_multimodal:
            log.warning("Multimodal retrieval not available.")
            return []

        return self._image_store.query(query, k=k)

    def retrieve_hybrid(
        self,
        query: str,
        text_k: int = 5,
        image_k: int = 3,
    ) -> HybridResult:
        """
        Retrieve both text and images for a query.
        """
        log.info("HYBRID RETRIEVAL: '%s' (text_k=%d, image_k=%d)", query[:60], text_k, image_k)
        t0 = time.time()

        result = HybridResult(query=query)

        # Text retrieval
        t1 = time.time()
        result.text_results = self.retrieve_text(query, k=text_k)
        result.text_latency_ms = (time.time() - t1) * 1000

        # Image retrieval
        if self._has_multimodal:
            t2 = time.time()
            result.image_results = self.retrieve_images(query, k=image_k)
            result.image_latency_ms = (time.time() - t2) * 1000

        elapsed = (time.time() - t0) * 1000
        log.info(
            "Hybrid retrieval complete: %d text + %d images in %.0fms",
            len(result.text_results), len(result.image_results), elapsed,
        )
        return result

    def clear_kb(self):
        """Clear all indexed data."""
        log.info("Clearing knowledge base ...")
        self._text_store.clear()
        if self._image_store:
            self._image_store.clear()
        self.manifest = {}
        self._save_manifest()
        log.info("Knowledge base cleared.")

    def status(self) -> Dict[str, Any]:
        """Return knowledge base status."""
        return {
            "text_chunks": self._text_store.size,
            "indexed_files": len(self.manifest),
            "files": list(self.manifest.keys()),
            "multimodal_enabled": self._has_multimodal,
            "image_count": self._image_store.count() if self._image_store else 0,
            "index_dir": self.index_dir,
        }

    def _load_manifest(self) -> Dict[str, float]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_manifest(self):
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            log.error("Failed to save manifest: %s", e)
