"""
MMR-based Reranker for RAG retrieval results.

Maximal Marginal Relevance (MMR) balances relevance to the query
with diversity among results to avoid near-duplicate chunks.
"""

from __future__ import annotations

from .logging_setup import get_logger
import time
from typing import List, Tuple

import numpy as np

from .chunker import ChunkRecord
from .image_store import ImageRecord

log = get_logger("reranker")


def mmr_rerank(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    candidates: list,
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> List[Tuple[any, float]]:
    """
    MMR-based reranking.

    MMR = lambda * sim(d, q) - (1 - lambda) * max sim(d, d')

    Args:
        query_embedding: Query vector (1D numpy array).
        candidate_embeddings: Candidate vectors (N x D numpy array).
        candidates: List of candidate objects (ChunkRecord or ImageRecord).
        top_k: Number of results to return.
        lambda_param: Trade-off between relevance (1.0) and diversity (0.0).

    Returns:
        List of (candidate, score) tuples sorted by MMR score.
    """
    if len(candidates) == 0:
        return []

    if len(candidates) <= top_k:
        similarities = _cosine_similarities(query_embedding, candidate_embeddings)
        return [(candidates[i], float(similarities[i])) for i in range(len(candidates))]

    t0 = time.time()
    query_emb = query_embedding.astype(np.float32)
    cand_embs = candidate_embeddings.astype(np.float32)

    # Compute query-candidate similarities
    q_sims = _cosine_similarities(query_emb, cand_embs)

    selected_indices = []
    remaining_indices = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_score = -np.inf
        best_idx = -1

        for idx in remaining_indices:
            relevance = q_sims[idx]

            # Max similarity to already selected items
            if selected_indices:
                selected_embs = cand_embs[selected_indices]
                cand_emb = cand_embs[idx]
                max_inter = np.max(_cosine_similarities(cand_emb, selected_embs))
            else:
                max_inter = 0.0

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_inter

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx == -1:
            break

        selected_indices.append(best_idx)
        remaining_indices.remove(best_idx)

    elapsed = (time.time() - t0) * 1000
    log.debug(
        "MMR rerank: %d candidates -> %d results (lambda=%.2f) in %.0fms",
        len(candidates), len(selected_indices), lambda_param, elapsed,
    )

    return [(candidates[i], float(q_sims[i])) for i in selected_indices]


def _cosine_similarities(
    query: np.ndarray,
    candidates: np.ndarray,
) -> np.ndarray:
    """
    Compute cosine similarities between a query vector and candidate vectors.
    """
    if candidates.ndim == 1:
        candidates = candidates.reshape(1, -1)

    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return np.zeros(len(candidates))

    cand_norms = np.linalg.norm(candidates, axis=1)
    cand_norms[cand_norms == 0] = 1.0

    dots = candidates @ query
    sims = dots / (cand_norms * query_norm)
    return sims


def deduplicate_chunks(
    chunks: List[ChunkRecord],
    scores: List[float],
    threshold: float = 0.95,
) -> List[Tuple[ChunkRecord, float]]:
    """
    Remove near-duplicate chunks based on text overlap.
    """
    if not chunks:
        return []

    kept: List[Tuple[ChunkRecord, float]] = []
    kept_texts: List[str] = []

    for chunk, score in sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True):
        chunk_words = set(chunk.text.lower().split())

        is_duplicate = False
        for kept_text in kept_texts:
            kept_words = set(kept_text.split())
            if not chunk_words or not kept_words:
                continue
            jaccard = len(chunk_words & kept_words) / len(chunk_words | kept_words)
            if jaccard > threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            kept.append((chunk, score))
            kept_texts.append(chunk.text)

    return kept
