"""
Document Handler — multi-format document inspection agent.

Shows:
  - DocumentHandlerRegistry for auto-detecting file format
  - PDFHandler, DocxHandler, TextHandler, CSVHandler, ExcelHandler
  - BasicAgent with a single universal inspect_document tool
  - Non-streaming async chat

Run:
    python examples/03_documents/doc_handler.py
    python examples/03_documents/doc_handler.py --file report.pdf
"""

from __future__ import annotations
import argparse, os, json
from logicore import BasicAgent, tool , Agent
from logicore.document import get_handler


# ── Tool ───────────────────────────────────────────────────────────────────

@tool("Inspect a document: auto-detect format, extract text, metadata, and convert to markdown")
def inspect_document(file_path: str, output_format: str = "markdown") -> str:
    """Inspect any supported document format.

    Args:
        file_path: Path to the document.
        output_format: 'markdown', 'text', or 'metadata'.
    """
    if not os.path.exists(file_path):
        return f"Error: file not found: {file_path}"

    try:
        handler = get_handler(file_path)
        if output_format == "metadata":
            result = handler.get_metadata()
        elif output_format == "text":
            result = handler.get_text()
        else:
            result = handler.to_markdown()

        # Truncate if too long
        text = str(result)
        if len(text) > 5000:
            text = text[:5000] + "\n\n... [truncated]"
        return text
    except Exception as e:
        return f"Error inspecting document: {e}"


@tool("List all supported document formats and their extensions")
def supported_formats() -> str:
    from logicore.document.registry import DocumentHandlerRegistry
    reg = DocumentHandlerRegistry()
    info = {}
    for ext, handler in reg._handlers.items():
        info[ext] = handler.__class__.__name__
    return json.dumps(info, indent=2)


# ── Sample documents ───────────────────────────────────────────────────────

def create_sample_files():
    # Text file
    with open("sample_report.txt", "w", encoding="utf-8") as f:
        f.write("QUARTERLY REPORT Q3 2025\n")
        f.write("=" * 40 + "\n\n")
        f.write("Revenue: $2.4M (up 12% QoQ)\n")
        f.write("Expenses: $1.8M\n")
        f.write("Net Income: $600K\n\n")
        f.write("Key Highlights:\n")
        f.write("- Launched v2.0 product\n")
        f.write("- Expanded to 3 new markets\n")
        f.write("- Customer base grew 25%\n")
    print("[setup] Created sample_report.txt")

    # CSV file
    import csv
    with open("sample_metrics.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Month", "Users", "Revenue", "Churn"])
        writer.writerow(["Jan", "1200", "48000", "3.2%"])
        writer.writerow(["Feb", "1350", "54000", "2.8%"])
        writer.writerow(["Mar", "1500", "62000", "2.5%"])
    print("[setup] Created sample_metrics.csv")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    parser.add_argument("--file", default=None, help="Document to inspect")
    args = parser.parse_args()

    # Create sample files if no file specified
    if not args.file:
        create_sample_files()
        args.file = "sample_report.txt"

    agent = BasicAgent(
        name="DocInspector",
        description="Inspect any document format: PDF, DOCX, XLSX, CSV, TXT, and more",
        tools=[inspect_document, supported_formats],
        provider=args.provider,
        model=args.model,
        debug=True
    )

    print(f"Agent: {agent.name}  |  File: {args.file}")
    print("Ask about the document. Type 'quit' to exit.\n")

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
