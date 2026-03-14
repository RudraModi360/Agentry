# How-To Guides: Patterns & Approaches for Every Use Case

This section shows you the **different ways** to do common tasks. Each approach has tradeoffs—know when to use which.

---

## 1. Working with Tools

Tools are how agents take action. There are 4 ways to add them. Pick the one that fits your situation.

### **Approach 1: Register Tools at Agent Init Time**

```python
from logicore.agents import BasicAgent

def calculate(expression: str) -> str:
    """Calculate math expressions."""
    return str(eval(expression))

def web_search(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"

# Pass all tools upfront
agent = BasicAgent(
    custom_tools=[calculate, web_search]
)

response = agent.chat("Search for Python news and calculate 5 + 3")
```

**Best for:**
- Small, fixed tool set (5-15 tools)
- All tools known at startup
- Simple applications

**Pros:**
- Fast initialization
- All tools available immediately
- Simple to understand

**Cons:**
- Tools loaded even if unused
- Can't add tools later easily
- Not flexible if tools are dynamic

---

### **Approach 2: Register Tools After Creation**

```python
from logicore.agents import BasicAgent

agent = BasicAgent()

# Add tools one by one
def calculate(expr: str) -> str:
    return str(eval(expr))

def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()

agent.register_tool_from_function(calculate)
agent.register_tool_from_function(read_file)

# Later, add more tools
def web_search(query: str) -> str:
    return f"Results for: {query}"

agent.register_tool_from_function(web_search)

response = agent.chat("Read config.txt and search for updates")
```

**Best for:**
- Dynamic tool loading
- Adding tools based on conditions
- Building progressive features

**Pros:**
- Tools added when needed
- Cleaner separation of concerns
- Works with conditional logic

**Cons:**
- Slightly more code
- Tools available at different times
- Need to remember which tools are registered

---

### **Approach 3: Use Tool Classes for Complex Logic**

```python
from logicore.tools.base import BaseTool
from typing import Any

class DatabaseQueryTool(BaseTool):
    """Query a database—more complex than a simple function."""
    
    name = "database_query"
    description = "Query the company database with SQL"
    
    def __init__(self, connection_string: str):
        self.conn_str = connection_string
    
    def execute(self, query: str) -> str:
        # Your database logic here
        return f"Query result: {query}"

# Use it with agent
from logicore.agents import BasicAgent

db_tool = DatabaseQueryTool(connection_string="sqlite:///app.db")
agent = BasicAgent()
agent.register_tool(db_tool)

response = agent.chat("Get all active users from the database")
```

**Best for:**
- Complex tools with state (connections, config)
- Tools that need initialization
- Enterprise integrations

**Pros:**
- Encapsulation and state management
- Reusable tool classes
- Clear error handling

**Cons:**
- More boilerplate
- Requires understanding class structure
- Overhead for simple tools

---

### **Approach 4: Load Skills (Pre-Built Tool Bundles)**

```python
from logicore.agents import BasicAgent
from logicore.skills import SkillLoader

agent = BasicAgent()

# Load pre-built skill (contains multiple related tools)
loader = SkillLoader()
code_skill = loader.load("code_review")  # Has: analyze_code, suggest_improvements, check_syntax
web_skill = loader.load("web_research")  # Has: search, fetch, summarize

agent.load_skill(code_skill)
agent.load_skill(web_skill)

# Agent now has 6 tools organized in 2 skills
response = agent.chat("Review my Python code and search for best practices")
```

**Best for:**
- Related tool bundles
- Scaling to many tools (50+)
- Reusing tool sets across projects

**Pros:**
- Grouped, organized tools
- Scales without LLM confusion
- Reusable across agents

**Cons:**
- Need to find or build skills
- Less flexibility than individual tools
- Harder to customize

---

### **Comparison: Which Approach When?**

| Scenario | Approach | Why |
|----------|----------|-----|
| Simple chatbot, 3 tools | #1 (Init time) | Fast, simple |
| Feature flags, conditional tools | #2 (Register after) | Dynamic loading |
| Database adapter | #3 (Tool class) | Needs state/config |
| Analytics + web research | #4 (Skills) | Bundles, scales |
| Building for production | Mix #2 + #4 | Load base skills, add custom tools |

---

## 2. Working with Memory

Memory is how agents learn across conversations. Here are the main strategies.

