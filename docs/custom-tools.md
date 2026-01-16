---
layout: page
title: Custom Tools
nav_order: 5
description: "Creating and registering custom tools for your AI agents"
---

# Custom Tools

Learn how to create and integrate custom tools into your Agentry agents.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Tool Registration Methods](#tool-registration-methods)
4. [Tool Schema Structure](#tool-schema-structure)
5. [Best Practices](#best-practices)
6. [Advanced Patterns](#advanced-patterns)
7. [Tool Approval System](#tool-approval-system)
8. [Real-World Examples](#real-world-examples)
9. [Testing Tools](#testing-tools)
10. [Debugging Tools](#debugging-tools)

---

## Overview

Custom tools are Python functions that extend your agent's capabilities beyond the built-in tools. They allow your agent to:

- Interact with external APIs
- Query databases
- Perform specialized calculations
- Integrate with third-party services
- Execute domain-specific logic

---

## Quick Start

### Simple Function Registration

```python
from agentry import Agent

def greet_user(name: str, language: str = "english") -> str:
    """Greet a user in the specified language."""
    greetings = {
        "english": f"Hello, {name}!",
        "spanish": f"Hola, {name}!",
        "french": f"Bonjour, {name}!",
        "german": f"Guten Tag, {name}!"
    }
    return greetings.get(language.lower(), greetings["english"])

# Register the tool
agent = Agent(llm="ollama")
agent.register_tool_from_function(greet_user)

# Agent can now use the tool
response = await agent.chat("Greet Alice in Spanish")
```

---

## Tool Registration Methods

### Method 1: Automatic Registration (Recommended)

Agentry automatically generates the tool schema from your function's signature and docstring:

```python
def calculate_tip(bill_amount: float, tip_percentage: float = 15.0) -> str:
    """Calculate tip amount and total bill.
    
    Use this when the user wants to calculate a tip for a restaurant bill.
    """
    tip = bill_amount * (tip_percentage / 100)
    total = bill_amount + tip
    return f"Tip: ${tip:.2f}, Total: ${total:.2f}"

agent.register_tool_from_function(calculate_tip)
```

**Requirements for Automatic Registration:**

| Requirement | Description |
|:------------|:------------|
| Type hints | All parameters must have type annotations |
| Docstring | Function must have a docstring describing its purpose |
| Return type | Function should return a string |

---

### Method 2: Manual Schema Definition

For complete control over the tool schema:

```python
def my_custom_tool(arg1, arg2):
    """Process two arguments."""
    return f"Processed {arg1} and {arg2}"

schema = {
    "type": "function",
    "function": {
        "name": "my_custom_tool",
        "description": "Processes two arguments and returns a formatted result",
        "parameters": {
            "type": "object",
            "properties": {
                "arg1": {
                    "type": "string",
                    "description": "The first argument to process"
                },
                "arg2": {
                    "type": "string",
                    "description": "The second argument to process"
                }
            },
            "required": ["arg1", "arg2"]
        }
    }
}

agent.add_custom_tool(schema, my_custom_tool)
```

---

### Method 3: Class-Based Tools

For tools requiring persistent state:

```python
class DatabaseTool:
    def __init__(self, connection_string: str):
        self.conn = connection_string
    
    def query(self, sql: str) -> str:
        """Execute a SQL query and return results."""
        # Database logic here
        return f"Results from: {sql}"

# Create instance
db_tool = DatabaseTool("postgresql://localhost/mydb")

# Register the method
agent.register_tool_from_function(db_tool.query)
```

---

## Tool Schema Structure

Every tool has a schema that tells the LLM:

![Tool Schema Structure](assets/images/tool-schema-structure.png)

**Schema Fields:**

| Field | Type | Description |
|:------|:-----|:------------|
| `type` | string | Always "function" |
| `function.name` | string | Tool identifier |
| `function.description` | string | When to use the tool |
| `function.parameters` | object | Input parameters definition |
| `parameters.properties` | object | Individual parameter definitions |
| `parameters.required` | array | List of required parameter names |

---

## Best Practices

### 1. Write Clear Docstrings

The docstring is crucial—it tells the LLM when to use your tool:

```python
# Poor: Vague description
def calc(x, y):
    """Calculate."""
    return x + y

# Good: Clear and specific
def calculate_compound_interest(
    principal: float,
    rate: float,
    time: int,
    compounds_per_year: int = 12
) -> str:
    """
    Calculate compound interest for an investment.
    
    Use this when the user wants to know how much money they'll have
    after investing a certain amount at a given interest rate.
    """
    amount = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * time)
    return f"Final amount: ${amount:.2f}"
```

### 2. Use Complete Type Hints

Type hints help generate accurate schemas:

```python
from typing import List, Dict, Optional

def search_products(
    query: str,
    category: Optional[str] = None,
    max_results: int = 10
) -> str:
    """Search for products in the catalog."""
    # Implementation
    return "Found 5 products matching query"
```

**Type Mapping:**

| Python Type | JSON Schema Type |
|:------------|:-----------------|
| `str` | `string` |
| `int` | `integer` |
| `float` | `number` |
| `bool` | `boolean` |
| `List[str]` | `array` |
| `Optional[str]` | `string` (not required) |

### 3. Return Structured Data

Return data in a format the LLM can understand:

```python
import json

def get_user_info(user_id: str) -> str:
    """Get user information by ID."""
    user = fetch_user(user_id)
    return json.dumps({
        "name": user.name,
        "email": user.email,
        "status": user.status
    }, indent=2)
```

### 4. Handle Errors Gracefully

Always catch and return errors as strings:

```python
import requests

def fetch_weather(city: str) -> str:
    """Get weather information for a city."""
    try:
        response = requests.get(f"https://api.weather.com/{city}")
        response.raise_for_status()
        data = response.json()
        return f"Temperature: {data['temp']}C, Conditions: {data['conditions']}"
    except requests.RequestException as e:
        return f"Error fetching weather: {str(e)}"
    except KeyError as e:
        return f"Unexpected response format: {str(e)}"
```

### 5. Keep Tools Focused

Each tool should do one thing well:

```python
# Poor: Too many responsibilities
def do_everything(action, data):
    """Do various things."""
    if action == "email":
        send_email(data)
    elif action == "sms":
        send_sms(data)

# Good: Separate, focused tools
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    # Email logic
    return "Email sent successfully"

def send_sms(phone: str, message: str) -> str:
    """Send an SMS to a phone number."""
    # SMS logic
    return "SMS sent successfully"
```

---

## Advanced Patterns

### Async Tools

For I/O-bound operations:

```python
import aiohttp
import asyncio

async def fetch_url_async(url: str) -> str:
    """Fetch content from a URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return content[:500]

# Wrapper for sync execution
def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    return asyncio.run(fetch_url_async(url))

agent.register_tool_from_function(fetch_url)
```

### Tools with Configuration

```python
class APITool:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def call_api(self, endpoint: str, method: str = "GET") -> str:
        """Call an API endpoint."""
        import requests
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.request(method, url, headers=headers)
        return response.text

# Initialize with config
api_tool = APITool(api_key="your-key", base_url="https://api.example.com")
agent.register_tool_from_function(api_tool.call_api)
```

### Caching Tool Results

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_calculation(n: int) -> str:
    """Perform an expensive calculation (results are cached)."""
    result = sum(i**2 for i in range(n))
    return f"Result: {result}"

agent.register_tool_from_function(expensive_calculation)
```

---

## Tool Approval System

For dangerous operations, Agentry can require user approval.

### Built-in Dangerous Tools

These tools automatically require approval:

- `delete_file`
- `run_shell_command`
- `execute_python`

### Custom Approval

```python
from agentry.tools import APPROVAL_REQUIRED_TOOLS

# Add your tool to the approval list
APPROVAL_REQUIRED_TOOLS.add("send_email")

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email (requires approval)."""
    # Email logic
    return f"Email sent to {to}"

agent.register_tool_from_function(send_email)

# Set approval callback
async def approval_callback(session_id, tool_name, args):
    print(f"Tool '{tool_name}' wants to execute with args: {args}")
    user_input = input("Approve? (y/n): ")
    return user_input.lower() == 'y'

agent.set_callbacks(on_tool_approval=approval_callback)
```

---

## Real-World Examples

### Slack Integration

```python
from slack_sdk import WebClient

class SlackTool:
    def __init__(self, token: str):
        self.client = WebClient(token=token)
    
    def send_message(self, channel: str, message: str) -> str:
        """Send a message to a Slack channel."""
        try:
            self.client.chat_postMessage(channel=channel, text=message)
            return f"Message sent to #{channel}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def list_channels(self) -> str:
        """List all Slack channels."""
        try:
            response = self.client.conversations_list()
            channels = [ch['name'] for ch in response['channels']]
            return f"Channels: {', '.join(channels)}"
        except Exception as e:
            return f"Error: {str(e)}"

slack = SlackTool(token="xoxb-your-token")
agent.register_tool_from_function(slack.send_message)
agent.register_tool_from_function(slack.list_channels)
```

### Database Operations

```python
import sqlite3

class DatabaseTool:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def execute_query(self, sql: str) -> str:
        """Execute a SELECT query and return results."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return "No results found"
            
            return "\n".join([str(row) for row in results])
        except Exception as e:
            return f"Database error: {str(e)}"

db = DatabaseTool("myapp.db")
agent.register_tool_from_function(db.execute_query)
```

### HTTP API Client

```python
import requests

def api_request(
    url: str,
    method: str = "GET",
    headers: str = "{}",
    body: str = "{}"
) -> str:
    """Make an HTTP request to an API endpoint.
    
    Use this to interact with REST APIs. Headers and body should be JSON strings.
    """
    import json
    
    try:
        parsed_headers = json.loads(headers)
        parsed_body = json.loads(body) if body != "{}" else None
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=parsed_headers,
            json=parsed_body
        )
        
        return json.dumps({
            "status_code": response.status_code,
            "body": response.text[:1000]
        }, indent=2)
    except Exception as e:
        return f"Request error: {str(e)}"

agent.register_tool_from_function(api_request)
```

---

## Testing Tools

### Unit Testing

```python
import pytest

def test_calculate_tip():
    result = calculate_tip(100.0, 20.0)
    assert "Tip: $20.00" in result
    assert "Total: $120.00" in result

def test_greet_user():
    result = greet_user("Alice", "spanish")
    assert "Hola, Alice!" in result
```

### Integration Testing

```python
async def test_tool_with_agent():
    agent = Agent(llm="ollama")
    agent.register_tool_from_function(calculate_tip)
    
    response = await agent.chat("Calculate a 20% tip on a $50 bill")
    assert "$10.00" in response
```

---

## Debugging Tools

### Enable Debug Mode

```python
agent = Agent(llm="ollama", debug=True)
# Shows when tools are called and their results
```

### Add Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

def my_tool(arg: str) -> str:
    """My custom tool."""
    logging.debug(f"Tool called with: {arg}")
    result = process(arg)
    logging.debug(f"Tool result: {result}")
    return result
```

### Use Callbacks

```python
def on_tool_start(session_id, tool_name, args):
    print(f"Starting: {tool_name}")
    print(f"Arguments: {args}")

def on_tool_end(session_id, tool_name, result):
    print(f"Completed: {tool_name}")
    print(f"Result: {result}")

agent.set_callbacks(
    on_tool_start=on_tool_start,
    on_tool_end=on_tool_end
)
```

---

## Next Steps

| Topic | Description |
|:------|:------------|
| [Examples](examples) | More practical examples |
| [MCP Integration](mcp-integration) | External tool servers |
| [API Reference](api-reference) | Complete API documentation |
