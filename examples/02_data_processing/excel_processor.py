"""
Excel Processor — read, transform, and write Excel files.

Shows:
  - BasicAgent with Excel-specific tools using openpyxl
  - ExcelHandler from logicore.document for reading
  - Custom tools for pivot, merge, and write operations
  - Non-streaming batch processing pattern

Run:
    python examples/02_data_processing/excel_processor.py
"""

from __future__ import annotations
import argparse, os, json
from typing import List, Dict, Any
from logicore import BasicAgent, tool
from logicore.document import get_handler


# ── Excel Tools ────────────────────────────────────────────────────────────

@tool("Read an Excel file and return all sheets as markdown tables")
def read_excel(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"
    handler = get_handler(file_path)
    return handler.to_markdown()


@tool("Get metadata about an Excel file (sheets, author, dates)")
def excel_info(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"
    handler = get_handler(file_path)
    meta = handler.get_metadata()
    return json.dumps(meta, indent=2, default=str)


@tool("Create a new Excel file with data. data is a JSON array of objects.")
def write_excel(file_path: str, data: str, sheet_name: str = "Sheet1") -> str:
    try:
        import openpyxl
        rows = json.loads(data) if isinstance(data, str) else data
        if not rows:
            return "Error: no data provided"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h, "") for h in headers])
        wb.save(file_path)
        return f"Created {file_path} with {len(rows)} rows and {len(headers)} columns"
    except Exception as e:
        return f"Error: {e}"


@tool("Merge multiple Excel files into one. Provide comma-separated file paths.")
def merge_excel(file_paths: str, output_path: str) -> str:
    try:
        import openpyxl
        merged_wb = openpyxl.Workbook()
        merged_ws = merged_wb.active
        merged_ws.title = "Merged"
        total_rows = 0
        first = True

        for path in [p.strip() for p in file_paths.split(",")]:
            if not os.path.exists(path):
                continue
            wb = openpyxl.load_workbook(path, data_only=True)
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                for i, row in enumerate(ws.iter_rows(values_only=True)):
                    if i == 0 and first:
                        merged_ws.append([str(c) if c else "" for c in row])
                        first = False
                    elif i > 0:
                        merged_ws.append([str(c) if c else "" for c in row])
                        total_rows += 1

        merged_wb.save(output_path)
        return f"Merged {len(file_paths.split(','))} files -> {output_path} ({total_rows} rows)"
    except Exception as e:
        return f"Error: {e}"


@tool("Create a pivot-like summary: group by a column and sum another column")
def pivot_summary(file_path: str, group_by: str, value_column: str) -> str:
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        headers = [str(h) for h in rows[0]]
        if group_by not in headers or value_column not in headers:
            return f"Error: columns must be in {headers}"
        gi = headers.index(group_by)
        vi = headers.index(value_column)
        groups: Dict[str, float] = {}
        for row in rows[1:]:
            key = str(row[gi]) if row[gi] else "empty"
            try:
                groups[key] = groups.get(key, 0) + float(row[vi])
            except (ValueError, TypeError):
                continue
        result = {k: round(v, 2) for k, v in sorted(groups.items())}
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {e}"


# ── Sample data ────────────────────────────────────────────────────────────

def create_sample_excel(path: str):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(["Product", "Region", "Revenue", "Units"])
    data = [
        ("Widget A", "North", 12000, 150),
        ("Widget B", "South", 8500, 95),
        ("Widget A", "South", 13200, 160),
        ("Widget C", "North", 9800, 110),
        ("Widget B", "North", 7600, 85),
        ("Widget C", "South", 11200, 130),
    ]
    for row in data:
        ws.append(row)
    wb.save(path)
    print(f"[setup] Created sample Excel: {path}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    parser.add_argument("--file", default="sample_sales.xlsx")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        create_sample_excel(args.file)

    agent = BasicAgent(
        name="ExcelProcessor",
        description="Read, write, pivot, and merge Excel spreadsheets",
        tools=[read_excel, excel_info, write_excel, merge_excel, pivot_summary],
        provider=args.provider,
        model=args.model,
    )

    print(f"Agent: {agent.name}  |  File: {args.file}")
    print("Ask me about the Excel file. Type 'quit' to exit.\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        prompt = f"[File: {args.file}] {msg}"
        response = agent.chat_sync(prompt)
        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()
