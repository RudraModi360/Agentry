"""
FastAPI Server for Smart File Search Agent.
Provides REST API endpoints for indexing, searching, and Q&A.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import shutil
import asyncio

from ..agents import FileSearchAgent
from ..config import settings


# Pydantic models for API
class IndexRequest(BaseModel):
    path: str = Field(..., description="Path to file or directory")
    parallel: bool = Field(True, description="Use parallel processing")
    max_workers: int = Field(4, description="Number of workers")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, description="Number of results")
    file_type: Optional[str] = Field(None, description="Filter by file type")


class AskRequest(BaseModel):
    question: str = Field(..., description="Question to ask")
    top_k: int = Field(5, description="Number of context documents")
    file_type: Optional[str] = Field(None, description="Filter by file type")


class ChatRequest(BaseModel):
    message: str = Field(..., description="Chat message")
    top_k: int = Field(5, description="Number of context documents")
    stream: bool = Field(False, description="Stream response")


class SearchResult(BaseModel):
    chunk_id: str
    text: str
    file_path: str
    file_name: str
    score: float
    highlight: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    confidence: float
    model_used: str


class IndexStats(BaseModel):
    total_documents: int
    total_chunks: int
    file_types: Dict[str, int]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Smart File Search Agent API",
        description="LLM-powered document search and Q&A API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize agent (lazily)
    _agent: Optional[FileSearchAgent] = None
    
    def get_agent() -> FileSearchAgent:
        nonlocal _agent
        if _agent is None:
            _agent = FileSearchAgent()
        return _agent
    
    @app.get("/")
    async def root():
        """API root endpoint."""
        return {
            "name": "Smart File Search Agent",
            "version": "1.0.0",
            "status": "running"
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    @app.post("/index")
    async def index_documents(request: IndexRequest):
        """Index documents from a path."""
        path = Path(request.path)
        
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        agent = get_agent()
        
        try:
            stats = agent.index(
                str(path),
                parallel=request.parallel,
                max_workers=request.max_workers
            )
            return {
                "status": "success",
                "indexed": stats.get("indexed", 0),
                "skipped": stats.get("skipped", 0),
                "duration": stats.get("duration", 0)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/index/upload")
    async def upload_and_index(file: UploadFile = File(...)):
        """Upload a file and index it."""
        agent = get_agent()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        try:
            result = agent.index(tmp_path)
            return {"status": "success", "filename": file.filename, **result}
        finally:
            # Cleanup temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    @app.post("/search", response_model=List[SearchResult])
    async def search_documents(request: SearchRequest):
        """Search indexed documents."""
        agent = get_agent()
        
        results = agent.search(
            query=request.query,
            top_k=request.top_k,
            file_type=request.file_type
        )
        
        return [
            SearchResult(
                chunk_id=r.chunk_id,
                text=r.text,
                file_path=r.file_path,
                file_name=r.file_name,
                score=r.score,
                highlight=r.highlight
            )
            for r in results
        ]
    
    @app.post("/ask", response_model=AskResponse)
    async def ask_question(request: AskRequest):
        """Ask a question about indexed documents."""
        agent = get_agent()
        
        response = agent.ask(
            question=request.question,
            top_k=request.top_k,
            file_type=request.file_type
        )
        
        return AskResponse(
            answer=response.answer,
            sources=[
                SearchResult(
                    chunk_id=s.chunk_id,
                    text=s.text,
                    file_path=s.file_path,
                    file_name=s.file_name,
                    score=s.score,
                    highlight=s.highlight
                )
                for s in response.sources
            ],
            confidence=response.confidence,
            model_used=response.model_used
        )
    
    @app.post("/chat")
    async def chat(request: ChatRequest):
        """Chat with documents."""
        agent = get_agent()
        
        if request.stream:
            # Return streaming response
            async def generate():
                for token in agent.chat_stream(request.message, top_k=request.top_k):
                    yield token
            
            return StreamingResponse(generate(), media_type="text/plain")
        else:
            response = agent.chat(request.message, top_k=request.top_k)
            return {
                "answer": response.answer,
                "confidence": response.confidence,
                "model_used": response.model_used
            }
    
    @app.post("/chat/clear")
    async def clear_chat():
        """Clear chat conversation history."""
        agent = get_agent()
        agent.clear_conversation()
        return {"status": "conversation cleared"}
    
    @app.get("/stats", response_model=IndexStats)
    async def get_stats():
        """Get indexing statistics."""
        agent = get_agent()
        stats = agent.get_stats()
        return IndexStats(**stats)
    
    @app.get("/documents")
    async def list_documents(
        file_type: Optional[str] = None,
        limit: int = 100
    ):
        """List indexed documents."""
        agent = get_agent()
        docs = agent.list_documents(file_type=file_type)[:limit]
        return docs
    
    @app.delete("/documents/{file_path:path}")
    async def delete_document(file_path: str):
        """Remove a document from the index."""
        agent = get_agent()
        success = agent.indexer.remove_document(file_path)
        
        if success:
            return {"status": "deleted", "path": file_path}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    
    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
