from agentry.agents import Agent
from agentry.session_manager import SessionManager
from agentry.client.display import DisplayManager
from agentry.client.commands import CommandProcessor
from agentry.client.input import build_user_message
import asyncio
from rich.console import Console

console = Console()

class ClientApp:
    def __init__(self, agent: Agent, session_manager: SessionManager, 
                 initial_session_id: str = "default", initial_attachments: list = None):
        self.agent = agent
        self.session_manager = session_manager
        self.display = DisplayManager()
        self.processor = CommandProcessor(agent, session_manager, self.display)
        
        self.processor.current_session_id = initial_session_id
        if initial_attachments:
            self.processor.pending_attachments = initial_attachments

        # Register callbacks
        self.agent.set_callbacks(
            on_tool_start=self.display.on_tool_start,
            on_tool_end=self.display.on_tool_end,
            on_tool_approval=self.display.on_tool_approval,
            on_final_message=self.display.on_final_message,
            on_token=self.display.on_token
        )

    async def run(self):
        current_id = self.processor.current_session_id
        
        # Load session if exists
        if self.session_manager.session_exists(current_id):
            self.display.console.print(f"[bold cyan]📂 Resuming session:[/][cyan] '{current_id}'[/]")
            self.processor._load_session(current_id)
        else:
            self.display.console.print(f"[bold green]✨ Started new session:[/][green] '{current_id}'[/]")

        self.display.console.print(f"\n[dim]💬 Type '/help' for commands or start chatting![/]\n")

        while True:
            try:
                # Prepare prompt
                attach_pending = len(self.processor.pending_attachments)
                attach_hint = f" [bold magenta](+{attach_pending} files)[/]" if attach_pending else ""
                sid = self.processor.current_session_id
                
                # Input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.display.console.input(f"[bold green]You[/]{attach_hint} ([dim]{sid}[/]): ")
                )
                user_input = user_input.strip()

                if not user_input and not self.processor.pending_attachments:
                    continue

                # Handle Commands
                try:
                    if await self.processor.handle_command(user_input):
                        continue
                except SystemExit:
                    break

                # Regular Chat
                final_input = await asyncio.get_event_loop().run_in_executor(
                    None, build_user_message, user_input, self.processor.pending_attachments
                )
                
                # Clear attachments once used
                self.processor.pending_attachments = []

                # Chat
                await self.agent.chat(final_input, session_id=self.processor.current_session_id)
                
                # Auto-save
                self.processor._save_current()

            except KeyboardInterrupt:
                self.processor._save_current()
                print("\n\n💾 Session saved. Goodbye!\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
