from typing import Optional, List, Callable
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from scratchy.session_manager import SessionManager
from scratchy import Agent
from scratchy.client.display import DisplayManager
from scratchy.client.input import pick_files
import os

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
  /attach <path>     Attach a file by path
  /upload            Open system file picker to attach files
  /previous          Switch to the previous session
  /clear             Clear current session history
  /exit, /quit       Exit the application

Session Management:
  - Sessions are automatically saved to persistent storage (SQLite/VFS)
  - You can switch between sessions freely
  - Use /resume or /previous to navigate history
  - Use /upload to easily add images or documents to your chat
"""

class CommandProcessor:
    def __init__(self, agent: Agent, session_manager: SessionManager, display: DisplayManager):
        self.agent = agent
        self.session_manager = session_manager
        self.display = display
        self.console = display.console
        
        self.current_session_id = "default"
        self.previous_session_id = None
        self.pending_attachments = []

    async def handle_command(self, user_input: str) -> bool:
        """
        Handles slash commands. Returns True if a command was handled, False otherwise.
        Raises SystemExit if exit command is given.
        """
        if not user_input.startswith('/'):
            return False
            
        command_parts = user_input.split(maxsplit=1)
        command = command_parts[0].lower()
        args = command_parts[1] if len(command_parts) > 1 else ""
        
        if command in ['/exit', '/quit']:
            self._save_current()
            self.console.print("\n[bold yellow]💾 Session saved. Goodbye![/]\n")
            raise SystemExit
        
        elif command == '/help':
            self.console.print(Panel(HELP_TEXT, title="Help", border_style="blue"))
            
        elif command in ['/status', '/info']:
            self._show_status()
            
        elif command == '/tools':
            await self.display.show_tools(self.agent)
            
        elif command == '/sessions':
            self.display.show_sessions(self.session_manager)
            
        elif command == '/new':
            self._handle_new(args)
            
        elif command == '/resume':
            self._handle_resume(args)
            
        elif command == '/previous':
            self._handle_previous()
            
        elif command == '/clear':
            self.agent.clear_session(self.current_session_id)
            self.console.print(f"[bold red]🗑️  Cleared session:[/][red] '{self.current_session_id}'[/]")
            
        elif command == '/attach':
            self._handle_attach(args)
            
        elif command in ['/upload', '/u']:
            self._handle_upload()
            
        else:
            self.console.print(f"[yellow]⚠️  Unknown command: {command}. Type '/help' for available commands.[/]")
            
        return True

    def _save_current(self):
        session = self.agent.get_session(self.current_session_id)
        if session:
            self.session_manager.save_session(self.current_session_id, session.messages)

    def _show_status(self):
        try:
            session = self.agent.get_session(self.current_session_id)
            text = Text()
            text.append(f"Session ID: {self.current_session_id}\n", style="bold")
            text.append(f"Messages: {len(session.messages)}\n")
            text.append(f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            text.append(f"Last Activity: {session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}\n")
            text.append(f"Saved: {'Yes' if self.session_manager.session_exists(self.current_session_id) else 'No'}\n")
            if self.previous_session_id:
                    text.append(f"Previous Session: {self.previous_session_id}\n", style="dim")
            self.console.print(Panel(text, title="📊 Current Session Status", border_style="cyan"))
        except Exception as e:
            self.console.print(f"[bold red]❌ Error getting status: {e}[/]")

    def _handle_new(self, args):
        if not args:
            self.console.print("[yellow]⚠️  Usage: /new <session_id>[/]")
            return
        
        self._save_current()
        self.previous_session_id = self.current_session_id
        self.current_session_id = args
        self.console.print(f"[bold green]✨ Created new session:[/][green] '{self.current_session_id}'[/]")

    def _handle_resume(self, args):
        if not args:
            self.console.print("[yellow]⚠️  Usage: /resume <session_id>[/]")
            return
        
        if not self.session_manager.session_exists(args):
            self.console.print(f"[red]⚠️  Session '{args}' not found.[/]")
            return
        
        self._save_current()
        self.previous_session_id = self.current_session_id
        self.current_session_id = args
        self._load_session(args)
        self.console.print(f"[bold cyan]📂 Resumed session:[/][cyan] '{self.current_session_id}'[/]")

    def _handle_previous(self):
        if not self.previous_session_id:
            self.console.print("[yellow]⚠️  No previous session to switch to.[/]")
            return
        
        if not self.session_manager.session_exists(self.previous_session_id):
            self.console.print(f"[red]⚠️  Previous session '{self.previous_session_id}' not found.[/]")
            return

        self._save_current()
        # Swap
        temp = self.current_session_id
        self.current_session_id = self.previous_session_id
        self.previous_session_id = temp
        
        self._load_session(self.current_session_id)
        self.console.print(f"[bold cyan]📂 Switched to previous session:[/][cyan] '{self.current_session_id}'[/]")

    def _load_session(self, session_id):
        messages = self.session_manager.load_session(session_id)
        session = self.agent.get_session(session_id)
        session.messages = messages

    def _handle_attach(self, args):
        if not args:
            self.console.print("[yellow]⚠️  Usage: /attach <file_path>[/]")
            return
        
        file_path = args.strip().strip('"').strip("'")
        if os.path.exists(file_path):
            self.pending_attachments.append(file_path)
            self.console.print(f"[bold green]📎 File queued: {file_path}[/]")
        else:
            self.console.print(f"[red]⚠️  File not found: {file_path}[/]")

    def _handle_upload(self):
        from scratchy.client.input import TK_AVAILABLE 
        if not TK_AVAILABLE:
            self.console.print("[red]⚠️  File picker not available. Use /attach <path>.[/]")
            return
        
        self.console.print("[cyan]📂 Opening file picker...[/]")
        files = pick_files()
        
        if files:
            self.pending_attachments.extend(files)
            self.console.print(f"[bold green]📎 Queued {len(files)} files:[/]")
            for f in files:
                self.console.print(f"  - {os.path.basename(f)}")
        else:
            self.console.print("[yellow]⚠️  No files selected.[/]")
