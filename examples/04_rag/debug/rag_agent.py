"""
RAG Agent — Text-only variant using Jina CLIP v2.

Demonstrates:
- Pure Python RAG with semantic chunking and FAISS retrieval
- Jina CLIP v2 for high-quality local text embeddings (no API key needed)
- Smart retrieval with MMR reranking
- Memory integration for cross-session learning
- Domain-agnostic: works with science papers, business docs, manuals, etc.

Run:
    python examples/04_rag/debug/rag_agent.py
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

# Ensure local imports work — rag_system is in parent directory (04_rag/)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from rag_system.logging_setup import setup_rag_logging

# Configure RAG logging
setup_rag_logging(level="INFO")

from logicore import BasicAgent, tool
from logicore.memory.manager import MemoryManager
from logicore.utils.colors import colored, error, info, success, tool_call, tool_result, BLUE

try:
    from rag_system.kb_manager import RAGKnowledgeBase
except ImportError as e:
    print(f"{error('[Import Error]')} Could not import rag_system: {e}")
    sys.exit(1)

# Configuration — rag_index is in parent directory (04_rag/rag_index)
KB_INDEX_PATH = os.path.join(os.path.dirname(current_dir), "rag_index")

# Initialize the Knowledge Base
kb = RAGKnowledgeBase(index_dir=KB_INDEX_PATH)


# ── RAG Tools ──────────────────────────────────────────────────────────────

@tool("Search the knowledge base for relevant text passages to answer the user's question")
def search_knowledge(query: str, k: int = 5) -> str:
    """
    Search the RAG knowledge base for text passages relevant to the query.
    Returns the top-k most relevant chunks with section, page info, and associated images.
    """
    results = kb.retrieve_text(query, k=k)

    if not results:
        return "No relevant information found in the knowledge base."

    formatted = []
    for i, (chunk, score) in enumerate(results, 1):
        section = f" [Section {chunk.section_path}]" if chunk.section_path else ""
        page = f" (p.{chunk.page_number})" if chunk.page_number else ""

        result_text = (
            f"--- Result {i} (score: {score:.3f}){section}{page} ---\n"
            f"{chunk.text}"
        )

        # Include associated image paths for visual context
        if chunk.image_paths:
            result_text += "\n\n[Associated Images:]"
            for img_path in chunk.image_paths:
                result_text += f"\n  ![{os.path.basename(img_path)}]({img_path})"

        formatted.append(result_text)

    return "\n\n".join(formatted)


@tool("Index a new document into the knowledge base")
def index_document(file_path: str) -> str:
    """
    Add a new document (PDF, TXT, or MD) to the RAG knowledge base.
    The document will be parsed, chunked, and embedded for future retrieval.
    """
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return f"Error: File not found at {abs_path}"

    success_flag = kb.index_file(abs_path)
    if success_flag:
        status = kb.status()
        return (
            f"Successfully indexed: {os.path.basename(abs_path)}\n"
            f"Total chunks in KB: {status['text_chunks']}\n"
            f"Total indexed files: {status['indexed_files']}"
        )
    return f"Failed to index {os.path.basename(abs_path)}. Check file format."


@tool("Get the current status of the knowledge base")
def kb_status() -> str:
    """Return information about the current state of the knowledge base."""
    status = kb.status()
    return (
        f"Knowledge Base Status:\n"
        f"  - Text chunks indexed: {status['text_chunks']}\n"
        f"  - Files indexed: {status['indexed_files']}\n"
        f"  - Multimodal enabled: {status['multimodal_enabled']}\n"
        f"  - Index directory: {status['index_dir']}"
    )


@tool("Clear the entire knowledge base")
def clear_knowledge_base() -> str:
    """Remove all indexed data from the knowledge base. This cannot be undone."""
    kb.clear_kb()
    return "Knowledge base has been cleared. All indexed data has been removed."


# ── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """# ROLE

You are a **NCERT Textbook Study Assistant** — a specialized RAG agent that answers questions using ONLY the indexed NCERT textbook content.

Your domain is strictly: **NCERT textbook question answering**. You are NOT a general-purpose chatbot.

## YOUR DOMAIN

- You answer questions from NCERT textbooks (Science, Biology, Chemistry, Physics, etc.)
- Every answer MUST be grounded in the retrieved knowledge base content
- If a question is outside NCERT textbook scope, respond:
  "I'm designed to answer questions from NCERT textbooks only. Please ask a question related to your textbook syllabus."

## HOW YOU WORK (ALGORITHM)

When a user asks a question, follow this EXACT process:

### Step 1: Analyze the question
- What topic/concept is being asked?
- What chapter/section might this come from?

### Step 2: Search the knowledge base (ALWAYS do this first)
- **ALWAYS call search_knowledge FIRST** — even if you think you know the answer
- Rewrite the question into multiple search queries to get comprehensive results:
  - Direct topic search
  - Related concept search
  - Section-specific search if you can guess the chapter

