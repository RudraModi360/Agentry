import asyncio
from agentry import Agent


async def main():
    # Create the default agent with all tools
    agent = Agent(
        llm="ollama",
        model="gpt-oss:20b-cloud",  # Change to your model
        debug=True
    )
    
    # Load all default tools (filesystem, web, documents, etc.)
    agent.load_default_tools()
    
    print("Default Agent - Full-featured agent with all tools")
    print(f"Tools loaded: {len(agent.internal_tools)}")
    print("-" * 50)
    
    # Test the agent
    questions = [
        "List the files in the current directory",
        "What is the current date and time?",
        "Search the web for Python best practices",
    ]
    
    for question in questions:
        print(f"\n🧑 User: {question}")
        response = await agent.chat(question)
        print(f"🤖 Agent: {response[:500]}...")  # Truncate long responses
    
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