### **Approach 1: Simple Memory (Default)**

```python
from logicore.agents import BasicAgent

# Enable memory—that's it
agent = BasicAgent(enable_memory=True)

# Conversation 1
agent.chat("My project uses Python and PostgreSQL")

# Conversation 2 (separate call)
response = agent.chat("What tech stack are we using?")
# Output: "You mentioned Python and PostgreSQL"
```

**Best for:**
- Getting started
- Single-user applications
- Learning projects

**How it works:**
- Every conversation stored automatically
- Similarity search retrieves relevant past contexts
- Automatic injection before LLM call

**Memory limit:** ~500 conversations before manual cleanup

---

### **Approach 2: Session-Based Memory (Multi-User)**

```python
from logicore.agents import BasicAgent
from logicore.session_manager import SessionManager

session_manager = SessionManager()

# User 1 session
user1_session = session_manager.create_session(user_id="user_1")
agent1 = BasicAgent(
    enable_memory=True,
    session_id=user1_session.id
)

# User 2 session
user2_session = session_manager.create_session(user_id="user_2")
agent2 = BasicAgent(
    enable_memory=True,
    session_id=user2_session.id
)

# Conversations stay isolated
agent1.chat("I work on finance apps")
agent2.chat("I work on gaming")

# Each agent only sees its own memory
agent1.chat("What's my domain?")  # "Finance apps"
agent2.chat("What's my domain?")  # "Gaming"
```

**Best for:**
- Multi-user SaaS
- Customer support bots
- Team collaboration tools

**Key benefit:**
- Complete conversation isolation
- One agent instance per user
- No cross-contamination

---

### **Approach 3: Filtered Memory (Selective Context)**

```python
from logicore.agents import Agent

agent = Agent(
    enable_memory=True,
    memory_config={
        "max_results": 3,           # Only pull top 3 memories
        "similarity_threshold": 0.7, # Only relevant matches
        "retention_days": 30,       # Auto-forget after 30 days
        "filter_tags": ["production"],  # Only tagged memories
    }
)

# Store with tags
agent.chat("User wants premium feature", tags=["production"])
agent.chat("Internal test conversation", tags=["test"])

# Retrieval respects filters
response = agent.chat("What features do users want?")
# Only sees production-tagged memories
```

**Best for:**
- Large-scale systems with lots of history
- Sensitive data that should be forgotten
- Multi-environment setups (test vs prod)

**Memory strategy:**
- Recent > Old
- Relevant > Irrelevant
- Tagged > Untagged

---

### **Approach 4: No Memory (Stateless)**

```python
from logicore.agents import BasicAgent

# Explicitly disable memory
agent = BasicAgent(enable_memory=False)

# Each conversation is independent
agent.chat("Remember: server is down")
response = agent.chat("What's the server status?")
# Output: "I don't have info about the server"
```

**Best for:**
- Stateless APIs
- One-off tasks
- Privacy-critical applications

**Trade-off:**
- Faster execution
- No context leakage
- But less intelligent over time

---

### **Approach 5: Intelligent Memory Judgment (SmartAgent - NEW)**

SmartAgent automatically judges whether retrieved memories are relevant and temporally current before injecting them. Perfect for knowledge-intensive applications needing real-time accuracy.

```python
from logicore.agents import SmartAgent

# Enable intelligent memory with built-in judge
agent = SmartAgent(
    llm="openai",
    model="gpt-4",
    mode="solo",
    memory=True,  # Enables SimpleMem + judge system
    debug=True    # See judge decisions
)

# Conversation: Event-based query (time-sensitive)
agent.chat("What was India's semi-final cricket score?")
# Memory found: "India vs NZ, Nov 15, 2023, Wankhede Stadium, 397/4"
# Judge decides: Event from 2023, user asking in 2026 → STALE
# Result: Memory suppressed, web_search triggered, current match returned ✅

# Conversation: Personal data query (always trust memory)
agent.chat("What's my preferred programming language?")
# Memory found: "User prefers Python for data science"
# Judge decides: Personal user preference → RELEVANT
# Result: Memory injected, agent responds from memory ✅

# Conversation: Timeless knowledge (trust if relevant)
agent.chat("How do I implement binary search?")
# Memory found: "Binary search requires sorted array, O(log n) complexity"
# Judge decides: Algorithm knowledge, age-independent → RELEVANT
# Result: Memory injected, agent confirms and builds on it ✅
```

