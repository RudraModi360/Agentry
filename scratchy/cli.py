import asyncio
import os
import argparse
import uuid
import sys
from rich.console import Console

from scratchy import Agent, CopilotAgent
from scratchy.config.settings import get_api_key
from scratchy.session_manager import SessionManager
from scratchy.reloader import start_reloader
from scratchy.client.app import ClientApp
from scratchy.client.display import DisplayManager

# --- Configuration ---
MCP_CONFIG_PATH = "mcp.json"
DEBUG_MODE = False

console = Console()

async def run_main():
    parser = argparse.ArgumentParser(description="Scratchy Agent with Session Management")
    parser.add_argument('--session', '-s', default=None, help='Session ID to use or autospecify with UUID')
    parser.add_argument('--provider', '-p', default='ollama', choices=['ollama', 'groq', 'gemini'], help='LLM provider')
    parser.add_argument('--model', '-m', help='Model name')
    parser.add_argument('--copilot', '-c', action='store_true', help='Use Copilot Agent')
    parser.add_argument('--attach', '-a', action='append', help='Attach file(s) to the session start')
    args = parser.parse_args()
    
    display = DisplayManager()
    display.print_startup_screen()
    
    # Initialize Session Manager
    session_manager = SessionManager()
    
    # Get API key if needed
    api_key = None
    if args.provider in ['groq', 'gemini']:
        api_key = get_api_key(args.provider) or console.input(f"[bold yellow]Enter {args.provider.title()} API Key: [/]")
    
    # Initialize Agent & Tools with Spinner
    observer = None
    agent = None
    
    # Fix for relative path usage when running as installed package
    # We need to find mcp.json relative to CWD, not the package file
    mcp_path = os.path.abspath(MCP_CONFIG_PATH)
    
    with console.status("[bold green]Booting Scratchy...[/]", spinner="dots") as status:
        # 1. Load Agent
        status.update("[bold green]Initializing Agent...[/]")
        if args.copilot:
            agent = CopilotAgent(
                llm=args.provider,
                model=args.model,
                api_key=api_key,
                debug=DEBUG_MODE
            )
        else:
            agent = Agent(
                llm=args.provider,
                model=args.model,
                api_key=api_key,
                debug=DEBUG_MODE
            )
            agent.load_default_tools()
        
        # 2. Connect MCP Servers
        if os.path.exists(mcp_path):
            status.update(f"[bold green]Connecting to MCP servers...[/]")
            try:
                await agent.add_mcp_server(mcp_path)
            except Exception as e:
                console.print(f"[bold red]⚠️  Failed to connect MCP servers: {e}[/]")
        
        # 3. Start Hot Reloader
        status.update("[bold green]Starting Hot Reloader...[/]")
        # For reloader, we want to watch the scratchy package directory
        import scratchy
        watch_dir = os.path.dirname(os.path.abspath(scratchy.__file__))
        observer = start_reloader(watch_dir)
        
    console.print("[bold green]✔ All systems operational.[/]")

    # Run Interactive Session
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
        # Cleanup & Save Memory
        print("\n💾 Cleaning up...")
        if observer:
            observer.stop()
            observer.join()
        await agent.cleanup()

def main():
    # Windows specific fix for asyncio loop
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
