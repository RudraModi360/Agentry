import asyncio
from logicore import Agent

# Define a custom tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2")
    
    Returns:
        The result of the calculation
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

async def main():
    # Create agent with your tool - use provider="ollama" for native Ollama API
    agent = Agent(
        provider="gemini",
        model="gemini-3.1-flash-lite",
        role="Math Assistant",
        # endpoint="https://generativelanguage.googleapis.com/v1beta/openai/",
        tools=[calculate],
        system_prompt="You are a helpful math assistant. Use the provided tools to answer questions.",
        skills=[],
        debug=True
    )
    
    # Chat with the agent
    resp = await agent.chat("What is 15 * 23?", stream=True, streaming_funct=lambda t: print(t, end="", flush=True))
    print()

if __name__ == "__main__":
    asyncio.run(main())
