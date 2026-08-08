"""
SmartAgent — reasoning-focused agent workflow.

Shows:
  - SmartAgent with enhanced reasoning prompts
  - reason() method for explicit step-by-step thinking
  - 'smart' preset (~30 tools including think, plan, web, bash)
  - status() for agent health check

Run:
    python examples/07_agent_variants/smart_reasoning.py
"""

from __future__ import annotations
import argparse, asyncio
from logicore.agent.variants.smart import SmartAgent


async def run(provider: str, model: str):
    agent = SmartAgent(
        provider=provider,
        model=model,
        debug=False,
    )

    status = agent.status()
    print(f"Agent: SmartAgent (reasoning-focused)")
    print(f"Model: {status['model']}  |  Tools: {status['tools_loaded']}")
    print("Commands:")
    print("  reason <problem>  - Step-by-step reasoning")
    print("  ask <question>    - General chat")
    print("  status            - Agent health check")
    print("  quit              - Exit\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        if msg.lower().startswith("reason "):
            problem = msg[7:]
            response = await agent.reason(problem)
        elif msg.lower() == "status":
            s = agent.status()
            response = f"Model: {s['model']}\nTools: {s['tools_loaded']}\nSessions: {s['sessions_active']}"
        else:
            response = await agent.chat(msg)

        print(f"\nBot: {response}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    args = parser.parse_args()
    asyncio.run(run(args.provider, args.model))


if __name__ == "__main__":
    main()
