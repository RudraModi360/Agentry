import os
from groq import Groq
from typing import List, Dict, Any, Optional
from .base import LLMProvider

class GroqProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required.")
        self.client = Groq(api_key=self.api_key)

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        # Groq's sync client is used here, wrapping in a way to fit async interface if needed, 
        # but for now we just call it. Ideally we'd use AsyncGroq.
        
        # Prepare arguments
        kwargs = {
            "model": self.model_name,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
            
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def get_model_name(self) -> str:
        return self.model_name
