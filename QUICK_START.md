# Quick Start: Your First AI Agent in 5 Minutes

**Goal:** Create and run your first AI agent in 5 minutes

---

## Step 1: Install Agentry (1 minute)

\\\ash
pip install logicore
\\\

## Step 2: Create Your First Script (1 minute)

Create a file called \my_first_agent.py\:

\\\python
import asyncio
from logicore import Agent

async def main():
    # Create an agent
    agent = Agent(llm="ollama", model="llama3.2")
    
    # Give it tools to use
    agent.load_default_tools()
    
    # Ask it something
    response = await agent.chat("What files are in the current directory?")
    print(f"Answer: {response}")

# Run it
if __name__ == "__main__":
    asyncio.run(main())
\\\

## Step 3: Run It (1 minute)

\\\ash
python my_first_agent.py
\\\

You should see the agent listing your files!

---

## Step 4: Try These Next (2 minutes)

### Chat with Memory

\\\python
agent = Agent(llm="ollama", model="llama3.2")
agent.load_default_tools()

# Multi-turn conversation
r1 = await agent.chat("My name is Alice", session_id="s1")
r2 = await agent.chat("What's my name?", session_id="s1")
# Agent remembers: Alice
\\\

### Add a Custom Tool

\\\python
def calculator(expression: str) -> str:
    \"\"\"Simple calculator\"\"\"
    return str(eval(expression))

agent = Agent(llm="ollama", model="llama3.2")
agent.register_tool(calculator)

response = await agent.chat("Calculate 10 * 5")
# Agent uses your calculator tool!
\\\

### Try Different Models

\\\python
# Free, local
Agent(llm="ollama", model="llama3.2")

# Fast cloud
Agent(llm="groq", model="llama-3.3-70b")

# Most capable (requires API key)
Agent(llm="azure", model="gpt-4")
\\\

---

## Understanding What Happened

1. **Created an Agent** - Your AI brain
2. **Loaded Tools** - Gave it abilities (filesystem access, web search, etc.)
3. **Asked a Question** - The agent thinks and uses tools to answer
4. **Got a Response** - The agent used the tools to answer your question

This is the core of AI agents! The agent:
- Understands your question
- Decides what tools to use
- Uses the tools
- Synthesizes a response

---

## Next Steps

- Read \AI_LEARNING_GUIDE.md\ for deep understanding
- Check \PYTHON_CONCEPTS_REFERENCE.md\ for code patterns
- Try \HANDS_ON_TUTORIAL.md\ for step-by-step learning

Congratulations! You've built your first AI agent! 🎉
