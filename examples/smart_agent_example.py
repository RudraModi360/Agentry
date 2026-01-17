import asyncio
from scratchy.agents import SmartAgent, SmartAgentMode


async def solo_mode_example():
    """Example of SmartAgent in Solo mode - general reasoning."""
    print("\n" + "="*50)
    print("SOLO MODE - General Reasoning")
    print("="*50)
    
    # Note: Use a model that supports tool calling for best results
    # Ollama: llama3.2:3b, qwen2.5:7b
    # Groq: llama-3.3-70b-versatile
    # Gemini: gemini-2.0-flash
    agent = SmartAgent(
        llm="ollama",
        model="gpt-oss:20b-cloud",  # Your preferred model
        mode=SmartAgentMode.SOLO,
        debug=True
    )
    
    print(f"Mode: {agent.mode}")
    print(f"Tools: {[t.get('function',{}).get('name') for t in agent.internal_tools]}")
    print("-" * 50)
    
    # Test reasoning
    questions = [
        "What are the key differences between REST and GraphQL APIs?"
    ]
    
    for question in questions:
        print(f"\n🧑 User: {question}")
        response = await agent.chat(question)
        print(f"🤖 Agent: {response[:500]}...")
    
    await agent.cleanup()


async def project_mode_example():
    """Example of SmartAgent in Project mode - focused on a specific project."""
    print("\n" + "="*50)
    print("PROJECT MODE - Project-Focused")
    print("="*50)
    
    agent = SmartAgent(
        llm="ollama",
        model="gpt-oss:20b-cloud",  # Use model with tool support
        mode=SmartAgentMode.PROJECT,
        project_id="demo-project",
        debug=True
    )
    
    # Create project context
    agent.create_project(
        project_id="demo-project",
        title="Demo Web App",
        goal="Build a FastAPI backend with authentication",
        environment={"language": "Python", "framework": "FastAPI"},
        key_files=["main.py", "requirements.txt"]
    )
    
    # Switch to the project to load its context
    agent.switch_to_project("demo-project")
    
    if agent.project_context:
        print(f"Project: {agent.project_context.title}")
        print(f"Goal: {agent.project_context.goal}")
    else:
        print("Project: demo-project (created)")
    print("-" * 50)
    
    # Test project-aware responses
    questions = [
        "What's the best way to structure this project?",
        "How should I implement JWT authentication?",
    ]
    
    for question in questions:
        print(f"\n🧑 User: {question}")
        response = await agent.chat(question)
        print(f"🤖 Agent: {response[:500]}...")
    
    # Check stored memories
    print("\n📝 Project Memories:")
    memories = agent.project_memory.get_memories(project_id="demo-project", limit=5)
    for mem in memories:
        print(f"  - [{mem.memory_type.value}] {mem.title}")
    
    await agent.cleanup()


async def main():
    await solo_mode_example()
    await project_mode_example()


if __name__ == "__main__":
    asyncio.run(main())
