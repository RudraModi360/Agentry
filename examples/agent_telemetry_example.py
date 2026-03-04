"""
Real-world example: SmartAgent with comprehensive telemetry tracking.
Shows how to integrate telemetry into your agent implementations.
"""

import json
import time
from typing import Optional, List, Dict, Any
from logicore.telemetry import TelemetryTracker, TokenBreakdown


class SmartAgentWithTelemetry:
    """Example SmartAgent implementation with full telemetry support."""
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        provider: str = "openai",
        telemetry_tracker: Optional[TelemetryTracker] = None
    ):
        self.model_name = model_name
        self.provider = provider
        self.telemetry = telemetry_tracker or TelemetryTracker(enabled=True)
        
        # Agent components
        self.system_prompt = self._get_system_prompt()
        self.tools = self._get_tools()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are a helpful AI assistant. You can help with:
- Answering questions
- Writing and editing content
- Code assistance
- Data analysis
- And much more

Always be clear, accurate, and helpful."""
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get the tools available to the agent."""
        return [
            {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "query": "string"
                }
            },
            {
                "name": "analyze_data",
                "description": "Analyze numerical data",
                "parameters": {
                    "data": "array",
                    "operation": "string"
                }
            },
            {
                "name": "code_execution",
                "description": "Execute Python code",
                "parameters": {
                    "code": "string"
                }
            }
        ]
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        if not text:
            return 0
        # Rough approximation: 1 token ≈ 1.3 words
        return int(len(text.split()) * 1.3)
    
    def _create_token_breakdown(
        self,
        response_data: Dict[str, Any]
    ) -> TokenBreakdown:
        """Create a TokenBreakdown from response data."""
        system_tokens = self._estimate_tokens(self.system_prompt)
        tool_tokens = self._estimate_tokens(json.dumps(self.tools))
        message_tokens = response_data.get("input_message_tokens", 0)
        tool_result_tokens = response_data.get("tool_result_tokens", 0)
        file_tokens = response_data.get("file_tokens", 0)
        
        return TokenBreakdown(
            system_instructions=system_tokens,
            tool_definitions=tool_tokens,
            messages=message_tokens,
            tool_results=tool_result_tokens,
            file_content=file_tokens,
            other=0
        )
    
    async def chat(
        self,
        session_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main chat method with telemetry tracking.
        
        Args:
            session_id: Unique session identifier for telemetry
            user_message: User's input message
            conversation_history: Previous messages in conversation
            files: Optional files to include in context
        
        Returns:
            Response dict with agent output
        """
        start_time = time.time()
        
        try:
            # Prepare request
            request_data = self._prepare_request(
                user_message,
                conversation_history,
                files
            )
            
            # Mock LLM call (replace with actual provider call)
            response_data = await self._call_llm(request_data)
            
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            
            # Create token breakdown
            breakdown = self._create_token_breakdown(response_data)
            
            # Record in telemetry
            self.telemetry.record_request(
                session_id=session_id,
                input_tokens=response_data.get("input_tokens", 0),
                output_tokens=response_data.get("output_tokens", 0),
                model=self.model_name,
                provider=self.provider,
                duration_ms=duration_ms,
                token_breakdown=breakdown,
                tool_calls=len(response_data.get("tool_calls", [])),
                error=None
            )
            
            return {
                "success": True,
                "response": response_data.get("text", ""),
                "tool_calls": response_data.get("tool_calls", []),
                "telemetry": {
                    "tokens_used": breakdown.total,
                    "duration_ms": duration_ms
                }
            }
        
        except Exception as e:
            # Record error in telemetry
            duration_ms = (time.time() - start_time) * 1000
            self.telemetry.record_request(
                session_id=session_id,
                model=self.model_name,
                provider=self.provider,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "telemetry": {
                    "duration_ms": duration_ms
                }
            }
    
    def _prepare_request(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Prepare the request for the LLM."""
        messages = []
        message_tokens = 0
        file_tokens = 0
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
            message_tokens += sum(
                self._estimate_tokens(msg.get("content", ""))
                for msg in conversation_history
            )
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        message_tokens += self._estimate_tokens(user_message)
        
        # Add files
        if files:
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        file_content = f.read()
                        file_tokens += self._estimate_tokens(file_content)
                        messages.append({
                            "role": "user",
                            "content": f"File: {file_path}\n{file_content}"
                        })
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
        
        return {
            "system": self.system_prompt,
            "messages": messages,
            "tools": self.tools,
            "input_message_tokens": message_tokens,
            "file_tokens": file_tokens,
        }
    
    async def _call_llm(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock LLM call. Replace with actual provider implementation.
        
        In production, call your actual LLM provider here:
        - OpenAI: openai.ChatCompletion.create()
        - Anthropic: anthropic.Anthropic().messages.create()
        - Groq: groq_client.chat.completions.create()
        - Etc.
        """
        # Simulate API response
        await asyncio.sleep(0.5)  # Simulate network latency
        
        return {
            "text": "This is a sample response from the LLM.",
            "input_tokens": 150,
            "output_tokens": 25,
            "tool_calls": [
                {"name": "search_web", "arguments": {"query": "example"}}
            ],
            "tool_result_tokens": 0,
        }
    
    def get_session_telemetry(self, session_id: str) -> Dict[str, Any]:
        """Get detailed telemetry for a session."""
        return self.telemetry.get_session_summary(session_id)
    
    def get_aggregate_telemetry(self) -> Dict[str, Any]:
        """Get aggregate telemetry across all sessions."""
        return self.telemetry.get_total_summary()


# ===================== USAGE EXAMPLES =====================

async def example_1_basic_usage():
    """Example 1: Basic chat with telemetry tracking."""
    print("\n=== Example 1: Basic Chat ===")
    
    agent = SmartAgentWithTelemetry()
    session_id = "user_001"
    
    # Chat with the agent
    response = await agent.chat(
        session_id=session_id,
        user_message="What is machine learning?"
    )
    
    print(f"Response: {response['response']}")
    print(f"Tokens Used: {response['telemetry']['tokens_used']}")
    print(f"Duration: {response['telemetry']['duration_ms']:.1f}ms")
    
    # Get and display telemetry
    telemetry = agent.get_session_telemetry(session_id)
    print(f"\nSession Telemetry:")
    print(f"  Total Tokens: {telemetry['tokens']['total']}")
    print(f"  Context Usage: {telemetry['context']['used_percent']}%")
    print(f"  Requests: {telemetry['requests']['total']}")


async def example_2_multi_turn_conversation():
    """Example 2: Multi-turn conversation tracking."""
    print("\n=== Example 2: Multi-Turn Conversation ===")
    
    agent = SmartAgentWithTelemetry()
    session_id = "user_002"
    conversation_history = []
    
    messages = [
        "What is Python?",
        "Tell me about decorators",
        "How do I use them in production code?",
    ]
    
    for message in messages:
        response = await agent.chat(
            session_id=session_id,
            user_message=message,
            conversation_history=conversation_history
        )
        
        # Add to history for next iteration
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response["response"]})
    
    # Get final telemetry
    telemetry = agent.get_session_telemetry(session_id)
    print(f"\nConversation Summary:")
    print(f"  Total Requests: {telemetry['requests']['total']}")
    print(f"  Total Tokens: {telemetry['tokens']['total']}")
    print(f"  Input Tokens: {telemetry['tokens']['input']}")
    print(f"  Output Tokens: {telemetry['tokens']['output']}")
    print(f"  Context Usage: {telemetry['context']['used_percent']}%")
    
    # Display token breakdown
    print(f"\nToken Breakdown:")
    breakdown = telemetry['token_breakdown']
    for category, percent in breakdown['percentages'].items():
        print(f"  {category}: {percent}%")


async def example_3_multiple_sessions():
    """Example 3: Track multiple concurrent sessions."""
    print("\n=== Example 3: Multiple Sessions ===")
    
    # Create shared telemetry tracker
    tracker = TelemetryTracker(enabled=True)
    
    # Create multiple agents (all using same tracker)
    agent1 = SmartAgentWithTelemetry(telemetry_tracker=tracker)
    agent2 = SmartAgentWithTelemetry(
        model_name="gpt-3.5-turbo",
        telemetry_tracker=tracker
    )
    
    # Run simultaneous requests
    import asyncio
    responses = await asyncio.gather(
        agent1.chat("session_user_1", "Hello from user 1"),
        agent2.chat("session_user_2", "Hello from user 2"),
    )
    
    # Get aggregate telemetry
    aggregate = tracker.get_total_summary()
    print(f"\nAggregate Telemetry:")
    print(f"  Total Sessions: {aggregate['total_sessions']}")
    print(f"  Total Requests: {aggregate['total_requests']}")
    print(f"  Total Tokens: {aggregate['total_tokens']}")
    print(f"  Models Used: {aggregate['models_used']}")
    print(f"  Providers Used: {aggregate['providers_used']}")


async def example_4_display_formatted_telemetry():
    """Example 4: Display formatted telemetry like the UI."""
    print("\n=== Example 4: Formatted Telemetry Display ===")
    
    agent = SmartAgentWithTelemetry()
    session_id = "session_display"
    
    # Generate some activity
    for i in range(3):
        await agent.chat(session_id=session_id, user_message=f"Question {i+1}")
    
    telemetry = agent.get_session_telemetry(session_id)
    
    # Display like the UI image
    context = telemetry['context']
    print(f"\n📊 Context Window")
    print(f"{context['used_tokens']}K / {context['window_size']}K tokens · {context['used_percent']}%")
    print("▓" * int(context['used_percent'] / 5) + "░" * (20 - int(context['used_percent'] / 5)))
    
    print(f"\n🔧 System")
    breakdown = telemetry['token_breakdown']
    print(f"  System Instructions: {breakdown['percentages'].get('system_instructions', 0)}%")
    print(f"  Tool Definitions: {breakdown['percentages'].get('tool_definitions', 0)}%")
    
    print(f"\n💬 User Context")
    print(f"  Messages: {breakdown['percentages'].get('messages', 0)}%")
    print(f"  Files: {breakdown['percentages'].get('file_content', 0)}%")
    print(f"  Tool Results: {breakdown['percentages'].get('tool_results', 0)}%")
    
    print(f"\n⚠️ Usage Warning")
    if context['used_percent'] > 90:
        print("Quality may decline as limit nears.")
    elif context['used_percent'] > 70:
        print("Context window is getting full.")
    else:
        print("Context window usage is healthy.")


if __name__ == "__main__":
    import asyncio
    
    print("SmartAgent Telemetry Examples")
    print("=" * 50)
    
    # Note: Add `import asyncio` at the top if not already present
    asyncio.run(example_1_basic_usage())
    asyncio.run(example_2_multi_turn_conversation())
    asyncio.run(example_3_multiple_sessions())
    asyncio.run(example_4_display_formatted_telemetry())
    
    print("\n" + "=" * 50)
    print("Examples completed! Check the telemetry API endpoints:")
    print("  GET  /api/telemetry/session/{session_id}")
    print("  GET  /api/telemetry/sessions")
    print("  GET  /api/telemetry/summary")
    print("  DELETE /api/telemetry/session/{session_id}")
