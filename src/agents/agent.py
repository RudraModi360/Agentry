import json
import asyncio
from typing import List, Dict, Any, Callable, Awaitable, Optional
from providers.base import LLMProvider
from tools import ALL_TOOL_SCHEMAS, DANGEROUS_TOOLS, APPROVAL_REQUIRED_TOOLS, execute_tool

class Agent:
    def __init__(
        self,
        provider: LLMProvider,
        system_message: str = "You are a helpful AI assistant.",
        debug: bool = False
    ):
        self.provider = provider
        self.system_message = system_message
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": self.system_message}]
        self.debug = debug
        
        # Callbacks
        self.on_tool_start: Callable[[str, Dict], None] = None
        self.on_tool_end: Callable[[str, Any], None] = None
        self.on_tool_approval: Callable[[str, Dict], Awaitable[bool]] = None
        self.on_final_message: Callable[[str], None] = None

    def set_tool_callbacks(
        self,
        on_tool_start: Callable[[str, Dict], None] = None,
        on_tool_end: Callable[[str, Any], None] = None,
        on_tool_approval: Callable[[str, Dict], Awaitable[bool]] = None,
        on_final_message: Callable[[str], None] = None,
    ):
        self.on_tool_start = on_tool_start
        self.on_tool_end = on_tool_end
        self.on_tool_approval = on_tool_approval
        self.on_final_message = on_final_message

    def clear_history(self):
        self.messages = [msg for msg in self.messages if msg.get('role') == 'system']

    async def chat(self, user_input: str):
        self.messages.append({"role": "user", "content": user_input})
        
        max_iterations = 20
        for _ in range(max_iterations):
            # Call the provider
            # Note: Providers might return different structures, but we expect a normalized message object or dict
            # with 'content' and optionally 'tool_calls'.
            # Our providers currently return the raw object from the library (e.g. Groq message, Ollama dict).
            # We need to normalize this here or in the provider.
            # For simplicity, let's assume the provider returns a dict or object with attributes we can access.
            
            response_message = await self.provider.chat(self.messages, tools=ALL_TOOL_SCHEMAS)
            
            # Normalize response_message
            content = None
            tool_calls = None
            
            if isinstance(response_message, dict): # Ollama style
                content = response_message.get('content')
                tool_calls = response_message.get('tool_calls')
                self.messages.append(response_message)
            else: # Groq/OpenAI object style
                content = response_message.content
                tool_calls = response_message.tool_calls
                # We need to convert object to dict for history if we are mixing providers, 
                # or ensure the provider handles the history format it expects.
                # For now, we'll append the object, but this might break if we switch providers mid-chat.
                # Better to convert to dict.
                msg_dict = {"role": "assistant", "content": content}
                if tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": getattr(tc, 'id', None),
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in tool_calls
                    ]
                self.messages.append(msg_dict)

            if not tool_calls:
                if self.on_final_message:
                    self.on_final_message(content)
                return

            if self.debug:
                print(f"Tool Calls: {tool_calls}")

            for tool_call in tool_calls:
                # Handle different tool call structures (dict vs object)
                if isinstance(tool_call, dict):
                    tool_name = tool_call['function']['name']
                    tool_args = tool_call['function']['arguments']
                    tool_call_id = None # Ollama might not have ID
                else:
                    tool_name = tool_call.function.name
                    if isinstance(tool_call.function.arguments, str):
                        tool_args = json.loads(tool_call.function.arguments)
                    else:
                        tool_args = tool_call.function.arguments
                    tool_call_id = getattr(tool_call, 'id', None)

                if self.on_tool_start:
                    self.on_tool_start(tool_name, tool_args)

                needs_approval = tool_name in DANGEROUS_TOOLS or tool_name in APPROVAL_REQUIRED_TOOLS

                if needs_approval and self.on_tool_approval:
                    approved = await self.on_tool_approval(tool_name, tool_args)
                    if not approved:
                        tool_result = {"success": False, "error": "Tool execution denied by user."}
                    else:
                        tool_result = execute_tool(tool_name, tool_args)
                else:
                    tool_result = execute_tool(tool_name, tool_args)

                if self.on_tool_end:
                    self.on_tool_end(tool_name, tool_result)

                # Append tool result to history
                tool_msg = {
                    "role": "tool",
                    "content": json.dumps(tool_result),
                }
                if tool_call_id:
                    tool_msg["tool_call_id"] = tool_call_id
                else:
                    # For Ollama (if not using ID), it often expects 'name' or 'tool_call_name' depending on version.
                    # Original code used 'tool_call_name'.
                    tool_msg["name"] = tool_name
                    tool_msg["tool_call_name"] = tool_name 
                
                self.messages.append(tool_msg)

        if self.on_final_message:
            self.on_final_message("Max tool iterations reached.")
