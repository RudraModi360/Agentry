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
        from .utils import extract_content
        
        # Groq's sync client is used here, wrapping in a way to fit async interface if needed, 
        # but for now we just call it. Ideally we'd use AsyncGroq.
        
        # Check for images and model support
        has_images = False
        for msg in messages:
            content = msg.get("content")
            _, images = extract_content(content)
            if images:
                has_images = True
                break
        
        if has_images:
            start_name = self.model_name.lower()
            if "vision" not in start_name and "llava" not in start_name:
                raise ValueError(f"Groq model '{self.model_name}' does not support vision capabilities.")

        # Prepare arguments
        kwargs = {
            "model": self.model_name,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
            
        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except Exception as e:
            error_msg = str(e)
            if "output text or tool calls" in error_msg.lower():
                raise ValueError(f"Groq model returned empty response (output text or tool calls cannot both be empty). Original error: {error_msg}")
            if "validation" in error_msg.lower() and "image" in error_msg.lower(): # Catch Groq specific validation errors for images
                 raise ValueError("Model not support to given data type") from e
            raise e

    def get_model_name(self) -> str:
        return self.model_name
