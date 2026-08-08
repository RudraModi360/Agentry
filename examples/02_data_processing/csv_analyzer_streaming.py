"""
CSV Analyzer — streaming variant.

Shows:
  - stream_sync() with on_event callback for real-time output
  - StreamEventType handling: TOKEN, TOOL_CALL_START, TOOL_CALL_END
  - Same CSV tools as the non-streaming variant, but with live feedback

Run:
    python examples/02_data_processing/csv_analyzer_streaming.py
"""

from __future__ import annotations
import argparse, csv, os, json
from logicore import BasicAgent, tool
from logicore.stream.events import StreamEventType
from logicore.utils.colors import colored, error, success, tool_call, tool_result, thinking, info, DIM, RESET, GRAY, BLUE, GREEN, RED
from logicore.document import get_handler


# ── CSV Tools (same as non-streaming) ─────────────────────────────────────

@tool("Read a CSV file and return headers + first rows as markdown")
def read_csv(file_path: str, limit: int = 20) -> str:
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"
    handler = get_handler(file_path)
    md = handler.to_markdown()
    lines = md.split("\n")
    if len(lines) > limit + 5:
        lines = lines[: limit + 5]
        lines.append(f"\n... ({limit} row limit)")
    return "\n".join(lines)


@tool("Compute aggregate stats (sum, avg, min, max) for a numeric CSV column")
def aggregate_csv(file_path: str, column: str) -> str:
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"
    values = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                values.append(float(row[column]))
            except (ValueError, KeyError):
                continue
    if not values:
        return f"No numeric data in column '{column}'"
    stats = {
        "column": column,
        "count": len(values),
        "sum": round(sum(values), 2),
        "avg": round(sum(values) / len(values), 2),
        "min": min(values),
        "max": max(values),
    }
    return json.dumps(stats, indent=2)


# ── Streaming event handler ────────────────────────────────────────────────

def make_stream_handler():
    """Returns an on_event callback that prints streaming events nicely."""
    in_thinking = [False]

    def on_event(ev):
        if ev.type == StreamEventType.TOKEN:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False
            print(ev.data.get("delta", ""), end="", flush=True)

        elif ev.type == StreamEventType.REASONING:
            if not in_thinking[0]:
                print(GRAY, end="", flush=True)
                in_thinking[0] = True
            print(ev.data.get("delta", ""), end="", flush=True)

        elif ev.type == StreamEventType.TOOL_CALL_START:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False
            name = ev.data.get("name", "?")
            args = ev.data.get("args", {})
            print(f"\n{tool_call(name)}({json.dumps(args)[:100]})", flush=True)

        elif ev.type == StreamEventType.TOOL_CALL_END:
            preview = str(ev.data.get("preview", ""))[:120]
            print(f" {tool_result(ev.data.get('success'), preview)}", flush=True)

        elif ev.type == StreamEventType.TOOL_OUTPUT:
            stream = ev.data.get("stream", "stdout")
            line = ev.data.get("line", "")
            if stream == "stderr":
                print(f"[stderr] {line}", flush=True)
            else:
                print(line, flush=True)

        elif ev.type == StreamEventType.ERROR:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False
            print(f"\n{error('[error]')} {ev.data.get('message')}", flush=True)

        elif ev.type == StreamEventType.DONE:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False

    return on_event


# ── Main ───────────────────────────────────────────────────────────────────

def create_sample_csv(path: str):
    rows = [
        {"name": "Alice", "dept": "Eng", "salary": "120000"},
        {"name": "Bob", "dept": "Mkt", "salary": "85000"},
        {"name": "Charlie", "dept": "Eng", "salary": "135000"},
        {"name": "Diana", "dept": "Sales", "salary": "92000"},
        {"name": "Eve", "dept": "Eng", "salary": "145000"},
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "dept", "salary"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{info('[setup]')} Created sample CSV: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    parser.add_argument("--file", default="sample_data.csv")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        create_sample_csv(args.file)

    agent = BasicAgent(
        name="CSVStreamAnalyzer",
        description="Analyze CSV files with live streaming output",
        tools=[read_csv, aggregate_csv,'execution'],
        provider=args.provider,
        model=args.model,
        system_prompt="You are a helpful assistant that can analyze CSV files. Use the provided tools to read and aggregate data from CSV files. Provide clear and concise answers.",
    )

    on_event = make_stream_handler()

    print(f"Agent: {colored(agent.name, BLUE)}  |  Streaming mode")
    print("Ask about the CSV. Type 'quit' to exit.\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        prompt = f"[File: {args.file}] {msg}"
        # stream_sync runs the agent and calls on_event for each StreamEvent
        agent.stream_sync(prompt, on_event=on_event)
        print("\n")


if __name__ == "__main__":
    main()
