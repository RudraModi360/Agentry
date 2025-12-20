import asyncio
from scratchy.agents import CopilotAgent


async def main():
    # Create the Copilot agent
    agent = CopilotAgent(
        llm="ollama",
        model="gpt-oss:20b-cloud",  # Change to your model (codellama works great)
        debug=True
    )
    
    print("CopilotAgent - Coding-Focused Agent")
    print("-" * 50)
    
    # Test coding tasks
    tasks = [
        "Write a Python function to check if a string is a palindrome",
        "Explain what this code does: lambda x: x**2 if x > 0 else -x**2",
        "What's wrong with this code: for i in range(10): print(i); i += 2",
    ]
    
    for task in tasks:
        print(f"\n🧑 User: {task}")
        response = await agent.chat(task)
        print(f"🤖 Copilot: {response}")
        print("-" * 50)
    
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
