"""
Advanced Agent Runner & Debugger with Session Management
---------------------------------------------------------
Features:
- Session persistence with .toon format
- Helper commands (/help, /tools, /sessions, /new, /resume)
- Multi-session support with automatic saving
- MCP server integration

Usage:
    python run_agent.py [--session SESSION_ID]
"""

import asyncio
import json
import sys
import os
import argparse
import uuid
import base64
import mimetypes
from typing import Union, List, Dict, Any
from scratchy import Agent, CopilotAgent
from scratchy.config.settings import get_api_key
from scratchy.session_manager import SessionManager
from scratchy.reloader import start_reloader
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.json import JSON
from rich.align import Align
from rich.text import Text

console = Console()

def print_startup_screen(version="0.1.0"):
    console.clear()
    
    # Simple ASCII or styled text
    title = Text("\n   SCRATCHY   \n", style="bold white on #ff8800")
    subtitle = Text("Advanced Agentic Framework", style="dim white")
    
    console.print(Align.center(title))
    console.print(Align.center(subtitle))
    console.print(Align.center(Text(f"v{version}", style="dim #444444")))
    console.print()

# --- Configuration ---
MCP_CONFIG_PATH = "mcp.json"
DEBUG_MODE = True

# --- Helper Commands ---
HELP_TEXT = """
🤖 Scratchy Agent - Available Commands:

Chat Commands:
  Just type your message to chat with the agent
  
Special Commands:
  /help              Show this help message
  /status            Show current session info
  /tools             List all available tools
  /sessions          List all saved sessions
  /new <session_id>  Create a new session with given ID
  /resume <id>       Resume a previous session
  /clear             Clear current session history
  /exit, /quit       Exit the application

Session Management:
  - Sessions are automatically saved to session_history/
  - Each session is stored as <session_id>_chat.toon
  - Use /resume to continue previous conversations
"""

async def show_tools(agent: Agent):
    """Display all available tools."""
    tools = await agent.get_all_tools()
    print(f"\n🛠️  Available Tools ({len(tools)}):\n")
    for tool in tools:
        name = tool['function']['name']
        desc = tool['function']['description']
        print(f"  • {name}")
        print(f"    {desc[:80]}...")
    print()

def show_sessions(session_manager: SessionManager):
    """Display all saved sessions."""
    sessions = session_manager.list_sessions()
    
    if not sessions:
        print("\n📂 No saved sessions found.\n")
        return
    
    print(f"\n📂 Saved Sessions ({len(sessions)}):\n")
    for session in sessions:
        print(f"  • {session['id']}")
        print(f"    Created: {session['created_at']}")
        print(f"    Messages: {session['message_count']}")
        print()

def process_multimodal_input(user_input: str) -> Union[str, List[Dict[str, Any]]]:
    """
    Scans the input for file paths to images. 
    If found, reads them and returns a multimodal list message.
    Otherwise returns the original string.
    """
    tokens = user_input.split()
    images = []
    
    # Check each token to see if it's a file
    for token in tokens:
        # Strip potential quotes
        clean_token = token.strip('"').strip("'")
        
        if os.path.exists(clean_token) and os.path.isfile(clean_token):
            # Check mime type
            mime_type, _ = mimetypes.guess_type(clean_token)
            if mime_type and mime_type.startswith('image/'):
                try:
                    with open(clean_token, "rb") as f:
                        data = f.read()
                        b64_data = base64.b64encode(data).decode('utf-8')
                        data_uri = f"data:{mime_type};base64,{b64_data}"
                        
                        images.append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_uri
                            }
                        })
                        print(f"   🖼️  Attached image: {clean_token}")
                except Exception as e:
                    print(f"   ⚠️  Failed to load image {clean_token}: {e}")

    if not images:
        return user_input
        
    # Construct multimodal message
    content = []
    content.append({"type": "text", "text": user_input})
    content.extend(images)
    
    return content

