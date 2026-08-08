"""
Chunk Store — save/load ChunkRecords to disk as JSON.

Enables two-phase ingestion:
  Phase A: chunk_only() → saves chunks.json
  Phase B: embed_only() → loads chunks.json, builds FAISS/LanceDB index
"""

from __future__ import annotations

import json
import os
import time
from typing import List

from .chunker import ChunkRecord
from .logging_setup import get_logger

log = get_logger("chunk_store")

CHUNKS_FILENAME = "chunks.json"


def save_chunks(chunks: List[ChunkRecord], index_dir: str) -> str:
    """Save chunks to JSON. Returns the file path written."""
    t0 = time.time()
    path = os.path.join(index_dir, CHUNKS_FILENAME)
    os.makedirs(index_dir, exist_ok=True)

    data = []
    for c in chunks:
        data.append({
            "text": c.text,
            "chunk_id": c.chunk_id,
            "section_path": c.section_path,
            "page_number": c.page_number,
            "source_file": c.source_file,
            "chunk_index": c.chunk_index,
            "chunk_type": c.chunk_type,
            "image_paths": c.image_paths,
            "image_ids": c.image_ids,
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    elapsed = time.time() - t0
    log.info("Saved %d chunks to %s (%.1f KB, %.2fs)",
             len(chunks), path, os.path.getsize(path) / 1024, elapsed)
    return path


def load_chunks(index_dir: str) -> List[ChunkRecord]:
    """Load chunks from JSON. Returns empty list if file missing."""
    path = os.path.join(index_dir, CHUNKS_FILENAME)
    if not os.path.exists(path):
        log.warning("No chunks file found at %s", path)
        return []

    t0 = time.time()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    for d in data:
        chunks.append(ChunkRecord(
            text=d["text"],
            chunk_id=d.get("chunk_id", ""),
            section_path=d.get("section_path", ""),
            page_number=d.get("page_number", 0),
            source_file=d.get("source_file", ""),
            chunk_index=d.get("chunk_index", 0),
            chunk_type=d.get("chunk_type", "topic"),
            image_paths=d.get("image_paths", []),
            image_ids=d.get("image_ids", []),
        ))

    elapsed = time.time() - t0
    log.info("Loaded %d chunks from %s (%.2fs)", len(chunks), path, elapsed)
    return chunks


def chunks_exist(index_dir: str) -> bool:
    """Check if chunks.json exists."""
    return os.path.exists(os.path.join(index_dir, CHUNKS_FILENAME))


def chunk_report(chunks: List[ChunkRecord]) -> str:
    """Generate a human-readable summary of chunk statistics."""
    if not chunks:
        return "No chunks to report."

    sizes = [len(c.text) for c in chunks]
    pages = sorted(set(c.page_number for c in chunks if c.page_number > 0))
    sections = sorted(set(c.section_path for c in chunks if c.section_path))
    types = {}
    for c in chunks:
        types[c.chunk_type] = types.get(c.chunk_type, 0) + 1
    with_images = sum(1 for c in chunks if c.image_paths)
    total_images = sum(len(c.image_paths) for c in chunks)

    lines = [
        "=" * 50,
        "CHUNK REPORT",
        "=" * 50,
        f"  Total chunks:    {len(chunks)}",
        f"  Avg chunk size:  {sum(sizes) // len(sizes)} chars",
        f"  Min/Max size:    {min(sizes)} / {max(sizes)} chars",
        f"  Total text:      {sum(sizes):,} chars",
        f"  Pages covered:   {len(pages)} ({pages[0]}-{pages[-1]})" if pages else "  Pages covered:   0",
        f"  Sections:        {len(sections)}",
        f"  With images:     {with_images} chunks ({total_images} total images)",
        "",
        "  Chunk types:",
    ]

    for t, count in sorted(types.items()):
        lines.append(f"    {t:>12s}: {count}")

    lines.append("")
    lines.append("  Section distribution:")

    # Count chunks per top-level section
    section_counts = {}
    for c in chunks:
        top = c.section_path.split(".")[0] if c.section_path else "unsectioned"
        section_counts[top] = section_counts.get(top, 0) + 1

    for sec in sorted(section_counts.keys()):
        count = section_counts[sec]
        bar = "#" * min(count, 40)
        lines.append(f"    {sec:>12s}: {count:>3d} {bar}")

    lines.append("=" * 50)
    return "\n".join(lines)
