import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from rag_system.kb_manager import RAGKnowledgeBase

KB_INDEX_PATH = os.path.join(current_dir, "rag_index")
kb = RAGKnowledgeBase(index_dir=KB_INDEX_PATH)

status = kb.status()
print(f"\nKB: {status['text_chunks']} chunks | {status['image_count']} images | {status['indexed_files']} files\n")

if status["text_chunks"] == 0:
    print("KB is empty. Index something first.")
    sys.exit(1)

while True:
    try:
        query = input("Query (or 'q' to quit): ").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if not query or query.lower() == "q":
        break

    t0 = time.time()
    results = kb.retrieve_text(query, k=5)
    latency = (time.time() - t0) * 1000

    print(f"\n  {len(results)} results in {latency:.0f}ms\n")

    for i, (chunk, score) in enumerate(results, 1):
        section = f" | Section: {'.'.join(chunk.section_path)}" if chunk.section_path else ""
        page = f" | Page: {chunk.page_number}" if chunk.page_number else ""
        source = f" | Source: {os.path.basename(chunk.source_file)}" if chunk.source_file else ""
        print(f"  [{i}] Score: {score:.4f}{section}{page}{source}")
        preview = chunk.text[:300].replace("\n", " ")
        print(f"      {preview}{'...' if len(chunk.text) > 300 else ''}\n")

print("\nDone.")
