#!/usr/bin/env python3
"""
Quick Start Example for Smart File Search Agent.

This example demonstrates:
1. Indexing documents from a directory
2. Performing semantic search
3. Asking natural language questions
4. Interactive chat mode

Usage:
    python quickstart.py

Make sure to set your API key:
    export OPENAI_API_KEY="your-key-here"
    or
    export ANTHROPIC_API_KEY="your-key-here"
"""

import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from file_search_agent import FileSearchAgent


def main():
    print("🔍 Smart File Search Agent - Quick Start\n")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  No API key found!")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
        print("\nFor local LLM (Ollama), you can use:")
        print("  agent = FileSearchAgent(llm_provider='ollama', llm_model='llama3.2')")
        return
    
    # Initialize the agent
    print("Initializing agent...")
    agent = FileSearchAgent()
    print("✅ Agent initialized\n")
    
    # Example 1: Index a directory
    print("=" * 50)
    print("Example 1: Indexing Documents")
    print("=" * 50)
    
    # Create sample documents
    sample_dir = Path("./sample_docs")
    sample_dir.mkdir(exist_ok=True)
    
    # Create sample files
    (sample_dir / "readme.md").write_text("""
# Project Documentation

This is a sample project for demonstrating the file search agent.

## Features
- Semantic search across documents
- Natural language Q&A
- Multi-format support
- Fast indexing

## Installation
Run `pip install -r requirements.txt`

## Usage
Import the FileSearchAgent and start searching!
    """)
    
    (sample_dir / "notes.txt").write_text("""
Meeting Notes - Q4 Planning

Date: 2024-01-15
Attendees: Alice, Bob, Charlie

Key Decisions:
1. Launch new product in March 2024
2. Budget allocation: $50,000 for marketing
3. Hire 3 new engineers by February

Action Items:
- Alice: Prepare marketing materials
- Bob: Set up interview pipeline
- Charlie: Finalize technical roadmap

Next meeting: January 22, 2024
    """)
    
    print(f"Created sample documents in: {sample_dir}")
    
    # Index the directory
    stats = agent.index(str(sample_dir))
    print(f"✅ Indexed {stats.get('indexed', 0)} documents\n")
    
    # Example 2: Search
    print("=" * 50)
    print("Example 2: Semantic Search")
    print("=" * 50)
    
    query = "budget and marketing"
    print(f"Query: '{query}'\n")
    
    results = agent.search(query, top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.file_name} (score: {result.score:.3f})")
        print(f"   {result.text[:100]}...")
        print()
    
    # Example 3: Ask a question
    print("=" * 50)
    print("Example 3: Natural Language Q&A")
    print("=" * 50)
    
    question = "What is the marketing budget and when is the product launch?"
    print(f"Question: {question}\n")
    
    response = agent.ask(question)
    print(f"Answer: {response.answer}")
    print(f"\nConfidence: {response.confidence:.2%}")
    print(f"Sources: {[s.file_name for s in response.sources]}")
    
    # Example 4: Interactive chat (commented out by default)
    print("\n" + "=" * 50)
    print("Example 4: Chat Mode (Interactive)")
    print("=" * 50)
    print("To start chat mode, run: python -m file_search_agent chat")
    
    # Cleanup sample docs
    import shutil
    shutil.rmtree(sample_dir, ignore_errors=True)
    print("\n✅ Cleanup complete")
    
    print("\n🎉 Quick start complete! Try the CLI:")
    print("  python -m file_search_agent index /your/docs")
    print("  python -m file_search_agent ask 'your question here'")
    print("  python -m file_search_agent chat")


if __name__ == "__main__":
    main()
