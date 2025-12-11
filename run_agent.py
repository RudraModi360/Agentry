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
import mimetypes
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False
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
    
    logo = """
   _____                _       _           
  / ____|              | |     | |          
 | (___   ___ _ __ __ _| |_ ___| |__  _   _ 
  \___ \ / __| '__/ _` | __/ __| '_ \| | | |
  ____) | (__| | | (_| | || (__| | | | |_| |
 |_____/ \___|_|  \__,_|\__\___|_| |_|\__, |
                                       __/ |
                                      |___/ 
    """
    
    console.print(Align.center(Text(logo, style="bold cyan")))
    subtitle = Text("Agentic Framework", style="dim white")
    
    console.print(Align.center(subtitle))
    console.print(Align.center(Text(f"v{version}", style="dim #444444")))
    console.print()

# --- Configuration ---
MCP_CONFIG_PATH = "mcp.json"
DEBUG_MODE = False

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
  /new <session_id>  Create a new session with given ID
  /resume <id>       Resume a previous session
  /attach <path>     Attach a file by path
  /upload            Open system file picker to attach files
  /previous          Switch to the previous session
  /clear             Clear current session history
  /exit, /quit       Exit the application

Session Management:
  - Sessions are automatically saved to persistent storage (SQLite/VFS)
  - You can switch between sessions freely
  - Use /resume or /previous to navigate history
  - Use /resume or /previous to navigate history
  - Use /upload to easily add images or documents to your chat
