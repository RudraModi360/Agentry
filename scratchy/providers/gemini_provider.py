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
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            # Skip empty messages
            if not content or content.strip() == "":
                continue
            
            if role == "system":
                # Store system instruction separately
                system_instruction = content
                continue 
            
            if role == "user":
                gemini_history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                # Only add non-empty assistant messages
                if content:
                    gemini_history.append({"role": "model", "parts": [content]})
            elif role == "tool":
                # Skip tool messages for now as Gemini handles them differently
                continue
        
        # Ensure we have at least one message
        if not gemini_history:
            raise ValueError("No valid messages to send to Gemini")
        
        # Split history and latest message
        history_context = gemini_history[:-1] if len(gemini_history) > 1 else []
        latest_message = gemini_history[-1]['parts'][0] if gemini_history else ""
        
        if not latest_message:
            raise ValueError("Latest message is empty")
        
        # Prepend system instruction to first user message if present
        if system_instruction and not history_context:
            latest_message = f"{system_instruction}\n\n{latest_message}"
        
        try:
            # Start chat with history
            chat = self.model.start_chat(history=history_context)
            response = chat.send_message(latest_message)
            
            # Check if response has text
            if not response.text or response.text.strip() == "":
                # Try to get any available content
                if hasattr(response, 'parts') and response.parts:
                    content = " ".join([part.text for part in response.parts if hasattr(part, 'text')])
                    if content:
                        return {
                            "role": "assistant",
                            "content": content,
                        }
                
                # If still empty, raise an error that will be caught by the agent
                raise ValueError("Gemini returned an empty response")
            
            # Convert back to a standardized response format
            return {
                "role": "assistant",
                "content": response.text,
                # "tool_calls": ... # if we supported tools
            }
            
        except Exception as e:
            error_msg = str(e)
            # Re-raise with more context
            if "empty" in error_msg.lower() or "must contain" in error_msg.lower():
                raise ValueError(f"Gemini model returned empty response. This may be due to content filtering or model limitations. Original error: {error_msg}")
            raise

    def get_model_name(self) -> str:
        return self.model_name
