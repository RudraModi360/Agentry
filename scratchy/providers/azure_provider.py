import os
import base64
import re
import asyncio
from typing import List, Dict, Any, Optional
from .base import LLMProvider


class AzureProvider(LLMProvider):
    """
    Azure AI Foundry Provider - supports multiple model families:
    1. OpenAI Models (GPT-4, etc.) - uses Azure OpenAI API
    2. Anthropic Models (Claude) - uses AnthropicFoundry SDK on Azure
    """
    
    # Model type constants
    MODEL_TYPE_OPENAI = "openai"
    MODEL_TYPE_ANTHROPIC = "anthropic"
    
    def __init__(
        self, 
        model_name: str, 
        api_key: Optional[str] = None, 
        endpoint: Optional[str] = None, 
        api_version: str = "2024-10-21",
        model_type: Optional[str] = None,  # "openai" or "anthropic"
        **kwargs
    ):
        """
        Initialize Azure AI Foundry Provider.
        
        Args:
            model_name: The deployment name in Azure.
            api_key: Azure API Key.
            endpoint: Azure Resource Endpoint (e.g., https://resourcename.services.ai.azure.com).
            api_version: API Version (for OpenAI models).
            model_type: "openai" or "anthropic" - auto-detected if not specified.
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("AZURE_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.environ.get("AZURE_ENDPOINT") or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version
        
        if not self.api_key:
            raise ValueError("Azure API key is required.")
        if not self.endpoint:
            raise ValueError("Azure Endpoint is required.")
        
        # Clean endpoint - remove trailing slashes
        self.endpoint = self.endpoint.rstrip("/")
        
        # Auto-detect model type from endpoint or model name if not specified
        if model_type:
            self.model_type = model_type.lower()
        elif "anthropic" in self.endpoint.lower() or "claude" in model_name.lower():
            self.model_type = self.MODEL_TYPE_ANTHROPIC
        else:
            self.model_type = self.MODEL_TYPE_OPENAI
        
        # Initialize appropriate client
        if self.model_type == self.MODEL_TYPE_ANTHROPIC:
            self._init_anthropic_client()
        else:
            self._init_openai_client()
    
    def _init_anthropic_client(self):
        """Initialize Anthropic client for Azure using AnthropicFoundry SDK."""
        from anthropic import AnthropicFoundry
        
        # Build base URL for Anthropic on Azure
        # Format: https://<resource>.services.ai.azure.com/anthropic
        base_url = self.endpoint
        
        # If the user provided a full messages URL, strip it back to the base
        if "/v1/messages" in base_url:
            base_url = base_url.split("/v1/messages")[0]
        elif "/messages" in base_url:
            base_url = base_url.split("/messages")[0]
            
        if "/anthropic" not in base_url.lower():
            base_url = f"{base_url.rstrip('/')}/anthropic"
        
        self.client = AnthropicFoundry(
            api_key=self.api_key,
            base_url=base_url
        )
    
    def _init_openai_client(self):
        """Initialize Azure OpenAI client."""
        from openai import AzureOpenAI
        
        # Extract base URL from endpoint
        base_url = self.endpoint
        if "/openai/" in base_url:
            base_url = base_url.split("/openai/")[0]
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=base_url
        )
    
    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        if self.model_type == self.MODEL_TYPE_ANTHROPIC:
            return await self._chat_anthropic(messages, tools)
        else:
            return await self._chat_openai(messages, tools)
    
    async def chat_stream(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, on_token: Optional[Any] = None) -> Any:
        """Streaming version of chat."""
        if self.model_type == self.MODEL_TYPE_ANTHROPIC:
            return await self._chat_anthropic_stream(messages, tools, on_token)
        else:
            return await self._chat_openai_stream(messages, tools, on_token)
            
    def _convert_to_anthropic_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert generic messages to Anthropic format, handling tool/user role mapping."""
        from .utils import extract_content
        import base64
        
        anthropic_messages = []
        current_tool_results = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            # Handle Tool Results (Generic 'tool' role -> Anthropic 'user' role with tool_result)
            if role == "tool":
                # Only add if we have an ID (which we should)
                tool_call_id = msg.get("tool_call_id")
                # If no ID, we might need a fallback or skip. 
                # Agent typically ensures ID is present.
                
                current_tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": content if content else ""
                })
                continue
            
            # Flush any pending tool results before processing next non-tool message
            if current_tool_results:
                anthropic_messages.append({
                    "role": "user",
                    "content": current_tool_results
                })
                current_tool_results = []
            
            # Skip system messages here (they are handled at top level)
            if role == "system":
                # We typically preserve them in list for extraction later, 
                # but this method is specifically for the 'messages' array.
                # Use a placeholder or just return it? 
                # Better to include it so the caller can extract it, 
                # but caller of this method filters it out.
                anthropic_messages.append(msg) 
                continue
                
            # Handle Assistant Messages with Tool Calls
            if role == "assistant":
                tool_calls = msg.get("tool_calls")
                
                # Base content (text)
                text_content = content if isinstance(content, str) else str(content)
                blocks = []
                
                if text_content:
                    blocks.append({"type": "text", "text": text_content})
                
                # Add tool_use blocks
                if tool_calls:
                    for tc in tool_calls:
                        # Parse args if string
                        args = tc.get("function", {}).get("arguments", "{}")
                        # tc structure from Agent: {id, type, function: {name, arguments}}
                        # Anthropic wants: {type: tool_use, id, name, input}
                        
                        # Ensure input is dict
                        if isinstance(args, str):
                            try:
                                import json
                                input_json = json.loads(args)
                            except:
                                input_json = {} # Error
                        else:
                            input_json = args
                            
                        blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id"),
                            "name": tc.get("function", {}).get("name"),
                            "input": input_json
                        })
                
                # If we have blocks (tool uses or text), use list content
                if blocks:
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": blocks
                    })
                else:
                    # Fallback for empty assistant message?
                    anthropic_messages.append({"role": "assistant", "content": ""})
                continue
                
            # Handle User Messages (Text/Image)
            if role == "user":
                extracted_text, images = extract_content(content)
                
                if images:
                    blocks = []
                    # Add images
                    for img in images:
                        data = img["data"]
                        if isinstance(data, bytes):
                            data = base64.b64encode(data).decode('utf-8')
                        
                        blocks.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": img.get("mime_type", "image/png"),
                                "data": data
                            }
                        })
                    # Add text
                    if extracted_text:
                        blocks.append({"type": "text", "text": extracted_text})
                        
                    anthropic_messages.append({
                        "role": "user",
                        "content": blocks
                    })
                else:
                    # Plain text
                    anthropic_messages.append({
                        "role": "user",
                        "content": extracted_text
                    })
                continue
                
            # Fallback for other roles (function, etc - older OpenAI)
            # Just pass through?
            anthropic_messages.append(msg)
            
        # Flush any trailing tool results at end
        if current_tool_results:
            anthropic_messages.append({
                "role": "user",
                "content": current_tool_results
            })
            
        return anthropic_messages
    
    async def _chat_anthropic_stream(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, on_token: Optional[Any] = None) -> Any:
        """Handle streaming chat with Anthropic Claude models on Azure."""
        import asyncio
        from .utils import extract_content
        
        # Convert messages to Anthropic format (handling tool roles)
        chat_messages = self._convert_to_anthropic_messages(messages)
        
        # System message is handled via kwargs in Anthropic
        system_content = None
        # Extract system message if present in original (it might have been filtered out or needs checking)
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
                break
        
        # Filter out system messages from chat_messages as they go into top-level param
        chat_messages = [m for m in chat_messages if m["role"] != "system"]
        
        # Build kwargs for Anthropic API
        kwargs = {
            "model": self.model_name,
            "messages": chat_messages,
            "max_tokens": 16384
        }
        
        if system_content:
            kwargs["system"] = system_content

        # Convert and add tools if present
        if tools:
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append(self._convert_tool_to_anthropic(tool))
            kwargs["tools"] = anthropic_tools
        
        try:
            # Stream the response in real-time
            accumulated_text = ""
            accumulated_tool_calls = []
            
            # Create stream in a thread-safe way
            import concurrent.futures
            import queue
            import threading
            
            q = queue.Queue()
            
            def stream_worker():
                """Worker thread to handle synchronous streaming."""
                try:
                    with self.client.messages.stream(**kwargs) as stream:
                        for event in stream:
                            q.put(('event', event))
                    q.put(('done', None))
                except Exception as e:
                    print(f"[AzureAnthropic] Stream Worker Error: {e}")
                    q.put(('error', e))
            
            # Start streaming in background thread
            thread = threading.Thread(target=stream_worker, daemon=True)
            thread.start()
            
            # Process chunks as they arrive
            while True:
                try:
                    msg_type, data = q.get(timeout=120)  # 2 minutes for large content
                    
                    if msg_type == 'event':
                        event = data
                        
                        # Handle Text Delta - print raw text like ChatGPT
                        if event.type == 'content_block_delta' and hasattr(event.delta, 'text'):
                            text = event.delta.text
                            accumulated_text += text
                            # Only use on_token for UI streaming, print for terminal debugging
                            if on_token:
                                await on_token(text)
                                await asyncio.sleep(0)
                            else:
                                print(text, end='', flush=True)
                        
                        # Handle Tool Use Start
                        elif event.type == 'content_block_start' and event.content_block.type == 'tool_use':
                            print(f"\n\n>>> TOOL: {event.content_block.name} <<<\n", flush=True)
                            accumulated_tool_calls.append({
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input_json": ""
                            })
                            
                        # Handle Tool Input JSON Delta - print raw JSON chunks
                        elif event.type == 'content_block_delta' and hasattr(event.delta, 'partial_json'):
                            chunk = event.delta.partial_json
                            print(chunk, end='', flush=True)
                            if accumulated_tool_calls:
                                accumulated_tool_calls[-1]["input_json"] += chunk
                                
                    elif msg_type == 'done':
                        print("\n\n>>> STREAM END <<<\n", flush=True)
                        break
                    elif msg_type == 'error':
                        print(f"\n\n>>> ERROR: {data} <<<\n", flush=True)
                        raise data
                except queue.Empty:
                    # Timeout - check if we have partial tool calls
                    print("\n\n>>> STREAM TIMEOUT <<<\n", flush=True)
                    if accumulated_tool_calls:
                        # We have incomplete tool calls - this is the Azure truncation bug
                        print(f"[Timeout with {len(accumulated_tool_calls)} incomplete tool call(s)]")
                        for tc in accumulated_tool_calls:
                            print(f"  - {tc['name']}: {len(tc['input_json'])} chars (incomplete)")
                    raise TimeoutError("Stream timeout - Azure may be limiting large tool outputs. Try smaller file content.")
            
            thread.join(timeout=5)
            
            # Finalize tool calls
            final_tool_calls = []
            for tc in accumulated_tool_calls:
                final_tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["input_json"]
                ))
            
            # Return final message
            return MockMessage(
                content=accumulated_text, 
                role="assistant",
                tool_calls=final_tool_calls if final_tool_calls else None
            )
            
        except Exception as e:
            raise ValueError(f"Azure Anthropic Streaming Error: {str(e)}")
    
    async def _chat_openai_stream(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, on_token: Optional[Any] = None) -> Any:
        """Handle streaming chat with OpenAI models on Azure."""
        
        # Pre-process messages to convert generic image format to OpenAI format
        processed_messages = []
        
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                new_content = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image":
                        b64_data = part.get("data", "")
                        
                        if isinstance(b64_data, str) and b64_data.startswith('data:'):
                            new_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": b64_data
                                }
                            })
                        else:
                            mime_type = "image/png"
                            if isinstance(b64_data, str):
                                if b64_data.startswith("/9j/"): mime_type = "image/jpeg"
                                elif b64_data.startswith("R0lGOD"): mime_type = "image/gif"
                                elif b64_data.startswith("UklGR"): mime_type = "image/webp"
                            
                            new_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_data}"
                                }
                            })
                    else:
                        new_content.append(part)
                
                processed_messages.append({**msg, "content": new_content})
            else:
                processed_messages.append(msg)

        kwargs = {
            "model": self.model_name,
            "messages": processed_messages,
            "stream": True
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            stream = self.client.chat.completions.create(**kwargs)
            accumulated_content = ""
            accumulated_tool_calls_data = [] # List of dicts: {index, id, name, arguments}

            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # 1. Handle Content
                if delta.content:
                    content = delta.content
                    accumulated_content += content
                    if on_token:
                        await on_token(content)
                
                # 2. Handle Tool Calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        
                        # Ensure list is long enough
                        while len(accumulated_tool_calls_data) <= idx:
                            accumulated_tool_calls_data.append({
                                "id": "", 
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        # Append data
                        if tc.id:
                            accumulated_tool_calls_data[idx]["id"] += tc.id
                        
                        if tc.function:
                            if tc.function.name:
                                accumulated_tool_calls_data[idx]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                accumulated_tool_calls_data[idx]["function"]["arguments"] += tc.function.arguments
            
            # Construct Final Tool Calls
            final_tool_calls = None
            if accumulated_tool_calls_data:
                final_tool_calls = []
                for tc_data in accumulated_tool_calls_data:
                    # Only add if it looks complete
                    if tc_data["function"]["name"]:
                         final_tool_calls.append(ToolCall(
                             id=tc_data["id"],
                             name=tc_data["function"]["name"],
                             arguments=tc_data["function"]["arguments"]
                         ))

            # Use MockMessage which is already defined and compatible with Agent
            return MockMessage(
                content=accumulated_content, 
                role="assistant", 
                tool_calls=final_tool_calls
            )
            
        except Exception as e:
            error_msg = str(e)
            if "content management policy" in error_msg.lower():
                raise ValueError("Azure Content Filter triggered. Please refine your prompt.") from e
            raise e
    
    async def _chat_anthropic(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Handle chat with Anthropic Claude models on Azure using AnthropicFoundry SDK."""
        import asyncio
        from .utils import extract_content
        
        # Separate system message from other messages
        system_content = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                # Anthropic wants system as top-level param
                system_content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            else:
                # Parse content for potential multimodal (text + images)
                raw_content = msg.get("content", "")
                text_content, images = extract_content(raw_content)
                
                # Build content blocks for Claude API
                if images:
                    # Multimodal message with images
                    content_blocks = []
                    print(f"[AzureProvider] Found {len(images)} images in message")
                    
                    # Add images first (Claude recommends images before text)
                    for idx, img in enumerate(images):
                        # Ensure data is base64 string, not bytes
                        img_data = img["data"]
                        if isinstance(img_data, bytes):
                            img_data = base64.b64encode(img_data).decode('utf-8')
                        
                        media_type = img.get("mime_type") or "image/png"
                        print(f"[AzureProvider] Processing image {idx+1}: {media_type} (data len: {len(img_data) if img_data else 0})")
                        
                        content_blocks.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_data
                            }
                        })
                    
                    # Add text content after images
                    if text_content and text_content.strip():
                        content_blocks.append({
                            "type": "text",
                            "text": text_content
                        })
                    
                    chat_messages.append({
                        "role": msg["role"],
                        "content": content_blocks
                    })
                else:
                    # Text-only message
                    chat_messages.append({
                        "role": msg["role"],
                        "content": text_content if text_content else ""
                    })
        
        # Build kwargs for Anthropic API
        kwargs = {
            "model": self.model_name,
            "messages": chat_messages,
            "max_tokens": 16384
        }
        
        if system_content:
            kwargs["system"] = system_content
            
        # Convert and add tools if present
        if tools:
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append(self._convert_tool_to_anthropic(tool))
            kwargs["tools"] = anthropic_tools
        
        try:
            # AnthropicFoundry is sync, run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.messages.create(**kwargs)
            )
            
            # Extract content and tool calls
            text_content = ""
            tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    import json
                    # Create ToolCall compatible with Agent
                    tool_calls.append(ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=json.dumps(block.input)
                    ))
            
            # Return MockMessage compatible with agentry
            return MockMessage(content=text_content, role="assistant", tool_calls=tool_calls if tool_calls else None)
            
        except Exception as e:
            raise ValueError(f"Azure Anthropic Error: {str(e)}")
            
    def _convert_tool_to_anthropic(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAI tool schema to Anthropic format."""
        if tool_schema.get("type") != "function":
            return tool_schema
            
        func = tool_schema.get("function", {})
        return {
            "name": func.get("name"),
            "description": func.get("description"),
            "input_schema": func.get("parameters")
        }
    
    async def _chat_openai(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Handle chat with OpenAI models on Azure."""
        
        # Pre-process messages to convert generic image format to OpenAI format
        processed_messages = []
        
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                new_content = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image":
                        # Convert generic image to OpenAI image_url
                        b64_data = part.get("data", "")
                        
                        # Handle data URL prefix if present
                        if isinstance(b64_data, str) and b64_data.startswith('data:'):
                            # It's already a full data URL, use it directly
                            new_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": b64_data
                                }
                            })
                        else:
                            # It's raw base64 data, detect mime type and add prefix
                            mime_type = "image/png"
                            if isinstance(b64_data, str):
                                if b64_data.startswith("/9j/"): mime_type = "image/jpeg"
                                elif b64_data.startswith("R0lGOD"): mime_type = "image/gif"
                                elif b64_data.startswith("UklGR"): mime_type = "image/webp"
                            
                            new_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_data}"
                                }
                            })
                    else:
                        new_content.append(part)
                
                processed_messages.append({**msg, "content": new_content})
            else:
                processed_messages.append(msg)

        kwargs = {
            "model": self.model_name,
            "messages": processed_messages,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except Exception as e:
            error_msg = str(e)
            if "content management policy" in error_msg.lower():
                raise ValueError("Azure Content Filter triggered. Please refine your prompt.") from e
            raise e
    
    def get_model_name(self) -> str:
        return self.model_name



class Function:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class ToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = Function(name, arguments)
        self.type = "function"

class MockMessage:
    """Mock message class to mimic OpenAI response structure."""
    def __init__(self, content: str, role: str = "assistant", tool_calls: List[ToolCall] = None):
        self.content = content
        self.role = role
        self.tool_calls = tool_calls

