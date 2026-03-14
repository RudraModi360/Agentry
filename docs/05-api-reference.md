# API Reference: Complete Class & Method Documentation

This section documents **every** public class, method, parameter, and field in Logicore following framework documentation standards.

---

## Agent Classes

### **Agent**

**Description:** Full-featured agent with all configuration options. Primary class for production use.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm` | Union[LLMProvider, str] | `"ollama"` | LLM provider. Can be string ("openai", "groq", "azure", "gemini", "ollama") or custom LLMProvider instance |
| `model` | str | None | Model name/identifier (e.g., "gpt-4", "mixtral-8x7b", "llama3.2:3b"). Auto-detected if None |
| `api_key` | str | None | API key for cloud providers. Read from environment if None |
| `endpoint` | str | None | Custom endpoint URL. Required for Azure, optional for self-hosted |
| `system_message` | str | None | Custom system prompt. Auto-generated based on role if None |
| `role` | str | `"general"` | Role for auto-generated prompt: "general", "developer", "data_analyst", "researcher" |
| `memory` | bool | `False` | Enable persistent memory across sessions using ProjectMemory |
| `context_compression` | bool | `False` | Auto-compress context when approaching token limits |
| `tools` | list | `[]` | List of tools to register. Accepts functions, BaseTool instances, or tool dicts |
| `capabilities` | ModelCapabilities | None | Model capability flags (auto-detected). Override if detection fails |
| `skills` | list | None | List of Skill objects to load at initialization |
| `workspace_root` | str | None | Root directory for file operations. Restricts tool access to subtree |
| `max_iterations` | int | `40` | Maximum tool-calling loops per chat() call. Prevents infinite loops |
| `telemetry` | bool | `False` | Enable token counting and usage metrics |
| `debug` | bool | `False` | Enable detailed logging for debugging |

**Usage Example:**

```python
from logicore.agents import Agent

# Create production-grade agent with all features
agent = Agent(
    llm="openai",
    model="gpt-4",
    api_key="sk-...",
    system_message="You are a code review expert. Be thorough and constructive.",
    memory=True,                  # Remember across conversations
    context_compression=True,     # Auto-manage long chats
    max_iterations=10,
    telemetry=True,              # Track token usage
    debug=False
)

# Chat
response = await agent.chat("Review this Python code")
```

**Core Methods:**

```python
# Chat interface
async def chat(
    message: str,
    stream: bool = False
) -> str:
    """Send message and get response. Returns response text."""

# Session management
def create_session(session_id: str = None) -> AgentSession:
    """Create new session."""

def get_session(session_id: str = None) -> AgentSession:
    """Get or create session."""

def clear_session(session_id: str = None, keep_system: bool = True) -> None:
    """Clear session messages."""

def get_conversation_history(session_id: str = None) -> List[Dict]:
    """Get all messages in session as [{"role": ..., "content": ...}, ...]"""

# Tool management
def register_tool_from_function(
    func: Callable,
    name: str = None,
    description: str = None
) -> None:
    """Register Python function as tool. Name/description auto-extracted if None."""

def register_tool(tool: BaseTool) -> None:
    """Register pre-built BaseTool instance."""

def disable_tool(tool_name: str) -> None:
    """Disable a specific tool by name."""

def get_available_tools() -> List[Dict]:
    """List all registered tools with schemas."""

# Skill management
def load_skill(skill: Skill) -> None:
    """Load single skill."""

def load_skills(skill_list: List[Skill]) -> None:
    """Load multiple skills at once."""

# Callbacks
def set_callback(event: str, callback: Callable) -> None:
    """Register callback for event: 'on_tool_start', 'on_tool_end', 'on_tool_approval', 'on_final_message'"""

# State inspection
def get_provider_info() -> Dict:
    """Get current provider details: {'name': 'openai', 'model': 'gpt-4', ...}"""

def get_memory_stats() -> Dict:
    """Get memory statistics: {'total_memories': 150, 'storage_size_mb': 2.5}"""

def get_telemetry() -> Dict:
    """Get usage metrics (if telemetry=True): {'total_tokens': 5000, 'sessions': 3}"""

def export_session(path: str) -> None:
    """Save current session to JSON file."""

