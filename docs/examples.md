---
layout: page
title: Examples
nav_order: 8
description: "Practical code examples and use cases for Agentry"
---

# Examples

Practical code examples and use cases for Agentry.

## Table of Contents

1. [Basic Examples](#basic-examples)
2. [Custom Tools](#custom-tools)
3. [Session Management](#session-management)
4. [Multi-Agent Systems](#multi-agent-systems)
5. [MCP Integration](#mcp-integration)
6. [Real-World Use Cases](#real-world-use-cases)
7. [Interactive Examples](#interactive-examples)

---

## Basic Examples

### Simple Chat

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    response = await agent.chat("Tell me a joke")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Filesystem Operations

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.load_default_tools()
    
    # List files
    response = await agent.chat("List files in the current directory")
    print(response)
    
    # Create file
    response = await agent.chat("Create a file called 'hello.txt' with 'Hello World'")
    print(response)
    
    # Read file
    response = await agent.chat("Read 'hello.txt'")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Web Search

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.load_default_tools()
    
    response = await agent.chat("Search for the latest Python version and tell me its features")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Code Execution

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.load_default_tools()
    
    response = await agent.chat("Write and execute a Python script to calculate Fibonacci sequence")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Custom Tools

### BMI Calculator

```python
import asyncio
from agentry import Agent

def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """Calculate BMI given weight in kg and height in meters."""
    bmi = weight_kg / (height_m ** 2)
    return f"BMI: {bmi:.2f}"

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.register_tool_from_function(calculate_bmi)
    
    response = await agent.chat("My weight is 70kg and height is 1.75m. What is my BMI?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Weather API Tool

```python
import asyncio
import requests
from agentry import Agent

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Mocking API response for example
    return f"Weather in {city}: 25°C, Sunny"

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.register_tool_from_function(get_weather)
    
    response = await agent.chat("What's the weather in New York?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Database Query Tool

```python
import asyncio
import sqlite3
from agentry import Agent

def query_database(sql: str) -> str:
    """Execute SQL query on the 'users.db' database."""
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return str(results)
    except Exception as e:
        return f"Error: {e}"

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.register_tool_from_function(query_database)
    
    response = await agent.chat("Find all users with age > 25")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Session Management

### Multi-Turn Conversation

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    session_id = "user_1"
    
    await agent.chat("My name is Alice", session_id=session_id)
    response = await agent.chat("What is my name?", session_id=session_id)
    print(response)  # Should say "Alice"

if __name__ == "__main__":
    asyncio.run(main())
```

### Saving and Loading Sessions

```python
import asyncio
from agentry import Agent, SessionManager

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    sm = SessionManager()
    session_id = "my_project"
    
    # Interaction 1
    await agent.chat("Let's plan a project", session_id=session_id)
    sm.save_session(session_id, agent.get_session(session_id).messages)
    
    # Later... Interaction 2
    messages = sm.load_session(session_id)
    agent.get_session(session_id).messages = messages
    
    response = await agent.chat("What was the first step?", session_id=session_id)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Session Metadata

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    session = agent.get_session("user_123")
    
    # Set metadata
    session.metadata = {
        "user_id": 123,
        "subscription": "premium",
        "preferences": {"theme": "dark"}
    }
    
    # Access metadata later
    print(agent.get_session("user_123").metadata)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Multi-Agent Systems

### Specialized Agents

```python
import asyncio
from agentry import Agent

async def main():
    # Coding specialist
    coder = Agent(
        llm="ollama", 
        model="codellama", 
        system_message="You are a Python expert."
    )
    
    # Writer specialist
    writer = Agent(
        llm="ollama", 
        model="llama3.2", 
        system_message="You are a technical writer."
    )
    
    # Workflow
    code_task = "Create a function to calculate factorial"
    code = await coder.chat(code_task)
    print(f"Code:\n{code}")
    
    doc_task = f"Write documentation for this code:\n{code}"
    docs = await writer.chat(doc_task)
    print(f"Docs:\n{docs}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Collaborative Agents

```python
import asyncio
from agentry import Agent

async def main():
    manager = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="...")
    researcher = Agent(llm="ollama", model="llama3.2")
    
    researcher.load_default_tools()
    
    # Manager delegates
    plan = await manager.chat("Create a plan to research quantum computing trends")
    print(f"Plan: {plan}")
    
    # Researcher executes
    report = await researcher.chat(f"Execute this research plan: {plan}")
    print(f"Report: {report}")
    
    # Manager summarizes
    summary = await manager.chat(f"Summarize this report for executives: {report}")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## MCP Integration

### Using Excel Tool

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    
    # Create mcp.json first
    # { "mcpServers": { "excel": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-excel"] } } }
    
    await agent.add_mcp_server("mcp.json")
    
    response = await agent.chat("Read the 'Sales' sheet from 'data.xlsx' and find the total revenue")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Multiple MCP Servers

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    
    # Configuration with filesystem and excel tools
    await agent.add_mcp_server("mcp_config.json")
    
    task = """
    1. List files in the 'data' directory
    2. Find the latest Excel file
    3. Read its contents
    4. Create a summary text file
    """
    
    response = await agent.chat(task)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Real-World Use Cases

### Automated Code Reviewer

```python
import asyncio
import os
from agentry import CopilotAgent

async def review_repo(repo_path):
    copilot = CopilotAgent(llm="ollama", model="codellama")
    copilot.load_default_tools()
    
    files = [f for f in os.listdir(repo_path) if f.endswith('.py')]
    
    for file in files:
        print(f"Reviewing {file}...")
        review = await copilot.review_file(os.path.join(repo_path, file))
        
        with open(f"{file}_review.md", "w") as f:
            f.write(review)
            
    print("Review complete!")

if __name__ == "__main__":
    asyncio.run(review_repo("./my_project"))
```

### Documentation Generator

```python
import asyncio
from agentry import Agent, CopilotAgent

async def generate_docs():
    reader = Agent(llm="ollama", model="llama3.2")
    reader.load_default_tools()
    
    writer = CopilotAgent(llm="ollama", model="codellama")
    
    # Read code
    code = await reader.chat("Read the file 'main.py'")
    
    # Generate docs
    docs = await writer.chat(f"Generate Google-style docstrings for this code:\n{code}")
    
    # Save docs
    await reader.chat(f"Save this documentation to 'docs.md':\n{docs}")

if __name__ == "__main__":
    asyncio.run(generate_docs())
```

### Data Analysis Assistant

```python
import asyncio
from agentry import Agent

async def analyze_data():
    agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="...")
    agent.load_default_tools()
    # Assuming MCP excel tool is configured
    await agent.add_mcp_server("mcp.json")
    
    query = """
    Analyze the sales data in 'sales_2024.xlsx'.
    Identify the top 3 products by revenue.
    Calculate the month-over-month growth rate.
    Suggest marketing strategies based on the data.
    """
    
    response = await agent.chat(query)
    print(response)

if __name__ == "__main__":
    asyncio.run(analyze_data())
```

### DevOps Helper

```python
import asyncio
from agentry import Agent

async def devops_task():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.load_default_tools()
    
    task = """
    Check disk usage on the current system.
    If any log files in /var/log are larger than 100MB, list them.
    Create a report in 'system_health.txt'.
    """
    
    # Note: Requires appropriate permissions and 'run_shell_command' tool
    response = await agent.chat(task)
    print(response)

if __name__ == "__main__":
    asyncio.run(devops_task())
```

### Customer Support Bot

```python
import asyncio
from agentry import Agent

async def support_bot():
    agent = Agent(
        llm="ollama", 
        model="llama3.2",
        system_message="You are a helpful support agent for TechCorp. Answer queries politely."
    )
    
    # Knowledge base tool
    def search_knowledge_base(query: str) -> str:
        """Search the support knowledge base."""
        # Simulated search
        kb = {
            "reset password": "Go to settings > security > reset password",
            "refund": "Contact billing@techcorp.com",
            "pricing": "Basic: $10/mo, Pro: $25/mo"
        }
        for key, value in kb.items():
            if key in query.lower():
                return value
        return "No information found."
        
    agent.register_tool_from_function(search_knowledge_base)
    
    print("Support Bot Ready (type 'exit' to quit)")
    while True:
        user_input = input("User: ")
        if user_input.lower() == 'exit':
            break
            
        response = await agent.chat(user_input)
        print(f"Bot: {response}")

if __name__ == "__main__":
    asyncio.run(support_bot())
```

---

## Interactive Examples

### Agent with Callbacks

```python
import asyncio
from agentry import Agent

def on_tool_start(session_id, tool_name, args):
    print(f"🔧 Tool Start: {tool_name}")

def on_tool_end(session_id, tool_name, result):
    print(f"✅ Tool Result: {result[:50]}...")

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.load_default_tools()
    
    agent.set_callbacks(
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end
    )
    
    await agent.chat("Search regular expressions for email validation")

if __name__ == "__main__":
    asyncio.run(main())
```

### Agent with Approval

```python
import asyncio
from agentry import Agent

async def on_approval(session_id, tool_name, args):
    print(f"⚠️ Tool '{tool_name}' requires approval.")
    print(f"Args: {args}")
    choice = input("Approve? (y/n): ")
    return choice.lower() == 'y'

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.load_default_tools()
    
    agent.set_callbacks(on_tool_approval=on_approval)
    
    # Dangerous operation
    await agent.chat("Delete the file 'important.txt'")

if __name__ == "__main__":
    asyncio.run(main())
```
