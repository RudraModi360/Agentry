import os
from typing import List, Dict, Any, Optional, Callable, Union
import asyncio
from .base import LLMProvider

class LlamaCppProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize LlamaCppProvider.
        
        Args:
            model_name: Absolute path to the .gguf model file.
            api_key: Not used for local models.
            **kwargs: Additional arguments for Llama constructor (n_ctx, n_gpu_layers, etc.)
        """
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError("llama-cpp-python is not installed. Please install it with: pip install llama-cpp-python")
            
        self.model_path = model_name
        if not os.path.exists(self.model_path):
            # If strictly a path, fail. If it's a model name, maybe we should search?
            # For now, assume it's a full path or we fail.
            # But let's allow a fallback if it's just a filename in a "models" dir if we had one.
            pass
            
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=kwargs.get("n_ctx", 4096),
            n_gpu_layers=kwargs.get("n_gpu_layers", -1), # -1 = all layers to GPU
            verbose=kwargs.get("verbose", False),
            chat_format=kwargs.get("chat_format", "chatml") # Default to chatml, but newer versions auto-detect
        )
        
    def get_model_name(self) -> str:
        return os.path.basename(self.model_path)

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        # Run blocking code in a thread
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._chat_sync, messages, tools)

    def _chat_sync(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        # Note: llama-cpp-python's create_chat_completion doesn't support tools natively in the same way 
        # as OpenAI yet (or it's experimental). We'll stick to text for now unless we manually format tools.
        # For this implementation, we'll ignore tools or rely on the agent to insert them into the system prompt.
        
        # Filter messages to ensure content is string
        safe_messages = []
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                # Flatten multimodal content to text (images not supported yet in this basic provider)
                text_parts = [p["text"] for p in content if p.get("type") == "text"]
                content = " ".join(text_parts)
            
            safe_messages.append({
                "role": msg["role"],
                "content": content
            })

        response = self.llm.create_chat_completion(
            messages=safe_messages,
            # tools=tools, # Not reliable yet in llama-cpp-python high level API for all models
            stream=False
        )
        
        return response["choices"][0]["message"]

    async def chat_stream(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        on_token: Optional[Callable[[str], None]] = None
    ) -> Any:
        loop = asyncio.get_event_loop()
        
        # Queue for passing tokens from thread
        token_queue = asyncio.Queue()
        
        def sync_stream():
            try:
                safe_messages = []
                for msg in messages:
                    content = msg.get("content")
                    if isinstance(content, list):
                        text_parts = [p["text"] for p in content if p.get("type") == "text"]
                        content = " ".join(text_parts)
                    
                    safe_messages.append({
                        "role": msg["role"],
                        "content": content
                    })

                stream = self.llm.create_chat_completion(
                    messages=safe_messages,
                    stream=True
                )
                
                full_content = ""
                
                for chunk in stream:
                    delta = chunk['choices'][0]['delta']
                    if 'content' in delta:
                        token = delta['content']
                        full_content += token
                        asyncio.run_coroutine_threadsafe(token_queue.put(token), loop)
                        
                asyncio.run_coroutine_threadsafe(token_queue.put({"done": True, "content": full_content}), loop)
                
            except Exception as e:
                asyncio.run_coroutine_threadsafe(token_queue.put({"error": e}), loop)

        # Start thread
        import threading
        t = threading.Thread(target=sync_stream)
        t.start()
        
        full_response_content = ""
        
        while True:
            item = await token_queue.get()
            
            if isinstance(item, dict):
                if "error" in item:
                    raise item["error"]
                if "done" in item:
                    full_response_content = item["content"]
                    break
            
            if isinstance(item, str):
                if on_token:
                    if asyncio.iscoroutinefunction(on_token):
                        await on_token(item)
                    else:
                        on_token(item)
                        
        return {"role": "assistant", "content": full_response_content}
