"""
MCP Agent — Model Context Protocol integration.

Shows:
  - MCPAgent with external MCP server (mcp-server-time)
  - Deferred tool loading (tool_search_regex for discovery)
  - init_mcp_servers() lifecycle
  - Session lifecycle callbacks
  - Preloading frequently-used tools

Run:
    python examples/05_mcp/mcp_agent.py
    python examples/05_mcp/mcp_agent.py --deferred

Requires mcp.json in project root with:
    { "mcpServers": { "time": { "command": "uvx", "args": ["mcp-server-time"] } } }
"""

from __future__ import annotations
import argparse, os, asyncio
from logicore.agent.variants.mcp import MCPAgent


async def run(provider: str, model: str, deferred: bool):
    mcp_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "mcp.json")
    if not os.path.exists(mcp_config_path):
        mcp_config_path = "mcp.json"

    agent = MCPAgent(
        provider=provider,
        model=model,
        mcp_config_path=mcp_config_path if os.path.exists(mcp_config_path) else None,
        deferred_tools=deferred,
        tool_threshold=10,
        debug=True,
    )

    # Session lifecycle callbacks
    agent.set_session_callbacks(
        on_session_created=lambda sid: print(f"  [session] Created: {sid}"),
        on_session_destroyed=lambda sid: print(f"  [session] Destroyed: {sid}"),
    )

    # Initialize MCP servers (must be in async context)
    if mcp_config_path and os.path.exists(mcp_config_path):
        print("[setup] Initializing MCP servers...")
        await agent.init_mcp_servers()
        stats = agent.get_registry_stats()
        print(f"[setup] Registry: {stats['total_registered']} tools, "
              f"{stats['loaded']} loaded, {stats['deferred']} deferred")

    # Preload known-useful tools
    if deferred:
        agent.preload_tools(["read_file", "list_files"])

    print(f"\nAgent: MCPAgent  |  Deferred: {deferred}")
    print("Ask about time, files, or anything. Type 'quit' to exit\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        response = await agent.chat(msg)
        print(f"\nBot: {response}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    parser.add_argument("--deferred", action="store_true", help="Enable deferred tool loading")
    args = parser.parse_args()
    asyncio.run(run(args.provider, args.model, args.deferred))


if __name__ == "__main__":
    main()
