import asyncio
from scratchy.agents import BasicAgent, tool


# --- Define Custom Tools as Functions ---

def calculator(expression: str) -> str:
    """Calculate a math expression like '2 + 2' or '10 * 5'."""
    try:
        # Safe eval for math only
        allowed = set('0123456789+-*/.() ')
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "Invalid expression"
    except Exception as e:
        return f"Error: {e}"


def get_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool("Convert temperature between Celsius and Fahrenheit")
def convert_temperature(value: float, from_unit: str) -> str:
    """Convert temperature. from_unit should be 'C' or 'F'."""
    if from_unit.upper() == 'C':
        result = (value * 9/5) + 32
        return f"{value}°C = {result:.1f}°F"
    elif from_unit.upper() == 'F':
        result = (value - 32) * 5/9
        return f"{value}°F = {result:.1f}°C"
    return "Unknown unit. Use 'C' or 'F'"


# --- Create the Agent ---

async def main():
    # Create a custom agent with your tools
    agent = BasicAgent(
        name="UtilityBot",
        description="A helpful assistant that can do math, tell time, and convert temperatures",
        provider="ollama",
        model="gpt-oss:20b-cloud",  # Change to your model
        tools=[calculator, get_time, convert_temperature],
        debug=True
    )
    
    print(f"Created: {agent}")
    print(f"Tools: {agent.tools}")
    print("-" * 50)
    
    # Test the agent
    questions = [
        "What is 25 * 4?",
        "What time is it?",
        "Convert 100 degrees Fahrenheit to Celsius",
    ]
    
    for question in questions:
        print(f"\n🧑 User: {question}")
        response = await agent.chat(question)
        print(f"🤖 Agent: {response}")
    
    # Cleanup
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
