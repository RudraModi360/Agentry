import asyncio
import os
from scratchy.agents import SmartAgent, SmartAgentMode

# Ensure we have the environment variables loaded if needed
from dotenv import load_dotenv
load_dotenv()

async def main():
    print("🚀 Starting SmartAgent Test Script...")

    # 1. Initialize SmartAgent in SOLO mode
    # We use 'gpt-oss:20b-cloud' as it is a capable model available in your list.
    # You can change this to 'qwen2.5:0.5b' for a faster, local (but less smart) test.
    model_name = "gpt-oss:20b-cloud" 
    
    print(f"\n[1/2] Testing SOLO Mode with model '{model_name}'...")
    agent = SmartAgent(
        llm="ollama",
        model=model_name,
        mode=SmartAgentMode.SOLO,
        debug=True  # useful to see tool calls and reasoning
    )

    query = "give me list of tools u have .."
    print(f"\nUSER: {query}")
    response = await agent.chat(query)
    print(f"AGENT: {response}")

    # 2. Initialize SmartAgent in PROJECT mode
    print(f"\n[2/2] Testing PROJECT Mode...")
    
    project_id = "test-project-001"
    
    # Create a dummy project context
    # This simulates setting up a new coding project
    agent.create_project(
        project_id=project_id,
        title="Test Context App",
        goal="Verify that the agent can recall project details.",
        environment={"language": "Python", "version": "3.11"},
        key_files=["main.py", "README.md"]
    )
    
    # Switch agent to this project
    agent.switch_to_project(project_id)
    
    # Ask a question that relies on the project context we just set
    project_query = "What is the goal of this project and what language are we using?"
    print(f"\nUSER: {project_query}")
    response_project = await agent.chat(project_query)
    print(f"AGENT: {response_project}")

    # Clean up
    await agent.cleanup()
    print("\n✅ Test Complete!")

if __name__ == "__main__":
    asyncio.run(main())
