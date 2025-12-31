"""
CLI Entry Point for Smart File Search Agent.
Run with: python -m file_search_agent
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from pathlib import Path
from typing import Optional
import sys

from .agents import FileSearchAgent
from .config import settings

app = typer.Typer(
    name="file-search",
    help="🔍 Smart File Search Agent - LLM-powered document search and Q&A"
)
console = Console()


def get_agent() -> FileSearchAgent:
    """Initialize the search agent."""
    try:
        return FileSearchAgent()
    except Exception as e:
        console.print(f"[red]Error initializing agent: {e}[/red]")
        console.print("[yellow]Make sure you have set up your API keys.[/yellow]")
        raise typer.Exit(1)


@app.command()
def index(
    path: str = typer.Argument(..., help="Path to file or directory to index"),
    parallel: bool = typer.Option(True, help="Use parallel processing"),
    workers: int = typer.Option(4, help="Number of parallel workers")
):
    """📂 Index documents from a file or directory."""
    path = Path(path)
    
    if not path.exists():
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[blue]Indexing: {path}[/blue]")
    
    agent = get_agent()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Indexing documents...", total=None)
        stats = agent.index(str(path), parallel=parallel, max_workers=workers)
    
    console.print(Panel(
        f"✅ Indexed: {stats.get('indexed', 0)} documents\n"
        f"⏭️ Skipped: {stats.get('skipped', 0)} files\n"
        f"⏱️ Duration: {stats.get('duration', 0):.1f}s",
        title="Indexing Complete"
    ))


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(5, "-k", "--top-k", help="Number of results"),
    file_type: Optional[str] = typer.Option(None, "-t", "--type", help="Filter by file type")
):
    """🔎 Search indexed documents."""
    agent = get_agent()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Searching...", total=None)
        results = agent.search(query, top_k=top_k, file_type=file_type)
    
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    
    table = Table(title=f"Search Results for: '{query}'")
    table.add_column("#", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Score", style="yellow")
    table.add_column("Preview", style="white")
    
    for i, result in enumerate(results, 1):
        preview = result.text[:100] + "..." if len(result.text) > 100 else result.text
        preview = preview.replace("\n", " ")
        table.add_row(
            str(i),
            result.file_name,
            f"{result.score:.3f}",
            preview
        )
    
    console.print(table)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(5, "-k", "--top-k", help="Number of context docs"),
    file_type: Optional[str] = typer.Option(None, "-t", "--type", help="Filter by file type")
):
    """❓ Ask a question about your documents."""
    agent = get_agent()
    
    console.print(f"[blue]Question: {question}[/blue]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Thinking...", total=None)
        response = agent.ask(question, top_k=top_k, file_type=file_type)
    
    # Display answer
    console.print(Panel(
        Markdown(response.answer),
        title="Answer",
        border_style="green"
    ))
    
    # Display sources
    if response.sources:
        console.print("\n[dim]Sources:[/dim]")
        for i, source in enumerate(response.sources, 1):
            console.print(f"  {i}. {source.file_name} (score: {source.score:.3f})")
    
    console.print(f"\n[dim]Confidence: {response.confidence:.2%} | Model: {response.model_used}[/dim]")


@app.command()
def chat():
    """💬 Interactive chat mode with your documents."""
    agent = get_agent()
    
    console.print(Panel(
        "🤖 Chat with your documents!\n"
        "Type your questions and get answers based on indexed content.\n"
        "Commands: 'quit' to exit, 'clear' to reset conversation",
        title="Chat Mode"
    ))
    
    while True:
        try:
            user_input = console.input("\n[bold blue]You:[/bold blue] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[dim]Goodbye![/dim]")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_conversation()
                console.print("[dim]Conversation cleared.[/dim]")
                continue
            
            # Stream response
            console.print("\n[bold green]Assistant:[/bold green] ", end="")
            
            full_response = ""
            for token in agent.chat_stream(user_input):
                console.print(token, end="")
                full_response += token
            
            console.print()  # Newline after response
            
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break


@app.command()
def stats():
    """📊 Show indexing statistics."""
    agent = get_agent()
    stats = agent.get_stats()
    
    console.print(Panel(
        f"📄 Total Documents: {stats.get('total_documents', 0)}\n"
        f"📝 Total Chunks: {stats.get('total_chunks', 0)}\n"
        f"📁 File Types: {stats.get('file_types', {})}",
        title="Index Statistics"
    ))


@app.command()
def list_docs(
    file_type: Optional[str] = typer.Option(None, "-t", "--type", help="Filter by file type"),
    limit: int = typer.Option(20, "-n", "--limit", help="Max documents to show")
):
    """📋 List indexed documents."""
    agent = get_agent()
    docs = agent.list_documents(file_type=file_type)[:limit]
    
    if not docs:
        console.print("[yellow]No documents indexed yet.[/yellow]")
        return
    
    table = Table(title="Indexed Documents")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Chunks", style="magenta")
    table.add_column("Indexed", style="dim")
    
    for doc in docs:
        size_kb = doc['size'] / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        table.add_row(
            doc['name'][:40],
            doc['type'],
            size_str,
            str(doc['chunks']),
            doc['indexed'][:10]
        )
    
    console.print(table)


@app.command()
def config():
    """⚙️ Show current configuration."""
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("LLM Provider", settings.llm_provider)
    table.add_row("LLM Model", settings.llm_model)
    table.add_row("Embedding Model", settings.embedding_model)
    table.add_row("Vector Store", settings.vector_store_type)
    table.add_row("Chunk Size", str(settings.chunk_size))
    table.add_row("Search Top-K", str(settings.search_top_k))
    table.add_row("Hybrid Search", str(settings.use_hybrid_search))
    
    console.print(table)


if __name__ == "__main__":
    app()
