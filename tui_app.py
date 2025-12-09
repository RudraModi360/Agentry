from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Container, VerticalScroll
from textual.widgets import (
    Header, Footer, Input, Static, Button, Markdown, 
    Label, ListView, ListItem, Collapsible
)
from textual.screen import ModalScreen
from textual.binding import Binding
from textual import on, work
from textual.reactive import reactive
from rich.text import Text
from rich.align import Align
import asyncio
import os
import json
import base64
import mimetypes

from scratchy import Agent
from scratchy.session_manager import SessionManager

# --- Custom Widgets ---

class LiveToolCallWidget(Vertical):
    """A sophisticated live-updating tool call display that shows params and results in real-time."""
    
    DEFAULT_CSS = """
    LiveToolCallWidget {
        height: auto;
        margin: 1 2;
        background: #1a1a1a;
        border-left: solid #ff8800;
        padding: 1;
    }
    
    LiveToolCallWidget.-running {
        border-left: solid #ffcc00;
    }
    
    LiveToolCallWidget.-complete {
        border-left: solid #00ff88;
    }
    
    LiveToolCallWidget.-error {
        border-left: solid #ff4444;
    }
    
    LiveToolCallWidget .tool-header {
        color: #ff8800;
        text-style: bold;
    }
    
    LiveToolCallWidget .tool-status {
        color: #888;
        text-style: italic;
        margin-left: 2;
    }
    
    LiveToolCallWidget .tool-params {
        background: #111;
        color: #aaa;
        padding: 1;
        margin: 1 0;
        height: auto;
        max-height: 10;
        overflow-y: scroll;
    }
    
    LiveToolCallWidget .tool-result {
        background: #0a1a0a;
        color: #88dd88;
        padding: 1;
        margin-top: 1;
        height: auto;
        max-height: 15;
        overflow-y: scroll;
    }
    
    LiveToolCallWidget .tool-error {
        background: #1a0a0a;
        color: #ff8888;
        padding: 1;
        margin-top: 1;
    }
    
    LiveToolCallWidget .param-key {
        color: #88aaff;
    }
    
    LiveToolCallWidget .param-value {
        color: #cccccc;
    }
    """
    
    def __init__(self, tool_name: str, args: dict = None):
        super().__init__()
        self.tool_name = tool_name
        self.tool_args = args or {}
        self.tool_result = None
        self.is_complete = False
        self.has_error = False
        self.add_class("-running")
        
    def compose(self) -> ComposeResult:
        # Header with tool name
        yield Static(f"🔧 {self.tool_name}", classes="tool-header", id="header")
        yield Static("⏳ Running...", classes="tool-status", id="status")
        
        # Parameters section
        if self.tool_args:
            params_text = self._format_params(self.tool_args)
            yield Static(params_text, classes="tool-params", id="params")
        
        # Result placeholder (will be updated)
        yield Static("", classes="tool-result", id="result")
    
    def _format_params(self, args: dict) -> str:
        """Format parameters for display."""
        lines = ["📥 Parameters:"]
        for key, value in args.items():
            # Truncate long values
            val_str = str(value)
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            lines.append(f"  • {key}: {val_str}")
        return "\n".join(lines)
    
    def set_result(self, result: str):
        """Update the widget with the tool result."""
        self.tool_result = result
        self.is_complete = True
        self.remove_class("-running")
        self.add_class("-complete")
        
        # Update header
        try:
            self.query_one("#header", Static).update(f"✅ {self.tool_name}")
            self.query_one("#status", Static).update("Complete")
        except: pass
        
        # Update result
        try:
            # If we have a result widget, replace it or update it
            try:
                self.query_one("#result").remove()
            except: pass
            
            # Format result
            result_str = str(result)
            
            # For web searches or long text, use Markdown to support links/formatting
            if self.tool_name == "web_search" or len(result_str) > 50:
                 self.mount(Markdown(result_str, classes="tool-result"))
            else:
                 self.mount(Static(f"📤 Result:\n{result_str}", classes="tool-result"))
                 
        except Exception as e:
            self.mount(Static(f"Error displaying result: {e}", classes="tool-error"))
    
    def set_error(self, error: str):
        """Update the widget with an error."""
        self.has_error = True
        self.is_complete = True
        self.remove_class("-running")
        self.add_class("-error")
        
        try:
            self.query_one("#header", Static).update(f"❌ {self.tool_name}")
            self.query_one("#status", Static).update("Failed")
        except: pass
        
        try:
            # Try to update existing result widget, or mount new one
            try:
                self.query_one("#result").remove()
            except: pass
            
            self.mount(Static(f"⚠️ Error: {error}", classes="tool-error"))
        except Exception as e:
            self.mount(Static(f"⚠️ Error (and display error): {error} / {e}", classes="tool-error"))
    
    def _format_web_search_result(self, result: str) -> str:
        """Format web search results nicely."""
        lines = ["🌐 Web Search Results:"]
        lines.append("─" * 40)
        
        # Try to parse and format the results
        result_str = str(result)
        
        # If it looks like search snippets, format them
        if "..." in result_str or "http" in result_str.lower():
            # Split by common separators
            chunks = result_str.split("\n")
            for chunk in chunks[:10]:  # Limit to 10 results
                chunk = chunk.strip()
                if chunk:
                    lines.append(f"• {chunk[:200]}")
        else:
            lines.append(result_str[:1500])
        
        return "\n".join(lines)


