from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.json import JSON
from rich.markdown import Markdown
from typing import Union, Dict, Any, List
import json
import asyncio
from mcp import Tool  # Assuming type hints, but dict is fine

console = Console()

class DisplayManager:
    def __init__(self):
        self.console = console
        self.current_live = None
        self.response_buffer = ""

    def print_startup_screen(self, version="0.1.0"):
        self.console.clear()
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
        self.console.print(Align.center(Text(logo, style="bold cyan")))
        subtitle = Text("Agentic Framework", style="dim white")
        self.console.print(Align.center(subtitle))
        self.console.print(Align.center(Text(f"v{version}", style="dim #444444")))
        self.console.print()

    async def show_tools(self, agent):
        """Display all available tools."""
        tools = await agent.get_all_tools()
        self.console.print(f"\n🛠️  Available Tools ({len(tools)}):\n")
        for tool in tools:
            name = tool['function']['name']
            desc = tool['function']['description']
            self.console.print(f"  • {name}")
            self.console.print(f"    {desc[:80]}...")
        self.console.print()

    def show_sessions(self, session_manager):
        """Display all saved sessions."""
        sessions = session_manager.list_sessions()
        if not sessions:
            self.console.print("\n📂 No saved sessions found.\n")
            return
        
        self.console.print(f"\n📂 Saved Sessions ({len(sessions)}):\n")
        for session in sessions:
            self.console.print(f"  • {session['id']}")
            self.console.print(f"    Created: {session['created_at']}")
            self.console.print(f"    Messages: {session['message_count']}")
            self.console.print()

    def on_tool_start(self, session, name, args):
        # If we were printing tokens manually, print a newline before tool output
        if self.response_buffer:
             print() # Newline to separate stream from tool box
             self.response_buffer = "" # Clear buffer
        
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
                summary = json.dumps(args, default=str)
                if len(summary) > 100: summary = summary[:97] + "..."
        else:
             summary = str(args)

        self.console.print(f"[dim]🔧 Executing: [bold cyan]{name}[/] ({summary})[/]")

    def on_tool_end(self, session, name, result):
        result_content = result
        if isinstance(result, dict):
            if 'content' in result:
                result_content = result['content']
        
        # Determine how to display the result
        if isinstance(result_content, (dict, list)):
            renderable = JSON.from_data(result_content)
        else:
            renderable = str(result_content)
            if len(renderable) > 2000:
                renderable = renderable[:2000] + "... (truncated)"
        
        self.console.print(Panel(
            renderable,
            title=f"[bold #00ff00]✅ Tool Finished: {name}[/]",
            border_style="#00ff00"
        ))

    def on_token(self, token):
        print(token, end='', flush=True)
        self.response_buffer += token

    def on_final_message(self, session, content):
        print() # Newline
        self.response_buffer = ""
            
        if content and content.strip():
            self.console.print(Panel(
                Markdown(content),
                title=f"[bold blue]🤖 Assistant ({session})[/]",
                border_style="blue"
            ))

    async def on_tool_approval(self, session, name, args):
        self.console.print()
        self.console.rule("[bold red]⚠️  APPROVAL REQUIRED", style="red")
        self.console.print(f" [bold]Tool:[/bold] [cyan]{name}[/cyan]")
        
        self.console.print(Panel(
            JSON.from_data(args),
            title="Arguments",
            border_style="yellow"
        ))
        
        result = False
        while True:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.console.input("[bold yellow]Execute?[/] [[green]Y[/]es/[red]N[/]o/[blue]E[/]dit]: ")
            )
            choice = response.strip().lower()
            
            if choice in ['y', 'yes', '']:
                self.console.print("[bold green]✅ Approved.[/]")
                result = True
                break
            elif choice in ['n', 'no']:
                self.console.print("[bold red]❌ Denied.[/]")
                result = False
                break
            elif choice in ['e', 'edit']:
                if name == 'run_command' and 'CommandLine' in args:
                    self.console.print(f"   [dim]Current Command:[/dim] {args['CommandLine']}")
                    new_cmd = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.console.input("[bold blue]   New Command > [/]")
                    )
                    if new_cmd.strip():
                        args['CommandLine'] = new_cmd.strip()
                        self.console.print("   [bold green]✅ Command updated and approved.[/]")
                        result = args
                        break
                    else:
                        self.console.print("   [yellow]⚠️  Empty input. Keeping original.[/]")
                        continue
                
                self.console.print("   [bold blue]📝 Enter new arguments (JSON format):[/]")
                try:
                    new_json_str = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.console.input("[dim]   JSON > [/]")
                    )
                    new_args = json.loads(new_json_str)
                    self.console.print("   [bold green]✅ Arguments updated and approved.[/]")
                    result = new_args
                    break
                except json.JSONDecodeError:
                    self.console.print("   [bold red]❌ Invalid JSON. Please try again.[/]")
                    continue
            else:
                self.console.print("   [red]⚠️  Invalid choice.[/]")
        
        return result
