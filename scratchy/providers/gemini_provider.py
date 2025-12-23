import os
from typing import List, Dict, Any, Optional
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        from google import genai
        
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini/Google API key is required.")
        
        self.client = genai.Client(api_key=self.api_key)

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        from .utils import extract_content
        
        # Build contents list for the new SDK
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role")
            raw_content = msg.get("content", "")
            
            text_content, images = extract_content(raw_content)
            
            # Skip empty messages (unless they have images)
            if not text_content.strip() and not images:
                if not msg.get("tool_calls"):
                    continue
            
            if role == "system":
                if text_content:
                    system_instruction = text_content
                continue
            
            parts = []
            if text_content:
                parts.append(text_content)
            
            for img in images:
                if img["data"] and img["mime_type"]:
                    parts.append({
                        "inline_data": {
                            "mime_type": img["mime_type"],
                            "data": img["data"]
                        }
                    })
            
            if role == "user":
                if parts:
                    contents.append({"role": "user", "parts": parts})
            elif role == "assistant":
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif role == "tool":
                continue
        
        # Ensure we have at least one message
        if not contents:
            raise ValueError("No valid messages to send to Gemini")
        
        # Prepend system instruction to first user message if present
        if system_instruction and contents:
            first_parts = contents[0].get("parts", [])
            if first_parts and isinstance(first_parts[0], str):
                first_parts[0] = f"{system_instruction}\n\n{first_parts[0]}"
            else:
                first_parts.insert(0, system_instruction)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            
            # Check if response has text
            if not response.text or response.text.strip() == "":
                raise ValueError("Gemini returned an empty response")
            
            return {
                "role": "assistant",
                "content": response.text,
            }
            
        except Exception as e:
            error_msg = str(e)
            if "image" in error_msg.lower() and ("support" in error_msg.lower() or "type" in error_msg.lower() or "argument" in error_msg.lower()):
                raise ValueError(f"Gemini model '{self.model_name}' does not support this image/data type.") from e
            
            if "empty" in error_msg.lower() or "must contain" in error_msg.lower():
                raise ValueError(f"Gemini model returned empty response. This may be due to content filtering or model limitations. Original error: {error_msg}")
            raise

    def get_model_name(self) -> str:
        return self.model_name
