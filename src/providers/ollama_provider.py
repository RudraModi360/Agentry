import ollama
from typing import List, Dict, Any, Optional
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.client = ollama.Client(**kwargs)

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        options = {}
        # Extract temperature if present in the last message or manage it via state if needed.
        # For now, we'll keep it simple.
        
        response = self.client.chat(
            model=self.model_name,
            messages=messages,
            tools=tools,
        )
        return response['message']

    def get_model_name(self) -> str:
        return self.model_name
