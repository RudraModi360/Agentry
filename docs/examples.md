# Examples

Practical examples to help you get started with Agentry.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Custom Tools](#custom-tools)
- [Session Management](#session-management)
- [Multi-Agent Systems](#multi-agent-systems)
- [MCP Integration](#mcp-integration)
- [Real-World Use Cases](#real-world-use-cases)

## Basic Examples

### Simple Chat Agent

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    agent.load_default_tools()
    
    response = await agent.chat("Hello! What can you help me with?")
    print(response)

asyncio.run(main())
```

### File Operations

```python
async def file_operations():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    # Create a file
    await agent.chat("Create a file called notes.txt with 'Hello World'")
    
    # Read it back
    response = await agent.chat("What's in notes.txt?")
    print(response)
    
    # Modify it
    await agent.chat("Add 'This is a new line' to notes.txt")

asyncio.run(file_operations())
```

### Web Search

```python
async def web_search():
    agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="your-key")
    agent.load_default_tools()
    
    response = await agent.chat("Search the web for latest Python 3.12 features")
    print(response)

asyncio.run(web_search())
```

### Code Execution

```python
async def code_execution():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    response = await agent.chat(
        "Write and execute Python code to calculate the factorial of 10"
    )
    print(response)

asyncio.run(code_execution())
```

## Custom Tools

### Simple Calculator Tool

```python
from agentry import Agent

def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """Calculate Body Mass Index given weight in kg and height in meters."""
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return f"BMI: {bmi:.2f} ({category})"

async def main():
    agent = Agent(llm="ollama")
    agent.register_tool_from_function(calculate_bmi)
    
    response = await agent.chat("Calculate BMI for someone 70kg and 1.75m tall")
    print(response)

asyncio.run(main())
```

### Weather Tool (API Integration)

```python
import requests

def get_weather(city: str) -> str:
    """Get current weather for a city using OpenWeatherMap API."""
    api_key = "your-api-key"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        
        return f"Weather in {city}: {temp}°C, {description}"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

async def main():
    agent = Agent(llm="ollama")
    agent.register_tool_from_function(get_weather)
    
    response = await agent.chat("What's the weather in London?")
    print(response)

asyncio.run(main())
```

### Database Query Tool

```python
import sqlite3

def query_database(sql: str) -> str:
    """Execute a SQL query on the local database and return results."""
    try:
        conn = sqlite3.connect('mydata.db')
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        
        return str(results)
    except Exception as e:
        return f"Database error: {str(e)}"

async def main():
    agent = Agent(llm="ollama")
    agent.register_tool_from_function(query_database)
    
    response = await agent.chat("Show me all users from the database")
    print(response)

asyncio.run(main())
```

## Session Management

### Multi-Turn Conversation

```python
async def multi_turn():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    session_id = "user_alice"
    
    # First interaction
    await agent.chat("My name is Alice", session_id=session_id)
    
    # Second interaction - agent remembers
    await agent.chat("Create a file called alice_notes.txt", session_id=session_id)
    
    # Third interaction - still remembers
    response = await agent.chat("What's my name?", session_id=session_id)
    print(response)  # "Your name is Alice"

asyncio.run(multi_turn())
```

### Saving and Loading Sessions

```python
from agentry import Agent
from agentry.session_manager import SessionManager

async def persistent_sessions():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    manager = SessionManager(storage_dir="./my_sessions")
    
    # Chat
    session_id = "project_123"
    await agent.chat("Create a Python project structure", session_id=session_id)
    
    # Save session
    session = agent.get_session(session_id)
    await manager.save_session(session)
    
    # Later... load it back
    loaded_session = await manager.load_session(session_id)
    agent.sessions[session_id] = loaded_session
    
    # Continue conversation
    await agent.chat("Now add a README", session_id=session_id)

asyncio.run(persistent_sessions())
```

### Session Metadata

```python
async def session_with_metadata():
    agent = Agent(llm="ollama")
    
    session = agent.get_session("user_bob")
    session.metadata = {
        "user_id": "bob123",
        "preferences": {"language": "python", "style": "concise"},
        "project": "web_scraper"
    }
    
    await agent.chat("Help me with my project", session_id="user_bob")
    
    # Access metadata later
    print(session.metadata["project"])  # "web_scraper"

asyncio.run(session_with_metadata())
```

## Multi-Agent Systems

### Specialized Agents

```python
async def multi_agent_system():
    # Research agent
    researcher = Agent(
        llm="groq",
        model="llama-3.3-70b-versatile",
        api_key="your-key",
        system_message="You are a research assistant. Focus on finding accurate information."
    )
    researcher.load_default_tools()
    
    # Coding agent
    coder = Agent(
        llm="ollama",
        model="codellama",
        system_message="You are a coding expert. Write clean, efficient code."
    )
    coder.load_default_tools()
    
    # Writer agent
    writer = Agent(
        llm="gemini",
        model="gemini-pro",
        api_key="your-key",
        system_message="You are a technical writer. Create clear documentation."
    )
    
    # Workflow
    research = await researcher.chat("Research best practices for REST APIs")
    code = await coder.chat(f"Based on this research, create a REST API example: {research}")
    docs = await writer.chat(f"Document this API: {code}")
    
    print(docs)

asyncio.run(multi_agent_system())
```

### Agent Collaboration

```python
async def collaborative_agents():
    planner = Agent(llm="ollama", system_message="You create project plans")
    executor = Agent(llm="ollama", system_message="You execute tasks")
    executor.load_default_tools()
    
    # Planner creates a plan
    plan = await planner.chat("Create a plan to build a todo app")
    
    # Executor follows the plan
    result = await executor.chat(f"Execute this plan: {plan}")
    
    print(result)

asyncio.run(collaborative_agents())
```

## MCP Integration

### Excel Integration

```python
async def excel_agent():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    # Connect to Excel MCP server
    await agent.add_mcp_server("mcp.json")
    
    # Now agent can work with Excel files
    await agent.chat("Read data from sales.xlsx and calculate total revenue")
    await agent.chat("Create a new sheet with monthly summaries")

asyncio.run(excel_agent())
```

**mcp.json:**
```json
{
  "mcpServers": {
    "excel": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-excel"]
    }
  }
}
```

### Multiple MCP Servers

```python
async def multi_mcp():
    agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="your-key")
    
    # Connect to multiple MCP servers
    await agent.add_mcp_server("mcp_excel.json")
    await agent.add_mcp_server("mcp_database.json")
    await agent.add_mcp_server("mcp_slack.json")
    
    # Agent can now use tools from all servers
    await agent.chat("Get data from database, analyze in Excel, and send summary to Slack")

asyncio.run(multi_mcp())
```

## Real-World Use Cases

### Code Review Assistant

```python
async def code_reviewer():
    agent = Agent(
        llm="ollama",
        model="codellama",
        system_message="You are a code reviewer. Provide constructive feedback."
    )
    agent.load_default_tools()
    
    response = await agent.chat(
        "Review the Python files in ./src directory and suggest improvements"
    )
    print(response)

asyncio.run(code_reviewer())
```

### Documentation Generator

```python
async def doc_generator():
    agent = Agent(llm="gemini", model="gemini-pro", api_key="your-key")
    agent.load_default_tools()
    
    await agent.chat(
        "Read all Python files in ./myproject and generate a comprehensive README.md"
    )

asyncio.run(doc_generator())
```

### Data Analysis Assistant

```python
async def data_analyst():
    agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="your-key")
    agent.load_default_tools()
    
    await agent.chat("""
        1. Read data.csv
        2. Calculate basic statistics (mean, median, std)
        3. Identify outliers
        4. Create a summary report in analysis.txt
    """)

asyncio.run(data_analyst())
```

### DevOps Helper

```python
async def devops_agent():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    # System monitoring
    await agent.chat("Check disk usage and list processes using most memory")
    
    # Log analysis
    await agent.chat("Search for errors in /var/log/app.log from the last hour")
    
    # Deployment
    await agent.chat("Run the deployment script and verify the service is running")

asyncio.run(devops_agent())
```

### Customer Support Bot

```python
async def support_bot():
    agent = Agent(
        llm="groq",
        model="llama-3.3-70b-versatile",
        api_key="your-key",
        system_message="You are a helpful customer support agent."
    )
    
    # Custom tool for checking order status
    def check_order(order_id: str) -> str:
        """Check the status of an order."""
        # In real app, query database
        return f"Order {order_id} is being shipped"
    
    agent.register_tool_from_function(check_order)
    
    # Handle customer query
    session_id = "customer_456"
    response = await agent.chat(
        "What's the status of my order #12345?",
        session_id=session_id
    )
    print(response)

asyncio.run(support_bot())
```

## Interactive Examples

### Chat Loop with Commands

```python
async def interactive_chat():
    agent = Agent(llm="ollama", debug=True)
    agent.load_default_tools()
    
    session_id = "interactive"
    
    print("Chat with the agent (type 'exit' to quit)")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            break
        
        if user_input.lower() == '/clear':
            agent.clear_session(session_id)
            print("Session cleared!")
            continue
        
        response = await agent.chat(user_input, session_id=session_id)
        print(f"\nAgent: {response}")

asyncio.run(interactive_chat())
```

### Callback Monitoring

```python
async def monitored_agent():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    # Set up callbacks
    def on_tool_start(session_id, tool_name, args):
        print(f"🔧 Calling tool: {tool_name}")
        print(f"   Args: {args}")
    
    def on_tool_end(session_id, tool_name, result):
        print(f"✅ Tool {tool_name} completed")
        print(f"   Result: {result}")
    
    def on_final_message(session_id, message):
        print(f"💬 Final response: {message}")
    
    agent.set_callbacks(
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
        on_final_message=on_final_message
    )
    
    await agent.chat("Create a file and write 'Hello' to it")

asyncio.run(monitored_agent())
```

## Next Steps

- Learn about [Custom Tools](custom-tools.md) in detail
- Explore [Session Management](session-management.md)
- Check the [API Reference](api-reference.md)
- Build your own agent!

---

**Need help?** Open an issue on [GitHub](https://github.com/RudraModi360/Agentry/issues)
