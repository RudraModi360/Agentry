import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from agentry.providers.base import LLMProvider
from agentry.agents.agent import Agent, AgentSession
from agentry.memory.project_memory import (
    ProjectMemory, ProjectContext, MemoryType, MemoryEntry,
    get_project_memory
)
from agentry.tools.agent_tools import (
    get_smart_agent_tools, get_smart_agent_tool_schemas,
    DateTimeTool, NotesTool, MemoryTool, SmartBashTool, ThinkTool
)
from agentry.config.prompts import get_system_prompt


class SmartAgentMode:
    """Agent operation modes."""
    SOLO = "solo"           # General chat, greater reasoning focus
    PROJECT = "project"     # Project-centered with context awareness


class SmartAgent(Agent):
    """
    A versatile AI Agent optimized for:
    - Simple to complex reasoning tasks
    - Project-based work with context memory
    - Solo chat with enhanced reasoning
    
    Key Features:
    - Pluggable project memory
    - Essential tools (web, bash, notes, datetime, memory)
    - Mode switching (project/solo)
    - Automatic learning capture
    """
    
    def __init__(
        self,
        llm: Union[LLMProvider, str] = "ollama",
        model: str = None,
        api_key: str = None,
        mode: str = SmartAgentMode.SOLO,
        project_id: str = None,
        debug: bool = False,
        max_iterations: int = 40,
        capabilities: Any = None
    ):
        # Initialize base agent
        super().__init__(
            llm=llm,
            model=model,
            api_key=api_key,
            system_message=None,  # Will be set based on mode
            role="general",
            debug=debug,
            max_iterations=max_iterations,
            capabilities=capabilities
        )
        
        # Smart Agent specific
        self.mode = mode
        self.project_id = project_id
        self.project_memory = get_project_memory()
        self.project_context: Optional[ProjectContext] = None
        
        # Load project context if in project mode
        if mode == SmartAgentMode.PROJECT and project_id:
            self.project_context = self.project_memory.get_project(project_id)
        
        # Set appropriate system message
        self._update_system_message()
        
        # Load Smart Agent tools
        self._load_smart_tools()
    
    def _update_system_message(self):
        """Update system message based on mode and project context."""
        model_name = getattr(self.provider, "model_name", "Unknown")
        
        if self.mode == SmartAgentMode.PROJECT and self.project_context:
            self.default_system_message = self._get_project_system_prompt(model_name)
        else:
            self.default_system_message = self._get_solo_system_prompt(model_name)
    
    def _get_solo_system_prompt(self, model_name: str) -> str:
        """Get system prompt for solo chat mode - Claude-style sophisticated prompt."""
        return f"""You are SmartAgent, an AI assistant created by the Agentry team. You are powered by {model_name}.

<identity>
You are a highly capable, thoughtful AI assistant designed for general-purpose reasoning and task completion. You combine strong analytical abilities with practical tool access to help users effectively.

Your core traits:
- **Thoughtful**: You think carefully before responding, considering multiple angles
- **Honest**: You acknowledge uncertainty and limitations rather than guessing
- **Helpful**: You genuinely try to understand and address what users need
- **Adaptive**: You match your communication style to the user's preferences
</identity>

<tools>
You have access to 6 tools. Use them judiciously:

1. **web_search** - Search the internet for current information
   - Use when: You need facts, current events, or information you don't have
   - Don't use when: The question is about reasoning, opinions, or you already know the answer

2. **image_search** - Find and display images inline in your response
   - Use when: The topic is visual (architecture, art, animals, places, diagrams, charts, products)
   - Use when: Showing an image would significantly enhance understanding
   - Use when: User explicitly or implicitly wants to see something visually
   - Don't use when: The topic is abstract, conceptual, or purely text-based
   - Returns: Images rendered inline in your response (Perplexity/ChatGPT style)

3. **memory** - Store and retrieve learnings, patterns, and approaches
   - Use when: You discover something valuable worth remembering, or need to recall past context
   - Actions: store (save new), search (find relevant), list (show recent), export (get all)

4. **notes** - Personal note-taking for temporary information
   - Use when: You need to track information within a session, make quick reminders
   - Actions: add, list, search, get, delete

5. **datetime** - Get current date and time
   - Use when: User asks about time, or you need to timestamp something

6. **bash** - Execute shell commands
   - Use when: User needs system operations, file manipulation, or command execution
   - Always explain what a command will do before running potentially impactful ones
</tools>

<thinking_approach>
When presented with a task or question:

1. **Parse the request**: What is the user actually asking for? What's the underlying need?

2. **Assess your knowledge**: Can you answer this directly, or do you need tools?
   - If confident in your knowledge → respond directly
   - If uncertain or needs current info → use web_search
   - If it involves system operations → use bash

3. **Consider the scope**: Is this a simple question or a complex multi-step task?
   - Simple → give a direct, concise answer
   - Complex → break it down, explain your approach, proceed step by step

4. **Maintain context**: Remember what happened earlier in the conversation. Use the memory tool to capture important insights for future reference.
</thinking_approach>

<communication_style>
- **Be direct**: Lead with the answer or action, not preamble
- **Be concise**: Respect the user's time; don't over-explain simple things
- **Be thorough**: For complex topics, provide comprehensive coverage
- **Use structure**: Lists, headers, and formatting help readability
- **Match tone**: Mirror the user's formality level and communication style
- **Show your work**: For reasoning tasks, explain your thought process
</communication_style>

<important_guidelines>
1. **Accuracy over speed**: Take time to get things right. It's better to say "I'm not sure" than to give wrong information.

2. **Clarify ambiguity**: If a request is unclear, ask a targeted clarifying question rather than guessing.

3. **Admit limitations**: Be upfront about what you can't do or don't know.

4. **Be safe with bash**: When executing commands, especially ones that modify the system, explain what you're doing and why.

5. **Learn and remember**: Use the memory tool to capture valuable patterns and insights that could help in future interactions.

6. **Stay on task**: Focus on what the user needs. Avoid tangents unless they add value.
</important_guidelines>

<current_context>
- Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Working directory: {__import__('os').getcwd()}
- Session: Active
</current_context>

You are ready to help. Respond thoughtfully and effectively.
"""
    
    def _get_project_system_prompt(self, model_name: str) -> str:
        """Get system prompt for project mode - Claude-style context-aware."""
        project = self.project_context
        
        env_section = ""
        if project.environment:
            env_items = "\n".join([f"  - {k}: {v}" for k, v in project.environment.items()])
            env_section = f"\nEnvironment:\n{env_items}"
        
        files_section = ""
        if project.key_files:
            files_items = "\n".join([f"  - {f}" for f in project.key_files])
            files_section = f"\nKey Files:\n{files_items}"
        
        focus_section = ""
        if project.current_focus:
            focus_section = f"\nCurrent Focus: {project.current_focus}"
        
        return f"""You are SmartAgent, an AI assistant created by the Agentry team, operating in Project Mode. You are powered by {model_name}.

<project_context>
Project: {project.title}
Goal: {project.goal}{env_section}{files_section}{focus_section}
</project_context>

<identity>
You are a focused, context-aware AI assistant dedicated to helping with this specific project. You maintain continuity across conversations and build upon previous work.

Your approach in project mode:
- **Project-First**: Every response considers the project's goal and constraints
- **Continuous**: You remember and build on previous interactions
- **Proactive**: You anticipate needs and capture learnings automatically
- **Efficient**: You stay focused on what moves the project forward
</identity>

<tools>
You have access to exactly 5 tools:

1. **web_search** - Research for the project
   - Use for: Finding documentation, best practices, solutions to project challenges

2. **memory** - Project knowledge management (critical for project mode)
   - **store**: Save learnings, approaches, and key decisions with project_id="{project.project_id}"
   - **search**: Find relevant past insights before tackling challenges
   - **list**: Review what you've learned about this project
   - Memory types: approach, learning, key_step, pattern, decision

3. **notes** - Quick project notes and temporary tracking

4. **datetime** - Time-related operations

5. **bash** - Execute commands for the project
</tools>

<project_workflow>
When helping with this project:

1. **Context First**: Before diving in, consider what you already know about this project. Search memory if needed.

2. **Stay Aligned**: Ensure your suggestions fit the project's goal, environment, and established patterns.

3. **Capture Value**: When you discover something useful (a working approach, a key decision, a pattern), store it in memory for future reference.

4. **Build Incrementally**: Reference and build upon previous work rather than starting fresh.

5. **Ask Smart Questions**: If something is unclear, ask about project-specific conventions or constraints.
</project_workflow>

<memory_protocol>
Storing insights:
- Use memory tool with action="store", project_id="{project.project_id}"
- Choose type: "approach" (how-to), "learning" (insight), "key_step" (important action), "pattern" (reusable template), "decision" (choice made)

Before tackling challenges:
- Search memory first: action="search" with relevant query
- Apply what worked before
</memory_protocol>

<communication_style>
- Be direct and action-oriented
- Reference project context in your responses
- Explain how suggestions align with project goals
- Note when you're storing something to memory
- Keep the project moving forward
</communication_style>

<current_context>
- Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Working directory: {__import__('os').getcwd()}
- Project: {project.title} ({project.project_id})
- Mode: Project-focused
</current_context>

You are ready to help with {project.title}. Focus on the project goal and build on what you know.
"""
    
    def _load_smart_tools(self):
        """Load only essential Smart Agent tools - lean and focused."""
        # DO NOT load default tools - SmartAgent is lean by design
        # Now loading 6 tools:
        # 1. web_search, 2. image_search, 3. memory, 4. notes, 5. datetime, 6. bash
        
        # Get Smart Agent specific tools
        smart_tools = get_smart_agent_tools()  # datetime, notes, memory, bash, think
        
        for tool in smart_tools:
            # Skip 'think' tool - not in the required toolkit
            if tool.name == 'think':
                continue
            self.internal_tools.append(tool.schema)
            self.custom_tool_executors[tool.name] = tool.run
        
        # Add web_search from web tools
        from agentry.tools.web import WebSearchTool, ImageSearchTool
        web_tool = WebSearchTool()
        self.internal_tools.append(web_tool.schema)
        self.custom_tool_executors[web_tool.name] = web_tool.run
        
        # Add image_search tool for inline image responses
        image_tool = ImageSearchTool()
        self.internal_tools.append(image_tool.schema)
        self.custom_tool_executors[image_tool.name] = image_tool.run
        
        # IMPORTANT: Mark that tools are loaded and supported
        self.supports_tools = True
        
        if self.debug:
            tool_names = [t.get("function", {}).get("name") for t in self.internal_tools]
            print(f"[SmartAgent] Loaded tools: {tool_names}")
    
    def set_mode(self, mode: str, project_id: str = None):
        """Switch agent mode."""
        self.mode = mode
        
        if mode == SmartAgentMode.PROJECT:
            if project_id:
                self.project_id = project_id
                self.project_context = self.project_memory.get_project(project_id)
            elif self.project_id:
                self.project_context = self.project_memory.get_project(self.project_id)
        else:
            self.project_context = None
        
        self._update_system_message()
        
        # Update all active sessions with new system message
        for session in self.sessions.values():
            if session.messages and session.messages[0]['role'] == 'system':
                session.messages[0]['content'] = self.default_system_message
    
    def create_project(self, project_id: str, title: str, goal: str = "",
                       environment: Dict[str, str] = None,
                       key_files: List[str] = None) -> ProjectContext:
        """Create a new project and optionally switch to project mode."""
        project = self.project_memory.create_project(
            project_id=project_id,
            title=title,
            goal=goal,
            environment=environment,
            key_files=key_files
        )
        
        if self.debug:
            print(f"[SmartAgent] Created project: {title} ({project_id})")
        
        return project
    
    def switch_to_project(self, project_id: str) -> Optional[ProjectContext]:
        """Switch to a specific project."""
        project = self.project_memory.get_project(project_id)
        if project:
            self.project_id = project_id
            self.project_context = project
            self.set_mode(SmartAgentMode.PROJECT, project_id)
            return project
        return None
    
    def switch_to_solo(self):
        """Switch to solo chat mode."""
        self.set_mode(SmartAgentMode.SOLO)
    
    def get_project_context_for_llm(self) -> str:
        """Get formatted project context for LLM injection."""
        if not self.project_id:
            return ""
        return self.project_memory.export_project_context(self.project_id)
    
    def list_projects(self) -> List[ProjectContext]:
        """List all available projects."""
        return self.project_memory.list_projects()
    
    # --- Enhanced Chat with Memory and Learning ---
    
    async def chat(self, user_input: Union[str, List[Dict[str, Any]]], 
                   session_id: str = "default") -> str:
        """
        Enhanced chat with automatic learning capture.
        """
        # Get project memories if in project mode
        if self.mode == SmartAgentMode.PROJECT and self.project_id:
            # Inject project context into session
            session = self.get_session(session_id)
            project_context = self.get_project_context_for_llm()
            
            if project_context and session.messages:
                # Update system message with project context
                if session.messages[0]['role'] == 'system':
                    base = self.default_system_message
                    session.messages[0]['content'] = base + "\n\n" + project_context
        
        # Call parent chat
        response = await super().chat(user_input, session_id)
        
        # Auto-capture significant learnings (can be enhanced with LLM-based extraction)
        # This is a simple heuristic - could use LLM to identify learnings
        if self.mode == SmartAgentMode.PROJECT and response:
            await self._maybe_capture_learning(user_input, response)
        
        return response
    
    async def _maybe_capture_learning(self, user_input: str, response: str):
        """
        Heuristically capture learnings from the conversation.
        This is a simple implementation - could be enhanced with LLM-based extraction.
        """
        # Check for patterns that indicate learnings
        learning_indicators = [
            "the solution is", "the fix is", "solved by", "the approach is",
            "remember to", "note that", "important:", "key insight",
            "best practice", "the pattern is", "always use", "never use"
        ]
        
        response_lower = response.lower()
        for indicator in learning_indicators:
            if indicator in response_lower:
                # Found a potential learning - store it
                try:
                    # Extract a snippet around the indicator
                    idx = response_lower.find(indicator)
                    start = max(0, idx - 50)
                    end = min(len(response), idx + 200)
                    snippet = response[start:end].strip()
                    
                    # Store as learning
                    self.project_memory.add_memory(
                        memory_type=MemoryType.LEARNING,
                        title=f"Learning from conversation",
                        content=snippet,
                        tags=["auto-captured"],
                        project_id=self.project_id
                    )
                    
                    if self.debug:
                        print(f"[SmartAgent] Auto-captured learning: {snippet[:50]}...")
                    
                    break  # Only capture one learning per response
                except Exception as e:
                    if self.debug:
                        print(f"[SmartAgent] Failed to capture learning: {e}")
    
    # --- Convenience Methods ---
    
    async def reason(self, problem: str, session_id: str = "default") -> str:
        """
        Explicitly request step-by-step reasoning for a problem.
        """
        prompt = f"""Please think through this problem step by step using the 'think' tool:

{problem}

After reasoning, provide your conclusion and solution."""
        
        return await self.chat(prompt, session_id)
    
    async def remember(self, memory_type: str, title: str, content: str,
                       tags: List[str] = None) -> str:
        """
        Store a memory directly.
        """
        mem_type = MemoryType(memory_type)
        entry = self.project_memory.add_memory(
            memory_type=mem_type,
            title=title,
            content=content,
            tags=tags,
            project_id=self.project_id if self.mode == SmartAgentMode.PROJECT else None
        )
        return f"Stored memory: [{mem_type.value}] {title} (ID: {entry.id})"
    
    async def recall(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Search memories.
        """
        return self.project_memory.search_memories(
            query=query,
            project_id=self.project_id if self.mode == SmartAgentMode.PROJECT else None,
            limit=limit
        )
    
    def status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "mode": self.mode,
            "project_id": self.project_id,
            "project_title": self.project_context.title if self.project_context else None,
            "model": getattr(self.provider, "model_name", "Unknown"),
            "tools_loaded": len(self.internal_tools),
            "sessions_active": len(self.sessions),
            "memory_entries": len(self.project_memory.get_memories(
                project_id=self.project_id, 
                limit=1000
            )) if self.project_id else 0
        }
