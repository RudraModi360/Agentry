"""
CopilotAgent — coding-focused agent workflow.

Shows:
  - CopilotAgent with coding-specific convenience methods
  - explain_code(), review_file(), write_code(), fix_bug()
  - discuss() for general chat in a separate session
  - 'copilot' preset tools (filesystem, execution, git, web)

Run:
    python examples/07_agent_variants/copilot_coding.py
"""

from __future__ import annotations
import argparse, os, asyncio
from logicore.agent.variants.copilot import CopilotAgent


async def run(provider: str, model: str):
    agent = CopilotAgent(
        provider=provider,
        model=model,
        debug=False,
    )

    print(f"Agent: CopilotAgent (coding-focused)")
    print("Commands:")
    print("  explain <code>    - Explain code")
    print("  review <filepath> - Review a file")
    print("  write <desc>      - Generate code")
    print("  fix <code>        - Fix a bug")
    print("  ask <question>    - General chat (separate session)")
    print("  quit              - Exit\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        if msg.lower().startswith("explain "):
            code = msg[8:]
            response = await agent.explain_code(code)
        elif msg.lower().startswith("review "):
            filepath = msg[7:].strip()
            response = await agent.review_file(filepath)
        elif msg.lower().startswith("write "):
            desc = msg[6:]
            response = await agent.write_code(desc)
        elif msg.lower().startswith("fix "):
            code = msg[4:]
            response = await agent.fix_bug(code)
        elif msg.lower().startswith("ask "):
            question = msg[4:]
            response = await agent.discuss(question)
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
