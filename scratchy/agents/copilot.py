from typing import Union
from .agent import Agent, AgentSession
from scratchy.providers.base import LLMProvider
from scratchy.config.prompts import get_system_prompt, get_copilot_prompt


class CopilotAgent(Agent):
    """
    A specialized Agent optimized for coding tasks (Copilot-like experience).
    
    Features:
    - Pre-loaded with filesystem and execution tools
    - Coding-focused Claude-style system prompt
    - Convenience methods for code explanation and review
    """
    
    def __init__(
        self, 
        llm: Union[LLMProvider, str] = "ollama",
        model: str = None,
        api_key: str = None,
        system_message: str = None,
        debug: bool = False
    ):
        # Use copilot-specific prompt if no custom message provided
        if not system_message:
            model_name = model or "Unknown Model"
            system_message = get_copilot_prompt(model_name)
        
        super().__init__(
            llm=llm,
            model=model,
            api_key=api_key,
            system_message=system_message,
            role="copilot",
            debug=debug
        )
        
        # Auto-load tools useful for coding
        self.load_default_tools()
        
    async def explain_code(self, code: str, language: str = None) -> str:
        """
        Convenience method to explain a piece of code.
        
        Args:
            code: The code to explain
            language: Optional language hint (e.g., 'python', 'javascript')
        """
        lang_tag = language or ""
        prompt = f"Please explain the following code concisely:\n\n```{lang_tag}\n{code}\n```"
        return await self.chat(prompt)

    async def review_file(self, filepath: str) -> str:
        """
        Convenience method to review a file for bugs and improvements.
        
        Args:
            filepath: Path to the file to review
        """
        prompt = f"Please review the file '{filepath}' for potential bugs, improvements, and security issues. Read the file first."
        return await self.chat(prompt)
    
    async def write_code(self, description: str, language: str = "python") -> str:
        """
        Convenience method to generate code based on a description.
        
        Args:
            description: What the code should do
            language: Target programming language
        """
        prompt = f"Write {language} code that: {description}"
        return await self.chat(prompt)
    
    async def fix_bug(self, code: str, error: str = None) -> str:
        """
        Convenience method to fix a bug in code.
        
        Args:
            code: The buggy code
            error: Optional error message or description of the issue
        """
        if error:
            prompt = f"Fix this bug. Error: {error}\n\nCode:\n```\n{code}\n```"
        else:
            prompt = f"Find and fix any bugs in this code:\n\n```\n{code}\n```"
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
