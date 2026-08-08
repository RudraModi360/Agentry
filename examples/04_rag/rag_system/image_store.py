"""
LanceDB-based Image Vector Store for multimodal RAG.

Stores image embeddings (from GeminiEmbedder) with metadata in LanceDB.
Images and text share the same vector space, so text queries can search images.
"""

from __future__ import annotations

import hashlib
import json
from .logging_setup import get_logger
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

log = get_logger("image_store")


@dataclass
class ImageRecord:
    """A stored image with its embedding and metadata."""

    image_path: str
    description: str = ""
    page_number: int = 0
    section_path: str = ""
    source_file: str = ""
    image_id: str = ""

    def __post_init__(self):
        if not self.image_id:
            self.image_id = hashlib.blake2b(
                self.image_path.encode("utf-8"), digest_size=12
            ).hexdigest()


class LanceImageStore:
    """LanceDB-backed store for image embeddings."""

    def __init__(
        self,
        embedding_fn=None,
        db_dir: str = "rag_index",
        table_name: str = "images",
    ):
        self.embedding_fn = embedding_fn
        self.db_dir = db_dir
        self.table_name = table_name
        self._db = None
        self._table = None
        self._indexed_ids: set = set()

        os.makedirs(db_dir, exist_ok=True)

    def _ensure_db(self):
        if self._db is not None:
            return
        log.debug("Connecting to LanceDB at %s", self.db_dir)
        import lancedb
        self._db = lancedb.connect(self.db_dir)

    def _ensure_table(self):
        self._ensure_db()
        if self._table is not None:
            return
        try:
            self._table = self._db.open_table(self.table_name)
            log.debug("Opened LanceDB table '%s'", self.table_name)
        except Exception:
            self._table = None

    def add_images(
        self,
        image_paths: List[str],
        descriptions: Optional[List[str]] = None,
        image_embeddings: Optional[np.ndarray] = None,
        page_numbers: Optional[List[int]] = None,
        section_paths: Optional[List[str]] = None,
        source_files: Optional[List[str]] = None,
    ) -> int:
        """
        Add images to the store. Deduplicates by image_id.
        """
        if not image_paths:
            return 0

        self._ensure_db()

        n = len(image_paths)
        if descriptions is None:
            descriptions = [""] * n
        if page_numbers is None:
            page_numbers = [0] * n
        if section_paths is None:
            section_paths = [""] * n
        if source_files is None:
            source_files = [""] * n

        # Compute image IDs and deduplicate
        print(f"    Processing {n} images for LanceDB ...", flush=True)
        t0 = time.time()
        new_records = []
        skipped = 0
        emb_idx = 0
        for i in range(n):
            img_id = hashlib.blake2b(
                image_paths[i].encode(), digest_size=12
            ).hexdigest()
            if img_id in self._indexed_ids:
                skipped += 1
                continue
            self._indexed_ids.add(img_id)

            # Build embedding — match by order if counts align, else skip
            vec = None
            if image_embeddings is not None and emb_idx < len(image_embeddings):
                vec = image_embeddings[emb_idx].tolist()
                emb_idx += 1

            if vec is None:
                skipped += 1
                continue

            new_records.append({
                "image_id": img_id,
                "image_path": image_paths[i],
                "description": descriptions[i],
                "page_number": page_numbers[i],
                "section_path": section_paths[i],
                "source_file": source_files[i],
                "vector": vec,
            })

            if (i + 1) % 5 == 0 or i == n - 1:
                print(f"    Image processing: {i+1}/{n} ({(i+1)/n*100:.0f}%) | {len(new_records)} new, {skipped} skipped", flush=True)

        if not new_records:
            print(f"    All {n} images already indexed. Skipping.")
            return 0

        # Append to existing table (never overwrite)
        print(f"    Writing {len(new_records)} new images to LanceDB ...", flush=True)
        try:
            self._ensure_table()
            if self._table is not None:
                self._table.add(new_records)
            else:
                import lancedb
                self._table = self._db.create_table(
                    self.table_name, new_records, mode="overwrite"
                )
        except Exception as e:
            print(f"    ERROR: LanceDB write failed: {e}")
            return 0

        elapsed = time.time() - t0
        print(f"    LanceDB updated: +{len(new_records)} images, skipped {skipped} | total: {self.count()} | {elapsed:.1f}s")
        return len(new_records)

    def add_image_record(
        self,
        record: ImageRecord,
        image_embedding: np.ndarray,
    ) -> bool:
        """Add a single ImageRecord with its embedding. Returns True if added."""
        if record.image_id in self._indexed_ids:
            log.debug("Image %s already indexed, skipping.", record.image_id[:8])
            return False
        self._indexed_ids.add(record.image_id)

        self._ensure_db()

        doc = {
            "image_id": record.image_id,
            "image_path": record.image_path,
            "description": record.description,
            "page_number": record.page_number,
            "section_path": record.section_path,
            "source_file": record.source_file,
            "vector": image_embedding.tolist(),
        }

        try:
            self._ensure_table()
            if self._table is not None:
                self._table.add([doc])
                return True
        except Exception:
            self._table = self._db.create_table(
                self.table_name, [doc], mode="overwrite"
            )
            return True
        return False

    def query(
        self,
        query_text: str,
        k: int = 3,
    ) -> List[Tuple[ImageRecord, float]]:
        """
        Search images by text query.
        """
        self._ensure_table()

        if self._table is None:
            log.debug("LanceDB query on empty table.")
            return []

        if self.embedding_fn is None:
            log.warning("No embedding function available for image search.")
            return []

        log.info("LanceDB image query: '%s' (k=%d) ...", query_text[:60], k)
        t0 = time.time()

        q_emb = self.embedding_fn(query_text)
        if q_emb is None:
            return []

        try:
            results = (
                self._table.search(q_emb.tolist())
                .metric("cosine")
                .limit(k)
                .to_list()
            )
        except Exception as e:
            log.error("LanceDB query failed: %s", e)
            return []

        records = []
        for row in results:
            record = ImageRecord(
                image_path=row.get("image_path", ""),
                description=row.get("description", ""),
                page_number=row.get("page_number", 0),
                section_path=row.get("section_path", ""),
                source_file=row.get("source_file", ""),
                image_id=row.get("image_id", ""),
            )
            score = row.get("_distance", 0.0)
            similarity = 1.0 - score if score <= 1.0 else 1.0 / (1.0 + score)
            records.append((record, similarity))

        elapsed = (time.time() - t0) * 1000
        log.info(
            "LanceDB image query complete: %d results (top=%.3f) in %.0fms",
            len(records), records[0][1] if records else 0, elapsed,
        )
        return records

    def clear(self):
        """Drop the image table and reset state."""
        self._ensure_db()
        try:
            self._db.drop_table(self.table_name)
        except Exception:
            pass
        self._table = None
        self._indexed_ids = set()
        log.info("LanceDB image table cleared.")

    def count(self) -> int:
        """Return number of stored images."""
        self._ensure_table()
        if self._table is None:
            return 0
        try:
            return self._table.count_rows()
        except Exception:
            return 0

    def _rebuild_indexed_ids(self):
        """Rebuild the dedup set from existing table data."""
        self._ensure_table()
        if self._table is None:
            return
        try:
            rows = self._table.to_pandas().to_dict("records")
            self._indexed_ids = {row.get("image_id", "") for row in rows}
            log.info("LanceDB dedup set rebuilt: %d existing images tracked", len(self._indexed_ids))
        except Exception:
            self._indexed_ids = set()

    def get_all(self) -> List[ImageRecord]:
        """Return all stored image records."""
        self._ensure_table()
        if self._table is None:
            return []

        try:
            rows = self._table.to_pandas().to_dict("records")
        except Exception:
            return []

        return [
            ImageRecord(
                image_path=row.get("image_path", ""),
                description=row.get("description", ""),
                page_number=row.get("page_number", 0),
                section_path=row.get("section_path", ""),
                source_file=row.get("source_file", ""),
                image_id=row.get("image_id", ""),
            )
            for row in rows
        ]
