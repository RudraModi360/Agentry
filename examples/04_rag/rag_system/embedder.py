"""
Unified embedding layer — Cohere Embed v4 (primary) + Gemini (fallback).

Cohere Embed v4: multimodal (text + images), 1024 dims, $0.12/1M tokens.
Gemini Embedding 2: multimodal fallback, 1536 dims.

Requires: CO_API_KEY env var (Cohere) or GEMINI_API_KEY env var.
"""

from __future__ import annotations

import base64
import os
import time
from typing import List, Optional, Union

import numpy as np

from .logging_setup import get_logger

log = get_logger("embedder")

# Cohere embed-v4.0 default dimension (Matryoshka: 256/512/1024/1536)
DEFAULT_DIMENSION = 1024


def _image_to_base64_url(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "image/png")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


class CohereEmbedder:
    """
    Unified embedder using Cohere Embed v4.

    Handles both text and images in the same vector space.
    Singleton — one instance shared across the system.

    Free tier: 2K text inputs/min, 5 image inputs/min.
    Paid: $0.12/1M text tokens, $0.47/1M image tokens.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = "embed-v4.0",
        api_key: Optional[str] = None,
        dimension: int = DEFAULT_DIMENSION,
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.model_name = model_name
        self.dimension = dimension
        self._client = None
        self._api_key = (
            api_key or os.environ.get("CO_API_KEY") or os.environ.get("COHERE_API_KEY")
        )
        self._load_failed = False
        self._last_call_time = 0.0
        self._min_call_interval = 1.6  # 40 req/min = 1 req/1.5s

    def _ensure_client(self):
        if self._client is not None:
            return
        if self._load_failed:
            return

        if not self._api_key:
            self._load_failed = True
            print(
                "  ERROR: No CO_API_KEY found. Set CO_API_KEY env var or pass api_key= to CohereEmbedder."
            )
            return

        print(
            f"  Initializing Cohere Embed v4 client (dim={self.dimension}) ...",
            flush=True,
        )
        t0 = time.time()
        try:
            import cohere

            self._client = cohere.ClientV2(api_key=self._api_key)
            print(f"  Cohere client ready in {time.time() - t0:.1f}s")
        except ImportError:
            self._load_failed = True
            print("  ERROR: cohere not installed. Run: pip install cohere>=5.0")
        except Exception as e:
            self._load_failed = True
            print(f"  ERROR: Failed to initialize Cohere client: {e}")

    def _call_embed(
        self,
        texts: list = None,
        images: list = None,
        input_type: str = "search_document",
        retries: int = 5,
    ) -> list:
        kwargs = dict(
            model=self.model_name, input_type=input_type, embedding_types=["float"]
        )
        if texts is not None:
            kwargs["texts"] = texts
        if images is not None:
            kwargs["images"] = images

        # Enforce rate limit between calls
        now = time.time()
        elapsed = now - self._last_call_time
        if elapsed < self._min_call_interval:
            time.sleep(self._min_call_interval - elapsed)

        for attempt in range(retries):
            try:
                self._last_call_time = time.time()
                result = self._client.embed(**kwargs)
                return [np.array(e, dtype=np.float32) for e in result.embeddings.float_]
            except Exception as e:
                if "429" in str(e) and attempt < retries - 1:
                    wait = 60
                    print(
                        f"    Rate limited (429), retry {attempt+1}/{retries-1} in {wait}s ...",
                        flush=True,
                    )
                    time.sleep(wait)
                    continue
                raise

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        self._ensure_client()
        if self._client is None:
            return None
        try:
            embs = self._call_embed(texts=[text], input_type="search_document")
            return embs[0] if embs else None
        except Exception as e:
            print(f"  ERROR: Cohere text embedding failed: {e}")
            return None

    def embed_text_batch(
        self, texts: List[str], batch_size: int = 96
    ) -> Optional[np.ndarray]:
        self._ensure_client()
        if self._client is None:
            return None

        all_embeddings = []
        total = len(texts)
        print(
            f"  Embedding {total} texts via Cohere Embed v4 (batch_size={batch_size}) ...",
            flush=True,
        )
        t0 = time.time()

        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            try:
                batch_embs = self._call_embed(texts=batch, input_type="search_document")
                all_embeddings.extend(batch_embs)
            except Exception as e:
                print(f"  ERROR: Batch embedding failed at offset {i}: {e}")
                for text in batch:
                    emb = self.embed_text(text)
                    if emb is not None:
                        all_embeddings.append(emb)

            done = min(i + batch_size, total)
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            print(
                f"    {done}/{total} ({done/total*100:.0f}%) | {elapsed:.1f}s elapsed | ETA {eta:.1f}s",
                flush=True,
            )

        print(
            f"  Text embedding done: {len(all_embeddings)} vectors in {time.time() - t0:.1f}s"
        )
        return np.array(all_embeddings, dtype=np.float32) if all_embeddings else None

    def embed_image(self, image_path: str) -> Optional[np.ndarray]:
        self._ensure_client()
        if self._client is None:
            return None
        try:
            url = _image_to_base64_url(image_path)
            embs = self._call_embed(images=[url], input_type="image")
            return embs[0] if embs else None
        except Exception as e:
            print(
                f"  ERROR: Cohere image embedding failed for {os.path.basename(image_path)}: {e}"
            )
            return None

    def embed_image_batch(self, image_paths: List[str]) -> Optional[np.ndarray]:
        self._ensure_client()
        if self._client is None:
            return None

        total = len(image_paths)
        print(f"  Embedding {total} images via Cohere Embed v4 ...", flush=True)
        t0 = time.time()

        embeddings = []
        for i, path in enumerate(image_paths, 1):
            emb = self.embed_image(path)
            if emb is not None:
                embeddings.append(emb)

            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            eta = (total - i) / rate if rate > 0 else 0
            print(
                f"    {i}/{total} ({i/total*100:.0f}%) | {elapsed:.1f}s | ETA {eta:.1f}s | {os.path.basename(path)}",
                flush=True,
            )

        print(
            f"  Image embedding done: {len(embeddings)}/{total} vectors in {time.time() - t0:.1f}s"
        )
        return np.array(embeddings, dtype=np.float32) if embeddings else None

    @property
    def embedding_dim(self) -> int:
        return self.dimension


class GeminiEmbedder:
    """
    Fallback embedder using Google Gemini Embedding 2.

    Handles both text and images in the same vector space.
    Singleton — one instance shared across the system.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = "gemini-embedding-2-preview",
        api_key: Optional[str] = None,
        dimension: int = 1536,
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.model_name = model_name
        self.dimension = dimension
        self._client = None
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._load_failed = False
        self._last_call_time = 0.0
        self._min_call_interval = 16.0  # 4 req/min = 1 req/15s, use 16s for safety

    def _ensure_client(self):
        if self._client is not None:
            return
        if self._load_failed:
            return

        if not self._api_key:
            self._load_failed = True
            print(
                "  ERROR: No GEMINI_API_KEY found. Set GEMINI_API_KEY env var or pass api_key= to GeminiEmbedder."
            )
            return

        print(
            f"  Initializing Gemini Embedding 2 client (dim={self.dimension}) ...",
            flush=True,
        )
        t0 = time.time()
        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
            print(f"  Gemini Embedding 2 client ready in {time.time() - t0:.1f}s")
        except ImportError:
            self._load_failed = True
            print(
                "  ERROR: google-genai not installed. Run: pip install google-genai>=1.0"
            )
        except Exception as e:
            self._load_failed = True
            print(f"  ERROR: Failed to initialize Gemini client: {e}")

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Embed a single text string."""
        self._ensure_client()
        if self._client is None:
            return None

        try:
            from google.genai import types

            result = self._client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimension,
                ),
            )
            return np.array(result.embeddings[0].values, dtype=np.float32)
        except Exception as e:
            print(f"  ERROR: Gemini text embedding failed: {e}")
            return None

    def embed_text_batch(
        self, texts: List[str], batch_size: int = 100
    ) -> Optional[np.ndarray]:
        """
        Embed a batch of texts.

        Gemini Embedding 2 supports batch input (list of strings).
        """
        self._ensure_client()
        if self._client is None:
            return None

        from google.genai import types

        all_embeddings = []
        total = len(texts)
        print(
            f"  Embedding {total} texts via Gemini Embedding 2 (batch_size={batch_size}) ...",
            flush=True,
        )
        t0 = time.time()

        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            try:
                result = self._client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.dimension,
                    ),
                )
                batch_embs = [
                    np.array(emb.values, dtype=np.float32) for emb in result.embeddings
                ]
                all_embeddings.extend(batch_embs)
            except Exception as e:
                print(f"  ERROR: Batch embedding failed at offset {i}: {e}")
                # Fall back to individual embedding
                for text in batch:
                    emb = self.embed_text(text)
                    if emb is not None:
                        all_embeddings.append(emb)

            done = min(i + batch_size, total)
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            print(
                f"    {done}/{total} ({done/total*100:.0f}%) | {elapsed:.1f}s elapsed | ETA {eta:.1f}s",
                flush=True,
            )

        print(
            f"  Text embedding done: {len(all_embeddings)} vectors in {time.time() - t0:.1f}s"
        )
        return np.array(all_embeddings, dtype=np.float32) if all_embeddings else None

    def embed_image(self, image_path: str, retries: int = 3) -> Optional[np.ndarray]:
        """Embed a single image file with retry on rate limit."""
        self._ensure_client()
        if self._client is None:
            return None

        for attempt in range(retries):
            try:
                from google.genai import types

                # Read image bytes
                with open(image_path, "rb") as f:
                    image_bytes = f.read()

                # Determine MIME type
                ext = os.path.splitext(image_path)[1].lower()
                mime_map = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }
                mime_type = mime_map.get(ext, "image/png")

                result = self._client.models.embed_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type,
                        ),
                    ],
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.dimension,
                    ),
                )
                return np.array(result.embeddings[0].values, dtype=np.float32)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < retries - 1:
                        wait = 30 * (attempt + 1)  # 30s, 60s, 90s
                        print(
                            f"    Rate limited, retry {attempt+1}/{retries} in {wait}s ...",
                            flush=True,
                        )
                        time.sleep(wait)
                        continue
                print(
                    f"  ERROR: Gemini image embedding failed for {os.path.basename(image_path)}: {e}"
                )
                return None
        return None

    def embed_image_batch(self, image_paths: List[str]) -> Optional[np.ndarray]:
        """
        Embed images with rate limit handling.
        Gemini free tier: 4 req/min for images.
        Process 2 images per batch, wait 16s between batches.
        """
        self._ensure_client()
        if self._client is None:
            return None

        total = len(image_paths)
        if total == 0:
            return np.array([], dtype=np.float32)

        print(
            f"  Embedding {total} images via Gemini Embedding 2 (2/batch, rate-limited) ...",
            flush=True,
        )
        t0 = time.time()

        BATCH_SIZE = 2
        DELAY_BETWEEN_BATCHES = 16  # seconds (4 req/min = 1 req/15s)

        embeddings = []
        for i in range(0, total, BATCH_SIZE):
            batch = image_paths[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

            # Enforce rate limit between batches
            now = time.time()
            elapsed_since_last = now - self._last_call_time
            if self._last_call_time > 0 and elapsed_since_last < DELAY_BETWEEN_BATCHES:
                wait_time = DELAY_BETWEEN_BATCHES - elapsed_since_last
                print(f"    Rate limit: waiting {wait_time:.1f}s ...", flush=True)
                time.sleep(wait_time)

            # Embed batch (2 images at a time)
            batch_embs = []
            for path in batch:
                emb = self.embed_image(path)
                if emb is not None:
                    batch_embs.append(emb)
                self._last_call_time = time.time()

            embeddings.extend(batch_embs)

            done = min(i + BATCH_SIZE, total)
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            print(
                f"    {done}/{total} ({done/total*100:.0f}%) | "
                f"batch {batch_num}/{total_batches} | "
                f"{elapsed:.1f}s | ETA {eta:.1f}s",
                flush=True,
            )

        print(
            f"  Image embedding done: {len(embeddings)}/{total} vectors in {time.time() - t0:.1f}s"
        )
        return np.array(embeddings, dtype=np.float32) if embeddings else None

    def embed_image_with_text(self, text: str, image_path: str) -> Optional[np.ndarray]:
        """
        Embed interleaved text + image for cross-modal understanding.
        Both are mapped into the same unified space.
        """
        self._ensure_client()
        if self._client is None:
            return None

        try:
            from google.genai import types

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_map.get(ext, "image/png")

            result = self._client.models.embed_content(
                model=self.model_name,
                contents=[
                    text,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimension,
                ),
            )
            return np.array(result.embeddings[0].values, dtype=np.float32)
        except Exception as e:
            print(f"  ERROR: Gemini multimodal embedding failed: {e}")
            return None

    @property
    def embedding_dim(self) -> int:
        return self.dimension


# ── Backward-compatible aliases ────────────────────────────────────────────


class TextEmbedder:
    """Backward-compatible wrapper — delegates to GeminiEmbedder."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = "gemini-embedding-2-preview",
        device: str = "cuda",
        dim: int = DEFAULT_DIMENSION,
        **kwargs,
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._gemini = GeminiEmbedder(model_name=model_name, dimension=dim, **kwargs)

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        return self._gemini.embed_text(text)

    def embed_batch(
        self, texts: List[str], batch_size: int = 100
    ) -> Optional[np.ndarray]:
        return self._gemini.embed_text_batch(texts, batch_size=batch_size)

    @property
    def embedding_dim(self) -> int:
        return self._gemini.dimension


