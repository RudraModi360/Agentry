# Tools: Giving Agents Superpowers

A **Tool** is any action an agent can perform: read files, search the web, execute code, query databases, etc.

---

## Why Tools Matter

Without tools, an agent is just a chatbot. With tools, it becomes:
- A **code reviewer** (can read files, run tests)
- A **researcher** (can search the web, fetch URLs)
- A **data analyst** (can query databases, run Python)
- A **system administrator** (can run commands, manage services)

Tools are what make agents actually **do things**.

---

## Built-in Tools (30+)

Logicore comes with a comprehensive toolkit ready to use.

### File Operations
```python
from logicore import Agent

agent = Agent()

# Automatically available:
# - read_file(path)
# - write_file(path, content)
# - list_files(directory)
# - search_files(pattern)
# - delete_file(path)

response = agent.chat("Read the README.md file and summarize it")
```

### Web & Search
```python
# - web_search(query)
# - fetch_url(url)
# - image_search(query)

response = agent.chat("Search for recent AI news")
```

### Code Execution
```python
# - execute_python(code)
# - execute_shell(command)
# - run_tests(directory)

response = agent.chat("Write and run Python code to analyze this data")
```

### Documents
```python
# - parse_pdf(path)
# - read_docx(path)
# - read_excel(path)
# - extract_text_from_image(image_path)

response = agent.chat("Parse this PDF and extract tables")
```

### Git Operations
```python
# - git_status()
# - git_log(n_commits)
# - git_diff(commit1, commit2)
# - git_add_commit(files, message)

response = agent.chat("Make a commit with my changes")
```

### Custom Operations
```python
# - register custom tools (see below)
```

---

## Creating Custom Tools

### Method 1: Simple Function

```python
from logicore import Agent

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    import requests
    response = requests.get(f"https://api.weatherapi.com/current?city={city}")
    return f"In {city}: {response.json()['current']['condition']}"

agent = Agent(custom_tools=[get_weather])

response = agent.chat("What's the weather in Tokyo?")
# Agent automatically calls get_weather("Tokyo")
```

### Method 2: Structured Tool Class

```python
from logicore.tools import BaseTool
from dataclasses import dataclass

@dataclass
class SearchParameters:
    query: str
    limit: int = 5

class SearchTool(BaseTool):
    name = "search"
    description = "Search for information"
    parameters_schema = SearchParameters
    
    async def execute(self, params: SearchParameters) -> str:
        # Your implementation
        results = search_api(params.query, limit=params.limit)
        return format_results(results)

agent = Agent(custom_tools=[SearchTool()])
```

### Method 3: Decorator Style

```python
from logicore import tool, Agent

@tool
def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text (positive, negative, neutral)."""
    from transformers import pipeline
    classifier = pipeline("sentiment-analysis")
    result = classifier(text)[0]
    return f"{result['label']}: {result['score']:.2f}"

@tool
def summarize_text(text: str, max_length: int = 100) -> str:
    """Summarize long text to concise version."""
    from transformers import pipeline
    summarizer = pipeline("summarization")
    summary = summarizer(text, max_length=max_length, min_length=30)
    return summary[0]["summary_text"]

agent = Agent(custom_tools=[analyze_sentiment, summarize_text])

response = agent.chat("""
Analyze this text: "I absolutely love this product! It works great."
Then summarize it.
""")
```

---

## Tool Discovery & Registration

### At Initialization
```python
def my_calculator(expression: str) -> str:
    """Calculate expressions."""
    return str(eval(expression))

agent = Agent(custom_tools=[my_calculator])
```

### After Creation
```python
agent = Agent()

def new_tool(x: str) -> str:
    """Do something."""
    return f"Result: {x}"

agent.register_tool(new_tool)
```

### From Skills (Collections)
```python
from logicore.skills import DataAnalysisSkill

agent = Agent(skills=[DataAnalysisSkill()])
# Now has: plot_chart, query_sql, run_analysis, etc.
```

### From MCP (Model Context Protocol)
```python
from logicore import MCPAgent

agent = MCPAgent(mcp_config="mcp.json")
# Automatically loads tools from MCP servers
```

---

## Tool Patterns

### Pattern 1: Input Validation

```python
from logicore import tool

@tool
def delete_file(path: str) -> str:
    """Delete a file (requires confirmation)."""
    if not path.startswith("/safe/directory/"):
        return "Error: Only files in /safe/directory can be deleted"
    
    import os
    os.remove(path)
    return f"Deleted {path}"

agent = Agent(custom_tools=[delete_file])
```

### Pattern 2: Error Handling

