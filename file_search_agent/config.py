"""
Configuration management for Smart File Search Agent.
Supports environment variables, .env files, and programmatic configuration.
"""

import os
from pathlib import Path
from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # === LLM Configuration ===
    llm_provider: Literal["openai", "anthropic", "ollama", "azure"] = Field(
        default="openai",
        description="LLM provider to use"
    )
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_KEY")
    ollama_host: str = Field(default="http://localhost:11434")
    
    # Model names
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )
    
    # === Vector Store Configuration ===
    vector_store_type: Literal["faiss", "chromadb"] = Field(default="faiss")
    vector_store_path: Path = Field(default=Path("./data/vector_store"))
    embedding_dimension: int = Field(default=384)  # all-MiniLM-L6-v2 dimension
    
    # === Index Configuration ===
    index_path: Path = Field(default=Path("./data/index"))
    metadata_db_path: Path = Field(default=Path("./data/metadata.db"))
    chunk_size: int = Field(default=512, description="Characters per chunk")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    
    # === Search Configuration ===
    search_top_k: int = Field(default=10, description="Number of results to return")
    similarity_threshold: float = Field(default=0.5, description="Minimum similarity score")
    use_hybrid_search: bool = Field(default=True, description="Combine vector + keyword search")
    
    # === File Processing ===
    supported_extensions: list[str] = Field(
        default=[
            ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
            ".txt", ".md", ".csv", ".json", ".xml", ".html",
            ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs",
            ".png", ".jpg", ".jpeg", ".gif", ".bmp"  # For OCR
        ]
    )
    max_file_size_mb: int = Field(default=100)
    ignore_patterns: list[str] = Field(
        default=[".*", "__pycache__", "node_modules", ".git", "venv", ".env"]
    )
    
    # === API Configuration ===
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8080)
    
    # === Logging ===
    log_level: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.metadata_db_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
