# 🔍 Smart File Search Agent

An intelligent, LLM-powered file search agent that understands multiple file systems and provides precise answers quickly. Built with modern Python using RAG (Retrieval Augmented Generation) architecture.

## 🌟 Features

- **Multi-Format Support**: PDF, DOCX, XLSX, PPTX, TXT, CSV, JSON, Markdown, Code files (30+ formats)
- **Semantic Search**: Vector-based similarity search using FAISS/ChromaDB
- **Hybrid Search**: Combines vector similarity with BM25 keyword search for better precision
- **LLM-Powered Understanding**: Uses OpenAI/Claude/Ollama for intelligent Q&A
- **Cross-Platform**: Works on Windows, macOS, Linux
- **Incremental Indexing**: Smart change detection - only re-indexes modified files
- **Natural Language Queries**: Ask questions in plain English
- **Multi-modal**: OCR support for images and scanned documents
- **REST API**: FastAPI server for integration with other applications
- **CLI**: Beautiful command-line interface with Rich

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Smart File Search Agent                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Indexer    │  │   Searcher   │  │  LLM Engine  │          │
│  │  (Crawl &    │──│  (Vector DB  │──│  (Answer     │          │
│  │   Parse)     │  │   + BM25)    │  │   Generator) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                │                  │                   │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Document Processors                      │      │
│  │  PDF | DOCX | XLSX | TXT | CSV | JSON | Code | IMG   │      │
│  └──────────────────────────────────────────────────────┘      │
│         │                                                       │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Vector Store (FAISS/ChromaDB)            │      │
│  │         + Metadata Store (SQLite/PostgreSQL)          │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Embeddings | `sentence-transformers` / `OpenAI Ada` | Text vectorization |
| Vector DB | `FAISS` / `ChromaDB` | Similarity search |
| LLM | `OpenAI` / `Anthropic` / `Ollama` | Answer generation |
| Document Parsing | `PyMuPDF`, `python-docx`, `openpyxl` | File reading |
| OCR | `pytesseract` / `easyocr` | Image text extraction |
| File Watching | `watchdog` | Real-time indexing |
| API | `FastAPI` | REST interface |
| CLI | `typer` / `click` | Command-line interface |

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Index a directory
python -m file_search_agent index /path/to/documents

# Search
python -m file_search_agent search "find all contracts from 2024"

# Interactive mode
python -m file_search_agent chat
```

## 💻 Python Usage

```python
from file_search_agent import FileSearchAgent

# Initialize agent (uses OpenAI by default)
agent = FileSearchAgent()

# Or use different LLM providers
agent = FileSearchAgent(llm_provider="anthropic", api_key="your-key")
agent = FileSearchAgent(llm_provider="ollama", llm_model="llama3.2")  # Local, free!

# Index documents
stats = agent.index("/path/to/documents")
print(f"Indexed {stats['indexed']} documents")

# Semantic search
results = agent.search("quarterly revenue report", top_k=5)
for r in results:
    print(f"{r.file_name}: {r.score:.3f}")

# Ask questions (RAG)
response = agent.ask("What was the Q4 revenue?")
print(response.answer)
print(f"Sources: {[s.file_name for s in response.sources]}")

# Interactive chat
for token in agent.chat_stream("Summarize the main findings"):
    print(token, end="")
```

## 🌐 REST API

Start the API server:
```bash
uvicorn file_search_agent.api:app --reload
```

API endpoints:
- `POST /index` - Index documents
- `POST /search` - Search documents
- `POST /ask` - Ask questions
- `POST /chat` - Chat with documents
- `GET /stats` - Get statistics
- `GET /documents` - List indexed documents

## 🔧 Configuration

Create a `.env` file:
```env
# LLM Settings
LLM_PROVIDER=openai  # openai, anthropic, ollama
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Search Settings
SEARCH_TOP_K=10
CHUNK_SIZE=512
USE_HYBRID_SEARCH=true

# Vector Store
VECTOR_STORE_TYPE=faiss  # faiss, chromadb
```

## 📁 Project Structure

```
file_search_agent/
├── __init__.py
├── __main__.py           # CLI entry point
├── config.py             # Configuration management
├── core/
│   ├── indexer.py        # Document indexing logic
│   ├── searcher.py       # Search engine
│   ├── embeddings.py     # Embedding models
│   └── llm.py            # LLM integration
├── parsers/
│   ├── base.py           # Base parser class
│   ├── pdf.py            # PDF parser
│   ├── docx.py           # Word document parser
│   ├── excel.py          # Excel parser
│   ├── text.py           # Plain text parser
│   ├── code.py           # Source code parser
│   └── image.py          # Image/OCR parser
├── storage/
│   ├── vector_store.py   # FAISS/ChromaDB wrapper
│   ├── metadata_store.py # SQLite metadata
│   └── cache.py          # Caching layer
├── agents/
│   ├── search_agent.py   # Main search agent
│   └── qa_agent.py       # Q&A agent
├── api/
│   ├── server.py         # FastAPI server
│   └── routes.py         # API endpoints
└── utils/
    ├── file_utils.py     # File system utilities
    └── text_utils.py     # Text processing
```

## 📄 License

MIT License
