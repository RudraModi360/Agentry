from typing import Union
from .agent import Agent, AgentSession
from scratchy.providers.base import LLMProvider
from scratchy.config.prompts import get_system_prompt

class CopilotAgent(Agent):
    """
    A specialized Agent optimized for coding tasks (Copilot-like experience).
    It comes pre-loaded with filesystem and execution tools and a coding-focused system prompt.
    """
    
    def __init__(
        self, 
        llm: Union[LLMProvider, str] = "ollama",
        model: str = None,
        api_key: str = None,
        system_message: str = None,
        debug: bool = False
    ):
        super().__init__(
            llm=llm,
            model=model,
            api_key=api_key,
            system_message=system_message,
            role="engineer",
            debug=debug
        )
        
        # Auto-load tools useful for coding
        self.load_default_tools()
        
    async def explain_code(self, code: str) -> str:
        """Convenience method to explain a piece of code."""
        prompt = f"Please explain the following code concisely:\n\n```\n{code}\n```"
        return await self.chat(prompt)

    async def review_file(self, filepath: str) -> str:
        """Convenience method to review a file."""
        prompt = f"Please review the file '{filepath}' for potential bugs, improvements, and security issues."
        return await self.chat(prompt)

    async def discuss(self, user_input: str) -> str:
        """
        Conducts a general chat session (acting as a normal assistant).
        Uses a separate session ID 'general' to keep context separate from coding tasks.
        """
        session_id = "general"
        if session_id not in self.sessions:
            # Create session with General Agent prompt
            model_name = getattr(self.provider, "model_name", "Unknown")
            prompt = get_system_prompt(model_name, role="general")
            self.sessions[session_id] = AgentSession(session_id, prompt)
            
        return await self.chat(user_input, session_id=session_id)
