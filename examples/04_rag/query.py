"""
RAG Query — Semantic search over ingested vector stores.

Usage:
  python query.py
  python query.py --db-path ./my_index
  python query.py --query "What is photosynthesis?" --top-k 3
"""

import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from rag_system.kb_manager import RAGKnowledgeBase
from rag_system.logging_setup import setup_rag_logging

setup_rag_logging(level="WARNING")

DEFAULT_DB_PATH = os.path.join(current_dir, "rag_index")


def query_loop(db_path: str, top_k: int = 5):
    """Interactive query loop against the vector store."""
    print("=" * 60)
    print("RAG QUERY")
    print("=" * 60)
    print(f"  DB path: {db_path}")
    print()

    if not os.path.exists(os.path.join(db_path, "text_index.faiss")):
        print("  ERROR: No vector DB found at this path.")
        print("  Run: python ingest.py --file <your.pdf> first.")
        return

    kb = RAGKnowledgeBase(index_dir=db_path)
    status = kb.status()
    print(f"  Text chunks: {status['text_chunks']}")
    print(f"  Images:      {status['image_count']}")
    print(f"  Multimodal:  {status['multimodal_enabled']}")
    print()
    print("  Type your query. Type 'quit' or Ctrl+C to exit.")
    print("-" * 60)

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye.")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("  Bye.")
            break

        # Text retrieval
        t0 = time.time()
        text_results = kb.retrieve_text(query, k=top_k)
        text_ms = (time.time() - t0) * 1000

        print(f"\n  TEXT RESULTS ({len(text_results)} chunks, {text_ms:.0f}ms):")
        print("  " + "-" * 56)
        for i, (chunk, score) in enumerate(text_results, 1):
            section = chunk.section_path if chunk.section_path else "N/A"
            page = chunk.page_number if chunk.page_number else "?"
            print(f"  [{i}] score={score:.3f} | section={section} | page={page}")
            preview = chunk.text[:200].replace("\n", " ")
            print(f"      {preview}...")
            if chunk.image_paths:
                print(f"      images: {len(chunk.image_paths)} attached")
        print()

        # Image retrieval (if available)
        if kb._has_multimodal and kb._image_store:
            t0 = time.time()
            image_results = kb.retrieve_images(query, k=3)
            img_ms = (time.time() - t0) * 1000

            if image_results:
                print(f"  IMAGE RESULTS ({len(image_results)} images, {img_ms:.0f}ms):")
                print("  " + "-" * 56)
                for i, (img, score) in enumerate(image_results, 1):
                    fname = os.path.basename(img.image_path)
                    print(f"  [{i}] score={score:.3f} | {fname}")
                    if img.description:
                        print(f"      {img.description}")
                print()


def single_query(db_path: str, query: str, top_k: int = 5):
    """Run a single query and print results."""
    kb = RAGKnowledgeBase(index_dir=db_path)

    t0 = time.time()
    results = kb.retrieve_text(query, k=top_k)
    ms = (time.time() - t0) * 1000

    print(f"\nQuery: {query}")
    print(f"Results ({len(results)}, {ms:.0f}ms):")
    print("-" * 60)
    for i, (chunk, score) in enumerate(results, 1):
        section = chunk.section_path if chunk.section_path else "N/A"
        page = chunk.page_number if chunk.page_number else "?"
        print(f"[{i}] score={score:.3f} | section={section} | page={page}")
        preview = chunk.text[:300].replace("\n", " ")
        print(f"    {preview}...")
        if chunk.image_paths:
            print(f"    images: {len(chunk.image_paths)} attached")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG Query — Semantic search over vector stores",
    )
    parser.add_argument(
        "--db-path", default=DEFAULT_DB_PATH,
        help=f"Vector DB path (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--query", "-q", default=None,
        help="Single query (if omitted, enters interactive mode)",
    )
    parser.add_argument(
        "--top-k", "-k", type=int, default=5,
        help="Number of results (default: 5)",
    )

    args = parser.parse_args()
    db_path = os.path.abspath(args.db_path)

    if args.query:
        single_query(db_path, args.query, args.top_k)
    else:
        query_loop(db_path, args.top_k)
