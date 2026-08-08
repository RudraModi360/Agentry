"""
Enhanced Hybrid Chunker — 3-layer chunking strategy.

Layer 1: Structural splitting on section headers (numbered sections like 5.1, 5.2, ## headers)
Layer 2: Semantic splitting using embedding cosine similarity within sections
Layer 3: Character-based size constraint with overlap

Each chunk is a ChunkRecord with full metadata for retrieval.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np

from .logging_setup import get_logger

log = get_logger("chunker")


@dataclass
class ChunkRecord:
    """A single chunk with full metadata for retrieval and display."""

    text: str
    chunk_id: str = ""
    section_path: str = ""  # "5.1.2"
    page_number: int = 0
    source_file: str = ""
    chunk_index: int = 0
    chunk_type: str = "topic"  # "topic" | "activity" | "question" | "sidebar"
    image_paths: List[str] = field(default_factory=list)
    image_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = hashlib.blake2b(
                self.text.encode("utf-8"), digest_size=16
            ).hexdigest()


# Regex patterns for structural splitting
_NUMBERED_SECTION_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)*)\s+", re.MULTILINE
)
_MD_HEADER_RE = re.compile(
    r"^(#{1,6})\s+", re.MULTILINE
)
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u024F\d])"
)


class HybridChunker:
    """
    Three-layer hybrid chunker for text content.

    1. Structural: splits on section boundaries (numbered sections, markdown headers)
    2. Semantic: uses embedding similarity to find meaning-based breaks within sections
    3. Size: enforces max chunk_size with overlap, respecting sentence boundaries
    """

    def __init__(
        self,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
        batch_embed_fn: Optional[Callable[[List[str]], np.ndarray]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        semantic_threshold: float = 0.60,
        min_chunk_size: int = 100,
    ):
        self.embed_fn = embed_fn
        self.batch_embed_fn = batch_embed_fn
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.semantic_threshold = semantic_threshold
        self.min_chunk_size = min_chunk_size

    def chunk_blocks(
        self,
        blocks: list,  # List[ContentBlock] from parser
        source_file: str = "",
    ) -> List[ChunkRecord]:
        """
        Chunk a list of ContentBlocks into ChunkRecords.

        Section headers create hard boundaries. Text blocks are chunked
        using the 3-layer strategy.
        """
        t0 = time.time()
        chunks: List[ChunkRecord] = []
        current_section: List[str] = []
        current_page: int = 0
        pending_text: List[str] = []

        structural_splits = 0
        semantic_splits = 0
        total_blocks = len(blocks)

        has_embedder = self.embed_fn is not None or self.batch_embed_fn is not None
        mode = "structural+semantic" if has_embedder else "structural+size (no embedder)"
        log.info("Chunking in %s mode", mode)

        for block_idx, block in enumerate(blocks):
            if block.type == "section_header":
                # Flush pending text before new section
                if pending_text:
                    section_text = "\n\n".join(pending_text)
                    new_chunks = self._chunk_text(
                        section_text, current_section, current_page, source_file, len(chunks)
                    )
                    chunks.extend(new_chunks)
                    structural_splits += 1
                    pending_text = []

                current_section = block.section_path
                current_page = block.page_number

            elif block.type == "text":
                current_page = block.page_number
                pending_text.append(block.content)

            # Progress logging every 50 blocks
            if (block_idx + 1) % 50 == 0 or block_idx == total_blocks - 1:
                log.info(
                    "  Chunking progress: %d/%d blocks (%.0f%%) | %d chunks so far",
                    block_idx + 1, total_blocks, (block_idx + 1) / total_blocks * 100,
                    len(chunks),
                )

        # Flush remaining text
        if pending_text:
            section_text = "\n\n".join(pending_text)
            new_chunks = self._chunk_text(
                section_text, current_section, current_page, source_file, len(chunks)
            )
            chunks.extend(new_chunks)

        # Renumber chunk indices
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i

        elapsed = time.time() - t0

        # Store stats for external access
        self.last_stats = {
            "total_chunks": len(chunks),
            "total_blocks": total_blocks,
            "structural_splits": structural_splits,
            "semantic_splits": semantic_splits,
            "elapsed_s": round(elapsed, 2),
            "mode": mode,
            "has_embedder": has_embedder,
        }

        log.info(
            "Chunking complete: %d chunks from %d blocks in %.1fs (structural=%d, semantic=%d)",
            len(chunks), total_blocks, elapsed, structural_splits, semantic_splits,
        )
        return chunks

    def chunk_text(
        self,
        text: str,
        section_path: Optional[List[str]] = None,
        page_number: int = 0,
        source_file: str = "",
        start_index: int = 0,
    ) -> List[ChunkRecord]:
        """
        Chunk raw text into ChunkRecords using the 3-layer strategy.
        """
        return self._chunk_text(
            text, section_path or [], page_number, source_file, start_index
        )

    def _chunk_text(
        self,
        text: str,
        section_path: List[str],
        page_number: int,
        source_file: str,
        start_index: int,
    ) -> List[ChunkRecord]:
        """Apply 3-layer chunking to a text block."""
        if not text.strip():
            return []

        # Layer 1: Structural split
        structural_parts = self._structural_split(text)
        log.debug(
            "  Section [%s]: %d structural parts from %d chars",
            ".".join(section_path) or "?", len(structural_parts), len(text),
        )

        all_chunks: List[ChunkRecord] = []
        semantic_count = 0

        for part_text, part_section in structural_parts:
            if not part_text.strip():
                continue

            effective_section = part_section if part_section else section_path

            # Layer 2: Semantic split (if any embedder available)
            has_embedder = self.embed_fn is not None or self.batch_embed_fn is not None
            if has_embedder and len(part_text) > self.min_chunk_size:
                semantic_parts = self._semantic_split(part_text)
                semantic_count += len(semantic_parts) - 1 if len(semantic_parts) > 1 else 0
            else:
                semantic_parts = [part_text]

            # Layer 3: Size constraint
            for sem_text in semantic_parts:
                size_chunks = self._size_split(sem_text)
                for sc in size_chunks:
                    all_chunks.append(ChunkRecord(
                        text=sc,
                        section_path=".".join(effective_section) if effective_section else "",
                        page_number=page_number,
                        source_file=source_file,
                        chunk_index=start_index + len(all_chunks),
                    ))

        if semantic_count > 0:
            log.debug("  Section [%s]: %d semantic splits", ".".join(section_path) or "?", semantic_count)

        return all_chunks

    def _structural_split(self, text: str) -> List[tuple]:
        """
        Split text on section boundaries. Returns list of (text, section_path) tuples.
        """
        lines = text.split("\n")
        parts: List[tuple] = []
        current_text: List[str] = []
        current_section: List[str] = []

        for line in lines:
            stripped = line.strip()

            # Check for numbered section header
            m = _NUMBERED_SECTION_RE.match(stripped)
            if m:
                if current_text:
                    parts.append(("\n".join(current_text), current_section))
                    current_text = []
                current_section = m.group(1).split(".")
                current_text.append(stripped)
                continue

            # Check for markdown header
            mmd = _MD_HEADER_RE.match(stripped)
            if mmd:
                if current_text:
                    parts.append(("\n".join(current_text), current_section))
                    current_text = []
                header_text = stripped.lstrip("#").strip()
                current_text.append(stripped)
                continue

            current_text.append(stripped)

        if current_text:
            parts.append(("\n".join(current_text), current_section))

        return parts

    def _semantic_split(self, text: str) -> List[str]:
        """
        Split text at semantic boundaries using embedding cosine similarity.
        Adjacent sentences with low similarity are split.
        Uses batch embedding when available for speed.
        """
        sentences = _SENTENCE_SPLIT_RE.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 2:
            return [text]

        try:
            t0 = time.time()
            # Prefer batch embedding for speed
            if self.batch_embed_fn is not None:
                embeddings = self.batch_embed_fn(sentences)
            else:
                embeddings = np.array([self.embed_fn(s) for s in sentences], dtype=np.float32)
            elapsed = time.time() - t0
            log.info("    Semantic: embedded %d sentences in %.2fs (%.1f sent/s)",
                     len(sentences), elapsed, len(sentences) / elapsed if elapsed > 0 else 0)
        except Exception as e:
            log.warning("    Semantic embedding failed, skipping semantic split: %s", e)
            self.embed_fn = None  # Disable further attempts this session
            return [text]

        # Compute cosine similarity between adjacent sentences
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = embeddings / norms
        similarities = np.sum(normalized[:-1] * normalized[1:], axis=1)

        # Find split points
        groups: List[List[str]] = [[sentences[0]]]
        splits = 0
        for i in range(len(similarities)):
            if similarities[i] < self.semantic_threshold:
                groups.append([sentences[i + 1]])
                splits += 1
            else:
                groups[-1].append(sentences[i + 1])

        if splits > 0:
            log.info("    Semantic: %d splits at threshold %.2f", splits, self.semantic_threshold)

        result = [" ".join(g) for g in groups if g]
        return result

    def _size_split(self, text: str) -> List[str]:
        """
        Split text into chunks of max chunk_size with overlap.
        Respects sentence boundaries.
        """
        if len(text) <= self.chunk_size:
            return [text]

        sentences = _SENTENCE_SPLIT_RE.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for sentence in sentences:
            sent_len = len(sentence)

            if current_len + sent_len + 1 > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))

                # Keep overlap: take sentences from end that fit in overlap
                overlap_chunk: List[str] = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) + 1 > self.chunk_overlap:
                        break
                    overlap_chunk.insert(0, s)
                    overlap_len += len(s) + 1

                current_chunk = overlap_chunk
                current_len = overlap_len

            current_chunk.append(sentence)
            current_len += sent_len + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Filter tiny chunks
        chunks = [c for c in chunks if len(c) >= self.min_chunk_size]
        return chunks if chunks else [text[:self.chunk_size]]