```python
@tool
def call_api(endpoint: str) -> str:
    """Call an API endpoint."""
    import requests
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return "Error: Request timed out"
    except requests.HTTPError as e:
        return f"Error: {e.response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### Pattern 3: Async Tools

```python
from logicore import tool
import asyncio

@tool
async def fetch_multiple_urls(urls: list[str]) -> str:
    """Fetch multiple URLs concurrently."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.text for r in responses]
```

### Pattern 4: Chainable Tools

```python
@tool
def step1_gather_data(query: str) -> str:
    """Step 1: Gather relevant data."""
    data = search_api(query)
    return data

@tool
def step2_analyze(data: str) -> str:
    """Step 2: Analyze gathered data."""
    analysis = analyze_api(data)
    return analysis

@tool
def step3_generate_report(analysis: str) -> str:
    """Step 3: Generate final report."""
    report = generate_report_api(analysis)
    return report

agent = Agent(custom_tools=[step1_gather_data, step2_analyze, step3_generate_report])
response = agent.chat("Generate a report on AI trends")
# Agent automatically chains: gather → analyze → generate
```

---

## Tool Execution Flow

```
User: "Do something"
  ↓
Agent reads tools available
  ↓
LLM decides which tool to use
  ↓
Agent validates tool exists
  ↓
Tool execution with parameters
  ↓
Result returned to LLM
  ↓
LLM formats final response
  ↓
Response to user
```

### Under the Hood

```python
agent = Agent(custom_tools=[my_tool])

response = agent.chat("Use my_tool with this input")

# Internally:
# 1. LLM sees: "I have tool: my_tool(param: str) -> str"
# 2. LLM outputs: {"tool": "my_tool", "params": {"param": "input"}}
# 3. Agent executes: my_tool(param="input")
# 4. Result added to context: "Tool result: 350"
# 5. LLM writes final response with result
```

---

## Managing Large Tool Sets

### Challenge: More Tools = More Confusion

With 50+ tools, LLMs struggle to:
- Remember what each tool does
- Pick the right one
- Use correct parameters

### Solution: Skills (Tool Groups)

```python
from logicore.skills import Skill

class DataEngineerSkill(Skill):
    name = "data_engineering"
    tools = [
        query_sql_tool,
        load_csv_tool,
        validate_data_tool,
        transform_data_tool,
    ]

class DataAnalystSkill(Skill):
    name = "data_analysis"
    tools = [
        run_statistics_tool,
        plot_chart_tool,
        generate_insights_tool,
    ]

# Only load relevant skills
agent = Agent(skills=[
    DataEngineerSkill(),
    DataAnalystSkill()
])

# LLM sees cleaner interface:
# - data_engineering (with 4 tools)
# - data_analysis (with 3 tools)
```

### Solution: Lazy Loading

```python
agent = Agent()

# Only load tools when asked
if "file" in user_query.lower():
    agent.load_skill(FileOperationSkill())

if "web" in user_query.lower():
    agent.load_skill(WebSkill())
```

---

## Tool Best Practices

✅ **DO:**
- Keep tools focused on one task
- Write clear descriptions (LLM reads these)
- Include type hints
- Add docstrings
- Return strings (easy for LLM to parse)
- Handle errors gracefully
- Add validation for dangerous operations

❌ **DON'T:**
- Create tools that do many things
- Use vague names ("do_thing", "execute")
- Return complex objects
- Raise exceptions (return error strings)
- Skip input validation
- Make tools synchronous-only in async code

### Good Tool Example

```python
@tool
def send_email(
    recipient: str,
    subject: str,
    body: str
) -> str:
    """
    Send an email to a recipient.
    
    Args:
        recipient: Email address to send to
        subject: Email subject line
        body: Email body text
    
    Returns:
        Success message or error description
    """
    try:
        if not "@" in recipient:
            return f"Error: Invalid email address: {recipient}"
        
        email_service.send(recipient, subject, body)
        return f"Email sent successfully to {recipient}"
    except Exception as e:
        return f"Error: Failed to send email: {str(e)}"
```

---

## Advanced: Tool Approval Workflows

Required confirmation before dangerous operations:

```python
agent = Agent(
    require_approval_for=[
        "delete_file",
        "execute_shell",
        "modify_database"
    ]
)

# When agent wants to use delete_file:
# 1. Agent outputs: {"tool": "delete_file", "path": "/important.txt"}
# 2. System pauses and asks human
# 3. Human approves/rejects
# 4. Only then does tool execute
```

---

## Next Steps

- [Skills](skills.md) — Organize tools into reusable packs
- [Memory](memory.md) — Tools + memory = smart agents
- [Guides: Tool Integration](../../guides/tool-integration.md) — Real examples