def import_session(path: str) -> None:
    """Load session from JSON file."""
```

---

### **BasicAgent**

**Description:** Simplified wrapper around Agent with sensible defaults. Best for getting started and rapid prototyping.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | `"Assistant"` | Agent name/identity |
| `description` | str | `None` | Agent description for context |
| `provider` | str | `"ollama"` | LLM provider: "ollama", "openai", "groq", "azure", "gemini" |
| `model` | str | None | Model name. Auto-detected if None |
| `api_key` | str | None | API key. Read from environment if None |
| `tools` | List[Union[Callable, BaseTool]] | None | Tools to register at init |
| `skills` | list | None | Skills to load at init |
| `system_prompt` | str | None | Custom system prompt |
| `memory_enabled` | bool | `True` | Enable memory (ProjectMemory) |
| `max_iterations` | int | `20` | Max tool-calling loops |
| `debug` | bool | `False` | Enable logging |
| `telemetry` | bool | `False` | Enable metrics |
| `workspace_root` | str | None | Root directory for file operations |

**Usage Example:**

```python
from logicore.agents import BasicAgent

def calculate(expr: str) -> str:
    """Calculate math expression."""
    return str(eval(expr))

agent = BasicAgent(
    name="CalculatorBot",
    provider="groq",
    tools=[calculate],
    memory_enabled=True
)

response = agent.chat("What is 5 * 3 + 2?")
```

**When to Use:**
- ✅ Getting started
- ✅ Simple chatbots
- ✅ Prototyping
- ❌ Complex production systems (use `Agent` instead)

---

### **CopilotAgent**

**Description:** Pre-configured agent optimized for coding tasks. Includes file operations, code execution, and git tools.

**Parameters:**

All **Agent** parameters, plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_web_tools` | bool | `True` | Include web search and fetch tools |
| `include_git_tools` | bool | `True` | Include git operation tools |
| `sandbox_code` | bool | `True` | Run code in isolated process |

**Built-in Tools:** File operations, code execution, git commands, web tools (optional)

**Usage Example:**

```python
from logicore.agents import CopilotAgent

agent = CopilotAgent(
    provider="openai",
    model="gpt-4",
    include_web_tools=True
)

response = agent.chat("Review my latest commit and suggest improvements")
```

---

### **MCPAgent**

**Description:** Enterprise-scale agent for 100+ tools. Uses Model Context Protocol (MCP) servers for tool discovery.

**Parameters:**

All **Agent** parameters, plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mcp_config_path` | str | `"mcp.json"` | Path to MCP server configuration |
| `tool_search_enabled` | bool | `True` | Enable deferred tool loading |
| `max_tools_per_request` | int | `10` | Limit tools shown per LLM request |

**MCP Config Format:**

```json
{
  "mcpServers": {
    "file_tools": {
      "command": "python",
      "args": ["-m", "file_tools_server"]
    },
    "data_tools": {
      "command": "node",
      "args": ["data_tools/server.js"],
      "env": {"DATABASE_URL": "postgresql://..."}
    }
  }
}
```

---

### **SmartAgent**

**Description:** Advanced conversational agent with intelligent memory management, real-time awareness, and temporal context judgment. Optimized for both solo chat and project-based work with automatic context verification.

**Purpose:** 
- **Solo Mode**: General-purpose chat with web search intelligence and current events awareness
- **Project Mode**: Project-centric conversations with tech stack detection and automatic learning capture

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm` | Union[LLMProvider, str] | `"ollama"` | LLM provider instance or string name |
| `model` | str | None | Model identifier (auto-detected if None) |
| `api_key` | str | None | API key (reads environment if None) |
| `mode` | str | `"solo"` | Operation mode: "solo" for general chat, "project" for project-based work |
| `project_id` | str | None | Project identifier (required if mode="project") |
| `memory` | bool | `True` | Enable SimpleMem vector store for fast semantic search |
| `debug` | bool | `False` | Enable detailed logging |
| `telemetry` | bool | `False` | Enable usage tracking |

**Key Features:**

