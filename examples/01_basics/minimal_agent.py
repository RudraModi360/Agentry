"""
Minimal Agent — the simplest possible logicore agent.

Shows:
  - create_agent() factory (3 lines to a working agent)
  - @tool decorator for auto-schema generation
  - chat_sync() for synchronous use (no async required)

Run:
    python examples/01_basics/minimal_agent.py
    python examples/01_basics/minimal_agent.py --provider ollama --model gemma4:cloud
"""

from __future__ import annotations
import argparse
from logicore import create_agent, tool


# ── Define tools as plain functions ───────────────────────────────────────

@tool("Add two numbers")
def add(a: float, b: float) -> str:
    return str(a + b)

@tool("Multiply two numbers")
def multiply(a: float, b: float) -> str:
    return str(a * b)

@tool("Get the current weather for a city (mock)")
def get_weather(city: str) -> str:
    return f"Weather in {city}: 28C, Partly Cloudy"


# ── Create agent in one line ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    args = parser.parse_args()

    agent = create_agent(
        name="MathBot",
        description="A quick math + weather assistant",
        tools=[add, multiply, get_weather],
        provider=args.provider,
        model=args.model,
    )

    print(f"Agent: {agent.name}  |  Tools: {agent.tools}")
    print("Type 'quit' to exit\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        # chat_sync wraps asyncio.run() — no event loop needed
        response = agent.chat_sync(msg)
        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()