**Judge Decision Criteria:**

```python
# SmartAgent's memory judgment rules (built into system prompt)

APPROVE memory if:
  ✅ Personal user data (name, preferences, history)
  ✅ Timeless knowledge (how things work, definitions, algorithms)
  ✅ Evergreen facts (gravity = 9.8 m/s², pi ≈ 3.14159)
  ✅ Relevant to current question (query-matching)

REJECT memory if:
  ❌ Event/result from past (match score, news headline, stock price)
  ❌ Technology version/ranking (outdated from 2 years ago)
  ❌ Irrelevant to current query (different topic)
  ❌ Explicitly outdated (tagged with past dates)
```

**How the Judge Works:**

```python
# Internal process (automatic, transparent to user)

1. User asks: "What was India's semi-final score?"
    ↓
2. Memory retrieval: "India vs NZ, Nov 15, 2023, 397/4"
    ↓
3. Judge call (outside session):
   - Same LLM, no session history, no tools
   - Given: today's date (March 6, 2026), user query, memory preview
   - Decision: Event from 2023, likely stale → REJECT
    ↓
4. memory_enabled = False (suppress injection for this call only)
    ↓
5. Agent sees no memory context, recognizes need for current info
    ↓
6. Triggers web_search → Finds 2026 semi-final → Returns current result ✅
    ↓
7. memory_enabled = True (restored for next converstion)
```

**Best for:**
- Knowledge-intensive applications
- Real-time awareness needed
- Preventing stale information injection
- Hybrid personal + factual data
- Production systems handling diverse query types

**Pros:**
- ✅ Automatic judgment (no manual intervention)
- ✅ Prevents outdated data confusion
- ✅ Trusts personal data without web search
- ✅ Single extra LLM call overhead (efficient)
- ✅ Completely isolated judge (no session contamination)
- ✅ Safe fallback if judge fails (defaults to injecting memory)

**Cons:**
- ⚠️ One extra LLM call per chat (minimal overhead, same model)
- ⚠️ Judge prompt is fixed (customizable if needed)
- ⚠️ Requires same provider for judge (not a limitation, same provider used anyway)

**Configuration & Debugging:**

```python
# Enable detailed judge logging
agent = SmartAgent(
    memory=True,
    debug=True  # Prints: "[SmartAgent] 🔍 Memory judge → USE ✅" or "SKIP 🚫"
)

# Access judge decision in callbacks
def on_judge_verdict(query, memory, decision):
    print(f"Query: {query}")
    print(f"Memory: {memory}")
    print(f"Judge says: {'INJECT' if decision else 'SKIP'}")

# Manually retrieve + judge if needed
preview = agent.simplemem._fast_retrieve("Your query")
decision = await agent._judge_memory_relevance("Your query", preview)
print(f"Memory should be injected: {decision}")
```

---

### **Comparison: Memory Strategies (Updated)**

| Strategy | Users | Isolation | Real-Time | Best For |
|----------|-------|-----------|-----------|----------|
| Simple | 1 | None | No | Basic projects |
| Session-based | Many | Per-user | No | SaaS, support |
| Filtered | Many | By tags | No | Enterprise, multi-env |
| None | 1-Many | Complete | N/A | Stateless APIs |
| **SmartAgent Judge** | 1-Many | Per-user | **Yes** | **Knowledge-intensive, real-time** |

Key distinction: **SmartAgent is the only strategy that actively prevents stale information injection while still trusting personal data.**

---



Switch providers without changing agent code.

### **Approach 1: Choose at Initialization**

```python
from logicore.agents import BasicAgent

# Local Ollama (free, no API key needed)
agent = BasicAgent(provider="ollama")

# OR OpenAI (need: export OPENAI_API_KEY=...)
# agent = BasicAgent(provider="openai")

# OR Groq (need: export GROQ_API_KEY=...)
# agent = BasicAgent(provider="groq")

# OR Azure OpenAI (need Azure credentials)
# agent = BasicAgent(provider="azure")

response = agent.chat("Hello!")
```

**Best for:**
- Single provider per agent
- Most applications

**How to pick:**
- **Ollama**: Development, offline, free
- **OpenAI**: Production, most capable, expensive
- **Groq**: Speed, cheaper, good reasoning
- **Azure**: Enterprise, compliance, VPC support

