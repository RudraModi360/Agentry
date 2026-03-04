"""
WebSocket Chat Handler v2
=========================
Improved WebSocket handler with session isolation.

Key improvements:
- Session-isolated streaming (page reload doesn't interrupt)
- Multiple sessions can stream simultaneously
- Proper cleanup on disconnect
- Connection tracking per user
"""

import os
import json
import asyncio
import sqlite3
import base64
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from weakref import WeakSet

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.config import DB_PATH, UI_DIR
from backend.core.dependencies import get_user_from_token
from backend.services.auth_service import AuthService
from backend.services.agent_cache import agent_cache
from backend.services.streaming_manager import get_streaming_manager, ActiveStream
from backend.services.simplemem_middleware import (
    get_simplemem_context,
    store_response_in_simplemem,
    is_simplemem_enabled
)

from logicore import Agent
from logicore.agents import SmartAgent, SmartAgentMode
from logicore.agents.agent_cloud import CloudAgent, create_cloud_agent
from logicore.session_manager import SessionManager
from logicore.providers.ollama_provider import OllamaProvider
from logicore.providers.groq_provider import GroqProvider
from logicore.providers.gemini_provider import GeminiProvider
from logicore.providers.azure_provider import AzureProvider
from logicore.providers.capability_detector import detect_model_capabilities

from backend.core.deployment import get_deployment_config, is_cloud_mode

router = APIRouter()


# ============================================================
# Connection Manager for tracking active WebSocket connections
# ============================================================
class ConnectionManager:
    """Manages WebSocket connections per user."""
    
    def __init__(self):
        # Map: user_id -> set of (connection_id, websocket)
        self.user_connections: Dict[int, Dict[str, WebSocket]] = {}
        # Map: connection_id -> (user_id, current_session_id)
        self.connection_state: Dict[str, tuple] = {}
    
    def add_connection(self, user_id: int, websocket: WebSocket) -> str:
        """Add a new connection and return its unique ID."""
        connection_id = str(uuid.uuid4())[:8]
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = {}
        
        self.user_connections[user_id][connection_id] = websocket
        self.connection_state[connection_id] = (user_id, None)
        
        print(f"[ConnMgr] Added connection {connection_id} for user {user_id}")
        return connection_id
    
    def remove_connection(self, connection_id: str):
        """Remove a connection."""
        if connection_id in self.connection_state:
            user_id, _ = self.connection_state[connection_id]
            
            if user_id in self.user_connections:
                self.user_connections[user_id].pop(connection_id, None)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            del self.connection_state[connection_id]
            print(f"[ConnMgr] Removed connection {connection_id}")
    
    def set_session(self, connection_id: str, session_id: str):
        """Update the current session for a connection."""
        if connection_id in self.connection_state:
            user_id, _ = self.connection_state[connection_id]
            self.connection_state[connection_id] = (user_id, session_id)
    
    def get_websocket(self, connection_id: str) -> Optional[WebSocket]:
        """Get websocket by connection ID."""
        if connection_id in self.connection_state:
            user_id, _ = self.connection_state[connection_id]
            return self.user_connections.get(user_id, {}).get(connection_id)
        return None
    
    async def broadcast_to_user(self, user_id: int, message: dict, exclude_connection: str = None):
        """Broadcast a message to all connections for a user."""
        connections = self.user_connections.get(user_id, {})
        for conn_id, websocket in connections.items():
            if conn_id != exclude_connection:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass


# Global connection manager
connection_manager = ConnectionManager()


# ============================================================
# Helper Functions
# ============================================================

def format_multimodal_content_multi(text: str, images_data: List[str]) -> list:
    """Format text and multiple images into multimodal content for vision models."""
    content = []
    if text:
        content.append({"type": "text", "text": text})
    for img_data in images_data:
        content.append({"type": "image", "data": img_data})
    return content