- **Memory Judgment System**: Out-of-band LLM judge call validates memory relevance before injection
- **Temporal Awareness**: Auto-detects and handles time-sensitive queries (scores, news, events)
- **Web Search Intelligence**: Knows when to verify facts vs. trust personal data
- **Project Context**: Maintains and evolves project-specific knowledge
- **Current Awareness**: Proactively surfaces trending and viral content

**Usage Example:**

```python
from logicore.agents import SmartAgent, SmartAgentMode

# Solo chat mode
agent = SmartAgent(
    llm="openai",
    model="gpt-4",
    mode=SmartAgentMode.SOLO,
    memory=True,
    debug=False
)

response = await agent.chat("What was India's semi-final score?")
# Judge detects: event query, might have stale memory
# If memory found → Judge decides relevance → If stale, triggers web_search ✅

# Project mode
project_agent = SmartAgent(
    llm="openai",
    mode=SmartAgentMode.PROJECT,
    project_id="my_app",
    memory=True
)

project_agent.create_project(
    project_id="my_app",
    title="Python Django App",
    goal="Build scalable REST API"
)

response = await project_agent.chat("What's our tech stack?")
# Project context: ["Python 3.11", "Django 4.2", "PostgreSQL 15"]
```

**Core Methods:**

```python
# Main chat with memory judgment
async def chat(
    user_input: Union[str, List[Dict[str, Any]]],
    session_id: str = "default",
    stream: bool = False,
    generate_walkthrough: bool = True,
    **kwargs
) -> str:
    """
    Send message and get response with intelligent memory management.
    
    Uses out-of-band judge call to validate memory relevance before injection.
    Returns response text.
    
    Args:
        user_input: User message or message list
        session_id: Conversation session identifier
        stream: Stream response tokens if True
        generate_walkthrough: Include reasoning in response
    
    Returns:
        Response string or async generator if stream=True
    """

# Memory judgment (internal)
async def _judge_memory_relevance(
    self,
    user_input: str,
    memory_entries: list
) -> bool:
    """
    Lightweight out-of-band LLM call to judge memory relevance.
    
    Uses same provider/model but completely outside session.
    No session history, no tools, pure judgment call.
    
    Decision criteria:
    - Personal user data → APPROVE (trust directly)
    - Timeless knowledge → APPROVE (if relevant)
    - Stale events/facts from past → REJECT (needs verification)
    - Irrelevant context → REJECT
    
    Args:
        user_input: User's question
        memory_entries: Preview of retrieved memories
    
    Returns:
        True to inject memory, False to suppress
    """

# Project management
def create_project(
    self,
    project_id: str,
    title: str,
    goal: str = "",
    environment: Dict[str, str] = None,
    key_files: List[str] = None
) -> ProjectContext:
    """Create and switch to new project context."""

def switch_to_project(self, project_id: str) -> Optional[ProjectContext]:
    """Switch to existing project."""

def switch_to_solo(self):
    """Switch to solo mode."""

def list_projects(self) -> List[ProjectContext]:
    """List all available projects."""

def get_project_context_for_llm(self) -> str:
    """Get project context for injection into prompts."""

# Reasoning shortcuts
async def reason(self, problem: str, session_id: str = "default") -> str:
    """Explicit reasoning mode - encourages step-by-step thinking."""

async def remember(
    self,
    memory_type: str,
    title: str,
    content: str,
    tags: List[str] = None
) -> str:
    """Manually store memory entry."""

async def recall(self, query: str, limit: int = 5) -> List:
    """Manually retrieve memory entries."""

def status(self) -> Dict[str, Any]:
    """Get agent status and configuration."""
```

**System Prompt Enhancements:**

SmartAgent includes sophisticated system prompts with:

1. **Memory Verification Policy**
   - Explicit rules for personal data (trust) vs factual content (verify)
   - Examples of each category for clarity

2. **Web Search Intelligence**
   - When to search despite having memory context
   - How to recognize stale information
   - Integration with judge decision

3. **Current Awareness**
   - Directive to proactively surface trending/viral content
   - Real-time consciousness without explicit tools
   - Time-sensitive query detection

4. **Project Workflow** (project mode only)
   - Tech stack verification and version awareness
   - Automatic learning capture
   - Context evolution over time

---



### **AgentSession**