async def run_interactive_session(agent: Agent, session_manager: SessionManager, initial_session_id: str = "default"):
    """Runs an interactive chat loop with session management."""
    current_session_id = initial_session_id
    
    # Try to load existing session
    if session_manager.session_exists(current_session_id):
        console.print(f"[bold cyan]📂 Resuming session:[/][cyan] '{current_session_id}'[/]")
        messages = session_manager.load_session(current_session_id)
        if messages:
            session = agent.get_session(current_session_id)
            session.messages = messages
            console.print(f"   [dim]Loaded {len(messages)} messages from history.[/]")
    else:
        console.print(f"[bold green]✨ Started new session:[/][green] '{current_session_id}'[/]")
    
    console.print(f"\n[dim]💬 Type '/help' for commands or start chatting![/]\n")
    
    while True:
        try:
            # Use console.input via executor to allow coloring
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: console.input(f"[bold green]You[/] ([dim]{current_session_id}[/]): ")
            )
            user_input = user_input.strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.startswith('/'):
                command_parts = user_input.split(maxsplit=1)
                command = command_parts[0].lower()
                args = command_parts[1] if len(command_parts) > 1 else ""
                
                if command in ['/exit', '/quit']:
                    # Save before exit
                    session = agent.get_session(current_session_id)
                    session_manager.save_session(current_session_id, session.messages)
                    console.print("\n[bold yellow]💾 Session saved. Goodbye![/]\n")
                    break
                
                elif command == '/help':
                    console.print(Panel(HELP_TEXT, title="Help", border_style="blue"))
                    continue
                
                elif command in ['/status', '/info']:
                    try:
                        session = agent.get_session(current_session_id)
                        text = Text()
                        text.append(f"Session ID: {current_session_id}\n", style="bold")
                        text.append(f"Messages: {len(session.messages)}\n")
                        text.append(f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        text.append(f"Last Activity: {session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        text.append(f"Saved: {'Yes' if session_manager.session_exists(current_session_id) else 'No'}")
                        console.print(Panel(text, title="📊 Current Session Status", border_style="cyan"))
                    except Exception as e:
                        console.print(f"[bold red]❌ Error getting status: {e}[/]")
                    continue
                
                elif command == '/tools':
                    await show_tools(agent)
                    continue
                
                elif command == '/sessions':
                    show_sessions(session_manager)
                    continue
                
                elif command == '/new':
                    if not args:
                        console.print("[yellow]⚠️  Usage: /new <session_id>[/]")
                        continue
                    
                    # Save current session
                    session = agent.get_session(current_session_id)
                    session_manager.save_session(current_session_id, session.messages)
                    
                    # Switch to new session
                    current_session_id = args
                    console.print(f"[bold green]✨ Created new session:[/][green] '{current_session_id}'[/]")
                    continue
                
                elif command == '/resume':
                    if not args:
                        console.print("[yellow]⚠️  Usage: /resume <session_id>[/]")
                        continue
                    
                    if not session_manager.session_exists(args):
                        console.print(f"[red]⚠️  Session '{args}' not found.[/]")
                        continue
                    
                    # Save current session
                    session = agent.get_session(current_session_id)
                    session_manager.save_session(current_session_id, session.messages)
                    
                    # Load and switch to requested session
                    current_session_id = args
                    messages = session_manager.load_session(current_session_id)
                    session = agent.get_session(current_session_id)
                    session.messages = messages
                    console.print(f"[bold cyan]📂 Resumed session:[/][cyan] '{current_session_id}'[/] [dim]({len(messages)} messages)[/]")
                    continue
                
                elif command == '/clear':
                    agent.clear_session(current_session_id)
                    console.print(f"[bold red]🗑️  Cleared session:[/][red] '{current_session_id}'[/]")
                    continue
                
                else:
                    console.print(f"[yellow]⚠️  Unknown command: {command}. Type '/help' for available commands.[/]")
                    continue
            
            # Regular chat
            final_input = await asyncio.get_event_loop().run_in_executor(
                None, process_multimodal_input, user_input
            )
            await agent.chat(final_input, session_id=current_session_id)
            
            # Auto-save after each interaction
            session = agent.get_session(current_session_id)
            session_manager.save_session(current_session_id, session.messages)
            
        except KeyboardInterrupt:
            # Save on interrupt
            session = agent.get_session(current_session_id)
            session_manager.save_session(current_session_id, session.messages)
            print("\n\n💾 Session saved. Goodbye!\n")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Scratchy Agent with Session Management")
    parser.add_argument('--session', '-s', default=None, help='Session ID to use or autospecify with UUID')
    parser.add_argument('--provider', '-p', default='ollama', choices=['ollama', 'groq', 'gemini'], help='LLM provider')
    parser.add_argument('--model', '-m', help='Model name')
    parser.add_argument('--copilot', '-c', action='store_true', help='Use Copilot Agent')
    args = parser.parse_args()
    
    print_startup_screen()
    
    # Initialize Session Manager
    session_manager = SessionManager()
    
    # Get API key if needed
    api_key = None
    if args.provider in ['groq', 'gemini']:
        api_key = get_api_key(args.provider) or console.input(f"[bold yellow]Enter {args.provider.title()} API Key: [/]")
    
    # Initialize Agent with Spinner
    agent = None
    with console.status("[bold green]Initializing Agent & Tools...[/]", spinner="dots"):
        if args.copilot:
            console.print("[dim]🚀 Loading Copilot Agent...[/]")
            agent = CopilotAgent(
                llm=args.provider,
                model=args.model,
                api_key=api_key,
                debug=DEBUG_MODE
            )
        else:
            console.print("[dim]🤖 Loading General Agent...[/]")
            agent = Agent(
                llm=args.provider,
                model=args.model,
                api_key=api_key,
                debug=DEBUG_MODE
            )
            agent.load_default_tools()
        
        # Connect MCP Servers (Optional)
        if os.path.exists(MCP_CONFIG_PATH):
            console.print(f"[dim]🔌 Connecting to MCP servers from {MCP_CONFIG_PATH}...[/]")
            try:
                await agent.add_mcp_server(MCP_CONFIG_PATH)
                console.print("[bold green]✅ MCP servers connected.[/]")
            except Exception as e:
                console.print(f"[bold red]⚠️  Failed to connect MCP servers: {e}[/]")
    
    # Setup Callbacks
    def on_tool_start(session, name, args):
        console.print(Panel(
            JSON.from_data(args),
            title=f"[bold #ffaa00]🔧 Executing Tool: {name}[/]",
            border_style="#ffaa00"
        ))

    def on_tool_end(session, name, result):
        result_content = result
        if isinstance(result, dict):
            # Check if it's a ToolResult dict
            if 'content' in result:
                result_content = result['content']
            else:
                result_content = result
        
        # Determine how to display the result
        if isinstance(result_content, (dict, list)):
            renderable = JSON.from_data(result_content)
        else:
            renderable = str(result_content)
            if len(renderable) > 2000:
                renderable = renderable[:2000] + "... (truncated)"
        
        console.print(Panel(
            renderable,
            title=f"[bold #00ff00]✅ Tool Finished: {name}[/]",
            border_style="#00ff00"
        ))

    def on_final_message(session, content):
        from rich.markdown import Markdown
        console.print(Panel(
            Markdown(content),
            title=f"[bold blue]🤖 Assistant ({session})[/]",
            border_style="blue"
        ))

    async def on_tool_approval(session, name, args):
        console.print()
        console.rule("[bold red]⚠️  APPROVAL REQUIRED", style="red")
        console.print(f" [bold]Tool:[/bold] [cyan]{name}[/cyan]")
        
        console.print(Panel(
            JSON.from_data(args),
            title="Arguments",
            border_style="yellow"
        ))
        
        while True:
            # Use run_in_executor for blocking input
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: console.input("[bold yellow]Execute?[/] [[green]Y[/]es/[red]N[/]o/[blue]E[/]dit]: ")
            )
            choice = response.strip().lower()
            
            if choice in ['y', 'yes', '']:
                console.print("[bold green]✅ Approved.[/]")
                return True
            elif choice in ['n', 'no']:
                console.print("[bold red]❌ Denied.[/]")
                return False
            elif choice in ['e', 'edit']:
                # Special handling for run_command to make it easier
                if name == 'run_command' and 'CommandLine' in args:
                    console.print(f"   [dim]Current Command:[/dim] {args['CommandLine']}")
                    new_cmd = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: console.input("[bold blue]   New Command > [/]")
                    )
                    if new_cmd.strip():
                        args['CommandLine'] = new_cmd.strip()
                        console.print("   [bold green]✅ Command updated and approved.[/]")
                        return args
                    else:
                        console.print("   [yellow]⚠️  Empty input. Keeping original.[/]")
                        continue
                
                # Generic JSON edit
                console.print("   [bold blue]📝 Enter new arguments (JSON format):[/]")
                try:
                    new_json_str = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: console.input("[dim]   JSON > [/]")
                    )
                    new_args = json.loads(new_json_str)
                    console.print("   [bold green]✅ Arguments updated and approved.[/]")
                    return new_args
                except json.JSONDecodeError:
                    console.print("   [bold red]❌ Invalid JSON. Please try again.[/]")
                    continue
            else:
                console.print("   [red]⚠️  Invalid choice.[/]")

    agent.set_callbacks(
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
        on_tool_approval=on_tool_approval,
        on_final_message=on_final_message
    )
    
    # Start Hot Reloader
    # Watch the 'scratchy' directory for changes
    base_dir = os.path.dirname(os.path.abspath(__file__))
    watch_dir = os.path.join(base_dir, "scratchy")
    observer = start_reloader(watch_dir)
    
    # Run Interactive Session
    if args.session:
        session_id = args.session
    else:
        session_id = str(uuid.uuid4())
        print(f"🆔 Generated new session ID: {session_id}")

    await run_interactive_session(agent, session_manager, session_id)
    
    # Cleanup & Save Memory
    print("\n💾 Cleaning up...")
    # Memory is now handled continuously by middleware, so no final consolidation is needed.
    
    observer.stop()
    observer.join()
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
