import ollama
from typing import List, Dict, Any, Optional
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.client = ollama.Client(**kwargs)

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        # Filter out empty messages
        filtered_messages = []
        for msg in messages:
            content = msg.get("content", "")
            # Skip completely empty messages, but keep messages with just role
            if msg.get("role") and (content or msg.get("tool_calls")):
                filtered_messages.append(msg)
        
        if not filtered_messages:
            raise ValueError("No valid messages to send to Ollama")
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=filtered_messages,
                tools=tools,
            )
            
            # Validate response
            if not response or 'message' not in response:
                raise ValueError("Ollama returned invalid response structure")
            
            message = response['message']
            
            # Check if message has content or tool calls
            if not message.get('content') and not message.get('tool_calls'):
                raise ValueError("Ollama returned empty message with no content or tool calls")
            
            return message
            
        except Exception as e:
            error_msg = str(e)
            if "empty" in error_msg.lower() or "invalid" in error_msg.lower():
                raise ValueError(f"Ollama error: {error_msg}. Try using a different model or check if Ollama is running properly.")
            raise

    def get_model_name(self) -> str:
        return self.model_name