**Description:** Represents a single conversation session with isolated message history and metadata.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `session_id` | str | Unique session identifier |
| `messages` | List[Dict] | Message history: [{"role": "user", "content": "..."}, ...] |
| `created_at` | datetime | When session was created |
| `last_activity` | datetime | Last user message timestamp |
| `metadata` | Dict[str, Any] | Custom metadata storage |

**Methods:**

```python
def add_message(
    role: str,          # "user", "assistant", "system", "tool"
    content: str,
    tool_calls: List = None
) -> None:
    """Add message to session history."""

def get_messages(limit: int = None) -> List[Dict]:
    """Get message history. If limit, gets last N messages."""

def clear(keep_system: bool = True) -> None:
    """Clear all messages. Optionally keep system prompt."""

def get_stats() -> Dict:
    """Get session stats: {'message_count': 10, 'total_tokens': 2500}"""
```

**Usage Example:**

```python
session = agent.get_session("user_123")
session.add_message("user", "What's your name?")
history = session.get_messages(limit=10)
session.metadata["user_tier"] = "premium"
```

---

## Memory Classes

### **ProjectMemory**

**Description:** Structured knowledge storage using SQLite + semantic search. Stores information with context and retrieval patterns.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_path` | str | None | SQLite database path. Default: `user_data/project_memory.db` |

**Methods:**

```python
async def store(
    memory_type: MemoryType,   # Type: APPROACH, LEARNING, KEY_STEP, PATTERN, PREFERENCE, DECISION, CONTEXT
    title: str,                # Brief title
    content: str,              # Full content
    tags: List[str],          # Categorization tags
    project_id: str = None    # Project scope
) -> MemoryEntry:
    """Store a memory entry. Returns stored entry with ID."""

async def retrieve(
    query: str,
    project_id: str = None,
    limit: int = 10,
    memory_types: List[MemoryType] = None
) -> List[MemoryEntry]:
    """Search memories by relevance."""

async def get_by_tag(
    tag: str,
    project_id: str = None
) -> List[MemoryEntry]:
    """Get all memories with specific tag."""

async def export(path: str, format: str = "json") -> None:
    """Export memories to JSON or Markdown."""
```

**MemoryEntry Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique identifier |
| `memory_type` | MemoryType | Type: APPROACH, LEARNING, KEY_STEP, PATTERN, PREFERENCE, DECISION, CONTEXT |
| `title` | str | Brief title |
| `content` | str | Full content |
| `tags` | List[str] | Categorization tags |
| `project_id` | str | Project scope |
| `created_at` | datetime | Creation timestamp |
| `relevance_score` | float | Semantic relevance (0-1) |
| `usage_count` | int | Times referenced |

**Usage Example:**

```python
from logicore.memory import ProjectMemory, MemoryType

memory = ProjectMemory()

# Store a learned pattern
await memory.store(
    memory_type=MemoryType.PATTERN,
    title="JSON API Response Format",
    content="APIs return {status, data, error} structure",
    tags=["api", "json", "response_format"],
    project_id="project_1"
)

# Search
results = await memory.retrieve(
    query="API response format",
    project_id="project_1",
    limit=5
)
```

---

### **AgentrySimpleMem**

**Description:** Fast vector-based memory using LanceDB. Optimized for rapid retrieval (10-50ms) with background processing.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | str | Required | User identifier (isolation key) |
| `session_id` | str | `"default"` | Session identifier |
| `max_context_entries` | int | `5` | Max memories to retrieve per query |
| `enable_background_processing` | bool | `True` | Non-blocking async storage |
| `debug` | bool | `False` | Enable logging |

**Methods:**

```python
async def on_user_message(message: str) -> List[str]:
    """Retrieve relevant context for user message. Returns list of relevant texts."""

async def on_assistant_message(response: str) -> None:
    """Queue assistant response for storage (if background processing enabled)."""

async def process_pending() -> None:
    """Process queued messages. Call if background_processing=False."""

async def search(
    query: str,
    top_k: int = 5,
    filters: Dict = None
) -> List[Dict]:
    """Search vector store. Optional filters: {'topic': 'python', ...}"""
