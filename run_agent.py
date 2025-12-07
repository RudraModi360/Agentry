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
from scratchy import Agent, CopilotAgent
from scratchy.config.settings import get_api_key
from scratchy.session_manager import SessionManager
from scratchy.reloader import start_reloader

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

async def run_interactive_session(agent: Agent, session_manager: SessionManager, initial_session_id: str = "default"):
    """Runs an interactive chat loop with session management."""
    current_session_id = initial_session_id
    
    # Try to load existing session
    if session_manager.session_exists(current_session_id):
        print(f"📂 Resuming session: '{current_session_id}'")
        messages = session_manager.load_session(current_session_id)
        if messages:
            session = agent.get_session(current_session_id)
            session.messages = messages
            print(f"   Loaded {len(messages)} messages from history.")
    else:
        print(f"✨ Started new session: '{current_session_id}'")
    
    print(f"\n💬 Type '/help' for commands or start chatting!\n")
    
    while True:
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, f"[{current_session_id}] You: "
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
                    print("\n💾 Session saved. Goodbye!\n")
                    break
                
                elif command == '/help':
                    print(HELP_TEXT)
                    continue
                
                elif command in ['/status', '/info']:
                    try:
                        session = agent.get_session(current_session_id)
                        print(f"\n📊 Current Session Status:")
                        print(f"   Session ID: {current_session_id}")
                        print(f"   Messages: {len(session.messages)}")
                        print(f"   Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"   Last Activity: {session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"   Saved: {'Yes' if session_manager.session_exists(current_session_id) else 'No'}")
                        print()
                    except Exception as e:
                        print(f"❌ Error getting status: {e}")
                    continue
                
                elif command == '/tools':
                    await show_tools(agent)
                    continue
                
                elif command == '/sessions':
                    show_sessions(session_manager)
                    continue
                
                elif command == '/new':
                    if not args:
                        print("⚠️  Usage: /new <session_id>")
                        continue
                    
                    # Save current session
                    session = agent.get_session(current_session_id)
                    session_manager.save_session(current_session_id, session.messages)
                    
                    # Switch to new session
                    current_session_id = args
                    print(f"✨ Created new session: '{current_session_id}'")
                    continue
                
                elif command == '/resume':
                    if not args:
                        print("⚠️  Usage: /resume <session_id>")
                        continue
                    
                    if not session_manager.session_exists(args):
                        print(f"⚠️  Session '{args}' not found.")
                        continue
                    
                    # Save current session
                    session = agent.get_session(current_session_id)
                    session_manager.save_session(current_session_id, session.messages)
                    
                    # Load and switch to requested session
                    current_session_id = args
                    messages = session_manager.load_session(current_session_id)
                    session = agent.get_session(current_session_id)
                    session.messages = messages
                    print(f"📂 Resumed session: '{current_session_id}' ({len(messages)} messages)")
                    continue
                
                elif command == '/clear':
                    agent.clear_session(current_session_id)
                    print(f"🗑️  Cleared session: '{current_session_id}'")
                    continue
                
                else:
                    print(f"⚠️  Unknown command: {command}. Type '/help' for available commands.")
                    continue
            
            # Regular chat
            await agent.chat(user_input, session_id=current_session_id)
            
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
    
    print("="*60)
    print("🎨 Scratchy Agent Framework")
    print("="*60)
    
    # Initialize Session Manager
    session_manager = SessionManager()
    
    # Get API key if needed
    api_key = None
    if args.provider in ['groq', 'gemini']:
        api_key = get_api_key(args.provider) or input(f"Enter {args.provider.title()} API Key: ")
    
    # Initialize Agent
    if args.copilot:
        print("\n🚀 Initializing Copilot Agent (Coding Specialized)...")
        agent = CopilotAgent(
            llm=args.provider,
            model=args.model,
            api_key=api_key,
            debug=DEBUG_MODE
        )
    else:
        print("\n🤖 Initializing General Agent...")
        agent = Agent(
            llm=args.provider,
            model=args.model,
            api_key=api_key,
            debug=DEBUG_MODE
        )
        agent.load_default_tools()
    
    # Connect MCP Servers (Optional)
    if os.path.exists(MCP_CONFIG_PATH):
        print(f"🔌 Connecting to MCP servers from {MCP_CONFIG_PATH}...")
        try:
            await agent.add_mcp_server(MCP_CONFIG_PATH)
            print("✅ MCP servers connected.")
        except Exception as e:
            print(f"⚠️  Failed to connect MCP servers: {e}")
    
    # Setup Callbacks
    def on_tool_start(session, name, args):
        print(f"\n[{session}] 🔧 Executing: {name}")

    def on_tool_end(session, name, result):
        print(f"[{session}] ✅ Finished: {name}")

    def on_final_message(session, content):
        print(f"\n[{session}] 🤖 Assistant:\n{content}\n")

    async def on_tool_approval(session, name, args):
        print(f"\n⚠️  APPROVAL REQUIRED: Tool '{name}' is about to execute.")
        print(f"   Arguments: {json.dumps(args, indent=2)}")
        
        while True:
            # Use run_in_executor for blocking input
            response = await asyncio.get_event_loop().run_in_executor(
                None, input, "   [Y]es / [N]o / [E]dit arguments: "
            )
            choice = response.strip().lower()
            
            if choice in ['y', 'yes']:
                print("   ✅ Approved.")
                return True
            elif choice in ['n', 'no']:
                print("   ❌ Denied.")
                return False
            elif choice in ['e', 'edit']:
                # Special handling for run_command to make it easier
                if name == 'run_command' and 'CommandLine' in args:
                    print(f"   Current Command: {args['CommandLine']}")
                    new_cmd = await asyncio.get_event_loop().run_in_executor(
                        None, input, "   New Command > "
                    )
                    if new_cmd.strip():
                        args['CommandLine'] = new_cmd.strip()
                        print("   ✅ Command updated and approved.")
                        return args
                    else:
                        print("   ⚠️  Empty input. Keeping original.")
                        continue
                
                # Generic JSON edit
                print("   📝 Enter new arguments (JSON format):")
                try:
                    new_json_str = await asyncio.get_event_loop().run_in_executor(
                        None, input, "   JSON > "
                    )
                    new_args = json.loads(new_json_str)
                    print("   ✅ Arguments updated and approved.")
                    return new_args
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON. Please try again.")
                    continue
            else:
                print("   ⚠️  Invalid choice.")

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
