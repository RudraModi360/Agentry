"""
Multi-Session — isolated conversation contexts per user/task.

Shows:
  - MCPAgent with create_session() / destroy_session()
  - list_sessions() for session overview
  - cleanup_stale_sessions() for memory management
  - Isolated contexts: each session has its own message history

Run:
    python examples/08_advanced/multi_session.py
"""

from __future__ import annotations
import argparse, asyncio
from logicore.agent.variants.mcp import MCPAgent


async def run(provider: str, model: str):
    agent = MCPAgent(
        provider=provider,
        model=model,
        debug=False,
    )

    print("Multi-Session Agent")
    print("Commands:")
    print("  new [name]           - Create a new session")
    print("  switch <name>        - Switch to a session")
    print("  list                 - List all sessions")
    print("  destroy <name>       - Destroy a session")
    print("  cleanup              - Remove stale sessions")
    print("  quit                 - Exit\n")

    active_session = "default"
    agent.create_session(active_session)
    print(f"[session] Active: {active_session}\n")

    while True:
        try:
            prefix = f"[{active_session}] "
            msg = input(f"{prefix}You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        if msg.lower().startswith("new "):
            name = msg[4:].strip() or f"session-{len(agent.list_sessions()) + 1}"
            agent.create_session(name)
            active_session = name
            print(f"[session] Created & switched to: {name}")

        elif msg.lower().startswith("switch "):
            name = msg[7:].strip()
            sessions = {s["session_id"]: s for s in agent.list_sessions()}
            if name in sessions:
                active_session = name
                print(f"[session] Switched to: {name}")
            else:
                print(f"[error] Session '{name}' not found. Available: {list(sessions.keys())}")

        elif msg.lower() == "list":
            sessions = agent.list_sessions()
            for s in sessions:
                marker = " <-- active" if s["session_id"] == active_session else ""
                print(f"  {s['session_id']}: {s['message_count']} messages{marker}")

        elif msg.lower().startswith("destroy "):
            name = msg[8:].strip()
            if agent.destroy_session(name):
                print(f"[session] Destroyed: {name}")
                if name == active_session:
                    active_session = "default"
                    agent.create_session(active_session)
                    print(f"[session] Switched back to: {active_session}")
            else:
                print(f"[error] Session '{name}' not found")

        elif msg.lower() == "cleanup":
            count = agent.cleanup_stale_sessions()
            print(f"[session] Cleaned up {count} stale sessions")

        else:
            response = await agent.chat(msg, session_id=active_session)
            print(f"\nBot: {response}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    args = parser.parse_args()
    asyncio.run(run(args.provider, args.model))


if __name__ == "__main__":
    main()