```

**Memory Entry Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `entry_id` | str | UUID |
| `lossless_restatement` | str | Canonical form |
| `keywords` | List[str] | Key terms |
| `timestamp` | datetime | Storage time |
| `location` | str | Where relevant |
| `persons` | List[str] | Involved people |
| `entities` | List[str] | Named entities |
| `topic` | str | Main topic |

**Usage Example:**

```python
from logicore.simplemem import AgentrySimpleMem

memory = AgentrySimpleMem(
    user_id="user_123",
    session_id="chat_456",
    max_context_entries=3
)

# During conversation
context = await memory.on_user_message("What did I say about Python?")
print(context)  # [relevant_memory_1, relevant_memory_2]

await memory.on_assistant_message("You mentioned Python is your primary language")
```

---

## Provider Classes

### **LLMProvider (Abstract Base)**

All built-in providers inherit from this. Create custom providers by extending this class.

**Abstract Methods to Implement:**

```python
async def chat(
    messages: List[Dict[str, str]],
    tools: List[Dict] = None,
    **kwargs
) -> NormalizedMessage:
    """Call LLM. Must return NormalizedMessage."""
```

---

### **OpenAIProvider**

**Description:** Provider for OpenAI models (GPT-4, GPT-3.5, etc.)

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | Required | Model name: "gpt-4", "gpt-3.5-turbo", etc. |
| `api_key` | str | None | API key. Reads OPENAI_API_KEY env var if None |
| `organization` | str | None | Optional organization ID |

**Usage:**

```python
from logicore.providers import OpenAIProvider

provider = OpenAIProvider(
    model_name="gpt-4",
    api_key="sk-..."
)
```

---

### **GroqProvider**

**Description:** Provider for Groq models. Fast inference optimized.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | `"mixtral-8x7b-32768"` | Model name |
| `api_key` | str | None | API key. Reads GROQ_API_KEY env var if None |

---

### **OllamaProvider**

**Description:** Provider for local Ollama models.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | `"llama2"` | Model name available in Ollama |
| `base_url` | str | `"http://localhost:11434"` | Ollama server URL |

---

### **AzureProvider**

**Description:** Provider for Azure OpenAI.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | Required | Model name (OpenAI model, not deployment name) |
| `api_key` | str | None | API key. Reads AZURE_API_KEY env var if None |
| `endpoint` | str | None | Azure endpoint URL. Required |
| `api_version` | str | `"2024-01-01"` | Azure API version |
| `deployment_name` | str | None | Azure deployment name |

---

### **GeminiProvider**

**Description:** Provider for Google Gemini models.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | `"gemini-pro"` | Model name: "gemini-pro", "gemini-pro-vision" |
| `api_key` | str | None | API key. Reads GEMINI_API_KEY or GOOGLE_API_KEY env var if None |

---

### **ProviderGateway**

**Description:** Standardizes all provider responses into uniform format. Handles provider-specific quirks transparently.

**Methods:**

```python
async def chat(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]] = None
) -> NormalizedMessage:
    """Call LLM via provider. Returns standard format."""
```

**NormalizedMessage Structure:**

```python
@dataclass
class NormalizedMessage:
    content: str                    # Response text
    tool_calls: List[ToolCall]     # Tools to execute (empty if none)
    usage: Usage                    # Token counts
    metadata: Dict                  # Provider-specific data

@dataclass
class ToolCall:
    id: str                    # Unique call ID
    function_name: str        # Tool name
    arguments: Dict           # Arguments

@dataclass
class Usage:
    input_tokens: int         # Prompt tokens
    output_tokens: int        # Completion tokens
    total_tokens: int         # Sum
```

---

## Tool Classes

### **BaseTool (Abstract Base)**

**Description:** Base class for all custom tools. Extend this to create new tools.

**Implementation Example:**

```python
from logicore.tools.base import BaseTool, ToolResult

