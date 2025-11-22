import asyncio
from scratchy.agents import Agent, CopilotAgent

async def main():
    # # 1. Simple Agent (defaults to Ollama)
    # print("--- Simple Agent ---")
    agent = Agent(llm="ollama", model="gpt-oss:20b-cloud")
    
    # # Add default tools (filesystem, web, etc.)
    agent.load_default_tools()
    
    # response = await agent.chat("Hello! Can you list the files in the current directory?")
    # print(f"Agent: {response}\n")

    # 2. Custom Tool Example
    # print("--- Custom Tool Example ---")
    
    # def calculate_bmi(weight_kg: float, height_m: float) -> str:
    #     """
    #     Calculates BMI given weight in kg and height in meters.
    #     Returns the BMI value and category.
    #     """
    #     bmi = weight_kg / (height_m ** 2)
    #     category = "Normal"
    #     if bmi < 18.5: category = "Underweight"
    #     elif bmi > 25: category = "Overweight"
    #     return f"BMI: {bmi:.2f} ({category})"

    # agent.register_tool_from_function(calculate_bmi)
    
    # response = await agent.chat("My weight is 70kg and height is 1.75m. What is my BMI?")
    # print(f"Agent: {response}\n")

    # # 3. Copilot Agent (Pre-configured for coding)
    print("--- Copilot Agent ---")
    copilot = CopilotAgent(llm="ollama", debug=True)
    
    # It already has tools loaded. Let's ask it to explain this file.
    explanation = await copilot.discuss(f"Explain : ,{open(__file__).read()}")
    print(f"Copilot Explanation:\n{explanation}")

if __name__ == "__main__":
    asyncio.run(main())
