---
title: API Reference
description: Complete API documentation for Logicore
---

# API Reference

Complete API documentation for all Logicore modules.

## Table of Contents

- [Agent](#agent)
- [SmartAgent](#smartagent)
- [CopilotAgent](#copilotagent)
- [MCPAgent](#mcpagent)
- [Tools](#tools)
- [Skills](#skills)
- [Memory](#memory)
- [Providers](#providers)
- [Streaming](#streaming)

---

## Agent

### Constructor

```python
Agent(
    provider: Union[LLMProvider, str] = "ollama",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    system_prompt: Optional[str] = None,
    role: str = "general",
    debug: bool = False,
    tools: Optional[Union[list, str]] = None,
    tool_preset: Optional[str] = None,
    max_iterations: int = 40,
    telemetry: bool = False,
    skills: Optional[list] = None,
    workspace_root: Optional[str] = None,
    reasoning_level: str = "medium",
    plan_mode: bool = False,
    agent_id: Optional[str] = None,
    approval_timeout: float = 120.0,
    allow_tools: Optional[set] = None,
    storage: Optional[Any] = None,
    tool_executor: Optional[ToolExecutor] = None,
    chat_orchestrator: Optional[ChatOrchestrator] = None,
    input_enricher: Optional[InputEnricher] = None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | `Union[LLMProvider, str]` | `"ollama"` | LLM provider instance or name |
| `model` | `Optional[str]` | `None` | Model name |
| `api_key` | `Optional[str]` | `None` | API key for cloud providers |
| `endpoint` | `Optional[str]` | `None` | Custom endpoint URL |
| `system_prompt` | `Optional[str]` | `None` | Custom system prompt |
| `role` | `str` | `"general"` | Agent persona |
| `debug` | `bool` | `False` | Enable debug logging |
| `tools` | `Optional[Union[list, str]]` | `None` | Tool list or preset name |
| `tool_preset` | `Optional[str]` | `None` | Tool preset name |
| `max_iterations` | `int` | `40` | Max tool-call iterations |
| `telemetry` | `bool` | `False` | Enable telemetry |
| `skills` | `Optional[list]` | `None` | Skills to load |
| `workspace_root` | `Optional[str]` | `None` | Workspace root for skill discovery |
| `reasoning_level` | `str` | `"medium"` | Reasoning depth (low/medium/high) |
| `plan_mode` | `bool` | `False` | Enable plan mode |
| `agent_id` | `Optional[str]` | `None` | Unique agent identifier |
| `approval_timeout` | `float` | `120.0` | Tool approval timeout (seconds) |
| `allow_tools` | `Optional[set]` | `None` | Pre-approved tools |
| `storage` | `Optional[Any]` | `None` | Storage backend for persistence |
| `tool_executor` | `Optional[ToolExecutor]` | `None` | Custom executor |
| `chat_orchestrator` | `Optional[ChatOrchestrator]` | `None` | Custom orchestrator |
| `input_enricher` | `Optional[InputEnricher]` | `None` | Custom enricher |

### Methods

#### chat()

```python
async def chat(
    message: str,
    session_id: Optional[str] = None,
    stream: bool = False,
    callbacks: Optional[Dict] = None,
    **kwargs
) -> Dict
```

Main chat entry point.

**Parameters:**
- `message` (str): User message
- `session_id` (Optional[str]): Session identifier
- `stream` (bool): Enable streaming
- `callbacks` (Optional[Dict]): Callback functions

**Returns:**
- `Dict`: Response with `content`, `tool_calls`, `usage`

#### stream()

```python
async def stream(
    message: str,
    session_id: Optional[str] = None,
    **kwargs
) -> AsyncGenerator[StreamEvent, None]
```

Async generator yielding stream events.

#### stream_sync()

```python
def stream_sync(
    message: str,
    session_id: Optional[str] = None,
    **kwargs
) -> Generator[StreamEvent, None, None]
```

Synchronous streaming (no async required).

#### create_session()

```python
def create_session(
    session_id: str,
    tags: Optional[Dict] = None
) -> AgentSession
```

Create a new session.

#### get_session()

```python
async def get_session(session_id: str) -> AgentSession
```

Get or create a session.

#### list_sessions()

```python
async def list_sessions() -> List[AgentSession]
```

List all sessions.

#### clear_session()

```python
async def clear_session(session_id: str) -> None
```

Clear session history.

#### delete_session()

```python
async def delete_session(session_id: str) -> None
```

Delete a session.

#### add_custom_tool()

```python
def add_custom_tool(tool: BaseTool) -> None
```

Register a custom tool.

#### register_tool_from_function()

```python
def register_tool_from_function(func: Callable) -> None
```

Auto-generate schema from function.

#### load_skill()

```python
def load_skill(skill: Union[str, Skill]) -> None
```

Load a skill.

#### load_skills()

```python
def load_skills(skills: List[Union[str, Skill]]) -> None
```

Load multiple skills.

#### unload_skill()

```python
def unload_skill(skill_name: str) -> None
```

Unload a skill.

#### enable_skill()

```python
def enable_skill(skill_name: str) -> None
```

Enable a skill.

#### disable_skill()

```python
def disable_skill(skill_name: str) -> None
```

Disable a skill.

#### list_available_skills()

```python
def list_available_skills() -> List[SkillMetadata]
```

List loaded and indexed skills.

#### add_mcp_server()

```python
def add_mcp_server(config: Dict) -> None
```

Add MCP server connection.

#### set_reasoning_level()

```python
def set_reasoning_level(level: str) -> None
```

Set reasoning depth.

#### cleanup()

```python
async def cleanup() -> None
```

Cleanup MCP connections and storage.

---

## SmartAgent

Inherits from `Agent` with optimized defaults for reasoning.

```python
SmartAgent(
    provider: Union[LLMProvider, str] = "ollama",
    model: Optional[str] = None,
    **kwargs
)
```

### Additional Methods

#### reason()

```python
async def reason(problem: str) -> str
```

Step-by-step problem solving.

#### status()

```python
def status() -> Dict
```

Returns agent status dict.

---

## CopilotAgent

Inherits from `Agent` with coding-focused tools and prompts.

```python
CopilotAgent(
    provider: Union[LLMProvider, str] = "ollama",
    model: Optional[str] = None,
    **kwargs
)
```

### Additional Methods

#### explain_code()

```python
async def explain_code(code: str) -> str
```

Explain code functionality.

#### review_file()

```python
async def review_file(file_path: str) -> str
```

Review a file for issues.

#### write_code()

```python
async def write_code(description: str) -> str
```

Generate code from description.

#### fix_bug()

```python
async def fix_bug(bug_description: str) -> str
```

Fix a bug.

#### discuss()

```python
async def discuss(topic: str) -> str
```

General chat in separate session.

---

## MCPAgent

Inherits from `Agent` with MCP server integration.

```python
MCPAgent(
    provider: Union[LLMProvider, str] = "ollama",
    model: Optional[str] = None,
    session_timeout: int = 3600,
    mcp_config_path: Optional[str] = None,
    mcp_config: Optional[Dict] = None,
    deferred_tools: bool = False,
    tool_threshold: int = 15,
    **kwargs
)
```

**Additional Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_timeout` | `int` | `3600` | Session timeout (seconds) |
| `mcp_config_path` | `Optional[str]` | `None` | Path to mcp.json |
| `mcp_config` | `Optional[Dict]` | `None` | MCP configuration dict |
| `deferred_tools` | `bool` | `False` | Enable deferred tool loading |
| `tool_threshold` | `int` | `15` | Auto-defer if tools exceed |

### Additional Methods

#### init_mcp_servers()

```python
async def init_mcp_servers() -> None
```

Connect to MCP servers.

#### get_all_tools()

```python
async def get_all_tools() -> List[Dict]
```

Get all tools (including MCP).

#### _search_tools()

```python
async def _search_tools(query: str) -> List[Dict]
```

Search tools by query.

#### preload_tools()

```python
async def preload_tools(tool_names: List[str]) -> None
```

Pre-load specific tools.

#### get_registry_stats()

```python
def get_registry_stats() -> Dict
```

Registry statistics.

#### create_session()

```python
async def create_session(
    session_id: str,
    on_session_created: Optional[Callable] = None,
    on_session_destroyed: Optional[Callable] = None
) -> AgentSession
```

Create session with callbacks.

#### destroy_session()

```python
async def destroy_session(session_id: str) -> None
```

Destroy session with cleanup.

#### cleanup_stale_sessions()

```python
async def cleanup_stale_sessions(timeout: int = 3600) -> None
```

Remove timed-out sessions.

#### list_mcp_tools_schema()

```python
def list_mcp_tools_schema() -> List[Dict]
```

MCP-compatible tool schemas.

#### export_mcp_config()

```python
def export_mcp_config() -> Dict
```

Export to JSON.

---

## Tools

### BaseTool

```python
class BaseTool:
    name: str
    description: str
    args_schema: Optional[Type[BaseModel]]
    
    async def run(**kwargs) -> ToolResult
    def is_read_only() -> bool
    def is_destructive() -> bool
    def interrupt_behavior() -> str
    def is_concurrency_safe() -> bool
    def is_enabled() -> bool
```

### ToolResult

```python
class ToolResult(dict):
    success: bool
    content: str
    error: Optional[str]
```

### ToolRegistry

```python
class ToolRegistry:
    def __init__(
        preset: Optional[str] = None,
        enabled_tools: Optional[Set[str]] = None,
        disabled_tools: Optional[Set[str]] = None
    )
```

**Presets:**
- `"lightweight"` - ~16 tools
- `"smart"` - ~30 tools
- `"copilot"` - ~18 tools
- `"full"` - All tools
- `"minimal"` - 6 tools
- `"webdev"` - ~12 tools

---

## Skills

### Skill

```python
class Skill:
    metadata: SkillMetadata
    instructions: str
    skill_dir: Path
    examples: List[str]
    templates: Dict[str, str]
    validation_rules: List[Dict]
    capabilities: List[Capability]
    
    @property
    def name() -> str
    
    @property
    def description() -> str
    
    @property
    def version() -> str
    
    @property
    def is_loaded() -> bool
    
    @property
    def is_enabled() -> bool
    
    def enable() -> None
    def disable() -> None
    def check_dependencies() -> bool
    def check_conflicts() -> List[str]
    def get_capabilities() -> List[Capability]
    def get_registered_capabilities() -> List[Capability]
    def has_capabilities(capability_names: List[str]) -> bool
    def build_validation_checklist() -> Dict
```

### SkillMetadata

```python
@dataclass
class SkillMetadata:
    name: str
    description: str
    version: str
    author: str
    tags: List[str]
    requires: List[str]
    conflicts_with: List[str]
    trigger: str
    cost_tier: str
    min_framework_version: str
```

### Capability

```python
@dataclass
class Capability:
    name: str
    cap_type: CapabilityType
    description: str
    schema: Optional[Dict]
    executor: Optional[Callable]
    path: Optional[str]
    language: Optional[str]
    complexity: Optional[str]
    alternatives: Optional[List[str]]
```

### SkillLoader

```python
class SkillLoader:
    @staticmethod
    def load(skill_dir: Union[str, Path]) -> Skill
    
    @staticmethod
    def discover(parent_dir: Union[str, Path]) -> List[SkillMetadata]
    
    @staticmethod
    def discover_workspace_skills(workspace_root: str) -> List[SkillMetadata]
    
    @staticmethod
    def load_skill_index(index_path: Union[str, Path]) -> List[SkillIndexEntry]
    
    @staticmethod
    def load_skill_by_index(
        parent_dir: Union[str, Path],
        skill_name: str
    ) -> Skill
    
    @staticmethod
    def load_skills_batch(
        skill_dirs: List[Union[str, Path]]
    ) -> List[Skill]
    
    @staticmethod
    def build_skill_index(parent_dir: Union[str, Path]) -> str
    
    @staticmethod
    def resolve_dependencies(skills: List[Skill]) -> List[Skill]
    
    @staticmethod
    def load_skill_graph(skill_dir: Union[str, Path]) -> Skill
```

---

## Memory

### MemoryManager

```python
class MemoryManager:
    def __init__(
        memory_dir: str = "~/.logicore/memory",
        llm_provider: Union[LLMProvider, str] = "ollama",
        llm_model: Optional[str] = None,
        enabled: bool = True,
        throttle_interval: int = 30,
        transcript_window: int = 50
    )
    
    async def start() -> None
    async def stop() -> None
    async def get_memory_prompt_section() -> str
    async def inject_context(messages: List[Dict]) -> List[Dict]
    async def submit_for_extraction(conversation: List[Dict]) -> None
    def reset_session() -> None
    def get_stats() -> Dict
```

### MemoryStore

```python
class MemoryStore:
    def __init__(memory_dir: str)
    
    async def scan_memory_files() -> List[MemoryHeader]
    async def read_memory_file(file_path: str) -> Tuple[MemoryMetadata, str]
    async def write_memory_file(
        file_path: str,
        metadata: MemoryMetadata,
        content: str
    ) -> None
    async def delete_memory_file(file_path: str) -> None
    async def update_index() -> None
    async def find_related_memories(tags: List[str]) -> List[MemoryHeader]
```

### MemoryRetriever

```python
class MemoryRetriever:
    def __init__(memory_dir: str)
    
    async def search(
        query: str,
        domain: Optional[MemoryDomain] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[MemoryScore]
```

---

## Providers

### LLMProvider (ABC)

```python
class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        messages: List[Dict],
        model: str,
        **kwargs
    ) -> Dict
    
    @abstractmethod
    async def stream(
        messages: List[Dict],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict, None]
```

### ModelAvailabilityService

```python
class ModelAvailabilityService:
    def register_provider(
        name: str,
        provider: LLMProvider,
        priority: int = 0
    ) -> None
    
    def get_available_provider() -> Optional[LLMProvider]
    
    def report_success(provider_name: str) -> None
    
    def report_failure(provider_name: str, error: Exception) -> None
```

---

## Streaming

### StreamEvent

```python
@dataclass
class StreamEvent:
    type: StreamEventType
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict] = None
    metadata: Optional[Dict] = None
```

### StreamEventType

```python
class StreamEventType(Enum):
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    REASONING = "reasoning"
    ERROR = "error"
    DONE = "done"
```

### AgentRunResult

```python
@dataclass
class AgentRunResult:
    content: str
    tool_calls: List[Dict]
    usage: Dict
    session_id: str
```
