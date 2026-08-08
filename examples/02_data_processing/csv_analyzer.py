"""
CSV Analyzer — non-streaming batch data agent.

Shows:
  - BasicAgent with custom CSV-specific tools
  - DocumentHandlerRegistry + CSVHandler for reading
  - chat_sync() for synchronous batch processing
  - Tool result aggregation pattern

Run:
    python examples/02_data_processing/csv_analyzer.py
    python examples/02_data_processing/csv_analyzer.py --file data.csv
"""

from __future__ import annotations
import argparse, csv, os, json
from typing import List, Dict, Any
from logicore import BasicAgent, tool
from logicore.document import get_handler


# ── CSV Tools ──────────────────────────────────────────────────────────────

@tool("Read a CSV file and return its headers + first N rows as markdown")
def read_csv(file_path: str, limit: int = 20) -> str:
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"
    handler = get_handler(file_path)
    md = handler.to_markdown()
    # Trim to limit rows if too large
    lines = md.split("\n")
    if len(lines) > limit + 5:
        lines = lines[: limit + 5]
        lines.append(f"\n... ({limit} row limit)")
    return "\n".join(lines)


@tool("Filter CSV rows by a column value. Returns matching rows as JSON.")
def filter_csv(file_path: str, column: str, value: str) -> str:
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        matches = [row for row in reader if value.lower() in row.get(column, "").lower()]
    return json.dumps(matches[:30], indent=2)


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
        return f"No numeric data found in column '{column}'"
    stats = {
        "column": column,
        "count": len(values),
        "sum": round(sum(values), 2),
        "avg": round(sum(values) / len(values), 2),
        "min": min(values),
        "max": max(values),
    }
    return json.dumps(stats, indent=2)


@tool("Export filtered rows to a new CSV file")
def export_csv(file_path: str, output_path: str, column: str = None, value: str = None) -> str:
    if not os.path.exists(file_path):
        return f"Error: source file not found: {file_path}"
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if column and value:
        rows = [r for r in rows if value.lower() in r.get(column, "").lower()]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return f"Exported {len(rows)} rows to {output_path}"


# ── Sample data generator ─────────────────────────────────────────────────

def create_sample_csv(path: str):
    rows = [
        {"name": "Alice", "department": "Engineering", "salary": "120000", "rating": "4.5"},
        {"name": "Bob", "department": "Marketing", "salary": "85000", "rating": "3.8"},
        {"name": "Charlie", "department": "Engineering", "salary": "135000", "rating": "4.7"},
        {"name": "Diana", "department": "Sales", "salary": "92000", "rating": "4.1"},
        {"name": "Eve", "department": "Engineering", "salary": "145000", "rating": "4.9"},
        {"name": "Frank", "department": "Marketing", "salary": "78000", "rating": "3.5"},
        {"name": "Grace", "department": "Sales", "salary": "98000", "rating": "4.3"},
        {"name": "Hank", "department": "Engineering", "salary": "128000", "rating": "4.2"},
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "department", "salary", "rating"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[setup] Created sample CSV: {path}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    parser.add_argument("--file", default="sample_employees.csv")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        create_sample_csv(args.file)

    agent = BasicAgent(
        name="CSVAnalyzer",
        description="Analyze CSV files: read, filter, aggregate, and export data",
        tools=[read_csv, filter_csv, aggregate_csv, export_csv],
        provider=args.provider,
        model=args.model,
    )

    print(f"Agent: {agent.name}  |  File: {args.file}")
    print("Ask me to analyze the CSV. Type 'quit' to exit.\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        # Include file context automatically
        prompt = f"[File: {args.file}] {msg}"
        response = agent.chat_sync(prompt)
        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()