def sanitize_session_messages(messages: List[Dict]) -> List[Dict]:
    """
    Sanitize session messages to fix broken tool_calls chains.
    
    The OpenAI API requires that every assistant message with tool_calls
    must be followed by tool messages responding to each tool_call_id.
    
    This function removes incomplete tool_call chains to prevent API errors.
    """
    if not messages:
        return messages
    
    sanitized = []
    i = 0
    
    while i < len(messages):
        msg = messages[i]
        role = msg.get('role', '')
        
        if role == 'assistant' and msg.get('tool_calls'):
            # This assistant message has tool_calls
            # We need to verify all tool_calls have corresponding tool responses
            tool_calls = msg.get('tool_calls', [])
            tool_call_ids = set()
            
            for tc in tool_calls:
                tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                if tc_id:
                    tool_call_ids.add(tc_id)
            
            # Look ahead for tool responses
            found_tool_ids = set()
            j = i + 1
            tool_messages = []
            
            while j < len(messages):
                next_msg = messages[j]
                next_role = next_msg.get('role', '')
                
                if next_role == 'tool':
                    tool_call_id = next_msg.get('tool_call_id')
                    if tool_call_id:
                        found_tool_ids.add(tool_call_id)
                    tool_messages.append(next_msg)
                    j += 1
                elif next_role in ['user', 'assistant']:
                    # Hit next user/assistant message, stop looking
                    break
                else:
                    j += 1
            
            # Check if all tool_calls have responses
            missing_ids = tool_call_ids - found_tool_ids
            
            if missing_ids:
                # Incomplete tool chain - skip this assistant message and its tools
                print(f"[Sanitize] Removing incomplete tool chain with missing IDs: {missing_ids}")
                i = j  # Skip past the tool messages
                continue
            else:
                # Complete chain - add assistant and all tool messages
                sanitized.append(msg)
                sanitized.extend(tool_messages)
                i = j
        else:
            # Regular message (user, system, or assistant without tool_calls)
            sanitized.append(msg)
            i += 1
    
    return sanitized


