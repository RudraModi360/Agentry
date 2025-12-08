import ollama
from typing import List, Dict, Any, Optional, Callable
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.client = ollama.Client(**kwargs)

    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> tuple:
        """Prepare and filter messages for Ollama. Returns (filtered_messages, has_images)."""
        from .utils import extract_content
        
        filtered_messages = []
        has_images = False
        
        for msg in messages:
            role = msg.get("role")
            raw_content = msg.get("content", "")
            tool_calls = msg.get("tool_calls")
            
            text_content, images = extract_content(raw_content)
            
            ollama_msg = {"role": role, "content": text_content}
            
            if images:
                has_images = True
                ollama_images = []
                for img in images:
                    if img.get("data"):
                        import base64
                        ollama_images.append(base64.b64encode(img["data"]).decode('utf-8'))
                
                if ollama_images:
                    ollama_msg["images"] = ollama_images
            
            if tool_calls:
                if isinstance(tool_calls, dict):
                    if 'required' in tool_calls or 'properties' in tool_calls:
                        tool_calls = None
                    else:
                        tool_calls = [tool_calls]
                
                if tool_calls:
                    clean_calls = []
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            if 'required' in tc or 'properties' in tc:
                                continue
                            clean_calls.append(tc)
                    
                    if clean_calls:
                        ollama_msg["tool_calls"] = clean_calls
            
            if role and (text_content or images or tool_calls):
                filtered_messages.append(ollama_msg)
        
        return filtered_messages, has_images

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Standard non-streaming chat."""
        filtered_messages, has_images = self._prepare_messages(messages)
        
        if not filtered_messages:
            raise ValueError("No valid messages to send to Ollama")
            
        if has_images and not self._supports_vision():
            raise ValueError("Model not support to given data type")

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=filtered_messages,
                tools=tools,
            )
            
            if not response or 'message' not in response:
                raise ValueError("Ollama returned invalid response structure")
            
            message = response['message']
            
            if not message.get('content') and not message.get('tool_calls'):
                raise ValueError("Ollama returned empty message with no content or tool calls")
            
            return message
            
        except Exception as e:
            error_msg = str(e)
            if "empty" in error_msg.lower() or "invalid" in error_msg.lower():
                raise ValueError(f"Ollama error: {error_msg}. Try using a different model or check if Ollama is running properly.")
            if "support" in error_msg.lower() and "image" in error_msg.lower():
                raise ValueError("Model not support to given data type") from e
            raise

    async def chat_stream(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        on_token: Optional[Callable[[str], None]] = None
    ) -> Any:
        """
        Streaming chat that yields tokens progressively.
        Returns the final complete message dict.
        """
        import asyncio
        
        filtered_messages, has_images = self._prepare_messages(messages)
        
        if not filtered_messages:
            raise ValueError("No valid messages to send to Ollama")
            
        if has_images and not self._supports_vision():
            raise ValueError("Model not support to given data type")

        def sync_stream():
            """Run the blocking stream iteration in a thread."""
            full_content = ""
            tool_calls = None
            
            try:
                stream = self.client.chat(
                    model=self.model_name,
                    messages=filtered_messages,
                    tools=tools,
                    stream=True
                )
                
                for chunk in stream:
                    if 'message' in chunk:
                        msg = chunk['message']
                        
                        if msg.get('content'):
                            token = msg['content']
                            full_content += token
                            if on_token:
                                on_token(token)
                        
                        if msg.get('tool_calls'):
                            tool_calls = msg['tool_calls']
                
            except Exception as e:
                raise e
            
            final_message = {"role": "assistant", "content": full_content}
            if tool_calls:
                final_message["tool_calls"] = tool_calls
                
            return final_message

        # Run the blocking stream in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_stream)
        return result

    def _supports_vision(self) -> bool:
        try:
            info = self.client.show(self.model_name)
            details = info.get('details', {})
            families = details.get('families', []) or []
            if details.get('family'):
                families.append(details.get('family'))
            
            for f in families:
                if f in ['clip', 'vision', 'momo', 'gemma']:
                    return True
            
            name = self.model_name.lower()
            if 'llava' in name or 'vision' in name or 'minicpm' in name or 'gemma' in name:
                return True
                
            return False
        except:
            return False

    def get_model_name(self) -> str:
        return self.model_name
