# Logicore Quickstart: From Zero to Agent in 5 Minutes

No theory. Just code. In this section, you'll:
- Create a working agent
- Add tools
- See memory in action
- Swap language models

Let's go.

---

## Prerequisites – 2 Minutes

You'll need:

1. **Python 3.8+** (check with `python --version`)
2. **Logicore installed**:
   ```bash
   pip install logicore
   ```
3. **An LLM to talk to** (pick one):

   **Option A: Local (Free, No API Key)**
   - Install [Ollama](https://ollama.ai)
   - Run: `ollama run qwen3.5:0.8b` (downloads a model, ~900MB)
   - Logicore will auto-detect it

   **Option B: Cloud (Need API Key)**
   - OpenAI: Get a key from [platform.openai.com](https://platform.openai.com)
   - Groq: Get a key from [console.groq.com](https://console.groq.com)
   - Set environment variable: `export OPENAI_API_KEY=sk-...`

For this walkthrough, **we'll use Ollama** (easiest). If you use cloud, just change one line.

---

## Step 1: Your First Agent (1 Minute)

Create a file called `quickstart.py`:

```python
from logicore.agents import BasicAgent

# Create an agent
agent = BasicAgent()

# Talk to it
response = agent.chat("What's 15 times 4?")
print(response)
```

Run it:
```bash
python quickstart.py
```

**What you'll see:**
```
The result of 15 times 4 is 60.
```

**That's it.** One agent, ready to go. No configuration, no setup.

---

## Step 2: Add a Tool (2 Minutes)

Let's give the agent access to a calculator. Update your code:

```python
from logicore.agents import BasicAgent

# Define a custom tool (just a regular Python function)
def calculate(expression: str) -> str:
    """Calculate a mathematical expression. Example: 15 * 4 + 2"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# Create an agent and give it the tool
agent = BasicAgent()
agent.register_tool_from_function(calculate)

# Now talk to it
response = agent.chat("What's 15 * 4 + 10 + 25?")
print(response)
```

Run it:
```bash
python quickstart.py
```

**What happens:**
- You ask a math question
- Agent sees the `calculate` tool is available
- Calls it with `15 * 4 + 10 + 25`
- Gets back `99`
- Tells you: "The answer is 99"

**Key insight**: You wrote one Python function. Logicore turned it into a tool the agent can call. No schemas, no decorators, no magic incantations.

---

## Step 3: See Memory in Action (1 Minute)

This is where Logicore really shines. Let's see the agent *learn*:

```python
from logicore.agents import BasicAgent

def calculate(expression: str) -> str:
    """Calculate a mathematical expression. Example: 15 * 4"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# Create agent with memory enabled
agent = BasicAgent(enable_memory=True)
agent.register_tool_from_function(calculate)

# First conversation
print("=== First Conversation ===")
response1 = agent.chat("We're tracking sales. Last month: 100 widgets. This month: 150 widgets. What's the percentage increase?")
print(f"Agent: {response1}\n")

# Second conversation (NEW instance, same session)
print("=== Second Conversation ===")
response2 = agent.chat("Using the same numbers, what's the absolute increase?")
print(f"Agent: {response2}\n")
```

Run it:
```bash
python quickstart.py
```

**What happens:**
1. First conversation: Agent calculates `(150-100)/100 * 100` = 50% increase
2. Second conversation: Agent *remembers* the numbers from the first conversation
   - Doesn't ask you again
   - Answers with context: "The absolute increase is 50 widgets (from 100 to 150)"

**The magic**: The agent stored the numbers in memory automatically. Next time you talk to it, it retrieves that context. No manual memory management. It just works.

---

## Step 4: Swap Language Models (30 Seconds)

Now let's switch providers. Say you tested with Ollama but want to go faster with Groq:

```python
from logicore.agents import BasicAgent

def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# Swap ONE LINE to change providers
# Option 1: Local Ollama (free)
agent = BasicAgent(provider="ollama")

# Option 2: Cloud Groq (fast, need API key)
# agent = BasicAgent(provider="groq")

# Option 3: OpenAI
# agent = BasicAgent(provider="openai")

agent.register_tool_from_function(calculate)
response = agent.chat("Calculate 999 * 888")
print(response)
```

**That's it.** Same agent, different backend. The memory, tools, and logic stay exactly the same. Just swap the provider and you're done.

---

## What Just Happened?

You built an agent that:

1. ✅ **Has persistent memory** – It remembers across conversations
2. ✅ **Uses custom tools** – You defined a function, it became a callable tool
3. ✅ **Swaps providers** – One line change to go local → cloud → different cloud
4. ✅ **Requires zero boilerplate** – No schemas, configs, or setup hell

That's Logicore's promise: **Simple for quick wins, powerful for production use.**

---

## Common Next Steps

### Want More Tools?

```python
def web_search(query: str) -> str:
    """Search the web for information."""
    # Your implementation
    return "Search results..."

def read_file(path: str) -> str:
    """Read a file from disk."""
    with open(path) as f:
        return f.read()

agent = BasicAgent()
agent.register_tool_from_function(web_search)
agent.register_tool_from_function(read_file)

# Agent now has both tools
response = agent.chat("Search for recent AI news and save to a file")
```

### Want More Control?

Instead of `BasicAgent`, use the full `Agent` class:

```python
from logicore.agents import Agent

agent = Agent(
    provider="groq",
    enable_memory=True,
    max_iterations=5,  # Limit tool calls per conversation
    debug=True,        # See what the agent is doing
)
```

### Want To See What's Happening?

Turn on debug mode:

```python
agent = BasicAgent(debug=True)
response = agent.chat("Your question here")
# Prints detailed logs of every step
```

### Want Skills (Pre-Built Tool Bundles)?

```python
from logicore.skills import SkillLoader

agent = BasicAgent()
loader = SkillLoader()
code_review_skill = loader.load("code_review")  # Pre-built skill
agent.load_skill(code_review_skill)

# Now agent has all code review tools
response = agent.chat("Review my Python code")
```

---

## Troubleshooting

**"Provider not found"**
- Make sure the LLM is running (Ollama: `ollama serve`)
- Or make sure your API key is set (`export OPENAI_API_KEY=...`)

**"Tool not recognized"**
- Check function name matches
- Function needs a docstring explaining what it does

**"Memory not working"**
- Make sure `enable_memory=True` when creating agent
- Memory needs a persistent session ID (automatic with `BasicAgent`)

**"Agent stuck in a loop"**
- Set `max_iterations=5` to limit tool calls
- Or check that tools are returning results (not hanging)

---

## Ready for More?

You've seen the basics. Next sections:

- **[Core Architecture](03-core-architecture.md)**: Deep dive into how memory, tools, and providers work
- **[How-To Guides](04-how-to-guides.md)**: Build custom agents, integrate with your apps, deploy to production
- **[API Reference](05-api-reference.md)**: Every class, method, parameter documented

But first: **go play with these examples.** The best way to learn Logicore is to build with it.

---

*Questions? Stuck? Check the troubleshooting section or open an issue on [GitHub](https://github.com/logicore).*
