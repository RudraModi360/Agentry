"""
FileSearchAgent - The main intelligent agent that orchestrates search and Q&A.
Combines indexing, search, and LLM for natural language file queries.
"""

import logging
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
from pathlib import Path

from ..config import settings
from ..core.indexer import DocumentIndexer
from ..core.searcher import SearchEngine, RankedResult
from ..core.llm import LLMEngine, Message, LLMResponse
from ..core.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from the search agent."""
    answer: str
    sources: List[RankedResult]
    confidence: float
    query: str
    model_used: str


class FileSearchAgent:
    """
    Intelligent file search agent that understands natural language queries.
    
    Features:
    - Natural language understanding
    - Semantic + keyword search
    - Context-aware answers with citations
    - Multi-turn conversations
    - File type awareness
    
    Usage:
        agent = FileSearchAgent()
        
        # Index documents
        agent.index("/path/to/docs")
        
        # Search and get answers
        response = agent.ask("What is the quarterly revenue?")
        print(response.answer)
        
        # Chat mode
        for token in agent.chat_stream("Summarize the main points"):
            print(token, end="")
    """
    
    SYSTEM_PROMPT = """You are an intelligent file search assistant. Your job is to:
1. Answer questions based on the document context provided
2. Always cite the source documents when giving information
3. If you can't find the answer in the context, say so clearly
4. Be precise and accurate - don't make up information
5. Organize complex answers with bullet points or sections
6. Highlight key information like numbers, dates, and names

When citing sources, use this format: [Source: filename.ext]"""

    def __init__(
        self,
        llm_provider: str = None,
        llm_model: str = None,
        api_key: str = None,
        embedding_model: str = None
    ):
        """
        Initialize the search agent.
        
        Args:
            llm_provider: LLM provider (openai, anthropic, ollama)
            llm_model: Model name
            api_key: API key for the LLM provider
            embedding_model: Embedding model name
        """
        # Initialize embedding engine
        self.embedding_engine = EmbeddingEngine(
            model_name=embedding_model or settings.embedding_model
        )
        
        # Initialize LLM
        provider = llm_provider or settings.llm_provider
        model = llm_model or settings.llm_model
        key = api_key or settings.openai_api_key or settings.anthropic_api_key
        
        self.llm = LLMEngine(
            provider=provider,
            model=model,
            api_key=key
        )
        
        # Initialize indexer and searcher (share embedding engine)
        self.indexer = DocumentIndexer(embedding_engine=self.embedding_engine)
        self.searcher = SearchEngine(
            embedding_engine=self.embedding_engine,
            vector_store=self.indexer.vector_store,
            metadata_store=self.indexer.metadata_store
        )
        
        # Conversation history for multi-turn
        self._conversation: List[Message] = []
    
    def index(
        self,
        path: str,
        parallel: bool = True,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Index documents from a path.
        
        Args:
            path: File or directory path
            parallel: Use parallel processing
            max_workers: Number of workers
            
        Returns:
            Indexing statistics
        """
        path = Path(path)
        
        if path.is_file():
            result = self.indexer.index_file(path)
            return {"indexed": 1 if result else 0, "path": str(path)}
        else:
            return self.indexer.index_directory(
                path, parallel=parallel, max_workers=max_workers
            )
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        file_type: str = None
    ) -> List[RankedResult]:
        """
        Search indexed documents.
        
        Args:
            query: Search query
            top_k: Number of results
            file_type: Filter by file type
            
        Returns:
            List of ranked results
        """
        return self.searcher.search(
            query=query,
            top_k=top_k,
            filter_file_type=file_type
        )
    
    def ask(
        self,
        question: str,
        top_k: int = 5,
        file_type: str = None
    ) -> AgentResponse:
        """
        Ask a question and get an LLM-powered answer.
        
        Args:
            question: Natural language question
            top_k: Number of documents to use as context
            file_type: Filter by file type
            
        Returns:
            AgentResponse with answer and sources
        """
        # Search for relevant documents
        results = self.search(question, top_k=top_k, file_type=file_type)
        
        if not results:
            return AgentResponse(
                answer="I couldn't find any relevant documents to answer your question.",
                sources=[],
                confidence=0.0,
                query=question,
                model_used=self.llm._engine.model
            )
        
        # Build context from results
        context = self._build_context(results)
        
        # Get answer from LLM
        llm_response = self.llm.answer_with_context(
            question=question,
            context=context,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        # Calculate confidence based on search scores
        avg_score = sum(r.score for r in results) / len(results)
        
        return AgentResponse(
            answer=llm_response.content,
            sources=results,
            confidence=avg_score,
            query=question,
            model_used=self.llm._engine.model
        )
    
    def chat(
        self,
        message: str,
        top_k: int = 5
    ) -> AgentResponse:
        """
        Multi-turn chat with context from documents.
        
        Args:
            message: User message
            top_k: Number of documents to use
            
        Returns:
            AgentResponse with answer
        """
        # Search for relevant context
        results = self.search(message, top_k=top_k)
        context = self._build_context(results) if results else ""
        
        # Build message with context
        user_msg = message
        if context:
            user_msg = f"Context from documents:\n{context}\n\nUser question: {message}"
        
        # Add to conversation
        self._conversation.append(Message("user", user_msg))
        
        # Get response with full conversation history
        messages = [Message("system", self.SYSTEM_PROMPT)] + self._conversation
        response = self.llm.chat(messages)
        
        # Add response to history
        self._conversation.append(Message("assistant", response.content))
        
        return AgentResponse(
            answer=response.content,
            sources=results,
            confidence=sum(r.score for r in results) / max(1, len(results)),
            query=message,
            model_used=self.llm._engine.model
        )
    
    def chat_stream(
        self,
        message: str,
        top_k: int = 5
    ) -> Generator[str, None, None]:
        """
        Stream a chat response token by token.
        
        Args:
            message: User message
            top_k: Number of documents
            
        Yields:
            Response tokens
        """
        results = self.search(message, top_k=top_k)
        context = self._build_context(results) if results else ""
        
        prompt = f"""Context from documents:
{context}

User question: {message}

Answer based on the context above:"""
        
        yield from self.llm.stream(prompt)
    
    def clear_conversation(self):
        """Clear conversation history."""
        self._conversation.clear()
    
    def _build_context(self, results: List[RankedResult], max_chars: int = 8000) -> str:
        """Build context string from search results."""
        context_parts = []
        total_chars = 0
        
        for i, result in enumerate(results, 1):
            source_info = f"[Document {i}: {result.file_name}]"
            chunk_text = result.text
            
            # Truncate if needed
            remaining = max_chars - total_chars - len(source_info) - 20
            if remaining <= 0:
                break
            
            if len(chunk_text) > remaining:
                chunk_text = chunk_text[:remaining] + "..."
            
            context_parts.append(f"{source_info}\n{chunk_text}")
            total_chars += len(source_info) + len(chunk_text) + 2
        
        return "\n\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return self.indexer.get_stats()
    
    def list_documents(self, file_type: str = None) -> List[Dict[str, Any]]:
        """List indexed documents."""
        docs = self.indexer.metadata_store.list_documents(file_type=file_type)
        return [
            {
                "path": doc.file_path,
                "name": doc.file_name,
                "type": doc.file_type,
                "size": doc.file_size,
                "chunks": doc.chunk_count,
                "indexed": doc.indexed_at.isoformat()
            }
            for doc in docs
        ]
