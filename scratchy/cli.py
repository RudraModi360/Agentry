import asyncio
import os
import argparse
import uuid
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from scratchy import Agent
from scratchy.agents import SmartAgent, SmartAgentMode, CopilotAgent
from scratchy.config.settings import get_api_key
from scratchy.session_manager import SessionManager
from scratchy.reloader import start_reloader
from scratchy.client.app import ClientApp
from scratchy.client.display import DisplayManager

# --- Configuration ---
MCP_CONFIG_PATH = "mcp.json"
DEBUG_MODE = False

console = Console()

def show_help():
    """Display a beautiful help screen."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🤖 AGENTRY[/bold cyan] - Smart AI Agent CLI",
        border_style="cyan"
    ))
    
    # Agent Types
    console.print("\n[bold yellow]📦 AGENT TYPES[/bold yellow]")
    agent_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    agent_table.add_column("Type", style="cyan")
    agent_table.add_column("Flag", style="green")
    agent_table.add_column("Description")
    agent_table.add_row("Default", "--agent default", "Standard agent with all tools")
    agent_table.add_row("Smart", "--agent smart / -a smart", "Enhanced reasoning + project memory")
    agent_table.add_row("Copilot", "--agent copilot / -c", "Optimized for coding tasks")
    console.print(agent_table)
    
    # Smart Agent Modes
    console.print("\n[bold yellow]🧠 SMART AGENT MODES[/bold yellow]")
    mode_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    mode_table.add_column("Mode", style="cyan")
    mode_table.add_column("Flag", style="green")
    mode_table.add_column("Description")
    mode_table.add_row("Solo", "--mode solo (default)", "General reasoning and chat")
    mode_table.add_row("Project", "--mode project --project <id>", "Project-focused with context memory")
    console.print(mode_table)
    
    # Providers
    console.print("\n[bold yellow]🌐 PROVIDERS[/bold yellow]")
    provider_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    provider_table.add_column("Provider", style="cyan")
    provider_table.add_column("Flag", style="green")
    provider_table.add_column("Notes")
    provider_table.add_row("Ollama", "-p ollama (default)", "Local models, no API key needed")
    provider_table.add_row("Groq", "-p groq", "Fast cloud inference, needs GROQ_API_KEY")
    provider_table.add_row("Gemini", "-p gemini", "Google AI, needs GEMINI_API_KEY")
    provider_table.add_row("Azure", "-p azure", "Azure OpenAI, needs Key + Endpoint")
    console.print(provider_table)
    
    # Examples
    console.print("\n[bold yellow]📝 EXAMPLES[/bold yellow]")
    examples = """
[green]# Basic usage (default agent with Ollama)[/green]
agentry

[green]# Smart Agent with Ollama[/green]
agentry -a smart -m llama3.2:3b

[green]# Smart Agent in Project Mode[/green]
agentry -a smart --mode project --project my-app

[green]# Use Groq provider with specific model[/green]
agentry -a smart -p groq -m llama-3.3-70b-versatile

[green]# Use Gemini[/green]
agentry -p gemini -m gemini-2.0-flash

[green]# Copilot for coding[/green]
agentry -c -p groq -m llama-3.3-70b-versatile

