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
        from .utils import extract_content
        
        # Convert OpenAI format messages to Gemini format
        gemini_history = []
        system_instruction = None
        
        has_images = False
        
        for msg in messages:
            role = msg.get("role")
            raw_content = msg.get("content", "")
            
            text_content, images = extract_content(raw_content)
            
            # Skip empty messages (unless they have images)
            if not text_content.strip() and not images:
                if not msg.get("tool_calls"): # Keep messages with tool calls if we supported them
                    continue
            
            if images:
                has_images = True

            parts = []
            if text_content:
                parts.append(text_content)
            
            for img in images:
                if img["data"] and img["mime_type"]:
                    parts.append({
                        "mime_type": img["mime_type"],
                        "data": img["data"]
                    })
            
            if role == "system":
                # Store system instruction separately. 
                # Note: System instructions in Gemini usually shouldn't include images, 
                # but if they do, we might need to handle differently. 
                # For now assuming text-only system instructions or appending to first user msg.
                if text_content:
                    system_instruction = text_content
                continue 
            
            if role == "user":
                if parts:
                    gemini_history.append({"role": "user", "parts": parts})
            elif role == "assistant":
                # Only add non-empty assistant messages
                if parts:
                    gemini_history.append({"role": "model", "parts": parts})
            elif role == "tool":
                # Skip tool messages for now as Gemini handles them differently
                continue
        
        # Ensure we have at least one message
        if not gemini_history:
            raise ValueError("No valid messages to send to Gemini")
        
        # Split history and latest message
        # Gemini expects history to be alternating user/model
        # We need to being careful with the last message extraction
        latest_message_parts = gemini_history[-1]['parts']
        history_context = gemini_history[:-1] if len(gemini_history) > 1 else []
        
        # Prepend system instruction to first user message if present and no history
        # (Or use the system_instruction argument in GenerativeModel if we reconstructed it efficiently, 
        # but here we follow the previous pattern of appending to message)
        if system_instruction and not history_context:
            # If the latest message is text-only, we can prepend. 
            # If it has images, we should add the system instruction as a text part before other parts.
            if isinstance(latest_message_parts[0], str):
                latest_message_parts[0] = f"{system_instruction}\n\n{latest_message_parts[0]}"
            else:
                latest_message_parts.insert(0, system_instruction)
        
        try:
            # Start chat with history
            chat = self.model.start_chat(history=history_context)
            response = chat.send_message(latest_message_parts)
            
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
            }
            
        except Exception as e:
            error_msg = str(e)
            # Check for unsupported media type or model errors related to vision
            if "image" in error_msg.lower() and ("support" in error_msg.lower() or "type" in error_msg.lower() or "argument" in error_msg.lower()):
                 raise ValueError("Model not support to given data type") from e
            
            # Re-raise with more context
            if "empty" in error_msg.lower() or "must contain" in error_msg.lower():
                raise ValueError(f"Gemini model returned empty response. This may be due to content filtering or model limitations. Original error: {error_msg}")
            raise

    def get_model_name(self) -> str:
        return self.model_name