# Legacy alias for compatibility
ToolCallWidget = LiveToolCallWidget


class LoadingSpinner(Static):
    """Animated loading indicator."""
    
    DEFAULT_CSS = """
    LoadingSpinner {
        color: #ff8800;
        text-align: center;
        height: auto;
        margin: 1 0;
    }
    """
    
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    frame_index = 0
    
    def __init__(self, message: str = "Thinking"):
        super().__init__()
        self.message = message
        self._timer = None
        
    def on_mount(self):
        self._timer = self.set_interval(0.1, self.animate)
        self.update(f"{self.frames[0]} {self.message}...")
        
    def animate(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.update(f"{self.frames[self.frame_index]} {self.message}...")
        
    def stop(self):
        if self._timer:
            self._timer.stop()

# --- Screens ---

class ToolApprovalScreen(ModalScreen[bool]):
    CSS = """
    ToolApprovalScreen {
        align: center middle;
        background: rgba(0,0,0,0.8);
    }
    #approval-dialog {
        width: 60;
        height: auto;
        border: solid #ff5555;
        background: #1e1e1e;
        padding: 2;
    }
    .args-box {
        border: solid #444;
        background: #111;
        height: auto;
        max-height: 15;
        overflow-y: scroll;
        margin: 1 0;
        padding: 1;
        color: #aaa;
    }
    #approval-buttons {
        align: center bottom;
        margin-top: 2;
        height: 3;
    }
    Button { width: 1fr; margin: 0 1; }
    """
    def __init__(self, tool_name: str, args: dict):
        super().__init__()
        self.tool_name = tool_name
        self.args = args

    def compose(self) -> ComposeResult:
        with Container(id="approval-dialog"):
            yield Label(f"EXECUTE: {self.tool_name}", classes="header-alert")
            with Container(classes="args-box"):
                yield Static(json.dumps(self.args, indent=2))
            with Horizontal(id="approval-buttons"):
                yield Button("CONFIRM", variant="success", id="yes")
                yield Button("DENY", variant="error", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


# --- Main App ---

class OpenCodeZen(App):
    """
    Minimalist, Keyboard-First Agent Interface inspired by OpenCode.
    Focus: Speed, Clarity, Aesthetics.
    """
    
    CSS = """
    /* --- THEME: Zen Dark --- */
    $bg: #0d0d0d;
    $fg: #e0e0e0;
    $accent: #ff8800; /* Orange/Amber accent */
    $accent-dim: #995500;
    $surface: #1a1a1a;
    $muted: #666666;

    Screen {
        background: $bg;
        color: $fg;
        align: center middle;
    }

    /* --- HERO SPLASH --- */
    #hero-container {
        width: 100%;
        height: 1fr;
        align: center middle;
        content-align: center middle;
        padding-bottom: 4;
    }
    
    .hero-title {
        text-style: bold;
        color: white;
        text-align: center;
        width: 100%;
    }
    
    .hero-subtitle {
        color: $muted;
        text-align: center;
        margin-bottom: 2;
        width: 100%;
    }
    
    .shortcut-list {
        color: $accent;
        text-align: center;
        width: 100%;
        margin-bottom: 4;
    }
    
    .hero-promo {
        color: #a0a0ff;
        text-align: center;
        width: 100%;
    }

    /* --- CHAT VIEW --- */
    #chat-scroll {
        width: 100%;
        height: 1fr;
        padding: 1 4;
        display: none; /* Hidden on start until active */
        scrollbar-gutter: stable;
    }
    
    /* Session Header */
    .session-header {
        color: #ff5555;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .session-hint {
        color: #666;
        text-style: italic;
        margin-bottom: 2;
    }
    
    /* Messages - OpenCode Style */
    .msg-container {
        margin: 1 0;
        padding: 0;
        height: auto;
    }
    
    .msg-meta {
        color: #888;
        text-style: bold;
        margin-bottom: 0;
        height: auto;
    }
    
    .msg-meta-user {
        color: #aaa;
    }
    
    .msg-meta-agent {
        color: #44aa44;
    }
    
    .msg-content {
        color: #ddd;
        padding-left: 2;
        margin-top: 0;
        height: auto;
    }
    
    .msg-user {
        background: transparent;
        color: white;
        padding: 0;
        margin: 1 0;
        height: auto;
    }
    
    .msg-agent {
        background: transparent;
        color: #ddd;
        padding: 0;
        margin: 1 0;
        height: auto;
    }
    
    .msg-tool {
        color: $muted;
        text-style: italic;
        padding: 0 4;
    }
    
    .msg-sys {
        color: #ff5555;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: #000;
        color: $muted;
        padding: 0 2;
    }
    
    .status-left {
        margin-right: 2;
    }
    
    .status-right {
        dock: right;
        color: $accent;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+n", "new_session", "New"),
        Binding("ctrl+h", "show_help", "Help"),
        Binding("ctrl+l", "clear_chat", "Clear"),
    ]

    session_id = reactive("default")
    is_chat_active = reactive(False)
    
    def __init__(self, provider="ollama", model=None, api_key=None):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.agent = None
        self.session_manager = SessionManager()
        self.streaming_widget = None  # Track the live streaming response widget
        self.streaming_content = ""   # Buffer for streaming content
        self.streaming_container = None  # Container for streaming message

    def compose(self) -> ComposeResult:
        # Hero / Start Screen
        with Vertical(id="hero-container"):
            yield Static("SCRATCHY", classes="hero-title")
            yield Static("v0.1.0", classes="hero-subtitle")
            
            help_text = """
            /new      new session     ctrl+n
            /help     show help       ctrl+h
            /clear    clear chat      ctrl+l
            /models   list models     ctrl+m
            """
            yield Static(help_text, classes="shortcut-list")
            
            yield Static("Powered by Local LLMs & MCP Tools", classes="hero-promo")

        # Active Chat View (starts hidden)
        yield VerticalScroll(id="chat-scroll")

        # Zen Input
        with Horizontal(id="input-container"):
            yield Static(">", classes="input-prompt")
            yield Input(placeholder="", id="zen-input")
        
        # Status footer - OpenCode style
        with Horizontal(id="status-bar"):
            yield Static("enter send", classes="status-left")
            model_name = self.model or "default"
            yield Static(f"Scratchy Zen {self.provider} {model_name}", classes="status-right")

    async def on_mount(self):
        # Big specific font for title if we could, but standard text for now
        # Initialize backend
        await self.init_agent()
        self.query_one("#zen-input").focus()

    async def init_agent(self):
        try:
            self.agent = Agent(
                llm=self.provider, 
                model=self.model, 
                api_key=self.api_key,
                debug=False
            )
            self.agent.load_default_tools()
            self.agent.set_callbacks(
                on_tool_start=self.on_tool_start,
                on_tool_end=self.on_tool_end,
                on_tool_approval=self.on_tool_approval,
                on_final_message=self.on_final_message,
                on_token=self.on_token  # Streaming callback
            )
            # Connect MCP
            if os.path.exists("mcp.json"):
                await self.agent.add_mcp_server("mcp.json")
        except: pass

    # --- Actions ---

    def action_new_session(self):
        # In this Zen mode, /new clears history and generates a UUID
        import uuid
        from datetime import datetime
        self.session_id = str(uuid.uuid4())[:8]
        self.session_start = datetime.now()
        self.query_one("#chat-scroll").remove_children()
        self.is_chat_active = False
        self.update_view_mode()
        self.notify(f"New Session: {self.session_id}")

    def action_clear_chat(self):
        self.query_one("#chat-scroll").remove_children()
        self.agent.clear_session(self.session_id)
        self.is_chat_active = False
        self.update_view_mode()

    def update_view_mode(self):
        hero = self.query_one("#hero-container")
        chat = self.query_one("#chat-scroll")
        
        if self.is_chat_active:
            hero.styles.display = "none"
            chat.styles.display = "block"
        else:
            hero.styles.display = "flex"
            chat.styles.display = "none"
    
    def add_session_header(self):
        """Add session header at the top of chat like OpenCode."""
        from datetime import datetime
        scroll = self.query_one("#chat-scroll")
        
        # Get session timestamp
        session_time = getattr(self, 'session_start', datetime.now())
        timestamp = session_time.isoformat()
        
        # Add header
        header = Static(f"# New session - {timestamp}", classes="session-header")
        hint = Static("/share to create a shareable link", classes="session-hint")
        
        scroll.mount(header)
        scroll.mount(hint)

    def show_help(self):
        """Show help information in the chat."""
        self.is_chat_active = True
        self.update_view_mode()
        
        help_text = """## 🤖 Scratchy Agent - Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/new` | Start a new session | `Ctrl+N` |
| `/help` | Show this help | `Ctrl+H` |
| `/clear` | Clear chat history | `Ctrl+L` |
| `/models` | List available models | - |
| `/search <query>` | Quick web search (snippets) | - |
| `/deepsearch <query>` | Deep research with AI analysis | - |
| `/open <url>` | Open URL in browser | - |
| `/quit` | Exit application | `Ctrl+C` |

### Features
- **Streaming Output**: Responses appear token-by-token
- **Tool Calls**: Live display with params and results
- **Web Search**: Use `/search` for quick lookups

### Tips
- Type naturally to chat with the agent
- The agent can use tools to help you
"""
        self.add_msg(help_text, "agent")

    def show_models(self):
        """Show available models."""
        self.is_chat_active = True
        self.update_view_mode()
        
        # Try to get models from Ollama
        try:
            import ollama
            client = ollama.Client()
            models_list = client.list()
            
            model_names = [m['name'] for m in models_list.get('models', [])]
            
            if model_names:
                text = "## Available Ollama Models\n\n"
                for name in model_names:
                    text += f"- `{name}`\n"
                text += f"\n**Current**: `{self.model or 'default'}`"
            else:
                text = "No models found. Run `ollama pull <model>` to download one."
                
            self.add_msg(text, "agent")
        except Exception as e:
            self.add_msg(f"Error fetching models: {e}", "sys")

    async def do_web_search(self, query: str, search_type: str = 'quick'):
        """Perform a direct web search without going through the agent."""
        import time
        self.is_chat_active = True
        self.update_view_mode()
        
        # Show search indicator with mode
        mode_label = "Deep Research" if search_type == 'deep' else "Quick Search"
        scroll = self.query_one("#chat-scroll")
        widget = LiveToolCallWidget("web_search", {"query": query, "mode": mode_label})
        widget.id = f"search-{int(time.time() * 1000)}"  # Unique ID
        scroll.mount(widget)
        scroll.scroll_end(animate=False)
        
        # Run the search in background thread
        import asyncio
        loop = asyncio.get_event_loop()
        
        def run_search():
            from scratchy.tools.web import WebSearchTool
            tool = WebSearchTool()
            result = tool.run(user_input=query, search_type=search_type)
            return result
        
        try:
            result = await loop.run_in_executor(None, run_search)
            
            # Update the widget (ToolResult is a dict)
            if result.get('success'):
                widget.set_result(result.get('content', ''))
            else:
                widget.set_error(result.get('error', 'Unknown error'))
        except Exception as e:
            widget.set_error(str(e))

    # --- Input Handling ---

    async def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if not text: return
        event.input.value = ""
        
        # Slash Commands
        if text.startswith('/'):
            cmd = text.split()[0]
            if cmd == '/new': 
                self.action_new_session()
            elif cmd == '/quit': 
                self.exit()
            elif cmd == '/clear': 
                self.action_clear_chat()
            elif cmd == '/help':
                self.show_help()
            elif cmd == '/models':
                self.show_models()
            elif cmd == '/search':
                # Quick web search (snippets only)
                query = text[len('/search'):].strip()
                if query:
                    await self.do_web_search(query, 'quick')
                else:
                    self.add_msg("Usage: /search <your query>", "sys")
            elif cmd == '/deepsearch':
                # Deep research with LLM analysis
                query = text[len('/deepsearch'):].strip()
                if query:
                    await self.do_web_search(query, 'deep')
                else:
                    self.add_msg("Usage: /deepsearch <your query>", "sys")
            elif cmd == '/open':
                # Open URL in default browser
                url = text[len('/open'):].strip()
                if url:
                    import webbrowser
                    webbrowser.open(url)
                    self.is_chat_active = True
                    self.update_view_mode()
                    self.add_msg(f"🌐 Opening: {url}", "sys")
                else:
                    self.add_msg("Usage: /open <url>", "sys")
            else:
                # Unknown command - show error in chat
                self.is_chat_active = True
                self.update_view_mode()
                self.add_msg(f"Unknown command: {cmd}\nType /help for available commands.", "sys")
            return
            
        # Switch to chat mode if not already
        if not self.is_chat_active:
            from datetime import datetime
            self.session_start = datetime.now()
            self.is_chat_active = True
            self.update_view_mode()
            self.add_session_header()  # Add OpenCode-style header
            
        # Add User Message
        self.add_msg(text, "user")
        
        # Add Animated Spinner
        scroll = self.query_one("#chat-scroll")
        spinner = LoadingSpinner("Thinking")
        spinner.id = "loading-spinner"
        scroll.mount(spinner)
        scroll.scroll_end(animate=False)
        
        # Run Agent as async task
        asyncio.create_task(self.run_agent(text))

    async def run_agent(self, text):
        """Run agent asynchronously."""
        try:
            await self.agent.chat(text, session_id=self.session_id)
        except Exception as e:
            self.add_msg(f"Error: {e}", "sys")
        finally:
            # Remove spinner when done
            try:
                spinner = self.query_one("#loading-spinner")
                spinner.stop()
                spinner.remove()
            except: pass

    # --- Callbacks ---
    
    def on_tool_start(self, session, name, args):
        """Called when a tool starts - shows live widget with params."""
        import time
        scroll = self.query_one("#chat-scroll")
        
        # Create a new live tool widget with unique ID
        widget = LiveToolCallWidget(name, args)
        # Use timestamp for truly unique ID
        unique_id = f"tool-{name}-{int(time.time() * 1000)}"
        widget.id = unique_id
        
        # Store the mapping for on_tool_end to find it
        if not hasattr(self, '_active_tools'):
            self._active_tools = {}
        self._active_tools[name] = unique_id
        
        scroll.mount(widget)
        scroll.scroll_end(animate=False)

    def on_tool_end(self, session, name, result):
        """Called when a tool completes - updates the live widget with result."""
        try:
            # Find the active widget using stored ID
            if hasattr(self, '_active_tools') and name in self._active_tools:
                widget_id = self._active_tools[name]
                widget = self.query_one(f"#{widget_id}", LiveToolCallWidget)
                widget.set_result(result)
                # Remove from active tools
                del self._active_tools[name]
            else:
                raise Exception("Widget not found")
        except Exception as e:
            # If widget not found, just add the result as new
            scroll = self.query_one("#chat-scroll")
            widget = LiveToolCallWidget(name, {})
            widget.set_result(result)
            scroll.mount(widget)
        
        scroll = self.query_one("#chat-scroll")
        scroll.scroll_end(animate=False)

    async def on_tool_approval(self, session, name, args):
        """Auto-approve all tools (modal has threading issues)."""
        # TODO: Fix push_screen_wait threading issue
        # For now, auto-approve all tools
        return True

    def on_token(self, token: str):
        """Called for each streaming token from the LLM (from a background thread)."""
        # Use call_from_thread since this is called from run_in_executor
        self.call_from_thread(self._handle_token, token)
    
    def _handle_token(self, token: str):
        """Actually update the UI with the token (main thread)."""
        from datetime import datetime
        scroll = self.query_one("#chat-scroll")
        
        # Create streaming widget on first token
        if self.streaming_widget is None:
            self.streaming_content = ""
            # Create a container with model name header
            model_name = self.model or "scratchy"
            time_str = datetime.now().strftime("%I:%M %p")
            
            self.streaming_container = Vertical(classes="msg-agent")
            self.streaming_header = Static(f"{model_name} ({time_str})", classes="msg-meta msg-meta-agent")
            self.streaming_widget = Static("", classes="msg-content")
            
            scroll.mount(self.streaming_container)
            self.streaming_container.mount(self.streaming_header)
            self.streaming_container.mount(self.streaming_widget)
        
        # Append token to buffer
        self.streaming_content += token
        
        # Update the widget content
        self.streaming_widget.update(self.streaming_content)
        scroll.scroll_end(animate=False)

    def on_final_message(self, session, content):
        """Called when the full response is complete."""
        scroll = self.query_one("#chat-scroll")
        
        # Use streaming content as fallback if content is empty
        final_content = content
        if not final_content or not final_content.strip():
            final_content = self.streaming_content
        
        # If we were streaming, replace Static with Markdown for proper rendering
        if self.streaming_widget is not None and self.streaming_container is not None:
            try:
                # Remove the Static streaming widget
                self.streaming_widget.remove()
                # Add a Markdown widget in its place
                md_widget = Markdown(final_content, classes="msg-content")
                self.streaming_container.mount(md_widget)
            except Exception as e:
                # Fallback: just update the static widget
                try:
                    self.streaming_widget.update(final_content)
                except: pass
            
            self.streaming_widget = None
            self.streaming_content = ""
            self.streaming_container = None
        else:
            # No streaming happened, add message normally
            if final_content and final_content.strip():
                self.add_msg(final_content, "agent")
        
        scroll.scroll_end(animate=False)

    # --- Rendering ---

    def add_msg(self, content: str, role: str):
        from datetime import datetime
        scroll = self.query_one("#chat-scroll")
        
        # Get current time
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")  # e.g., "07:24 AM"
        
        if role == "user":
            # User message with name and timestamp
            container = Vertical(classes="msg-user")
            scroll.mount(container)  # Mount container FIRST
            container.mount(Static(f"rudra ({time_str})", classes="msg-meta msg-meta-user"))
            container.mount(Static(content, classes="msg-content"))
        elif role == "agent":
            # Agent message with model name and timestamp
            model_name = self.model or "scratchy"
            container = Vertical(classes="msg-agent")
            scroll.mount(container)  # Mount container FIRST
            container.mount(Static(f"{model_name} ({time_str})", classes="msg-meta msg-meta-agent"))
            container.mount(Markdown(content, classes="msg-content"))
        elif role == "tool":
            scroll.mount(Static(content, classes="msg-tool"))
        elif role == "sys":
            scroll.mount(Static(content, classes="msg-sys"))
        else:
            scroll.mount(Static(content, classes="msg-tool"))  # Fallback
        
        scroll.scroll_end(animate=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", "-p", default="ollama")
    parser.add_argument("--model", "-m", default=None)
    parser.add_argument("--api-key", "-k", default=None)
    args = parser.parse_args()

    # ASCII Art Title for Hero
    print("Starting Scratchy TUI...")
    app = OpenCodeZen(args.provider, args.model, args.api_key)
    app.run()