[green]# List available Ollama models[/green]
agentry --list-models
"""
    console.print(Panel(examples, title="Usage Examples", border_style="green"))
    
    # All Options
    console.print("\n[bold yellow]⚙️  ALL OPTIONS[/bold yellow]")
    options_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    options_table.add_column("Option", style="cyan")
    options_table.add_column("Short", style="green")
    options_table.add_column("Description")
    options_table.add_row("--agent", "-a", "Agent type: default, smart, copilot")
    options_table.add_row("--copilot", "-c", "Shortcut for --agent copilot")
    options_table.add_row("--mode", "", "Smart Agent mode: solo, project")
    options_table.add_row("--project", "", "Project ID for project mode")
    options_table.add_row("--provider", "-p", "LLM provider: ollama, groq, gemini, azure")
    options_table.add_row("--model", "-m", "Model name (provider-specific)")
    options_table.add_row("--endpoint", "", "Azure Endpoint URL")
    options_table.add_row("--session", "-s", "Session ID to resume")
    options_table.add_row("--attach", "", "Attach file(s) to session")
    options_table.add_row("--debug", "-d", "Enable debug mode")
    options_table.add_row("--list-models", "", "List available Ollama models")
    options_table.add_row("--help", "-h", "Show this help")
    console.print(options_table)
    console.print()


def list_models():
    """List available Ollama models."""
    console.print("\n[bold cyan]📋 Available Ollama Models[/bold cyan]\n")
    
    try:
        import ollama
        client = ollama.Client()
        models_list = client.list()
        
        if models_list.get('models'):
            table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Model", style="cyan")
            table.add_column("Size", style="yellow")
            table.add_column("Modified", style="dim")
            
            for model in models_list['models']:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                size_gb = f"{size / (1024**3):.1f} GB" if size else "?"
                modified = model.get('modified_at', '')[:10] if model.get('modified_at') else "?"
                table.add_row(name, size_gb, modified)
            
            console.print(table)
            console.print(f"\n[dim]Use with: agentry -m <model_name>[/dim]")
        else:
            console.print("[yellow]No models found. Run 'ollama pull <model>' to download.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")
        console.print("[dim]Make sure Ollama is running.[/dim]")
    
    # Also show popular Groq models
    console.print("\n[bold cyan]🚀 Popular Groq Models[/bold cyan]\n")
    groq_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    groq_table.add_column("Model", style="cyan")
    groq_table.add_column("Description", style="dim")
    groq_table.add_row("llama-3.3-70b-versatile", "Best quality, versatile")
    groq_table.add_row("llama-3.1-8b-instant", "Fast, good for simple tasks")
    groq_table.add_row("mixtral-8x7b-32768", "Large context window")
    groq_table.add_row("gemma2-9b-it", "Google's Gemma 2")
    console.print(groq_table)
    console.print(f"\n[dim]Use with: agentry -p groq -m <model_name>[/dim]")
    
    # Gemini models
    console.print("\n[bold cyan]✨ Popular Gemini Models[/bold cyan]\n")
    gemini_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    gemini_table.add_column("Model", style="cyan")
    gemini_table.add_column("Description", style="dim")
    gemini_table.add_row("gemini-2.0-flash", "Latest, fast and capable")
    gemini_table.add_row("gemini-1.5-pro", "Best quality")
    gemini_table.add_row("gemini-1.5-flash", "Fast, good balance")
    console.print(gemini_table)
    console.print(f"\n[dim]Use with: agentry -p gemini -m <model_name>[/dim]\n")

    # Azure models
    console.print("\n[bold cyan]🏢 Azure OpenAI[/bold cyan]\n")
    console.print("Azure models depend on your specific deployments.")
    console.print("Common deployment names: [green]gpt-4, gpt-35-turbo, claude-3-opus[/green]")
    console.print(f"\n[dim]Use with: agentry -p azure --endpoint <url> -m <deployment_name>[/dim]\n")


async def run_main():
    parser = argparse.ArgumentParser(
        description="Agentry - Smart AI Agent CLI",
        add_help=False  # We'll handle help ourselves
    )
    parser.add_argument('--help', '-h', action='store_true', help='Show help')
    parser.add_argument('--list-models', action='store_true', help='List available models')
    parser.add_argument('--session', '-s', default=None, help='Session ID')
    parser.add_argument('--provider', '-p', default='ollama', choices=['ollama', 'groq', 'gemini', 'azure'], help='LLM provider')
    parser.add_argument('--model', '-m', help='Model name')
    parser.add_argument('--endpoint', help='Endpoint URL (required for Azure)')
    
    # Agent type selection
    parser.add_argument('--agent', '-a', default='default', 
                        choices=['default', 'smart', 'copilot'],
                        help='Agent type')
    parser.add_argument('--copilot', '-c', action='store_true', help='Use Copilot Agent')
    
    # Smart Agent options
    parser.add_argument('--mode', default='solo', choices=['solo', 'project'],
                        help='Smart Agent mode')
    parser.add_argument('--project', default=None, help='Project ID')
    
    parser.add_argument('--attach', action='append', help='Attach file(s)')
    parser.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    args = parser.parse_args()
    
    # Handle special commands
    if args.help:
        show_help()
        return
    
    if args.list_models:
        list_models()
        return
    
    # Handle --copilot shortcut
    if args.copilot:
        args.agent = 'copilot'
    
    display = DisplayManager()
    display.print_startup_screen()
    
    # Show agent type info
    if args.agent == 'smart':
        console.print(f"[bold cyan]🧠 Smart Agent[/] • Mode: [yellow]{args.mode}[/]" + 
                     (f" • Project: [green]{args.project}[/]" if args.project else ""))
    elif args.agent == 'copilot':
        console.print("[bold cyan]💻 Copilot Agent[/] • Optimized for coding")
    else:
        console.print("[bold cyan]🤖 Default Agent[/]")
    
    console.print(f"[dim]Provider: {args.provider} • Model: {args.model or 'default'}[/dim]")
    
    # Initialize Session Manager
    session_manager = SessionManager()
    
    # Get API key if needed
    api_key = None
    if args.provider in ['groq', 'gemini', 'azure']:
        api_key = get_api_key(args.provider) or console.input(f"[bold yellow]Enter {args.provider.title()} API Key: [/]")
    
    # Get Endpoint if needed
    endpoint = args.endpoint
    if args.provider == 'azure' and not endpoint:
        # Try to load from env or input
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT") or console.input("[bold yellow]Enter Azure Endpoint URL: [/]")
    
    # Initialize Agent & Tools with Spinner
    observer = None
    agent = None
    debug = args.debug or DEBUG_MODE
    
    mcp_path = os.path.abspath(MCP_CONFIG_PATH)
    
    with console.status("[bold green]Booting Agentry...[/]", spinner="dots") as status:
        status.update(f"[bold green]Initializing {args.agent.title()} Agent...[/]")
        
        if args.agent == 'smart':
            mode = SmartAgentMode.PROJECT if args.mode == 'project' else SmartAgentMode.SOLO
            agent = SmartAgent(
                llm=args.provider,
                model=args.model,
                api_key=api_key,
                endpoint=endpoint,
                mode=mode,
                project_id=args.project,
                debug=debug
            )
            
        elif args.agent == 'copilot':
            agent = CopilotAgent(
                llm=args.provider,
                model=args.model,
                api_key=api_key,
                endpoint=endpoint,
                debug=debug
            )
            
        else:
            agent = Agent(
                llm=args.provider,
                model=args.model,
                api_key=api_key,
                endpoint=endpoint,
                debug=debug
            )
            agent.load_default_tools()
        
        if os.path.exists(mcp_path):
            status.update(f"[bold green]Connecting to MCP servers...[/]")
            try:
                await agent.add_mcp_server(mcp_path)
            except Exception as e:
                console.print(f"[bold red]⚠️  Failed to connect MCP servers: {e}[/]")
        
        status.update("[bold green]Starting Hot Reloader...[/]")
        import scratchy
        watch_dir = os.path.dirname(os.path.abspath(scratchy.__file__))
        observer = start_reloader(watch_dir)
        
    console.print("[bold green]✔ All systems operational.[/]")

    if args.session:
        session_id = args.session
    else:
        session_id = str(uuid.uuid4())
        print(f"🆔 Generated new session ID: {session_id}")

    try:
        app = ClientApp(
            agent=agent, 
            session_manager=session_manager, 
            initial_session_id=session_id, 
            initial_attachments=args.attach
        )
        await app.run()
    finally:
        print("\n💾 Cleaning up...")
        if observer:
            observer.stop()
            observer.join()
        await agent.cleanup()

def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(run_main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal Error: {e}")

if __name__ == "__main__":
    main()
