"""
RAG Agent — Multimodal variant (text + images).

Split architecture:
- Text retrieval:  Jina CLIP v2 (local CPU, 1024 dim, text↔text similarity)
- Image retrieval: Gemini Embedding 2 (API, 1536 dim, cross-modal text↔image)

Run:
    python examples/04_rag/debug/rag_agent_multimodal.py
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
from logicore.stream.events import StreamEvent, StreamEventType
from logicore.memory.manager import MemoryManager
from logicore.utils.colors import (
    BLUE, GRAY, RESET,
    colored, error, info, success, tool_call, tool_result,
)

try:
    from rag_system.kb_manager import RAGKnowledgeBase
except ImportError as e:
    print(f"{error('[Import Error]')} Could not import rag_system: {e}")
    sys.exit(1)

# Configuration — rag_index is in parent directory (04_rag/rag_index)
KB_INDEX_PATH = os.path.join(os.path.dirname(current_dir), "rag_index")

# Initialize with multimodal support (Jina text + Gemini images)
kb = RAGKnowledgeBase(
    index_dir=KB_INDEX_PATH,
    strategy="topic",
)


# ── RAG Tools ──────────────────────────────────────────────────────────────

@tool("Search the knowledge base for relevant text passages (Jina CLIP v2)")
def search_knowledge(query: str, k: int = 5) -> str:
    """Search for text passages relevant to the query using Jina CLIP v2 (local).
    Returns text chunks with their associated image paths for visual context."""
    results = kb.retrieve_text(query, k=k)

    if not results:
        return "No relevant text found in the knowledge base."

    formatted = []
    for i, (chunk, score) in enumerate(results, 1):
        section = f" [Section {chunk.section_path}]" if chunk.section_path else ""
        page = f" (p.{chunk.page_number})" if chunk.page_number else ""

        # Build result with text
        result_text = (
            f"--- Text Result {i} (score: {score:.3f}){section}{page} ---\n"
            f"{chunk.text}"
        )

        # Include associated image paths for visual context
        if chunk.image_paths:
            result_text += "\n\n[Associated Images:]"
            for img_path in chunk.image_paths:
                result_text += f"\n  ![{os.path.basename(img_path)}]({img_path})"

        formatted.append(result_text)

    return "\n\n".join(formatted)


@tool("Search for relevant images, diagrams, or figures in the knowledge base")
def search_images(query: str, k: int = 3) -> str:
    """Search for images relevant to the query using Gemini Embedding 2 (cross-modal)."""
    results = kb.retrieve_images(query, k=k)

    if not results:
        return "No relevant images found in the knowledge base."

    formatted = []
    for i, (img, score) in enumerate(results, 1):
        section = f" [Section {img.section_path}]" if img.section_path else ""
        page = f" (p.{img.page_number})" if img.page_number else ""
        formatted.append(
            f"--- Image {i} (score: {score:.3f}){section}{page} ---\n"
            f"Path: {img.image_path}\n"
            f"Description: {img.description}"
        )

    return "\n\n".join(formatted)


@tool("Index a new document into the knowledge base")
def index_document(file_path: str) -> str:
    """Add a new document (PDF, TXT, or MD) to the knowledge base, including images."""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return f"Error: File not found at {abs_path}"

    ok = kb.index_file(abs_path, include_images=True)
    if ok:
        status = kb.status()
        return (
            f"Successfully indexed: {os.path.basename(abs_path)}\n"
            f"Text chunks: {status['text_chunks']} | "
            f"Images: {status['image_count']} | "
            f"Total files: {status['indexed_files']}"
        )
    return f"Failed to index {os.path.basename(abs_path)}."


@tool("Get knowledge base status")
def kb_status() -> str:
    """Return current KB statistics."""
    status = kb.status()
    return (
        f"Knowledge Base Status:\n"
        f"  Text chunks: {status['text_chunks']}\n"
        f"  Images indexed: {status['image_count']}\n"
        f"  Files indexed: {status['indexed_files']}\n"
        f"  Multimodal: {'enabled' if status['multimodal_enabled'] else 'disabled'}"
    )


@tool("Clear the entire knowledge base")
def clear_knowledge_base() -> str:
    """Wipe all indexed data."""
    kb.clear_kb()
    return "Knowledge base cleared."


# ── Streaming Consumer ─────────────────────────────────────────────────────

async def consume_stream(agent: BasicAgent, message: str):
    async for ev in agent.stream(message):
        if ev.type == StreamEventType.TOKEN:
            print(ev.data.get("delta", ""), end="", flush=True)
        elif ev.type == StreamEventType.REASONING:
            print(f"{GRAY}{ev.data.get('delta', '')}{RESET}", end="", flush=True)
        elif ev.type == StreamEventType.TOOL_CALL_START:
            name = ev.data.get("name", "?")
            print(f"\n{tool_call(name)}", end="", flush=True)
        elif ev.type == StreamEventType.TOOL_CALL_END:
            status = "ok" if ev.data.get("success") else "FAIL"
            print(f" {tool_result(ev.data.get('success'), status)}", flush=True)
        elif ev.type == StreamEventType.ERROR:
            print(f"\n{error('[error]')} {ev.data.get('message')}", flush=True)


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
- Would diagrams help explain this?

### Step 2: Search the knowledge base (ALWAYS do this first)
- **ALWAYS call search_knowledge FIRST** — even if you think you know the answer
- Rewrite the question into multiple search queries to get comprehensive results:
  - Direct topic search: "digestion process mouth stomach"
  - Related concept search: "alimentary canal food breakdown"
  - Section-specific search if you can guess the chapter
- **ALWAYS call search_images** if the question involves:
  - Diagrams, processes, structures, anatomy, experiments
  - "Explain the..." type questions
  - Anything that would benefit from visual reference

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
- If a separate diagram was found via search_images, include that too
- Always cite the source (page number, section)
- If the KB doesn't have enough info, say so clearly

## TOOLS

- **search_knowledge**: Search text passages from NCERT textbook (USE THIS FIRST, ALWAYS)
  - Returns text chunks WITH associated image paths from the same section
  - These images are complementary visual context for the text
- **search_images**: Search diagrams, figures, illustrations from the textbook
  - Use for explicit diagram requests or when you need additional visual context
- **index_document**: Add a new document to the knowledge base
- **kb_status**: Check knowledge base statistics

## CRITICAL RULES

1. **NEVER answer without searching the KB first** — ALWAYS call search_knowledge before answering
2. **NEVER use general knowledge** as your primary answer source — only use KB content
3. **ALWAYS check for [Associated Images:]** in search results — embed them in your answer
4. **NEVER skip image search** for "explain", "describe", "diagram", "process" questions
5. **ALWAYS rewrite the query** into better search terms before calling tools
6. **ALWAYS search with multiple angles** — topic, related concepts, section names
7. **If KB returns nothing useful**, say: "This topic isn't covered in the indexed textbook content."

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

User asks: "Explain the digestion system"
→ search_knowledge("digestion system alimentary canal food breakdown")
→ search_knowledge("human digestive system mouth stomach intestine")
→ search_images("digestive system diagram alimentary canal")

User asks: "What is photosynthesis"
→ search_knowledge("photosynthesis process sunlight chlorophyll")
→ search_knowledge("photosynthesis equation light reaction")
→ search_images("photosynthesis diagram chloroplast")

User asks: "How does the heart pump blood"
→ search_knowledge("heart blood pumping cardiac cycle")
→ search_knowledge("circulation blood vessels arteries veins")
→ search_images("heart diagram blood flow")

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
    agent = BasicAgent(
        name="RAGMultimodalAgent",
        description="NCERT Textbook Study Assistant with text (Jina) + image (Gemini) retrieval",
        tools=[
            search_knowledge,
            search_images,
            index_document,
            kb_status,
            clear_knowledge_base,
        ],
        provider=provider,
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )

    memory = MemoryManager(llm_provider=provider, llm_model=model)
    await memory.start()

    print(f"Agent: {colored(agent.name, BLUE)}  |  NCERT Textbook Assistant (Multimodal)")
    print(f"  Text:  Jina CLIP v2 (local CPU)")
    print(f"  Image: Gemini Embedding 2 (API)")
    print("Type 'quit' to exit, 'status' to check KB\n")

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

            await consume_stream(agent, msg)
            print("\n")

            await memory.submit_for_extraction(
                messages + [{"role": "assistant", "content": "(streamed response)"}]
            )
    finally:
        await memory.stop()


def main():
    parser = argparse.ArgumentParser(description="Multimodal RAG Agent")
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gemma4:cloud")
    args = parser.parse_args()

    try:
        asyncio.run(run(args.provider, args.model))
    except Exception as e:
        print(f"Critical runtime error: {e}")


if __name__ == "__main__":
    main()