class CodeAnalyzerTool(BaseTool):
    name: str = "analyze_code"
    description: str = "Analyze code for issues and quality metrics"
    
    async def execute(self, code: str, language: str) -> ToolResult:
        """Execute the tool. Must return ToolResult."""
        try:
            issues = self._find_issues(code, language)
            return ToolResult(
                success=True,
                data={
                    "issues": issues,
                    "language": language,
                    "lines": len(code.split('\n'))
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _find_issues(self, code: str, language: str) -> List[Dict]:
        # Implementation
        pass

# Register it
agent.register_tool(CodeAnalyzerTool())
```

---

### **ToolRegistry**

**Description:** Central registry for all available tools. Auto-populated with built-in tools.

**Methods:**

```python
def register_tool(tool: BaseTool) -> None:
    """Register a tool in registry."""

def get_tool(name: str) -> BaseTool:
    """Get tool by name."""

def get_all() -> List[BaseTool]:
    """Get all registered tools."""

def execute_tool(
    name: str,
    args: Dict
) -> Result:
    """Execute named tool with args."""

def has_tool(name: str) -> bool:
    """Check if tool exists."""
```

**Built-in Tool Categories:**

| Category | Tools | Approval Required |
|----------|-------|-------------------|
| SAFE_TOOLS | read_file, list_files, search_files, fast_grep, read_document, media_search, datetime, think | No |
| APPROVAL_REQUIRED | create_file, edit_file, delete_file, web_search, url_fetch, convert_document, execute_command, code_execute, git_command, office_tools, pdf_tools | Yes |
| DANGEROUS_TOOLS | delete_file, execute_code | Blocked by default |

---

## Skill Classes

### **Skill**

**Description:** Bundle of related tools. Organized by domain or functionality.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | Skill name |
| `description` | str | What the skill does |
| `version` | str | Semantic version |
| `tools` | List[Dict] | Tool schema definitions |
| `tool_executors` | Dict[str, Callable] | Tool name → implementation mapping |
| `resources_dir` | str | Path to skill resources |

**Methods:**

```python
async def execute_tool(
    tool_name: str,
    **kwargs
) -> Result:
    """Execute tool from this skill."""
```

---

### **SkillLoader**

**Description:** Discovers and loads skills from filesystem.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_paths` | List[str] | None | Directories to search. Default: built-in + project + workspace |

**Search Priority:**

1. Built-in skills (shipped with Logicore)
2. Project skills (`.agent/skills/`)
3. Workspace skills (`_agent/skills/`)

**Methods:**

```python
def load(skill_name: str) -> Skill:
    """Load single skill by name."""

def load_family(family_name: str) -> List[Skill]:
    """Load all skills matching family pattern (e.g., 'code_*')."""

def list_available() -> List[str]:
    """List all discoverable skill names."""

def validate(skill_path: str) -> bool:
    """Check if skill is valid (has SKILL.md, valid structure)."""
```

**Usage Example:**

```python
from logicore.skills import SkillLoader

loader = SkillLoader()
code_skill = loader.load("code_review")
agent.load_skill(code_skill)

# Or load a family
python_skills = loader.load_family("python_*")
for skill in python_skills:
    agent.load_skill(skill)
```

---

## Configuration

### **AgentrySettings**

**Description:** Centralized configuration with priority chain: Environment → TOML → Defaults

**Access Settings:**

```python
from logicore.config import AgentrySettings, settings

# Via singleton
print(settings.DEPLOYMENT_MODE)
print(settings.OPENAI_API_KEY)

# Or import specific
from logicore.config import get_setting
api_key = get_setting("OPENAI_API_KEY")
```

**Available Settings:**

| Setting | Type | Description |
|---------|------|-------------|
| `DEPLOYMENT_MODE` | str | "local" or "cloud" |
| `OLLAMA_BASE_URL` | str | Ollama server URL |
| `OPENAI_API_KEY` | str | OpenAI API key |
| `GROQ_API_KEY` | str | Groq API key |
| `GEMINI_API_KEY` | str | Google Gemini API key |
| `AZURE_API_KEY` | str | Azure OpenAI API key |
| `STORAGE_DB_PATH` | str | SQLite database location |
| `STORAGE_EMBEDDING_DIR` | str | Vector store location |
| `SERVER_HOST` | str | API server host |
| `SERVER_PORT` | int | API server port |
| `TELEMETRY_ENABLED` | bool | Enable usage tracking |
| `DEBUG_MODE` | bool | Enable verbose logging |

**Priority Chain:**

```
Environment Variable  (highest priority)
    ↓
logicore.toml config
    ↓
Code defaults       (lowest priority)
```

**Examples:**

```bash
# Via environment
export LOGICORE_DEPLOYMENT_MODE=cloud
export LOGICORE_OPENAI_API_KEY=sk-...
export LOGICORE_OLLAMA_BASE_URL=http://localhost:11434
```

```toml
# logicore.toml
[deployment]
mode = "cloud"

[providers]
openai_api_key = "sk-..."
ollama_base_url = "http://localhost:11434"

[storage]
db_path = "data/logicore.db"
embedding_dir = "data/embeddings"

[server]
host = "0.0.0.0"
port = 8000
```

---

## Exceptions

**Provider Errors:**

| Exception | Description |
|-----------|-------------|
| `ProviderError` | Base provider exception |
| `ProviderNotFoundError` | Provider doesn't exist |
| `ProviderConnectionError` | Can't connect to LLM |
| `ProviderAuthError` | Authentication failed |

**Tool Errors:**

| Exception | Description |
|-----------|-------------|
| `ToolError` | Base tool exception |
| `ToolNotFoundError` | Tool doesn't exist |
| `ToolExecutionError` | Tool execution failed |
| `ToolTimeoutError` | Tool exceeded timeout |

**Session/Memory Errors:**

| Exception | Description |
|-----------|-------------|
| `SessionError` | Base session exception |
| `SessionNotFoundError` | Session doesn't exist |
| `MemoryError` | Memory operation failed |
| `VectorStoreError` | Vector store operation failed |

**Usage:**

```python
from logicore.errors import *

try:
    response = agent.chat("Your question")
except ProviderConnectionError:
    print("LLM offline")
except ToolExecutionError as e:
    print(f"Tool failed: {e}")
except Exception as e:
    print(f"Unexpected: {e}")
```

---

## Callbacks

**Available Callback Events:**

```python
# Before/after tool execution
def on_tool_start(tool_name: str, args: Dict) -> None:
    """Called before executing tool."""

def on_tool_end(tool_name: str, result: str, duration: float) -> None:
    """Called after executing tool."""

# Approval gate
def on_tool_approval(tool_name: str, args: Dict) -> bool:
    """Return True to allow, False to deny."""

# Token streaming
def on_token(token: str) -> None:
    """Called per streamed token."""

# Final message
def on_final_message(response: str) -> None:
    """Called before returning final response."""

# Register callbacks
agent.set_callback("on_tool_start", on_tool_start)
agent.set_callback("on_tool_approval", on_tool_approval)
```

**Complete Example:**

```python
def approval_handler(tool_name: str, args: Dict) -> bool:
    dangerous = ["delete_file", "execute_code"]
    if tool_name in dangerous:
        print(f"⚠️  {tool_name} requested")
        return input("Approve? [y/n] ").lower() == "y"
    return True

def token_handler(token: str) -> None:
    print(token, end="", flush=True)

agent.set_callback("on_tool_approval", approval_handler)
agent.set_callback("on_token", token_handler)
```

---

## Quick Reference Table

| Class | Purpose | When to Use |
|-------|---------|------------|
| `Agent` | Full-featured agent | Production use, all features needed |
| `BasicAgent` | Simplified agent | Getting started, prototyping |
| `CopilotAgent` | Code-focused agent | Developer tools, code tasks |
| `MCPAgent` | Enterprise agent | 100+ tools, MCP servers |
| `AgentSession` | Conversation state | Multi-turn conversations |
| `ProjectMemory` | Structured memory | Learning systems, patterns |
| `AgentrySimpleMem` | Vector memory | Fast retrieval, embeddings |
| `ToolRegistry` | Tool management | Finding, executing tools |
| `SkillLoader` | Skill discovery | Loading tool bundles |
| `ProviderGateway` | LLM abstraction | Unified provider interface |

---

## Related Documentation

- **[How-To Guides](03-how-to-guides.md)** — Multiple approaches for each task
- **[Core Architecture](04-core-architecture.md)** — How things work internally
- **[Quickstart](02-quickstart.md)** — Get running in 5 minutes
- **[Bird's-Eye View](01-birds-eye-view.md)** — Conceptual overview

---

*API Reference for Logicore v1.0.0+*  
*Last Updated: March 5, 2026*
