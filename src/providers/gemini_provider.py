import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini/Google API key is required.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.chat_session = None # Gemini maintains history in chat session usually, but we might want stateless for compatibility

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        # Convert OpenAI format messages to Gemini format
        gemini_history = []
        last_user_message = ""
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "system":
                # Gemini doesn't strictly have system role in history in the same way, 
                # usually passed at model init or as first user message.
                # For simplicity, we might prepend it or use system_instruction if model supports it.
                # This is a basic implementation.
                continue 
            
            if role == "user":
                gemini_history.append({"role": "user", "parts": [content]})
                last_user_message = content
            elif role == "assistant":
                gemini_history.append({"role": "model", "parts": [content]})
        
        # We need to handle the case where we are sending the whole history vs just the new message.
        # If we use start_chat, we pass history.
        
        # Filter out the last message if it's the one we are sending?
        # The `messages` argument usually contains the full history including the latest user message.
        
        history_context = gemini_history[:-1] if gemini_history else []
        latest_message = gemini_history[-1]['parts'][0] if gemini_history else ""
        
        # Tools handling for Gemini is specific. 
        # We would need to convert OpenAI tool definitions to Gemini tool definitions.
        # For now, we will omit tools implementation for Gemini to keep it simple, 
        # or we would need a converter.
        
        chat = self.model.start_chat(history=history_context)
        response = chat.send_message(latest_message)
        
        # Convert back to a standardized response format
        return {
            "role": "assistant",
            "content": response.text,
            # "tool_calls": ... # if we supported tools
        }

    def get_model_name(self) -> str:
        return self.model_name