---

### **Approach 2: Conditional Provider Selection**

```python
from logicore.agents import BasicAgent
import os

# Pick provider based on environment
if os.getenv("ENVIRONMENT") == "production":
    provider = "openai"  # Reliable, powerful
    model = "gpt-4"
elif os.getenv("ENVIRONMENT") == "staging":
    provider = "groq"    # Fast, cheaper
    model = "mixtral-8x7b"
else:
    provider = "ollama"  # Local, free
    model = "qwen:7b"

agent = BasicAgent(
    provider=provider,
    model=model
)

response = agent.chat("Process this request")
```

**Best for:**
- Development vs production
- Cost optimization
- Feature flagging

**Typical setup:**
```
Development -> Ollama (free)
Staging     -> Groq (fast, cheap)
Production  -> OpenAI (reliable, capable)
```

---

### **Approach 3: Multi-Provider Fallback**

```python
from logicore.agents import BasicAgent

def get_agent_with_fallback():
    """Try providers in order of preference."""
    providers_to_try = ["groq", "openai", "ollama"]
    
    for provider in providers_to_try:
        try:
            agent = BasicAgent(provider=provider)
            # Test if provider is available
            agent.chat("ping")
            return agent
        except Exception:
            continue
    
    raise Exception("No providers available!")

agent = get_agent_with_fallback()
# Uses first available provider
response = agent.chat("What is your name?")
```

**Best for:**
- High availability
- Handling API outages
- Cost management (use cheapest available)

**Trade-off:**
- Complexity
- Inconsistent responses (different models)
- Latency (testing each provider)

---

### **Approach 4: Hybrid Providers (Mix and Match)**

```python
from logicore.agents import Agent

agent = Agent(
    provider_routing={
        "simple_questions": "groq",       # Fast, cheap
        "complex_reasoning": "openai",    # Better, exp.
        "code_generation": "openai",      # Specialized
        "fallback": "ollama",             # Local backup
    }
)

# Route based on question type
simple = agent.chat("What's 2+2?", route="simple_questions")
# Uses Groq

complex_q = agent.chat("Explain quantum entanglement", route="complex_reasoning")
# Uses OpenAI
```

**Best for:**
- Cost optimization
- Specialized tasks
- Enterprise systems

**Benefit:**
- Use expensive model only when needed
- Save costs significantly

---

### **Comparison: Provider Approaches**

| Approach | Complexity | Flexibility | Cost | Maintenance |
|----------|-----------|------------|------|-------------|
| Single provider | Low | None | Variable | Easy |
| Conditional | Medium | By environment | Good | Medium |
| Fallback | Medium | Auto-switching | Good | Medium |
| Hybrid | High | Per-task | Best | Hard |

---

## 4. Working with Context & Sessions

Different strategies for managing conversation state.

### **Approach 1: Single Continuous Session**

```python
from logicore.agents import BasicAgent

agent = BasicAgent(enable_memory=True)

# All messages in one session
agent.chat("I'm building a web app")
agent.chat("Should I use React?")
agent.chat("How do I deploy it?")

# Agent remembers all 3 conversations
response = agent.chat("What's the tech stack we discussed?")
# Returns: "Web app, React, deployment..."
```

**Best for:**
- Tutorials and learning
- Personal assistants
- Single-topic workflows

---

### **Approach 2: Multi-Topic Sessions**

```python
from logicore.agents import Agent
from logicore.session_manager import SessionManager

manager = SessionManager()

# Create separate sessions per topic
coding_session = manager.create_session(topic="coding")
sales_session = manager.create_session(topic="sales")

agent_code = Agent(session_id=coding_session.id, enable_memory=True)
agent_sales = Agent(session_id=sales_session.id, enable_memory=True)

# Keep concerns separate
agent_code.chat("How do I optimize this database query?")
agent_code.chat("Should I use indexes?")

agent_sales.chat("Client wants a 20% discount")
agent_sales.chat("Can we negotiate?")

# Each session has its own context
```

**Best for:**
- Complex applications
- Multiple concurrent workflows
- Team collaboration

---

### **Approach 3: Stateless Per-Request**

