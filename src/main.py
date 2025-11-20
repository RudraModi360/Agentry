import asyncio
import sys
import os
from agents.agent import Agent
from providers.ollama_provider import OllamaProvider
from providers.groq_provider import GroqProvider
from providers.gemini_provider import GeminiProvider
from config.settings import get_api_key

async def main():
    print("Welcome to the Modular AI Agent!")
    print("Select a provider:")
    print("1. Ollama")
    print("2. Groq")
    print("3. Gemini")
    
    choice = input("Enter choice (1-3): ").strip()
    
    provider = None
    
    if choice == '1':
        model = input("Enter Ollama model (default: gpt-oss:20b-cloud): ").strip() or "gpt-oss:20b-cloud"
        provider = OllamaProvider(model_name=model)
    elif choice == '2':
        model = input("Enter Groq model (default: openai/gpt-oss-20b): ").strip() or "openai/gpt-oss-20b"
        api_key = get_api_key("groq")
        if not api_key:
            api_key = input("Enter Groq API Key: ").strip()
        provider = GroqProvider(model_name=model, api_key=api_key)
    elif choice == '3':
        model = input("Enter Gemini model (default: gemini-pro): ").strip() or "gemini-pro"
        api_key = get_api_key("gemini")
        if not api_key:
            api_key = input("Enter Gemini API Key: ").strip()
        provider = GeminiProvider(model_name=model, api_key=api_key)
    else:
        print("Invalid choice.")
        return

    agent = Agent(provider=provider, debug=True)

    # Callbacks
    def print_tool_start(name, args):
        print(f"\n[Tool Start] {name} with args: {args}")

    def print_tool_end(name, result):
        print(f"[Tool End] {name} result: {result}\n")

    async def ask_approval(name, args):
        res = input(f"\n[Approval] Allow {name} with {args}? (y/n): ")
        return res.lower() == 'y'

    def print_final(content):
        print(f"\n[Assistant]: {content}\n")

    agent.set_tool_callbacks(
        on_tool_start=print_tool_start,
        on_tool_end=print_tool_end,
        on_tool_approval=ask_approval,
        on_final_message=print_final
    )

    print(f"Agent initialized with {provider.get_model_name()}. Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            await agent.chat(user_input)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