"""

def pick_files():
    """Opens a native file picker dialog."""
    if not TK_AVAILABLE:
        return []
    
    try:
        root = tk.Tk()
        root.withdraw() # Hide main window
        root.attributes('-topmost', True) # Bring to front
        
        file_paths = filedialog.askopenfilenames(
            title="Select files to upload",
            filetypes=[("All files", "*.*")]
        )
        
        root.destroy()
        return list(file_paths)
    except Exception as e:
        print(f"Error opening file picker: {e}")
        return []

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

def build_user_message(user_input: str, attachments: List[str] = None) -> Union[str, List[Dict[str, Any]]]:
    """
    Constructs a message payload from user input and optional file attachments.
    Scans the input for file paths and processes explicit attachments.
    Supports Images (added as image_url) and Documents (converted to text).
    """
    attachments = attachments or []
    tokens = user_input.split()
    
    # Collect all potential file paths (explicit + implicit)
    potential_paths = list(attachments)
    for token in tokens:
        clean_token = token.strip('"').strip("'")
        if clean_token not in potential_paths:
            potential_paths.append(clean_token)
            
    processed_content: List[Dict[str, Any]] = []
    processed_paths = set()
    
    # Process files
    for path in potential_paths:
        if not os.path.exists(path) or not os.path.isfile(path):
            continue
            
        # Avoid processing the same file twice
        if path in processed_paths:
            continue
            
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        
        # 1. Document Handling (PDF, DOCX, PPTX, etc.)
        from scratchy.document_handlers import get_handler, DocumentHandlerRegistry
        if ext in DocumentHandlerRegistry._handlers and ext not in ['.txt', '.md', '.py']:
            print(f"   ⏳ Processing document: {os.path.basename(path)}...", end='\r')
            try:
                handler = get_handler(path)
                md_content = handler.to_markdown()
                
                content_block = f"\n\n--- Document Attachment: {os.path.basename(path)} ---\n{md_content}\n-----------------------------------\n"
                processed_content.append({
                    "type": "text",
                    "text": content_block
                })
                print(f"   📄 Attached document: {path}")
                processed_paths.add(path)
                continue
            except Exception as e:
                print(f"   ⚠️  Failed to attach document {path}: {e}")

        # 2. Image Handling
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type and mime_type.startswith('image/'):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    b64_data = base64.b64encode(data).decode('utf-8')
                    data_uri = f"data:{mime_type};base64,{b64_data}"
                    
                    processed_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri
                        }
                    })
                    print(f"   🖼️  Attached image: {path}")
                    processed_paths.add(path)
            except Exception as e:
                print(f"   ⚠️  Failed to load image {path}: {e}")

    # If no attachments processed, just return text (unless it was empty, but usually handle text)
    if not processed_content:
        return user_input
        
    # Construct final message
    # Put text first
    final_message = []
    if user_input.strip():
        final_message.append({"type": "text", "text": user_input})
    
    # Add all processed extra content (images, doc text blocks)
    final_message.extend(processed_content)
    
    return final_message

async def run_interactive_session(agent: Agent, session_manager: SessionManager, initial_session_id: str = "default", initial_attachments: List[str] = None):
    """Runs an interactive chat loop with session management."""
    current_session_id = initial_session_id
    pending_attachments = initial_attachments or []
    
    if pending_attachments:
        console.print(f"[bold magenta]📎 {len(pending_attachments)} files ready to attach.[/]")
    
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
    
    previous_session_id = None

    while True:
        try:
            # Use console.input via executor to allow coloring
            attach_hint = f" [bold magenta](+{len(pending_attachments)} files)[/]" if pending_attachments else ""
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: console.input(f"[bold green]You[/]{attach_hint} ([dim]{current_session_id}[/]): ")
            )
            user_input = user_input.strip()
            
            # Allow empty input if we have attachments we want to send
            if not user_input and not pending_attachments:
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
                        text.append(f"Saved: {'Yes' if session_manager.session_exists(current_session_id) else 'No'}\n")
                        if previous_session_id:
                             text.append(f"Previous Session: {previous_session_id}\n", style="dim")
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
                    
                    # Update History
                    previous_session_id = current_session_id

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
                    
                    # Update History
                    previous_session_id = current_session_id

                    # Load and switch to requested session
                    current_session_id = args
                    messages = session_manager.load_session(current_session_id)
                    session = agent.get_session(current_session_id)
                    session.messages = messages
                    console.print(f"[bold cyan]📂 Resumed session:[/][cyan] '{current_session_id}'[/] [dim]({len(messages)} messages)[/]")
                    continue

                elif command == '/previous':
                    if not previous_session_id:
                        console.print("[yellow]⚠️  No previous session to switch to.[/]")
                        continue
                    
                    if not session_manager.session_exists(previous_session_id):
                        console.print(f"[red]⚠️  Previous session '{previous_session_id}' not found (maybe deleted?).[/]")
                        continue

                    # Save current session
                    session = agent.get_session(current_session_id)
                    session_manager.save_session(current_session_id, session.messages)

                    # Swap logic: current becomes prev, prev becomes current
                    # But usually "previous" just goes back. If I toggle, it's like Alt-Tab.
                    temp = current_session_id
                    current_session_id = previous_session_id
                    previous_session_id = temp

                    # Load
                    messages = session_manager.load_session(current_session_id)
                    session = agent.get_session(current_session_id)
                    session.messages = messages
                    console.print(f"[bold cyan]📂 Switched to previous session:[/][cyan] '{current_session_id}'[/] [dim]({len(messages)} messages)[/]")
                    continue

                elif command == '/clear':
                    agent.clear_session(current_session_id)
                    console.print(f"[bold red]🗑️  Cleared session:[/][red] '{current_session_id}'[/]")
                    continue
                
                elif command == '/attach':
                    if not args:
                        console.print("[yellow]⚠️  Usage: /attach <file_path>[/]")
                        continue
                    
                    file_path = args.strip().strip('"').strip("'")
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        pending_attachments.append(file_path)
                        console.print(f"[bold green]📎 File queued: {file_path}[/]")
                    else:
                        console.print(f"[red]⚠️  File not found: {file_path}[/]")
                    continue



                elif command in ['/upload', '/u']:
                    if not TK_AVAILABLE:
                        console.print("[red]⚠️  File picker not available (tkinter missing). Use /attach <path> instead.[/]")
                        continue
                    
                    console.print("[cyan]📂 Opening file picker...[/]")
                    # Run within main thread to ensure Tkinter compatibility
                    files = pick_files()
                    
                    if files:
                        pending_attachments.extend(files)
                        console.print(f"[bold green]📎 Queued {len(files)} files:[/]")
                        for f in files:
                            console.print(f"  - {os.path.basename(f)}")
                    else:
                        console.print("[yellow]⚠️  No files selected.[/]")
                    continue

                else:
                    console.print(f"[yellow]⚠️  Unknown command: {command}. Type '/help' for available commands.[/]")
                    continue
            
            # Regular chat
            final_input = await asyncio.get_event_loop().run_in_executor(
                None, build_user_message, user_input, pending_attachments
            )
            
            # Clear pending attachments after they are sent
            # Clear pending attachments after they are sent
            pending_attachments = []

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
    parser.add_argument('--attach', '-a', action='append', help='Attach file(s) to the session start')
    args = parser.parse_args()
    
    print_startup_screen()
    
    # Initialize Session Manager
    session_manager = SessionManager()
    
    # Get API key if needed
    api_key = None
    if args.provider in ['groq', 'gemini' , 'ollama']:
        api_key = get_api_key(args.provider) or console.input(f"[bold yellow]Enter {args.provider.title()} API Key: [/]")
    
    # Initialize Agent & Tools with Spinner
    observer = None
    agent = None
    
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
        if os.path.exists(MCP_CONFIG_PATH):
            status.update(f"[bold green]Connecting to MCP servers...[/]")
            try:
                await agent.add_mcp_server(MCP_CONFIG_PATH)
            except Exception as e:
                console.print(f"[bold red]⚠️  Failed to connect MCP servers: {e}[/]")
        
        # 3. Start Hot Reloader
        status.update("[bold green]Starting Hot Reloader...[/]")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        watch_dir = os.path.join(base_dir, "scratchy")
        observer = start_reloader(watch_dir)
        
    console.print("[bold green]✔ All systems operational.[/]")

    # Setup Callbacks
    def on_tool_start(session, name, args):
        nonlocal current_live, response_buffer
        
        # If we were printing tokens manually, print a newline before tool output
        if response_buffer:
             print() # Newline to separate stream from tool box
             response_buffer = "" # Clear buffer
        
        # Concise tool logging
        summary = ""
        # Heuristics for common arguments to show meaningful summaries
        if isinstance(args, dict):
            if "file_path" in args: summary = f"file='{args['file_path']}'"
            elif "AbsolutePath" in args: summary = f"file='{args['AbsolutePath']}'"
            elif "TargetFile" in args: summary = f"file='{args['TargetFile']}'"
            elif "Url" in args: summary = f"url='{args['Url']}'"
            elif "CommandLine" in args: summary = f"cmd='{args['CommandLine']}'"
            elif "query" in args: summary = f"query='{args['query']}'"
            else:
                # Fallback to truncated JSON
                summary = json.dumps(args, default=str)
                if len(summary) > 100: summary = summary[:97] + "..."
        else:
             summary = str(args)

        console.print(f"[dim]🔧 Executing: [bold cyan]{name}[/] ({summary})[/]")

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

    # Stream State
    from rich.live import Live
    from rich.markdown import Markdown
    
    current_live: Union[Live, None] = None
    response_buffer: str = ""

    def on_token(token):
        nonlocal current_live, response_buffer
        
        # We are intentionally NOT using Rich Live for now because it causes overwriting/flickering issues 
        # in some terminals, as reported by the user.
        # Instead, we just accumulate the buffer.
        # We could print tokens directly, but Markdown rendering breaks if printed token-by-token.
        # So we wait for the final message.
        
        # If the user absolutely wants "streaming" feel, we can just print(token, end='', flush=True) 
        # but that won't have Markdown formatting. 
        # Let's try simple print for now to show activity.
        print(token, end='', flush=True)
        response_buffer += token

    def on_final_message(session, content):
        nonlocal current_live, response_buffer
        # Print a newline after usage of print(..., end='')
        print() 
        
        # Clean up Live display (if any remains)
        if current_live:
            current_live.stop()
            current_live = None
            response_buffer = ""
            
        # Always print the final clean Markdown
        if content and content.strip():
            console.print(Panel(
                Markdown(content),
                title=f"[bold blue]🤖 Assistant ({session})[/]",
                border_style="blue"
            ))

    async def on_tool_approval(session, name, args):
        # Pause Live display if active to allow user interaction
        nonlocal current_live
        was_live = False
        if current_live:
            current_live.stop()
            was_live = True
            
        console.print()
        console.rule("[bold red]⚠️  APPROVAL REQUIRED", style="red")
        console.print(f" [bold]Tool:[/bold] [cyan]{name}[/cyan]")
        
        console.print(Panel(
            JSON.from_data(args),
            title="Arguments",
            border_style="yellow"
        ))
        
        result = False
        while True:
            # Use run_in_executor for blocking input
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: console.input("[bold yellow]Execute?[/] [[green]Y[/]es/[red]N[/]o/[blue]E[/]dit]: ")
            )
            choice = response.strip().lower()
            
            if choice in ['y', 'yes', '']:
                console.print("[bold green]✅ Approved.[/]")
                result = True
                break
            elif choice in ['n', 'no']:
                console.print("[bold red]❌ Denied.[/]")
                result = False
                break
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
                        result = args
                        break
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
                    result = new_args
                    break
                except json.JSONDecodeError:
                    console.print("   [bold red]❌ Invalid JSON. Please try again.[/]")
                    continue
            else:
                console.print("   [red]⚠️  Invalid choice.[/]")
        
        # Resume Live display if it was active
        if was_live and current_live:
            current_live.start()
            
        return result

    agent.set_callbacks(
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
        on_tool_approval=on_tool_approval,
        on_final_message=on_final_message,
        on_token=on_token
    )
    
    # Run Interactive Session
    if args.session:
        session_id = args.session
    else:
        session_id = str(uuid.uuid4())
        print(f"🆔 Generated new session ID: {session_id}")

    await run_interactive_session(agent, session_manager, session_id, initial_attachments=args.attach)
    
    # Cleanup & Save Memory
    print("\n💾 Cleaning up...")
    # Memory is now handled continuously by middleware, so no final consolidation is needed.
    
    if observer:
        observer.stop()
        observer.join()
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