```python
from logicore.agents import BasicAgent

def process_request(request_text: str) -> str:
    """One request = one agent instance."""
    agent = BasicAgent(enable_memory=False)
    return agent.chat(request_text)

# Each call is independent
result1 = process_request("What's the weather?")
result2 = process_request("Who won the game?")

# No context between calls
# But very clean, predictable, scalable
```

**Best for:**
- API endpoints
- Batch processing
- Microservices
- Privacy-critical work

**Benefit:**
- Zero state between requests
- Easy to scale
- No memory leaks

---

## 5. Tool Approval & Safety

Control what tools agents can use.

### **Approach 1: Allow-List (Safest)**

```python
from logicore.agents import BasicAgent

def delete_file(path: str) -> str:
    import os
    os.remove(path)
    return f"Deleted: {path}"

agent = BasicAgent()
agent.register_tool_from_function(delete_file)

# Only these tools are allowed to run
agent.tools_allowed = ["delete_file"]

# This tool is *registered* but not in allow-list
# Agent will see it, but won't be allowed to use it
response = agent.chat("Delete my cache files")
# Returns: "I cannot delete files in this context"
```

**Best for:**
- Production environments
- Sensitive operations
- High-security requirements

---

### **Approach 2: Approval Callback**

```python
from logicore.agents import BasicAgent

def delete_file(path: str) -> str:
    import os
    os.remove(path)
    return f"Deleted: {path}"

def approval_handler(tool_name: str, args: dict) -> bool:
    """Ask human before running dangerous tools."""
    dangerous = ["delete_file", "stop_server", "modify_database"]
    
    if tool_name in dangerous:
        user_input = input(f"Allow {tool_name}({args})? [y/n] ")
        return user_input.lower() == "y"
    
    return True  # Auto-approve safe tools

agent = BasicAgent(
    on_tool_approval=approval_handler
)
agent.register_tool_from_function(delete_file)

response = agent.chat("Delete files older than 30 days")
# Prompts: "Allow delete_file({'path': '...'})? [y/n]"
```

**Best for:**
- Interactive applications
- Tools that need human oversight
- Learning environments

---

### **Approach 3: Tool Categorization**

```python
from logicore.agents import BasicAgent

# Mark tools by risk level
safe_tools = [
    ("read_file", "Read a file from disk"),
    ("search", "Search the web"),
]

unsafe_tools = [
    ("delete_file", "Delete files"),
    ("execute_code", "Run arbitrary code"),
]

agent = BasicAgent()

# Register all
for name, desc in safe_tools + unsafe_tools:
    agent.register_tool(name, desc)

# But mark which ones need approval
agent.tools_require_approval = [name for name, _ in unsafe_tools]

response = agent.chat("Read the config file")
# Executes immediately (safe tool)

response2 = agent.chat("Delete old logs")
# Requires approval (unsafe tool)
```

**Best for:**
- Large tool sets with mixed risk
- Automated + human-supervised work
- Enterprise deployments

---

## 6. Scaling to Many Tools

### **Approach 1: Tool Search (Before Loading)**

```python
from logicore.agents import MCPAgent

# MCPAgent doesn't load all tools upfront
# Instead, it searches which tools might be relevant
agent = MCPAgent(
    tool_search_enabled=True,
    max_tools_per_request=10,  # Limit tools shown per call
)

# Add 100 tools from MCP servers
# But agent only sees ~5-10 relevant ones per request
response = agent.chat("Search for data science papers")
# Only loads: search_papers, summarize, convert_format tools
# Ignores: video_editing, music_generation tools

# Then next request
response2 = agent.chat("Edit this video")
# Loads different set of tools
```

**Best for:**
- 50+ tools
- Heterogeneous tool sets
- MCP (Model Context Protocol) servers

**Benefit:**
- LLM doesn't see all tools
- Faster decisions
- Lower token usage

---

### **Approach 2: Skill Hierarchy**

```python
from logicore.agents import Agent
from logicore.skills import SkillLoader

agent = Agent()
loader = SkillLoader()

# Load skill *families*
file_skills = loader.load_family("file_operations")  # read, write, search, monitor
web_skills = loader.load_family("web_tools")         # search, fetch, screenshot
code_skills = loader.load_family("code_tools")       # analyze, test, debug, format

agent.load_skill_family(file_skills)
agent.load_skill_family(web_skills)
agent.load_skill_family(code_skills)

# Agent organizes tools under 3 families
# Much clearer than 50 individual tools
response = agent.chat("Search the web and save results to a file")
# Agent: "I'll use web_tools.search, then file_operations.write"
```

