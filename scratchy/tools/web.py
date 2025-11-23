import requests
import os
from typing import Any, Literal
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult
from langchain_community.tools import DuckDuckGoSearchRun
from groq import Groq
from scratchy.config.settings import get_api_key

# --- Schemas ---

class WebSearchParams(BaseModel):
    user_input: str = Field(..., description='Content to search for.')
    search_type: Literal['general', 'critical'] = Field('general', description='Type of search: "general" for quick lookups, "critical" for deep research where results are analyzed by an LLM.')

class UrlFetchParams(BaseModel):
    url: str = Field(..., description='URL to fetch content from.')

# --- Tools ---

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the internet. Use 'general' for basic queries and 'critical' for complex/deep research."
    args_schema = WebSearchParams

    def run(self, user_input: str, search_type: str = 'general') -> ToolResult:
        try:
            # Step 1: Always perform the actual web search using DuckDuckGo first
            ddg_results = DuckDuckGoSearchRun().invoke(user_input)

            if search_type == 'general':
                return ToolResult(success=True, content=ddg_results)
            
            elif search_type == 'critical':
                # Step 2: For critical searches, use Groq to analyze/synthesize the DDG results
                api_key = get_api_key("groq")
                if not api_key:
                    return ToolResult(success=False, error="Groq API key not found for critical search.")
                
                client_groq = Groq(api_key=api_key)
                
                # Construct a prompt that includes the search results
                prompt = (
                    f"User Query: {user_input}\n\n"
                    f"Web Search Results:\n{ddg_results}\n\n"
                    f"Based on the above search results, please provide a comprehensive and detailed answer to the user's query."
                )

                response = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile", # Using a capable model for synthesis
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful research assistant. Analyze the provided web search results to answer the user's question accurately."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return ToolResult(success=True, content=response.choices[0].message.content)
            
            return ToolResult(success=True, content=ddg_results)

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to search web: {e}")

class UrlFetchTool(BaseTool):
    name = "url_fetch"
    description = "Fetch content from a URL."
    args_schema = UrlFetchParams

    def run(self, url: str) -> ToolResult:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            return ToolResult(success=True, content=response.text)
        except requests.exceptions.RequestException as e:
            return ToolResult(success=False, error=f"Failed to fetch URL: {e}")
