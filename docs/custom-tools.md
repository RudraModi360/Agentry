# Custom Tools

Learn how to create and integrate custom tools into your Scratchy agents.

## Table of Contents

- [What are Custom Tools?](#what-are-custom-tools)
- [Quick Start](#quick-start)
- [Tool Registration Methods](#tool-registration-methods)
- [Best Practices](#best-practices)
- [Advanced Patterns](#advanced-patterns)
- [Tool Approval System](#tool-approval-system)

## What are Custom Tools?

Custom tools are Python functions that extend your agent's capabilities beyond the built-in tools. They allow your agent to:

- Interact with external APIs
- Query databases
- Perform specialized calculations
- Integrate with third-party services
- Execute domain-specific logic

## Quick Start

### Simple Function to Tool

```python
from scratchy import Agent

def greet_user(name: str, language: str = "english") -> str:
    """Greet a user in the specified language."""
    greetings = {
        "english": f"Hello, {name}!",
        "spanish": f"¡Hola, {name}!",
        "french": f"Bonjour, {name}!",
        "german": f"Guten Tag, {name}!"
    }
    return greetings.get(language.lower(), greetings["english"])

# Register the tool
agent = Agent(llm="ollama")
agent.register_tool_from_function(greet_user)

# Use it
await agent.chat("Greet Alice in Spanish")
```

That's it! The agent can now use your function.

## Tool Registration Methods

### Method 1: Auto-Registration (Recommended)

The easiest way - Scratchy automatically generates the schema from your function:

```python
def calculate_tip(bill_amount: float, tip_percentage: float = 15.0) -> str:
    """Calculate tip amount and total bill."""
    tip = bill_amount * (tip_percentage / 100)
    total = bill_amount + tip
    return f"Tip: ${tip:.2f}, Total: ${total:.2f}"

agent.register_tool_from_function(calculate_tip)
```

**Requirements:**
- Type hints for parameters
- Docstring describing what the function does
- Return type annotation

### Method 2: Manual Schema Definition

For more control over the schema:

```python
def my_custom_tool(arg1, arg2):
    """Do something custom."""
    return f"Processed {arg1} and {arg2}"

# Define schema manually
schema = {
    "type": "function",
    "function": {
        "name": "my_custom_tool",
        "description": "Processes two arguments and returns a result",
        "parameters": {
            "type": "object",
            "properties": {
                "arg1": {
                    "type": "string",
                    "description": "The first argument"
                },
                "arg2": {
                    "type": "string",
                    "description": "The second argument"
                }
            },
            "required": ["arg1", "arg2"]
        }
    }
}

agent.add_custom_tool(schema, my_custom_tool)
```

### Method 3: Class-Based Tools

For complex tools with state:

```python
class DatabaseTool:
    def __init__(self, connection_string):
        self.conn = connection_string
    
    def query(self, sql: str) -> str:
        """Execute a SQL query and return results."""
        # Your database logic here
        return f"Results from: {sql}"

# Create instance
db_tool = DatabaseTool("postgresql://localhost/mydb")

# Register the method
agent.register_tool_from_function(db_tool.query)
```

## Best Practices

### 1. Write Clear Docstrings

The docstring is crucial - it tells the LLM when to use your tool:

```python
# ❌ Bad
def calc(x, y):
    """Calculate."""
    return x + y

# ✅ Good
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

### 2. Use Type Hints

Type hints help generate accurate schemas:

```python
from typing import List, Dict, Optional

def search_products(
    query: str,
    category: Optional[str] = None,
    max_results: int = 10
) -> List[Dict[str, str]]:
    """Search for products in the catalog."""
    # Implementation
    return [{"name": "Product 1", "price": "$10"}]
```

### 3. Return Structured Data

Return data in a format the LLM can understand:

```python
# ✅ Good - Clear structure
def get_user_info(user_id: str) -> str:
    """Get user information by ID."""
    user = fetch_user(user_id)
    return f"Name: {user.name}, Email: {user.email}, Status: {user.status}"

# ✅ Also good - JSON string
import json

def get_user_info_json(user_id: str) -> str:
    """Get user information as JSON."""
    user = fetch_user(user_id)
    return json.dumps({
        "name": user.name,
        "email": user.email,
        "status": user.status
    })
```

### 4. Handle Errors Gracefully

Always catch and return errors as strings:

```python
def fetch_weather(city: str) -> str:
    """Get weather information for a city."""
    try:
        response = requests.get(f"https://api.weather.com/{city}")
        response.raise_for_status()
        data = response.json()
        return f"Temperature: {data['temp']}°C, Conditions: {data['conditions']}"
    except requests.RequestException as e:
        return f"Error fetching weather: {str(e)}"
    except KeyError as e:
        return f"Unexpected response format: {str(e)}"
```

### 5. Keep Tools Focused

Each tool should do one thing well:

```python
# ❌ Bad - Too many responsibilities
def do_everything(action, data):
    """Do various things."""
    if action == "email":
        send_email(data)
    elif action == "sms":
        send_sms(data)
    # ...

# ✅ Good - Separate, focused tools
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    # Email logic
    return "Email sent successfully"

def send_sms(phone: str, message: str) -> str:
    """Send an SMS to a phone number."""
    # SMS logic
    return "SMS sent successfully"
```

## Advanced Patterns

### Async Tools

For I/O-bound operations:

```python
import aiohttp

async def fetch_url_async(url: str) -> str:
    """Fetch content from a URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return content[:500]  # Return first 500 chars

# Note: Currently, Scratchy's execute_tool is sync
# You'll need to wrap async functions:
import asyncio

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
    """Perform an expensive calculation (cached)."""
    # Expensive operation
    result = sum(i**2 for i in range(n))
    return f"Result: {result}"

agent.register_tool_from_function(expensive_calculation)
```

### Tools with Side Effects

```python
def create_backup(directory: str) -> str:
    """Create a backup of the specified directory."""
    import shutil
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.zip"
    
    try:
        shutil.make_archive(
            f"backups/{backup_name}",
            'zip',
            directory
        )
        return f"Backup created: {backup_name}"
    except Exception as e:
        return f"Backup failed: {str(e)}"

agent.register_tool_from_function(create_backup)
```

## Tool Approval System

For dangerous operations, you can require user approval:

### Built-in Dangerous Tools

Scratchy automatically requires approval for:
- `delete_file`
- `run_shell_command`
- `execute_python`

### Custom Approval

```python
from scratchy.tools import APPROVAL_REQUIRED_TOOLS

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
            response = self.client.chat_postMessage(
                channel=channel,
                text=message
            )
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

# Setup
slack = SlackTool(token="xoxb-your-token")
agent.register_tool_from_function(slack.send_message)
agent.register_tool_from_function(slack.list_channels)

# Use
await agent.chat("Send 'Hello team!' to the #general channel")
```

### Database Operations

```python
import sqlite3
from typing import List

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
    
    def insert_record(self, table: str, data: dict) -> str:
        """Insert a record into a table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            cursor.execute(sql, list(data.values()))
            conn.commit()
            conn.close()
            
            return f"Record inserted into {table}"
        except Exception as e:
            return f"Insert error: {str(e)}"

# Setup
db = DatabaseTool("myapp.db")
agent.register_tool_from_function(db.execute_query)
agent.register_tool_from_function(db.insert_record)
```

### Email Tool

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailTool:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email to a recipient."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return f"Email sent to {to}"
        except Exception as e:
            return f"Email error: {str(e)}"

# Setup
email = EmailTool(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password"
)
agent.register_tool_from_function(email.send_email)
```

## Testing Your Tools

### Unit Testing

```python
import pytest

def test_calculate_tip():
    result = calculate_tip(100.0, 20.0)
    assert "Tip: $20.00" in result
    assert "Total: $120.00" in result

def test_greet_user():
    result = greet_user("Alice", "spanish")
    assert "¡Hola, Alice!" in result
```

### Integration Testing with Agent

```python
async def test_tool_with_agent():
    agent = Agent(llm="ollama")
    agent.register_tool_from_function(calculate_tip)
    
    response = await agent.chat("Calculate a 20% tip on a $50 bill")
    assert "$10.00" in response  # Expected tip amount
```

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
    print(f"🔧 Starting: {tool_name}")
    print(f"   Arguments: {args}")

def on_tool_end(session_id, tool_name, result):
    print(f"✅ Completed: {tool_name}")
    print(f"   Result: {result}")

agent.set_callbacks(
    on_tool_start=on_tool_start,
    on_tool_end=on_tool_end
)
```

## Next Steps

- Check out [Examples](examples.md) for more use cases
- Learn about [MCP Integration](MCP_AGENT.md) for external tools
- Read the [API Reference](api-reference.md) for detailed documentation

---

**Questions?** Open an issue on [GitHub](https://github.com/RudraModi360/Agentry/issues)