class VisionEmbedder:
    """Backward-compatible wrapper — delegates to GeminiEmbedder."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = "gemini-embedding-2-preview",
        device: str = "cuda",
        **kwargs,
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._gemini = GeminiEmbedder(model_name=model_name, **kwargs)

    def embed_image(self, image_path: str) -> Optional[np.ndarray]:
        return self._gemini.embed_image(image_path)

    def embed_batch(self, image_paths: List[str]) -> Optional[np.ndarray]:
        return self._gemini.embed_image_batch(image_paths)

    @property
    def embedding_dim(self) -> int:
        return self._gemini.dimension


class OllamaEmbeddingModel:
    """Fallback embedding model using Ollama for local/offline environments."""

    def __init__(
        self,
        model_name: str = "mxbai-embed-large:latest",
        base_url: str = "http://localhost:11434",
    ):
        import requests as _requests

        self.model_name = model_name
        self.base_url = base_url
        self._requests = _requests

    def embed_text(self, text: str) -> Optional[List[float]]:
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model_name, "prompt": text, "keep_alive": "30m"}
        try:
            response = self._requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception as e:
            print(f"  ERROR: Ollama embedding error: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> Optional[np.ndarray]:
        from concurrent.futures import ThreadPoolExecutor

        total = len(texts)
        print(f"  Embedding {total} texts via Ollama ...", flush=True)
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            embeddings = list(executor.map(self.embed_text, texts))
        print(
            f"  Ollama embedding done: {len(embeddings)} vectors in {time.time() - t0:.1f}s"
        )
        return np.array(embeddings, dtype=np.float32)