def save_media_to_disk(user_id: int, image_data: str, filename: str = None) -> dict:
    """Saves base64 image data to the local media directory."""
    ext = "png"
    mime_type = "image/png"
    
    raw_data = image_data
    if image_data.startswith('data:'):
        try:
            header, data = image_data.split(',', 1)
            mime_type = header.split(':', 1)[1].split(';', 1)[0]
            ext = mime_type.split('/', 1)[1]
            raw_data = data
        except:
            pass

    if not filename:
        timestamp = int(time.time() * 1000)
        filename = f"media_{user_id}_{timestamp}.{ext}"
    
    filepath = os.path.join(UI_DIR, "media", filename)
    
    try:
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(raw_data))
    except Exception as e:
        print(f"[Server] Error saving media to disk: {e}")
        return None
    
    media_id = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_media (user_id, filename, filepath, content_type)
            VALUES (?, ?, ?, ?)
        """, (user_id, filename, f"/media/{filename}", mime_type))
        media_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Server] Error saving media record to DB: {e}")
    
    return {
        "id": media_id,
        "filename": filename,
        "url": f"/media/{filename}",
        "mime_type": mime_type,
        "created_at": datetime.now().isoformat()
    }


async def resolve_media_inline(
    query: str, 
    media_type: str, 
    placeholder: str, 
    websocket: WebSocket, 
    session_id: str = None, 
    session_manager: SessionManager = None, 
    active_stream: ActiveStream = None
):
    """Background task to resolve inline media search request."""
    from backend.services.media_orchestrator import media_orchestrator
    try:
        results = await media_orchestrator.search_media(query, [media_type])
        
        formatted_results = []
        for r in results:
            if r.get("type") == media_type:
                formatted_results.append({
                    "url": r.get("url") or r.get("thumbnail"),
                    "title": r.get("title", "Media"),
                    "source": r.get("source") or r.get("channel") or "Source",
                    "thumbnail": r.get("thumbnail"),
                    "link": r.get("url")
                })
            if len(formatted_results) >= 4:
                break
        
        # Update stream state
        if active_stream is not None:
            active_stream.media_state["data"][placeholder] = formatted_results
            
            # Patch DB if already committed
            if active_stream.media_state.get("committed") and session_id and session_manager:
                messages = session_manager.load_session(session_id)
                if messages:
                    for i in range(len(messages) - 1, -1, -1):
                        msg = messages[i]
                        if msg.get("role") == "assistant":
                            content = msg.get("content", "")
                            if isinstance(content, str) and placeholder in content:
                                if "media" not in msg:
                                    msg["media"] = {}
                                msg["media"][placeholder] = formatted_results
                                session_manager.save_session(session_id, messages)
                                break

        if websocket:
            await websocket.send_json({
                "type": "media_resolved",
                "query": query,
                "media_type": media_type,
                "placeholder": placeholder,
                "results": formatted_results
            })
    except Exception as e:
        print(f"[Server] Media resolution failed for '{query}': {e}")
        if websocket:
            await websocket.send_json({
                "type": "media_resolved",
                "query": query,
                "media_type": media_type,
                "placeholder": placeholder,
                "results": [],
                "error": str(e)
            })


async def generate_title(
    session_id: str, 
    messages: list, 
    provider, 
    session_manager: SessionManager, 
    websocket: WebSocket = None
):
    """Generate and save session title."""
    try:
        first_user_msg = None
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            first_user_msg = part.get("text", "")
                            break
                else:
                    first_user_msg = content
                break
        
        if not first_user_msg or len(first_user_msg) < 3:
            return
        
        prompt = f'Create a 3-5 word title summarizing this conversation starter. Return ONLY the title, no quotes:\n\n"{first_user_msg[:200]}"'
        messages_for_title = [{"role": "user", "content": prompt}]
        response = await provider.chat(messages_for_title)
        
        if isinstance(response, dict):
            title = response.get("content", "")
        elif hasattr(response, "content"):
            title = response.content or ""
        else:
            title = str(response)

        title = title.strip().strip('"\'').strip()[:50]
        
        if title and len(title) > 2:
            session_manager.storage.update_session_metadata(session_id, {"title": title})
            
            if websocket:
                try:
                    await websocket.send_json({
                        "type": "title_generated",
                        "session_id": session_id,
                        "title": title
                    })
                except:
                    pass
    except Exception as e:
        print(f"[Server] Title generation failed: {e}")


# ============================================================
# Main WebSocket Endpoint
# ============================================================

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    user = None
    agent = None
    connection_id = None
    
    try:
        # Authentication
        auth_data = await websocket.receive_json()
        token = auth_data.get("token")
        
        if not token:
            await websocket.send_json({"type": "error", "message": "Token required"})
            await websocket.close()
            return
        
        user = get_user_from_token(token)
        if not user:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close()
            return
        
        user_id = user["id"]
        connection_id = connection_manager.add_connection(user_id, websocket)
        
        # Initialize or get agent
        agent = await initialize_agent(user_id, websocket)
        if not agent:
            return
        
        # Send connected message
        cached_capabilities = agent_cache.get(user_id, {}).get("capabilities", {})
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Agentry",
            "capabilities": cached_capabilities,
            "connection_id": connection_id
        })
        
        session_manager = SessionManager()
        streaming_manager = get_streaming_manager()
        
        # Main message loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "message":
                await handle_chat_message(
                    data, websocket, user_id, agent, 
                    session_manager, streaming_manager, connection_id
                )
            
            elif msg_type == "load_session":
                session_id = data.get("session_id")
                connection_manager.set_session(connection_id, session_id)
                messages = session_manager.load_session(session_id)
                
                # Sanitize messages to fix broken tool_calls chains
                if messages:
                    messages = sanitize_session_messages(messages)
                
                # Refresh the system message date when loading session from history
                # This ensures the AI has the current date, not the stale date from session creation
                if agent and hasattr(agent, 'refresh_system_message_date'):
                    agent.refresh_system_message_date(session_id)
                
                # Check if session has an active stream
                is_streaming = await streaming_manager.is_streaming(session_id)
                
                await websocket.send_json({
                    "type": "session_loaded",
                    "session_id": session_id,
                    "messages": messages or [],
                    "is_streaming": is_streaming
                })
            
            elif msg_type == "delete_message":
                await handle_delete_message(
                    data, websocket, user_id, agent, session_manager
                )
            
            elif msg_type == "cancel_stream":
                session_id = data.get("session_id")
                if session_id:
                    await streaming_manager.cancel_stream(session_id)
                    await websocket.send_json({
                        "type": "stream_cancelled",
                        "session_id": session_id
                    })
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"[WS] Client disconnected: {user['username'] if user else 'unknown'}")
    except Exception as e:
        print(f"[WS] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection_id:
            connection_manager.remove_connection(connection_id)


async def initialize_agent(user_id: int, websocket: WebSocket):
    """Initialize or get cached agent for user."""
    # Check if running in cloud mode
    deployment_config = get_deployment_config()
    use_cloud_agent = deployment_config.is_cloud()
    
    if user_id in agent_cache:
        cached = agent_cache[user_id]
        
        if cached.get("needs_init"):
            # Lazy initialization
            provider = cached["provider"]
            config = cached["config"]
            capabilities_dict = cached["capabilities"]
            
            from logicore.providers.capability_detector import ModelCapabilities
            capabilities = ModelCapabilities.from_dict(capabilities_dict)
            
            # Cloud mode: Always use CloudAgent
            if use_cloud_agent:
                api_key = AuthService.get_api_key(user_id, config["provider"])
                agent = CloudAgent(
                    llm=config["provider"],
                    model=config["model"],
                    api_key=api_key,
                    user_id=str(user_id),
                    debug=True,
                    capabilities=capabilities
                )
                await agent.initialize_mcp()
                current_agent_type = "cloud"
            else:
                # Local mode: Use appropriate agent type
                agent_type_config = get_agent_type_config(user_id)
                disabled_tools_list = get_disabled_tools(user_id)
                
                if agent_type_config and agent_type_config.get("agent_type") == "smart":
                    mode = agent_type_config.get("mode") or SmartAgentMode.SOLO
                    project_id = agent_type_config.get("project_id")
                    agent = SmartAgent(
                        llm=provider, mode=mode, project_id=project_id,
                        debug=True, capabilities=capabilities
                    )
                    current_agent_type = "smart"
                else:
                    current_agent_type = agent_type_config.get("agent_type") if agent_type_config else "default"
                    tools_enabled = config.get("tools_enabled", True)
                    
                    if current_agent_type == "default" and tools_enabled:
                        capabilities.supports_tools = True

                    agent = Agent(llm=provider, debug=True, capabilities=capabilities)
                    
                    if disabled_tools_list:
                        agent.disabled_tools = set(disabled_tools_list)
                    
                    if tools_enabled and capabilities.supports_tools:
                        agent.load_default_tools()
                        await load_mcp_config(agent, user_id, current_agent_type or "default")
            
            agent_cache[user_id] = {
                "agent": agent,
                "config": config,
                "provider": provider,
                "capabilities": capabilities_dict,
                "needs_init": False,
                "agent_type": current_agent_type
            }
        else:
            agent = cached["agent"]
            if not use_cloud_agent:
                refresh_disabled_tools(agent, user_id)
        
        return agent
    else:
        # Full initialization
        config = AuthService.get_current_active_settings(user_id)
        if not config:
            await websocket.send_json({
                "type": "error",
                "message": "Provider not configured. Please complete setup."
            })
            await websocket.close()
            return None
        
        try:
            provider = await create_provider(user_id, config)
            capabilities = await detect_model_capabilities(
                provider_name=config["provider"],
                model_name=config["model"],
                provider_instance=provider
            )
            
            # Cloud mode: Always use CloudAgent
            if use_cloud_agent:
                api_key = AuthService.get_api_key(user_id, config["provider"])
                agent = CloudAgent(
                    llm=config["provider"],
                    model=config["model"],
                    api_key=api_key,
                    user_id=str(user_id),
                    debug=True,
                    capabilities=capabilities
                )
                await agent.initialize_mcp()
                agent_type = "cloud"
            else:
                # Local mode: Use appropriate agent type
                agent_type_config = get_agent_type_config(user_id)
                disabled_tools_list = get_disabled_tools(user_id)
                
                if agent_type_config and agent_type_config.get("agent_type") == "smart":
                    mode = agent_type_config.get("mode") or SmartAgentMode.SOLO
                    project_id = agent_type_config.get("project_id")
                    agent = SmartAgent(
                        llm=provider, mode=mode, project_id=project_id,
                        debug=True, capabilities=capabilities
                    )
                    agent_type = "smart"
                else:
                    current_agent_type = agent_type_config.get("agent_type") if agent_type_config else "default"
                    tools_enabled = config.get("tools_enabled", True)

                    if current_agent_type == "default" and tools_enabled:
                        capabilities.supports_tools = True

                    agent = Agent(llm=provider, debug=True, capabilities=capabilities)
                    
                    if disabled_tools_list:
                        agent.disabled_tools = set(disabled_tools_list)

                    if tools_enabled and capabilities.supports_tools:
                        agent.load_default_tools()
                        await load_mcp_config(agent, user_id, current_agent_type or "default")
                    agent_type = current_agent_type or "default"
            
            agent_cache[user_id] = {
                "agent": agent,
                "config": config,
                "provider": provider,
                "capabilities": capabilities.to_dict(),
                "agent_type": agent_type
            }
            
            return agent
        
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Failed to initialize agent: {str(e)}"
            })
            await websocket.close()
            return None


async def create_provider(user_id: int, config: dict):
    """Create LLM provider instance."""
    provider_name = config["provider"]
    api_key = AuthService.get_api_key(user_id, provider_name)
    
    if api_key:
        if provider_name == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif provider_name == "gemini":
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ["GEMINI_API_KEY"] = api_key
    
    if provider_name == "ollama":
        return OllamaProvider(model_name=config["model"] or "llama3.2:3b")
    elif provider_name == "groq":
        return GroqProvider(model_name=config["model"], api_key=api_key)
    elif provider_name == "gemini":
        return GeminiProvider(model_name=config["model"], api_key=api_key)
    elif provider_name == "azure":
        endpoint = AuthService.get_provider_endpoint(user_id, "azure")
        model_name_lower = (config.get("model") or "").lower()
        model_type = "anthropic" if "claude" in model_name_lower else config.get("model_type", "openai")
        return AzureProvider(
            model_name=config["model"],
            api_key=api_key,
            endpoint=endpoint,
            model_type=model_type
        )
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def get_agent_type_config(user_id: int) -> Optional[dict]:
    """Get agent type configuration for user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_agent_config WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    except:
        pass
    return None


