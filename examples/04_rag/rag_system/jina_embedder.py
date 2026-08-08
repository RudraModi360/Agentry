"""
Jina CLIP v2 — Local multimodal embedding (text + images, unified space).

- 0.9B params, 1024-dim (Matryoshka: 64–1024), runs on CPU
- No API key needed, no rate limits
- Concurrent batch execution for fast ingestion
- Unified text ↔ image similarity in one vector space

Requires: pip install sentence-transformers einops timm pillow
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Union

import numpy as np

from .logging_setup import get_logger

log = get_logger("jina_embedder")

# Default model and dimensions
MODEL_NAME = "jinaai/jina-clip-v2"
DEFAULT_DIMENSION = 1024
TEXT_BATCH_SIZE = 128
IMAGE_BATCH_SIZE = 32

# Auto-detect CPU cores for parallel data loading
import multiprocessing
_NUM_CPU = multiprocessing.cpu_count()
NUM_WORKERS = max(2, _NUM_CPU - 1)  # leave 1 core for main thread


class JinaClipEmbedder:
    """
    Local multimodal embedder using Jina CLIP v2.

    Embeds text and images into the same 1024-dim vector space.
    Runs fully on CPU — no API keys, no rate limits.

    Singleton — one model instance shared across the system.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        dimension: int = DEFAULT_DIMENSION,
        device: str = "cpu",
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.model_name = model_name
        self.dimension = dimension
        self.device = device
        self._model = None
        self._load_failed = False

    def _ensure_model(self):
        if self._model is not None:
            return
        if self._load_failed:
            return

        print(f"  Loading Jina CLIP v2 (dim={self.dimension}, device={self.device}, workers={NUM_WORKERS}) ...", flush=True)
        t0 = time.time()
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                trust_remote_code=True,
                device=self.device,
            )
            elapsed = time.time() - t0
            print(f"  Jina CLIP v2 ready in {elapsed:.1f}s ({_NUM_CPU} CPU cores detected)")
        except ImportError:
            self._load_failed = True
            print("  ERROR: sentence-transformers not installed. Run: pip install sentence-transformers einops timm pillow")
        except Exception as e:
            self._load_failed = True
            print(f"  ERROR: Failed to load Jina CLIP v2: {e}")

    # ── Text embedding ──────────────────────────────────────────────────

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Embed a single text string."""
        self._ensure_model()
        if self._model is None:
            return None

        try:
            embs = self._model.encode(
                [text],
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return embs[0][:self.dimension].astype(np.float32)
        except Exception as e:
            log.error("Text embedding failed: %s", e)
            return None

    def embed_text_batch(
        self, texts: List[str], batch_size: int = TEXT_BATCH_SIZE
    ) -> Optional[np.ndarray]:
        """Embed a batch of texts with progress bar."""
        self._ensure_model()
        if self._model is None:
            return None

        total = len(texts)
        if total == 0:
            return np.array([], dtype=np.float32)

        print(f"  Embedding {total} texts via Jina CLIP v2 (batch_size={batch_size}) ...", flush=True)
        t0 = time.time()

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=True,
                convert_to_numpy=True,
            )
            elapsed = time.time() - t0
            print(f"  Text embedding done: {len(embeddings)} vectors in {elapsed:.1f}s ({total/elapsed:.0f} texts/s)")
            return embeddings[:, :self.dimension].astype(np.float32)
        except Exception as e:
            log.error("Batch text embedding failed: %s", e)
            return self._fallback_embed_texts(texts)

    def _fallback_embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """Fallback: encode in smaller batches to avoid tensor issues."""
        total = len(texts)
        print(f"  Fallback: embedding {total} texts in small batches ...", flush=True)
        t0 = time.time()

        all_embeddings = []
        small_batch = 8
        for i in range(0, total, small_batch):
            batch = texts[i:i + small_batch]
            try:
                embs = self._model.encode(
                    batch,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                all_embeddings.append(embs[:, :self.dimension].astype(np.float32))
            except Exception as e:
                log.error("Fallback batch %d failed: %s", i, e)
                # Try one by one as last resort
                for t in batch:
                    try:
                        emb = self._model.encode(
                            [t], normalize_embeddings=True,
                            show_progress_bar=False, convert_to_numpy=True,
                        )
                        all_embeddings.append(emb[:, :self.dimension].astype(np.float32))
                    except Exception:
                        pass

        elapsed = time.time() - t0
        if all_embeddings:
            result = np.concatenate(all_embeddings, axis=0)
            print(f"  Fallback done: {len(result)}/{total} vectors in {elapsed:.1f}s")
            return result
        print(f"  Fallback failed: 0/{total} vectors in {elapsed:.1f}s")
        return None

    # ── Image embedding ─────────────────────────────────────────────────

    def embed_image(self, image_path: str) -> Optional[np.ndarray]:
        """Embed a single image file."""
        self._ensure_model()
        if self._model is None:
            return None

        try:
            from PIL import Image
            img = Image.open(image_path).convert("RGB")
            emb = self._model.encode(
                img,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return emb[:self.dimension].astype(np.float32)
        except Exception as e:
            log.error("Image embedding failed for %s: %s", os.path.basename(image_path), e)
            return None

    def embed_image_batch(
        self, image_paths: List[str], batch_size: int = IMAGE_BATCH_SIZE
    ) -> Optional[np.ndarray]:
        """
        Embed images with concurrent loading + batched model inference.
        Images are loaded in parallel (I/O-bound), then encoded in batches
        by the model (CPU-bound). This maximizes throughput on CPU.
        """
        self._ensure_model()
        if self._model is None:
            return None

        total = len(image_paths)
        if total == 0:
            return np.array([], dtype=np.float32)

        print(f"  Embedding {total} images via Jina CLIP v2 (batch_size={batch_size}) ...", flush=True)
        t0 = time.time()

        # Phase 1: Load images concurrently (I/O-bound — threading helps)
        print(f"    Phase 1: Loading {total} images (concurrent) ...", flush=True)
        images = [None] * total
        valid_indices = []

        def _load_image(idx: int, path: str):
            from PIL import Image
            try:
                return idx, Image.open(path).convert("RGB")
            except Exception as e:
                log.warning("Failed to load image %s: %s", os.path.basename(path), e)
                return idx, None

        with ThreadPoolExecutor(max_workers=NUM_WORKERS * 2) as executor:
            futures = {executor.submit(_load_image, i, p): i for i, p in enumerate(image_paths)}
            for future in as_completed(futures):
                idx, img = future.result()
                images[idx] = img
                if img is not None:
                    valid_indices.append(idx)
                done = len(valid_indices)
                if done % 5 == 0 or done == total:
                    print(f"    Loaded {done}/{total} images", flush=True)

        load_time = time.time() - t0
        print(f"    Phase 1 done: {len(valid_indices)}/{total} images in {load_time:.1f}s")

        if not valid_indices:
            print(f"  ERROR: No images could be loaded")
            return None

        # Phase 2: Batch encode (CPU-bound)
        valid_images = [images[i] for i in valid_indices]
        print(f"    Phase 2: Encoding {len(valid_images)} images (batch_size={batch_size}) ...", flush=True)
        t1 = time.time()

        try:
            embeddings = self._model.encode(
                valid_images,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=True,
                convert_to_numpy=True,
            )
            encode_time = time.time() - t1
            total_time = time.time() - t0
            print(f"  Image embedding done: {len(embeddings)}/{total} vectors in {total_time:.1f}s (encode: {encode_time:.1f}s)")
            return embeddings[:, :self.dimension].astype(np.float32)
        except Exception as e:
            log.error("Batch image encoding failed: %s", e)
            return self._fallback_encode_images(valid_images, valid_indices, total)

    def _fallback_encode_images(
        self, images: list, valid_indices: List[int], total: int
    ) -> Optional[np.ndarray]:
        """Fallback: encode images in small batches."""
        print(f"    Fallback: encoding {len(images)} images in small batches ...", flush=True)
        t0 = time.time()

        all_embeddings = []
        small_batch = 4
        for i in range(0, len(images), small_batch):
            batch = images[i:i + small_batch]
            try:
                embs = self._model.encode(
                    batch,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                all_embeddings.append(embs[:, :self.dimension].astype(np.float32))
            except Exception as e:
                log.error("Fallback image batch %d failed: %s", i, e)
                for img in batch:
                    try:
                        emb = self._model.encode(
                            img, normalize_embeddings=True,
                            show_progress_bar=False, convert_to_numpy=True,
                        )
                        all_embeddings.append(emb[:self.dimension].astype(np.float32).reshape(1, -1))
                    except Exception:
                        pass

        elapsed = time.time() - t0
        if all_embeddings:
            result = np.concatenate(all_embeddings, axis=0)
            print(f"    Fallback done: {len(result)}/{total} vectors in {elapsed:.1f}s")
            return result
        print(f"    Fallback failed: 0/{total} vectors in {elapsed:.1f}s")
        return None

    # ── Utilities ───────────────────────────────────────────────────────

    @property
    def embedding_dim(self) -> int:
        return self.dimension

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
