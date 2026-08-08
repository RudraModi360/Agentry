"""
Custom Tools Agent — deep-dive into all 3 tool registration methods.

Shows:
  1. @tool decorator (auto-schema from type hints + docstring)
  2. BaseTool subclass with Pydantic args_schema (full control)
  3. agent.add_custom_tool(schema_dict, executor) (raw schema)

Also demonstrates set_callbacks() for event hooks.

Run:
    python examples/01_basics/custom_tools_agent.py
"""

from __future__ import annotations
import argparse
import json
from pydantic import BaseModel, Field
from logicore import BasicAgent, tool
from logicore.tools.base import BaseTool, ToolResult


# ── Method 1: @tool decorator ─────────────────────────────────────────────

@tool("Evaluate a math expression safely (e.g. '2+2', '10*5')")
def calculator(expression: str) -> str:
    import ast
    try:
        tree = ast.parse(expression, mode="eval")
        return str(eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"


# ── Method 2: BaseTool subclass ───────────────────────────────────────────

class QueryDBParams(BaseModel):
    query: str = Field(..., description="SQL query to execute (SELECT only)")
    database: str = Field("main.db", description="Database file path")


class QueryDBTool(BaseTool):
    name = "query_db"
    description = "Run a read-only SQL query against a SQLite database"
    args_schema = QueryDBParams

    def run(self, query: str, database: str = "main.db") -> ToolResult:
        import sqlite3, os
        if not os.path.exists(database):
            return ToolResult(success=False, error=f"Database not found: {database}")
        try:
            conn = sqlite3.connect(database)
            cursor = conn.execute(query)
            columns = [d[0] for d in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            conn.close()
            return ToolResult(success=True, content={"columns": columns, "rows": rows[:50]})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def is_read_only(self, args=None) -> bool:
        return True


# ── Method 3: Raw schema + executor ───────────────────────────────────────

def _exec_web_status(url: str) -> dict:
    """Fetch HTTP status code for a URL."""
    import urllib.request
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=5)
        return {"success": True, "status": resp.status, "url": url}
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


WEB_STATUS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_web_status",
        "description": "Check if a URL is reachable and return its HTTP status",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to check"}
            },
            "required": ["url"],
        },
    },
}


# ── Agent ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    args = parser.parse_args()

    agent = BasicAgent(
        name="ToolDemo",
        description="Demonstrates 3 ways to register tools in logicore",
        # tools=[calculator, QueryDBTool()],
        provider=args.provider,
        model=args.model,
        tool_preset=''
        # tool_preset="lightweight",
    )

    # Method 3: register raw schema + executor
    agent.add_tool(_exec_web_status)

    # Set callbacks for event hooks
    agent.set_callbacks(
        on_tool_start=lambda sid, name, args: print(f"  [tool:start] {name}({args})"),
        on_tool_end=lambda sid, name, res: print(f"  [tool:end]   {name} -> OK"),
        on_token=lambda tok: print(tok, end="", flush=True),
    )

    print(f"Agent: {agent.name}")
    print(f"Tools: {agent.tools}")
    print("Type 'quit' to exit\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        response = agent.chat_sync(msg)
        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()