def get_disabled_tools(user_id: int) -> list:
    """Get disabled tools for user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT disabled_tools_json FROM user_disabled_tools WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
    except:
        pass
    return []


def refresh_disabled_tools(agent, user_id: int):
    """Refresh disabled tools from database."""
    try:
        disabled_tools_list = get_disabled_tools(user_id)
        agent.disabled_tools = set(disabled_tools_list) if disabled_tools_list else set()
    except:
        pass


async def load_mcp_config(agent, user_id: int, agent_type: str):
    """Load MCP configuration for agent."""
    if agent_type != "default":
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT config_json FROM user_mcp_config WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            mcp_config = json.loads(row["config_json"])
            await agent.add_mcp_server(config=mcp_config)
    except Exception as e:
        print(f"[Server] Failed to load MCP config: {e}")


async def handle_chat_message(
    data: dict,
    websocket: WebSocket,
    user_id: int,
    agent,
    session_manager: SessionManager,
    streaming_manager,
    connection_id: str
):
    """Handle incoming chat message with session isolation."""
    content = data.get("content", "")
    image_data = data.get("image")
    images_data = data.get("images", [])
    session_id = data.get("session_id", f"user_{user_id}_default")
    is_edit = data.get("is_edit", False)
    edit_index = data.get("edit_index")
    
    # Normalize images
    all_images = []
    if image_data:
        all_images.append(image_data)
    if images_data and isinstance(images_data, list):
        all_images.extend(images_data)

    if all_images:
        content = format_multimodal_content_multi(content, all_images)
        for img in all_images:
            media_info = save_media_to_disk(user_id, img)
            if media_info:
                await websocket.send_json({"type": "media_saved", "media": media_info})
    
    # Ensure session_id has user prefix
    if not session_id.startswith(f"user_{user_id}_"):
        session_id = f"user_{user_id}_{session_id}"

    # Update connection's current session
    connection_manager.set_session(connection_id, session_id)

    # Load session if needed
    if session_id not in agent.sessions:
        loaded_msgs = session_manager.load_session(session_id)
        if loaded_msgs:
            # Sanitize messages to fix broken tool_calls chains
            loaded_msgs = sanitize_session_messages(loaded_msgs)
            session_obj = agent.get_session(session_id)
            session_obj.messages = loaded_msgs
            # Refresh the system message date when loading from history
            # This ensures the AI has current date, not stale date from session creation
            if hasattr(agent, 'refresh_system_message_date'):
                agent.refresh_system_message_date(session_id)

    # Handle edit
    if is_edit and edit_index is not None:
        session = agent.get_session(session_id)
        if 0 <= edit_index < len(session.messages):
            session.messages = session.messages[:edit_index]

    # Start stream tracking
    active_stream = await streaming_manager.start_stream(session_id, user_id)
    
    # Track connection state
    ws_connected = True
    in_thinking = False
    stream_buffer = ""
    all_text_buffer = ""
    detected_placeholders = set()

    async def on_token(token_text: str):
        nonlocal ws_connected, in_thinking, stream_buffer, all_text_buffer, detected_placeholders
        
        # Check if stream was cancelled
        if active_stream.is_cancelled:
            return
        
        print(token_text, end="", flush=True)
        
        if not ws_connected:
            return
            
        try:
            stream_buffer += token_text
            all_text_buffer += token_text
            active_stream.accumulated_response = all_text_buffer
            
            # Detect media placeholders
            import re
            media_patterns = [
                (r'!\[SEARCH:\s*"([^"]+)"\]', 'image'),
                (r'!\[VIDEO:\s*"([^"]+)"\]', 'video')
            ]
            
            for pattern, m_type in media_patterns:
                matches = re.finditer(pattern, all_text_buffer)
                for match in matches:
                    full_placeholder = match.group(0)
                    query = match.group(1)
                    if full_placeholder not in detected_placeholders:
                        detected_placeholders.add(full_placeholder)
                        asyncio.create_task(resolve_media_inline(
                            query, m_type, full_placeholder, websocket,
                            session_id=session_id, session_manager=session_manager,
                            active_stream=active_stream
                        ))

            # Process thinking tags and send tokens
            await process_stream_buffer(
                websocket, active_stream, stream_buffer, in_thinking
            )
            stream_buffer = ""

        except Exception as e:
            print(f"[Server] Error in on_token: {e}")
            ws_connected = False

    async def on_tool_start(sess, name: str, args: dict):
        nonlocal ws_connected
        if active_stream.is_cancelled or not ws_connected:
            return
        try:
            await websocket.send_json({
                "type": "tool_start",
                "tool_name": name,
                "args": args,
                "session_id": session_id
            })
        except:
            ws_connected = False

    async def on_tool_end(sess, name: str, result):
        nonlocal ws_connected
        if active_stream.is_cancelled or not ws_connected:
            return
        try:
            await websocket.send_json({
                "type": "tool_end",
                "tool_name": name,
                "result": str(result)[:500] if result else "",
                "session_id": session_id
            })
        except:
            ws_connected = False

    async def on_tool_approval(sess, name: str, args: dict):
        return True
    
    async def on_parallel_tools_start(sess, tool_names: list):
        """Notify frontend that a batch of tools is starting in parallel."""
        nonlocal ws_connected
        if active_stream.is_cancelled or not ws_connected:
            return
        try:
            await websocket.send_json({
                "type": "parallel_tools_start",
                "tool_names": tool_names,
                "count": len(tool_names),
                "session_id": session_id
            })
        except:
            ws_connected = False
    
    async def on_parallel_tools_end(sess, results: list):
        """Notify frontend that a batch of parallel tools has completed."""
        nonlocal ws_connected
        if active_stream.is_cancelled or not ws_connected:
            return
        try:
            await websocket.send_json({
                "type": "parallel_tools_end",
                "results": results,
                "count": len(results),
                "session_id": session_id
            })
        except:
            ws_connected = False

    chat_callbacks = {
        "on_token": on_token,
        "on_tool_start": on_tool_start,
        "on_tool_end": on_tool_end,
        "on_tool_approval": on_tool_approval,
        "on_parallel_tools_start": on_parallel_tools_start,
        "on_parallel_tools_end": on_parallel_tools_end
    }

    try:
        # SimpleMem context
        if is_simplemem_enabled() and isinstance(content, str):
            contexts = await get_simplemem_context(str(user_id), session_id, content)
        
        response = await agent.chat(content, session_id=session_id, callbacks=chat_callbacks)
        print()
        
        session = agent.get_session(session_id)
        
        # Save metadata
        save_metadata = None
        if user_id in agent_cache:
            conf = agent_cache[user_id].get("config", {})
            save_metadata = {
                "provider": conf.get("provider"),
                "model": conf.get("model"),
                "model_type": conf.get("model_type")
            }
        
        # Merge media state
        if active_stream.media_state["data"]:
            if session.messages and session.messages[-1]["role"] == "assistant":
                if "media" not in session.messages[-1]:
                    session.messages[-1]["media"] = {}
                session.messages[-1]["media"].update(active_stream.media_state["data"])

        active_stream.media_state["committed"] = True
        session_manager.save_session(session_id, session.messages, metadata=save_metadata)
        
        # SimpleMem store
        if is_simplemem_enabled() and response:
            await store_response_in_simplemem(str(user_id), session_id, response)
        
        if ws_connected and not active_stream.is_cancelled:
            await websocket.send_json({
                "type": "complete",
                "content": response,
                "session_id": session_id
            })

        # Auto-title generation
        current_title = None
        try:
            session_data = session_manager.storage.load_state(session_id, "metadata")
            if session_data:
                current_title = session_data.get("title")
        except:
            pass
        
        needs_title = not current_title or current_title in ["New Chat", "Untitled Chat", ""]
        if len(session.messages) >= 2 and len(session.messages) <= 10 and needs_title:
            asyncio.create_task(generate_title(
                session_id, session.messages, agent.provider, session_manager, websocket
            ))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if ws_connected:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "session_id": session_id
                })
            except:
                pass
    finally:
        # Complete the stream
        await streaming_manager.complete_stream(session_id)


async def process_stream_buffer(websocket: WebSocket, stream: ActiveStream, buffer: str, in_thinking: bool):
    """Process stream buffer and send appropriate messages."""
    # Simple implementation - just send tokens
    # Can be expanded for thinking tag handling
    if buffer and not stream.is_cancelled:
        await websocket.send_json({
            "type": "token",
            "content": buffer
        })


async def handle_delete_message(
    data: dict,
    websocket: WebSocket,
    user_id: int,
    agent,
    session_manager: SessionManager
):
    """Handle message deletion."""
    session_id = data.get("session_id")
    msg_index = data.get("index")
    
    if not session_id or msg_index is None:
        await websocket.send_json({
            "type": "error",
            "message": "Missing session_id or index for delete"
        })
        return
    
    if not agent:
        await websocket.send_json({
            "type": "error",
            "message": "Agent not initialized"
        })
        return
    
    if not session_id.startswith(f"user_{user_id}_"):
        session_id = f"user_{user_id}_{session_id}"

    if session_id not in agent.sessions:
        loaded_msgs = session_manager.load_session(session_id)
        if loaded_msgs:
            session_obj = agent.get_session(session_id)
            session_obj.messages = loaded_msgs
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Session {session_id} not found"
            })
            return
    
    try:
        session = agent.get_session(session_id)
        
        if not session or not session.messages:
            await websocket.send_json({
                "type": "error",
                "message": "Session has no messages"
            })
            return
        
        if msg_index < 0 or msg_index >= len(session.messages):
            await websocket.send_json({
                "type": "error",
                "message": f"Invalid message index {msg_index}"
            })
            return
        
        def get_role(msg):
            if isinstance(msg, dict):
                return msg.get('role', 'unknown')
            return getattr(msg, 'role', 'unknown')
        
        target_role = get_role(session.messages[msg_index])
        indices_to_delete = [msg_index]
        
        next_idx = msg_index + 1
        while next_idx < len(session.messages):
            next_msg = session.messages[next_idx]
            next_role = get_role(next_msg)
            
            if target_role == 'user':
                if next_role == 'user':
                    break
                indices_to_delete.append(next_idx)
            elif target_role == 'assistant':
                if next_role == 'tool':
                    indices_to_delete.append(next_idx)
                else:
                    break
            else:
                break
            
            next_idx += 1
                
        indices_to_delete.sort(reverse=True)
        
        deleted_roles = []
        for idx in indices_to_delete:
            removed = session.messages.pop(idx)
            removed_role = get_role(removed)
            deleted_roles.append(removed_role)
        
        remaining_user_msgs = sum(1 for m in session.messages if get_role(m) == 'user')
        
        if remaining_user_msgs == 0:
            session_manager.delete_session(session_id)
            if session_id in agent.sessions:
                del agent.sessions[session_id]
            
            await websocket.send_json({
                "type": "session_deleted",
                "session_id": session_id,
                "reason": "all_messages_deleted"
            })
        else:
            session_manager.save_session(session_id, session.messages)
            
            await websocket.send_json({
                "type": "message_deleted",
                "session_id": session_id,
                "index": msg_index,
                "deleted_count": len(indices_to_delete),
                "deleted_roles": deleted_roles
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to delete message: {str(e)}"
        })
