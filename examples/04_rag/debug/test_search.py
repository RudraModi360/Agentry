"""Quick semantic search test on embedded chunks."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from rag_system.kb_manager import RAGKnowledgeBase
from rag_system.logging_setup import setup_rag_logging
setup_rag_logging(level="WARNING")

KB_INDEX_PATH = os.path.join(os.path.dirname(__file__), "rag_index")

def search(query, top_k=3):
    kb = RAGKnowledgeBase(index_dir=KB_INDEX_PATH)
    results = kb.retrieve_text(query, k=top_k)
    
    print(f"\nQuery: {query}")
    print(f"{'='*60}")
    for chunk, score in results:
        print(f"  [{score:.3f}] {chunk.section_path} (chunk {chunk.chunk_index}, page {chunk.page_number})")
        print(f"    {chunk.text[:120].replace(chr(10), ' ')}...")
    return results

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What is autotrophic nutrition?"
    search(q)