**Best for:**
- Organized tool ecosystems
- Domain-specific agents
- Enterprise setups

---

### **Approach 3: Tool Namespacing**

```python
from logicore.agents import BasicAgent

agent = BasicAgent()

# Tools organized by namespace
# file_ops.read, file_ops.write, file_ops.delete
# web.search, web.fetch, web.screenshot

def read_file(path: str) -> str:
    """Read a file"""
    with open(path) as f:
        return f.read()

def write_file(path: str, content: str) -> str:
    """Write a file"""
    with open(path, 'w') as f:
        f.write(content)
    return "Written"

# Register with namespace
agent.register_tool_from_function(read_file, namespace="file_ops")
agent.register_tool_from_function(write_file, namespace="file_ops")

response = agent.chat("Read config and write to log")
# Agent sees: file_ops.read, file_ops.write
# Clear organization in prompt
```

**Best for:**
- Clear mental model
- Self-documenting code
- Tools that belong together

---

## 7. Framework Patterns

### **Pattern 1: Builder Pattern (Flexible Setup)**

```python
from logicore.agents import Agent

class AgentBuilder:
    def __init__(self):
        self.config = {}
        self.tools = []
        self.skills = []
    
    def with_provider(self, provider: str):
        self.config["provider"] = provider
        return self
    
    def with_memory(self, enabled: bool = True):
        self.config["enable_memory"] = enabled
        return self
    
    def add_tool(self, tool):
        self.tools.append(tool)
        return self
    
    def add_skill(self, skill):
        self.skills.append(skill)
        return self
    
    def build(self) -> Agent:
        agent = Agent(**self.config)
        for tool in self.tools:
            agent.register_tool(tool)
        for skill in self.skills:
            agent.load_skill(skill)
        return agent

# Use it
agent = (AgentBuilder()
    .with_provider("groq")
    .with_memory(True)
    .add_tool(calculate)
    .add_skill(web_research)
    .build())
```

**Best for:**
- Complex configurations
- Reusable agent factories
- Flexible setup

---

### **Pattern 2: Factory Method**

```python
from logicore.agents import Agent, BasicAgent, CopilotAgent

class AgentFactory:
    @staticmethod
    def create_chatbot():
        """Simple conversational agent"""
        return BasicAgent(enable_memory=True)
    
    @staticmethod
    def create_developer_assistant():
        """Full-featured agent for developers"""
        agent = CopilotAgent()
        # Comes with: file tools, git, execution
        return agent
    
    @staticmethod
    def create_enterprise():
        """Production-grade with all safeguards"""
        return Agent(
            provider="openai",
            enable_memory=True,
            max_iterations=5,
            debug=False,
            tools_require_approval=["delete_file", "execute_code"],
        )

# Use it
chatbot = AgentFactory.create_chatbot()
dev_agent = AgentFactory.create_developer_assistant()
enterprise_agent = AgentFactory.create_enterprise()
```

**Best for:**
- Predefined agent types
- Consistent setups
- Team collaboration

---

## Summary Table: Choosing Your Approach

| Component | Best Approach | When |
|-----------|--------------|------|
| **Tools** | #1 Init time | Simple apps |
| **Tools** | #2 Register | Dynamic features |
| **Tools** | #3 Classes | Complex state |
| **Tools** | #4 Skills | 50+ tools |
| **Memory** | Simple | Solo, <500 convs |
| **Memory** | Sessions | Multi-user |
| **Memory** | Filtered | Large scale, sensitive |
| **Memory** | None | APIs, privacy |
| **Providers** | Single | Stable setup |
| **Providers** | Conditional | Dev/prod difference |
| **Providers** | Fallback | High availability |
| **Providers** | Hybrid | Cost optimization |
| **Safety** | Allow-list | Production |
| **Safety** | Callback | Interactive apps |
| **Safety** | Categorized | Large tool sets |

---

## Next: Deep Dives

Ready to go deeper? Check out:
- **[Core Architecture](04-core-architecture.md)**: How these patterns work under the hood
- **[API Reference](05-api-reference.md)**: Every class and method documented

Or jump to building: pick an approach above and start coding!
