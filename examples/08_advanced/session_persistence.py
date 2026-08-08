"""
Session Persistence — 3-tier storage for conversation resumption.

Shows:
  - Agent with create_storage() for DB + snapshot persistence
  - Session resume across restarts
  - clear_session() / get_session() API
  - 3-tier storage: SQLite DB + JSON snapshots + binary media

Run:
    python examples/08_advanced/session_persistence.py
    # Run once, chat, quit, run again — session resumes automatically
"""

from __future__ import annotations
import argparse, os, asyncio
from logicore import Agent
from logicore.storage import create_storage


async def run(provider: str, model: str):
    # 3-tier storage: database + snapshots + media
    storage = create_storage()

    agent = Agent(
        provider=provider,
        model=model,
        storage=storage,
        debug=False,
        telemetry=True,
    )

    # Create or resume a named session
    session_id = "demo-session"
    print(f"Session: {session_id}")
    print(f"Storage: {storage}")
    print("Your conversation persists across restarts. Type 'quit' to exit.\n")

    try:
        while True:
            try:
                msg = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not msg or msg.lower() in ("quit", "exit"):
                break

            if msg.lower() == "clear":
                agent.clear_session(session_id)
                print("[session cleared]")
                continue

            if msg.lower() == "history":
                session = agent.get_session(session_id)
                if session:
                    for m in session.messages[-6:]:
                        role = m.get("role", "?")
                        content = str(m.get("content", ""))[:80]
                        print(f"  [{role}] {content}")
                continue

            response = await agent.chat(msg, session_id=session_id)
            print(f"\nBot: {response}\n")
    finally:
        storage.shutdown()
        print("[done] Session saved to disk")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    args = parser.parse_args()
    asyncio.run(run(args.provider, args.model))


if __name__ == "__main__":
    main()
