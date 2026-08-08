---
title: Architecture
description: System design and component relationships
---

# Architecture

Understanding Logicore's system design and component relationships.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│                    (Your Agent Code)                         │
├─────────────────────────────────────────────────────────────┤
│                       Agent Layer                            │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   Session   │  │  Skills  │  │  Memory  │  │  Tasks  │ │
│  │   Manager   │  │  Loader  │  │  Manager │  │ Manager │ │
│  └─────────────┘  └──────────┘  └──────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Execution Layer                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Tool     │  │    Chat      │  │      Input       │  │
│  │   Executor  │  │ Orchestrator │  │     Enricher     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Context Layer                            │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │    Token     │  │    Context    │  │     Prompt     │  │
│  │  Estimator   │  │  Window Mgr   │  │   Assembler    │  │
│  └──────────────┘  └───────────────┘  └────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Provider Layer                            │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────┐ │
│  │ Ollama │  │ OpenAI │  │ Gemini │  │  Groq  │  │Azure │ │
│  └────────┘  └────────┘  └────────┘  └────────┘  └──────┘ │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           ModelAvailabilityService (Failover)        │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Storage Layer                             │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │   Database   │  │   Snapshot    │  │     Media      │  │
│  │   Backend    │  │   Backend     │  │    Backend     │  │
│  └──────────────┘  └───────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Agent (`logicore.agent.base`)

The central orchestrator managing all agent operations.

```python
class Agent:
    # Core components
    context_engine: ContextEngine      # Context management
    tool_executor: ToolExecutor        # Tool execution
    chat_orchestrator: ChatOrchestrator # Conversation loop
    input_enricher: InputEnricher      # Input processing
    
    # Sub-systems
    _loop_engine: LoopDetectionEngine  # Loop detection
    _turn_manager: TurnManager         # Turn management
    _reasoning_controller: ReasoningController # Reasoning
```

### ToolExecutor (`logicore.agent.tool_executor`)

Handles tool dispatch, approval, and execution.

```python
class ToolExecutor:
    custom_tool_executors: Dict[str, Callable]  # Custom tools
    skill_tool_executors: Dict[str, Callable]   # Skill tools
    mcp_managers: List[MCPClientManager]        # MCP servers
    _approval_cache: Dict[str, ApprovalDecision] # Approval state
```

### ChatOrchestrator (`logicore.agent.chat_orchestrator`)

Manages the conversation loop and tool execution flow.

```python
class ChatOrchestrator:
    guardrail_controller: ToolCallGuardrailController
    feedback_handler: FeedbackHandler
    hook_system: HookSystem
    operational_memory: OperationalMemoryManager
    progressive_compressor: ProgressiveCompressor
```

### ContextEngine (`logicore.runtime.context.manager`)

Manages context window, token budget, and message pipeline.

```python
class ContextEngine:
    token_estimator: TokenEstimator
    prompt_assembler: PromptAssembler
    message_pipeline: MessagePipeline
    tool_output_distiller: ToolOutputDistiller
    _window_manager: ContextWindowManager
```

## Data Flow

### Chat Request Flow

```
User Input
    │
    ▼
┌─────────────────┐
│  Input Enricher │ ← Add context, references
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Manager │ ← Manage token budget
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Provider  │ ← Generate response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tool Executor  │ ← Run tool calls
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Chat Orchestrator│ ← Continue loop
└────────┬────────┘
         │
         ▼
    Response
```

### Tool Execution Flow

```
Tool Call Request
    │
    ▼
┌─────────────────┐
│  Deduplication  │ ← Check for duplicates
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Approval     │ ← Check if approved
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Cache       │ ← Check result cache
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Dispatch     │ ← Route to handler
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Custom    MCP/Skill
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│  Error Handler  │ ← Classify errors
└────────┬────────┘
         │
         ▼
    ToolResult
```

## Session Management

### In-Memory Sessions

```python
# Sessions stored in agent
agent.sessions: Dict[str, AgentSession] = {}
agent._session_locks: Dict[str, asyncio.Lock] = {}
```

### Persistent Sessions

```python
# Three-tier storage
StorageManager:
    DatabaseBackend  # SQLite/PostgreSQL (source of truth)
    SnapshotBackend  # JSON manifests (filesystem)
    MediaBackend     # Binary files (local/S3)
```

## Memory System

### Memory Pipeline

```
Conversation
    │
    ▼
┌─────────────────┐
│  Extraction     │ ← Extract facts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Classification │ ← Categorize
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Storage      │ ← Save to files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Retrieval     │ ← Semantic search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Consolidation  │ ← Merge duplicates
└─────────────────┘
```

### Memory Domains

| Domain | Purpose |
|--------|---------|
| IDENTITY | User identity |
| PREFERENCES | User preferences |
| RELATIONSHIPS | People connections |
| KNOWLEDGE | Facts and information |
| DOMAIN | Domain-specific |
| OPERATIONAL | Operational data |

## Hook System

### Hook Points

```python
class HookPoint(Enum):
    BEFORE_MODEL = "before_model"
    AFTER_MODEL = "after_model"
    BEFORE_TOOL = "before_tool"
    AFTER_TOOL = "after_tool"
    ON_ERROR = "on_error"
    ON_CONTEXT_COMPRESS = "on_context_compress"
```

### Hook Registration

```python
@hooks.register(HookPoint.BEFORE_MODEL, priority=10)
async def inject_context(ctx):
    return HookResult(action=HookAction.MODIFY, modified_messages=...)
```

## Skills Architecture

### Skill Structure

```
skill/
├── SKILL.md          # Metadata + instructions
├── examples/         # Usage examples
├── scripts/          # Executable scripts
├── templates/        # Prompt templates
└── validation_rules/ # Validation logic
```

### Skill Loading

```
SkillLoader
    │
    ├── discover()        # Find skills
    ├── load()            # Load skill
    ├── resolve_dependencies()  # Resolve deps
    └── register()        # Register tools
```

## MCP Architecture

### MCP Client

```
MCPClientManager
    │
    ├── load_config()     # Load mcp.json
    ├── connect_to_servers()  # Connect
    ├── get_tools()       # Discover tools
    ├── execute_tool()    # Run tool
    └── cleanup()         # Disconnect
```

### Server Connection

```
mcp.json
    │
    ▼
┌─────────────────┐
│  Server Config  │ ← Command + args
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   stdio_client  │ ← Spawn process
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ClientSession  │ ← MCP protocol
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tool Discovery │ ← list_tools()
└─────────────────┘
```

## Performance Characteristics

| Operation | Latency |
|-----------|---------|
| Token Streaming | <50ms (network-bound) |
| Tool Execution | ~1ms overhead |
| Memory Lookup | <10ms (10K embeddings) |
| Context Compression | 100-500ms |

## Design Principles

1. **Single Responsibility**: Each component has one job
2. **Provider Agnosticism**: No provider-specific code
3. **Fail-Safe Execution**: Errors don't crash agents
4. **Transparency**: Full execution logs
5. **Extensibility**: Hooks everywhere
6. **Resilience**: Automatic failover
7. **Observability**: Telemetry and debugging

## Next Steps

- [Component API Reference](../api/)
- [Custom Components](../tutorials/custom-components.md)
- [Performance Tuning](../guides/performance.md)