### Step 3: Synthesize from retrieved content
- Read ALL retrieved text chunks carefully
- Each text chunk may include **[Associated Images:]** — these are diagrams from the SAME section as the text
- Use these associated images to add visual context to your answer
- Combine information from multiple chunks into a coherent answer
- Reference specific page numbers and sections

### Step 4: Answer
- Structure your answer clearly with headings and bullet points
- Use simple language appropriate for students
- **ALWAYS reference associated images** when available — embed them in your answer using markdown:
  `![description](image_path)`
- Always cite the source (page number, section)
- If the KB doesn't have enough info, say so clearly

## TOOLS

- **search_knowledge**: Search text passages from NCERT textbook (USE THIS FIRST, ALWAYS)
  - Returns text chunks WITH associated image paths from the same section
  - These images are complementary visual context for the text
- **index_document**: Add a new document to the knowledge base
- **kb_status**: Check knowledge base statistics

## CRITICAL RULES

1. **NEVER answer without searching the KB first** — ALWAYS call search_knowledge before answering
2. **NEVER use general knowledge** as your primary answer source — only use KB content
3. **ALWAYS check for [Associated Images:]** in search results — embed them in your answer
4. **ALWAYS rewrite the query** into better search terms before calling tools
5. **ALWAYS search with multiple angles** — topic, related concepts, section names
6. **If KB returns nothing useful**, say: "This topic isn't covered in the indexed textbook content."

## HOW TO USE ASSOCIATED IMAGES

When search_knowledge returns results, each chunk may have `[Associated Images:]` like:
```
[Associated Images:]
  ![jesc105_p7_5_2_4_figure_conf95_abc123.png](C:/path/to/extracted_images/jesc105_p7_5_2_4_figure_conf95_abc123.png)
```

In your answer, reference these images inline:
```markdown
### Digestive System
The human digestive system consists of the alimentary canal...

![Human Alimentary Canal](C:/path/to/extracted_images/jesc105_p7_5_2_4_figure_conf95_abc123.png)
*Figure: Human Alimentary Canal (Page 7, Section 5.2.4)*
```

This helps students visualize the concept alongside the text explanation.

## QUERY REWRITING EXAMPLES

User asks: "What is photosynthesis"
→ search_knowledge("photosynthesis process sunlight chlorophyll")
→ search_knowledge("photosynthesis equation light reaction")

User asks: "Explain the digestion system"
→ search_knowledge("digestion system alimentary canal food breakdown")
→ search_knowledge("human digestive system mouth stomach intestine")

## RESPONSE STYLE

- Start with a brief direct answer
- Then provide detailed explanation from the KB
- **Embed associated images** using markdown `![description](path)`
- Use headings, bullet points, and structured format
- Reference page numbers: "(Page 45, Section 5.2)"
- End with: "Source: NCERT [Subject] Class [X]"
"""


# ── Main ───────────────────────────────────────────────────────────────────

async def run(provider: str, model: str):
    """Main conversation loop."""
    agent = BasicAgent(
        name="RAGAgent",
        description="NCERT Textbook Study Assistant with Jina CLIP v2 (local text retrieval)",
        tools=[search_knowledge, index_document, kb_status, clear_knowledge_base],
        provider=provider,
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )

    memory = MemoryManager(llm_provider=provider, llm_model=model)
    await memory.start()

    print(f"Agent: {colored(agent.name, BLUE)}  |  NCERT Textbook Assistant (Jina CLIP v2 — local)")
    print(f"Type 'quit' to exit, 'status' to check KB, 'index <path>' to add a document\n")

    try:
        while True:
            try:
                msg = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not msg or msg.lower() in ("quit", "exit"):
                break

            if msg.lower() == "status":
                print(f"\n{info(kb_status())}\n")
                continue

            if msg.lower().startswith("index "):
                file_path = msg[6:].strip()
                result = index_document(file_path)
                print(f"\n{result}\n")
                continue

            messages = [{"role": "user", "content": msg}]
            messages = await memory.inject_context(messages, user_input=msg)

            response = await agent.chat(msg)
            print(f"\n{colored('Agent:', BLUE)} {response}\n")

            await memory.submit_for_extraction(
                messages + [{"role": "assistant", "content": response}]
            )
    finally:
        await memory.stop()


def main():
    parser = argparse.ArgumentParser(description="Text RAG Agent with Jina CLIP v2")
    parser.add_argument("--provider", default="ollama", help="LLM provider")
    parser.add_argument("--model", default="gpt-oss:20b-cloud", help="LLM model name")
    args = parser.parse_args()

    try:
        asyncio.run(run(args.provider, args.model))
    except Exception as e:
        print(f"Critical runtime error: {e}")


if __name__ == "__main__":
    main()
