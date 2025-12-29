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
        if "/anthropic" not in base_url.lower():
            base_url = f"{base_url}/anthropic"
        
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
    
    async def _chat_anthropic(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Handle chat with Anthropic Claude models on Azure using AnthropicFoundry SDK."""
        import asyncio
        import json
        from .utils import extract_content
        
        # --- Helper: Convert Tools ---
        anthropic_tools = []
        if tools:
            for t in tools:
                if t.get("type") == "function":
                    func = t.get("function", {})
                    anthropic_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description"),
                        "input_schema": func.get("parameters")
                    })

        # --- Helper: Convert Messages ---
        anthropic_messages = []
        system_content = None
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "system":
                # System message
                system_content = content if isinstance(content, str) else str(content)
                continue
                
            if role == "tool":
                # Convert OpenAI "tool" role -> Anthropic "user" role with "tool_result" content
                tool_call_id = msg.get("tool_call_id")
                tool_content = content
                
                # Check if we can merge with previous user message? 
                # Anthropic allows sequence of user messages, but usually prefers alternating.
                # Ideally, a tool_result follows an assistant tool_use.
                # We'll create a new user message for the result.
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": str(tool_content)
                    }]
                })
                continue
            
            if role == "assistant":
                # Check for tool_calls
                tool_calls = msg.get("tool_calls")
                assistant_content_blocks = []
                
                # specific text content?
                if content:
                    # Strip trailing whitespace to avoid Azure Anthropic validation errors
                    text_content = str(content).strip()
                    if text_content:  # Only add if non-empty after stripping
                        assistant_content_blocks.append({
                            "type": "text",
                            "text": text_content
                        })
                
                if tool_calls:
                    print(f"[AzureProvider] Processing {len(tool_calls)} tool calls")
                    for tc in tool_calls:
                        # Debug info
                        # print(f"[AzureProvider] Tool Call: {tc}")
                        
                        func = tc.get("function", {})
                        try:
                            args = json.loads(func.get("arguments", "{}"))
                        except:
                            args = {}
                        
                        # Ensure ID is present and string
                        tc_id = tc.get("id")
                        if not tc_id:
                            print("[AzureProvider] Warning: Tool call missing ID, generating one")
                            import uuid
                            tc_id = f"call_{str(uuid.uuid4())[:8]}"
                        else:
                            tc_id = str(tc_id)
                        
                        assistant_content_blocks.append({
                            "type": "tool_use",
                            "id": tc_id,
                            "name": func.get("name"),
                            "input": args
                        })
                
                if assistant_content_blocks:
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": assistant_content_blocks
                    })
                continue
            
            # User messages (generic)
            # Parse content for potential multimodal (text + images)
            raw_content = content or ""
            text_content, images = extract_content(raw_content)
            
            # Build content blocks for Claude API
            user_blocks = []
            
            if images:
                print(f"[AzureProvider] Found {len(images)} images in message")
                for idx, img in enumerate(images):
                    img_data = img["data"]
                    if isinstance(img_data, bytes):
                        img_data = base64.b64encode(img_data).decode('utf-8')
                    
                    media_type = img.get("mime_type") or "image/png"
                    user_blocks.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data
                        }
                    })
            
            if text_content and text_content.strip():
                user_blocks.append({
                    "type": "text",
                    "text": text_content
                })
            elif not user_blocks:
                # Empty message?
                user_blocks.append({"type": "text", "text": " "})
                
            anthropic_messages.append({
                "role": msg.get("role", "user"),
                "content": user_blocks
            })

        # --- Execute Call ---
        kwargs = {
            "model": self.model_name,
            "messages": anthropic_messages,
            "max_tokens": 4096
        }
        
        if system_content:
            kwargs["system"] = system_content
            
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools
        
        try:
            # AnthropicFoundry is sync, run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.messages.create(**kwargs)
            )
            
            # --- Convert Response to OpenAI format ---
            # The response is an Anthropic Message object
            
            final_text = ""
            final_tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
                elif block.type == "tool_use":
                    final_tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input)
                        }
                    })
            
            # Strip trailing whitespace to prevent validation errors in subsequent API calls
            # This is critical because Azure Anthropic rejects messages ending with whitespace
            final_text = final_text.rstrip() if final_text else ""
            
            # Return Object mimicking OpenAI Message
            msg_obj = MockMessage(content=final_text, role="assistant")
            if final_tool_calls:
                msg_obj.tool_calls = final_tool_calls
            
            return msg_obj
            
        except Exception as e:
            # Log full error for debugging
             print(f"Azure Anthropic Error Details: {str(e)}")
             raise ValueError(f"Azure Anthropic Error: {str(e)}")
    
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


class MockMessage:
    """Mock message class to mimic OpenAI response structure."""
    def __init__(self, content: str, role: str = "assistant"):
        self.content = content
        self.role = role
        self.tool_calls = None
