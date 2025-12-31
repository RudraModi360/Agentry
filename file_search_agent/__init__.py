"""
Smart File Search Agent
An intelligent, LLM-powered file search agent for semantic document search.

Usage:
    from file_search_agent import FileSearchAgent
    
    agent = FileSearchAgent()
    agent.index("/path/to/documents")
    
    # Search
    results = agent.search("your query")
    
    # Ask questions
    response = agent.ask("What is the revenue?")
    print(response.answer)
"""

__version__ = "0.1.0"
__author__ = "Smart File Search Agent"

from .config import Settings, settings
from .agents import FileSearchAgent

__all__ = [
    "FileSearchAgent",
    "Settings",
    "settings",
]
