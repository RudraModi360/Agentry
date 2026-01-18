"""
WebSocket chat handler.
This is the main real-time chat endpoint for the application.
"""
import os
import json
import asyncio
import sqlite3
import base64
import time
from datetime import datetime
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.config import DB_PATH, UI_DIR
from backend.core.dependencies import get_user_from_token
from backend.services.auth_service import AuthService
from backend.services.agent_cache import agent_cache
from backend.services.simplemem_middleware import (
    get_simplemem_context,
    store_response_in_simplemem,
    augment_prompt_with_context,
    is_simplemem_enabled
)

from agentry import Agent
from agentry.agents import SmartAgent, SmartAgentMode
from agentry.session_manager import SessionManager
from agentry.providers.ollama_provider import OllamaProvider
from agentry.providers.groq_provider import GroqProvider
from agentry.providers.gemini_provider import GeminiProvider
from agentry.providers.azure_provider import AzureProvider
from agentry.providers.capability_detector import detect_model_capabilities

router = APIRouter()


def format_multimodal_content_multi(text: str, images_data: List[str]) -> list:
    """Format text and multiple images into multimodal content for vision models."""
    content = []
    
    if text:
        content.append({
            "type": "text",
            "text": text
        })
    
    for img_data in images_data:
        content.append({
            "type": "image",
            "data": img_data
        })
    
    return content


def save_media_to_disk(user_id: int, image_data: str, filename: str = None) -> dict:
    """Saves base64 image data to the local media directory and records it in the DB."""
    # Extract extension and base64 data
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

    # Generate unique filename if not provided
    if not filename:
        timestamp = int(time.time() * 1000)
        filename = f"media_{user_id}_{timestamp}.{ext}"
    
    filepath = os.path.join(UI_DIR, "media", filename)
    
    # Decode and save
    try:
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(raw_data))
    except Exception as e:
        print(f"[Server] Error saving media to disk: {e}")
        return None
    
    # Save to database
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


async def generate_title(session_id: str, messages: list, provider, session_manager: SessionManager, websocket: WebSocket = None):
    """Generate and save 3-5 word title for the session."""
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
            elif hasattr(msg, "role") and msg.role == "user":
                first_user_msg = str(msg.content) if hasattr(msg, "content") else str(msg)
                break
        
        if not first_user_msg or len(first_user_msg) < 3:
            return
        
        prompt = (
            f"Create a 3-5 word title summarizing this conversation starter. "
            f"Return ONLY the title, no quotes or punctuation:\n\n\"{first_user_msg[:200]}\""
        )
        
        # Use chat method (providers have chat, not generate)
        messages = [{"role": "user", "content": prompt}]
        response = await provider.chat(messages)
        
        # Extract content from response (could be dict or object)
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
            print(f"[Server] Generated title for {session_id}: {title}")
    except Exception as e:
        print(f"[Server] Title generation failed: {e}")
        import traceback
        traceback.print_exc()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    user = None
    agent = None
    
    try:
        # Wait for authentication message
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
        
        # Get or create agent from cache
        if user_id in agent_cache:
            cached = agent_cache[user_id]
            
            # Check if agent needs lazy initialization (from quick configure)
            if cached.get("needs_init"):
                print(f"[Server WS] Lazy initializing agent for user {user_id}...")
                provider = cached["provider"]
                config = cached["config"]
                capabilities_dict = cached["capabilities"]
                
                from agentry.providers.capability_detector import ModelCapabilities
                capabilities = ModelCapabilities.from_dict(capabilities_dict)
                
                # Check agent type configuration
                agent_type_config = None
                try:
                    from backend.core.db_pool import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM user_agent_config WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()
                    if row:
                        agent_type_config = {"agent_type": row[0] if row else "default", "mode": row[1] if len(row) > 1 else None, "project_id": row[2] if len(row) > 2 else None}
                except Exception as e:
                    print(f"[Server WS] Error loading agent config: {e}")
                
                # Load disabled tools
                disabled_tools_list = []
                try:
                    from backend.core.db_pool import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT disabled_tools_json FROM user_disabled_tools WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()
                    if row:
                        disabled_tools_list = json.loads(row[0])
                        print(f"[Server WS] Loaded {len(disabled_tools_list)} disabled tools for user {user_id}")
                except Exception as e:
                    print(f"[Server WS] Error loading disabled tools: {e}")
                
                # Create appropriate agent type
                if agent_type_config and agent_type_config.get("agent_type") == "smart":
                    mode = agent_type_config.get("mode") or SmartAgentMode.SOLO
                    project_id = agent_type_config.get("project_id")
                    
                    agent = SmartAgent(
                        llm=provider,
                        mode=mode,
                        project_id=project_id,
                        debug=True,
                        capabilities=capabilities
                    )
                    print(f"[Server WS] Created SmartAgent in {mode} mode")
                else:
                    # Default Agent: Enable tools if user wants them, even if model support is ambiguous
                    current_agent_type = agent_type_config.get("agent_type") if agent_type_config else "default"
                    tools_enabled = config.get("tools_enabled", True)
                    
                    if current_agent_type == "default" and tools_enabled:
                         capabilities.supports_tools = True
                         print(f"[Server WS] Forcing tool support for Default Agent")

                    agent = Agent(llm=provider, debug=True, capabilities=capabilities)
                    
                    if disabled_tools_list:
                        agent.disabled_tools = set(disabled_tools_list)
                    
                    if tools_enabled and capabilities.supports_tools:
                        agent.load_default_tools()
                        print(f"[Server WS] Loaded tools for {config.get('model')}")
                        
                        # Load MCP Configuration (only for default agent)
                        if current_agent_type == "default":
                            try:
                                from backend.core.db_pool import get_connection
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("SELECT config_json FROM user_mcp_config WHERE user_id = ?", (user_id,))
                                row = cursor.fetchone()
                                if row:
                                    mcp_config = json.loads(row[0])
                                    await agent.add_mcp_server(config=mcp_config)
                                    print(f"[Server WS] Loaded MCP tools for user {user_id}")
                            except Exception as e:
                                print(f"[Server WS] Failed to load MCP config: {e}")
                
                # Update cache with initialized agent
                agent_cache[user_id] = {
                    "agent": agent,
                    "config": config,
                    "provider": provider,
                    "capabilities": capabilities_dict,
                    "needs_init": False
                }
                print(f"[Server WS] Agent lazy initialization complete")
            else:
                agent = cached["agent"]
            
                # Refresh disabled tools from database
                try:
                    from backend.core.db_pool import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT disabled_tools_json FROM user_disabled_tools WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()
                    if row:
                        disabled_tools_list = json.loads(row[0])
                        agent.disabled_tools = set(disabled_tools_list)
                        print(f"[Server WS] Refreshed {len(disabled_tools_list)} disabled tools for cached agent")
                    else:
                        agent.disabled_tools = set()
                except Exception as e:
                    print(f"[Server WS] Error refreshing disabled tools: {e}")
        else:
            # Load config and create agent
            config = AuthService.get_current_active_settings(user_id)
            if not config:
                await websocket.send_json({"type": "error", "message": "Provider not configured. Please complete setup."})
                await websocket.close()
                return
            
            try:
                provider_name = config["provider"]
                api_key = AuthService.get_api_key(user_id, provider_name)
                
                # Restore API keys to environment
                if api_key:
                    if provider_name == "groq":
                        os.environ["GROQ_API_KEY"] = api_key
                    elif provider_name == "gemini":
                        os.environ["GOOGLE_API_KEY"] = api_key
                        os.environ["GEMINI_API_KEY"] = api_key
                    elif provider_name == "ollama":
                        os.environ["OLLAMA_API_KEY"] = api_key
                
                # Create provider
                if provider_name == "ollama":
                    provider = OllamaProvider(model_name=config["model"] or "llama3.2:3b")
                elif provider_name == "groq":
                    provider = GroqProvider(model_name=config["model"], api_key=api_key)
                elif provider_name == "gemini":
                    provider = GeminiProvider(model_name=config["model"], api_key=api_key)
                elif provider_name == "azure":
                    endpoint = AuthService.get_provider_endpoint(user_id, "azure")
                    model_name_lower = (config.get("model") or "").lower()
                    if "claude" in model_name_lower:
                        model_type = "anthropic"
                    else:
                        model_type = config.get("model_type", "openai")
                    provider = AzureProvider(
                        model_name=config["model"], 
                        api_key=api_key, 
                        endpoint=endpoint,
                        model_type=model_type
                    )
                else:
                    raise ValueError(f"Unknown provider: {provider_name}")
                
                # Detect capabilities
                capabilities = await detect_model_capabilities(
                    provider_name=provider_name,
                    model_name=config["model"],
                    provider_instance=provider
                )
                
                # Check agent type configuration
                agent_type_config = None
                try:
                    conn = sqlite3.connect(DB_PATH)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM user_agent_config WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()
                    if row:
                        agent_type_config = dict(row)
                    conn.close()
                except:
                    pass
                
                # Load disabled tools
                disabled_tools_list = []
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT disabled_tools_json FROM user_disabled_tools WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()
                    if row:
                        disabled_tools_list = json.loads(row[0])
                        print(f"[Server WS] Loaded {len(disabled_tools_list)} disabled tools for user {user_id}")
                    conn.close()
                except Exception as e:
                    print(f"[Server WS] Error loading disabled tools: {e}")

                # Create appropriate agent type
                if agent_type_config and agent_type_config.get("agent_type") == "smart":
                    mode = agent_type_config.get("mode") or SmartAgentMode.SOLO
                    project_id = agent_type_config.get("project_id")
                    
                    agent = SmartAgent(
                        llm=provider,
                        mode=mode,
                        project_id=project_id,
                        debug=True,
                        capabilities=capabilities
                    )
                    print(f"[Server WS] Created SmartAgent in {mode} mode" + 
                          (f" for project {project_id}" if project_id else ""))
                else:
                    # Default Agent: Enable tools if user wants them, even if model support is ambiguous
                    current_agent_type = agent_type_config.get("agent_type") if agent_type_config else "default"
                    tools_enabled_by_user = config.get("tools_enabled", True)

                    if current_agent_type == "default" and tools_enabled_by_user:
                        capabilities.supports_tools = True
                        print(f"[Server WS] Forcing tool support for Default Agent (Model: {config.get('model')})")

                    agent = Agent(llm=provider, debug=True, capabilities=capabilities)
                    
                    if disabled_tools_list:
                        agent.disabled_tools = set(disabled_tools_list)
                        print(f"[Server WS] Applied {len(agent.disabled_tools)} disabled tools to agent")

                    if tools_enabled_by_user and capabilities.supports_tools:
                        agent.load_default_tools()
                        print(f"[Server WS] Loaded tools for {config['model']}")

                        # Load MCP Configuration
                        if current_agent_type == "default":
                            try:
                                conn = sqlite3.connect(DB_PATH)
                                conn.row_factory = sqlite3.Row
                                cursor = conn.cursor()
                                cursor.execute("SELECT config_json FROM user_mcp_config WHERE user_id = ?", (user_id,))
                                row = cursor.fetchone()
                                if row:
                                    mcp_config = json.loads(row["config_json"])
                                    await agent.add_mcp_server(config=mcp_config)
                                    print(f"[Server WS] Loaded MCP tools for user {user_id}")
                                conn.close()
                            except Exception as e:
                                print(f"[Server WS] Failed to load MCP config: {e}")
                    elif not tools_enabled_by_user:
                        agent.disable_tools("User disabled tools in setup")
                        print(f"[Server WS] Tools disabled by user for {config['model']}")
                    else:
                        print(f"[Server WS] Skipping tools - {config['model']} does not support tools")
                
                agent_cache[user_id] = {
                    "agent": agent,
                    "config": config,
                    "provider": provider,
                    "capabilities": capabilities.to_dict(),
                    "agent_type": agent_type_config.get("agent_type") if agent_type_config else "default"
                }
            
            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"Failed to initialize agent: {str(e)}"})
                await websocket.close()
                return
        
        # Send capabilities to client on connection
        cached_capabilities = agent_cache.get(user_id, {}).get("capabilities", {})
        await websocket.send_json({
            "type": "connected", 
            "message": "Connected to Agentry",
            "capabilities": cached_capabilities
        })
        
        session_manager = SessionManager()
        
        # Chat loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "message":
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

                # Process images if present
                if all_images:
                    content = format_multimodal_content_multi(content, all_images)
                    print(f"[Server] Processing {len(all_images)} images (Vision support: {agent_cache.get(user_id, {}).get('capabilities', {}).get('supports_vision', False)})")
                    
                    # Save ALL images to media library
                    for img in all_images:
                        media_info = save_media_to_disk(user_id, img)
                        if media_info:
                            await websocket.send_json({
                                "type": "media_saved",
                                "media": media_info
                            })
                
                # Ensure session_id has user prefix
                if not session_id.startswith(f"user_{user_id}_"):
                    session_id = f"user_{user_id}_{session_id}"

                # Ensure session is loaded in Agent
                if session_id not in agent.sessions:
                    loaded_msgs = session_manager.load_session(session_id)
                    if loaded_msgs:
                        print(f"[Server] Restoring session {session_id} from DB ({len(loaded_msgs)} msgs)")
                        session_obj = agent.get_session(session_id)
                        session_obj.messages = loaded_msgs

                # Handle Editing Logic
                if is_edit and edit_index is not None:
                    session = agent.get_session(session_id)
                    if 0 <= edit_index < len(session.messages):
                        session.messages = session.messages[:edit_index]
                
                # Track connection state
                ws_connected = True
                
                # Track thinking state
                in_thinking = False
                stream_buffer = ""
                
                # Define callbacks for streaming
                async def on_token(token_text: str):
                    nonlocal ws_connected, in_thinking, stream_buffer
                    
                    print(token_text, end="", flush=True)
                    
                    if not ws_connected:
                        return
                        
                    try:
                        stream_buffer += token_text
                        
                        # List of potential thinking tags to handle
                        start_tags = ["<thinking>", "<thought>"]
                        end_tags = ["</thinking>", "</thought>"]
                        
                        while stream_buffer:
                            if not in_thinking:
                                # Check for any start tag
                                found_start = None
                                for tag in start_tags:
                                    if stream_buffer.startswith(tag):
                                        found_start = tag
                                        break
                                
                                if found_start:
                                    in_thinking = True
                                    await websocket.send_json({"type": "thinking_start"})
                                    stream_buffer = stream_buffer[len(found_start):]
                                    continue
                                
                                # Check if a start tag might be appearing (partial match at end)
                                earliest_start = -1
                                for tag in start_tags:
                                    idx = stream_buffer.find(tag)
                                    if idx != -1 and (earliest_start == -1 or idx < earliest_start):
                                        earliest_start = idx
                                
                                if earliest_start != -1:
                                    text_chunk = stream_buffer[:earliest_start]
                                    if text_chunk:
                                        await websocket.send_json({
                                            "type": "token",
                                            "content": text_chunk
                                        })
                                    stream_buffer = stream_buffer[earliest_start:]
                                    continue
                                
                                # Handle partial tags at the very end of the buffer
                                partial_match = False
                                for tag in start_tags:
                                    for i in range(1, len(tag)):
                                        suffix = stream_buffer[-i:]
                                        if tag.startswith(suffix):
                                            partial_match = True
                                            if len(stream_buffer) > i:
                                                safe_chunk = stream_buffer[:-i]
                                                await websocket.send_json({
                                                    "type": "token",
                                                    "content": safe_chunk
                                                })
                                                stream_buffer = suffix
                                            break
                                    if partial_match: break
                                
                                if partial_match:
                                    break
                                
                                await websocket.send_json({
                                    "type": "token",
                                    "content": stream_buffer
                                })
                                stream_buffer = ""
                                
                            else:
                                # Check for any end tag
                                found_end = None
                                for tag in end_tags:
                                    if stream_buffer.startswith(tag):
                                        found_end = tag
                                        break
                                
                                if found_end:
                                    in_thinking = False
                                    await websocket.send_json({"type": "thinking_end"})
                                    stream_buffer = stream_buffer[len(found_end):]
                                    continue
                                    
                                earliest_end = -1
                                for tag in end_tags:
                                    idx = stream_buffer.find(tag)
                                    if idx != -1 and (earliest_end == -1 or idx < earliest_end):
                                        earliest_end = idx
                                
                                if earliest_end != -1:
                                    thought_chunk = stream_buffer[:earliest_end]
                                    if thought_chunk:
                                        await websocket.send_json({
                                            "type": "thinking_delta",
                                            "content": thought_chunk
                                        })
                                    stream_buffer = stream_buffer[earliest_end:]
                                    continue
                                
                                # Handle partial end tags
                                partial_match = False
                                for tag in end_tags:
                                    for i in range(1, len(tag)):
                                        suffix = stream_buffer[-i:]
                                        if tag.startswith(suffix):
                                            partial_match = True
                                            if len(stream_buffer) > i:
                                                safe_chunk = stream_buffer[:-i]
                                                await websocket.send_json({
                                                    "type": "thinking_delta",
                                                    "content": safe_chunk
                                                })
                                                stream_buffer = suffix
                                            break
                                    if partial_match: break
                                
                                if partial_match:
                                    break
                                    
                                await websocket.send_json({
                                    "type": "thinking_delta",
                                    "content": stream_buffer
                                })
                                stream_buffer = ""

                    except Exception as e:
                        print(f"[Server] Error in on_token: {e}")
                        ws_connected = False
                
                async def on_tool_start(sess, name: str, args: dict):
                    nonlocal ws_connected
                    print(f"\n[Server] 🛠️ Executing Tool: {name} (Args: {str(args)[:100]}...)")
                    if not ws_connected:
                        return
                    try:
                        await websocket.send_json({
                            "type": "tool_start",
                            "tool_name": name,
                            "args": args
                        })
                    except Exception:
                        ws_connected = False
                
                async def on_tool_end(sess, name: str, result):
                    nonlocal ws_connected
                    print(f"[Server] ✅ Tool Finished: {name}")
                    if not ws_connected:
                        return
                    try:
                        await websocket.send_json({
                            "type": "tool_end",
                            "tool_name": name,
                            "result": str(result)[:500] if result else ""
                        })
                    except Exception:
                        ws_connected = False
                
                async def on_tool_approval(sess, name: str, args: dict):
                    return True
                
                # Prepare callbacks for this specific chat call
                chat_callbacks = {
                    "on_token": on_token,
                    "on_tool_start": on_tool_start,
                    "on_tool_end": on_tool_end,
                    "on_tool_approval": on_tool_approval
                }
                
                try:
                    print(f"[Server] Calling agent.chat with session_id: {session_id}")
                    
                    # SimpleMem: Get relevant context for the message
                    original_content = content
                    if is_simplemem_enabled() and isinstance(content, str):
                        contexts = await get_simplemem_context(str(user_id), session_id, content)
                        if contexts:
                            print(f"[SimpleMem] Retrieved {len(contexts)} memory contexts:")
                            for i, ctx in enumerate(contexts):
                                display_ctx = ctx[:200] + "..." if len(ctx) > 200 else ctx
                                print(f" - [{i+1}] {display_ctx}")
                    
                    if isinstance(content, list):
                        has_images = any(p.get("type") == "image" for p in content)
                        print(f"[Server] Content is multimodal. Has images: {has_images}")
                    else:
                        print(f"[Server] Content is plain text.")
                        
                    response = await agent.chat(content, session_id=session_id, callbacks=chat_callbacks)
                    print()
                    
                    session = agent.get_session(session_id)
                    
                    save_metadata = None
                    if user_id in agent_cache:
                        conf = agent_cache[user_id].get("config", {})
                        save_metadata = {
                            "provider": conf.get("provider"),
                            "model": conf.get("model"),
                            "model_type": conf.get("model_type")
                        }
                    
                    session_manager.save_session(session_id, session.messages, metadata=save_metadata)
                    
                    # SimpleMem: Store the response in memory
                    if is_simplemem_enabled() and response:
                        await store_response_in_simplemem(str(user_id), session_id, response)
                    
                    if ws_connected:
                        await websocket.send_json({
                            "type": "complete",
                            "content": response
                        })

                    # Check for Auto-Title Generation
                    current_title = None
                    try:
                        session_data = session_manager.storage.load_state(session_id, "metadata")
                        if session_data:
                            current_title = session_data.get("title")
                    except:
                        pass
                    
                    needs_title = (not current_title or current_title in ["New Chat", "Untitled Chat", ""])
                    if len(session.messages) >= 2 and len(session.messages) <= 10 and needs_title:
                        asyncio.create_task(generate_title(session_id, session.messages, agent.provider, session_manager, websocket))
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    if ws_connected:
                        try:
                            await websocket.send_json({
                                "type": "error",
                                "message": str(e)
                            })
                        except:
                            pass
            
            elif msg_type == "load_session":
                session_id = data.get("session_id")
                messages = session_manager.load_session(session_id)
                await websocket.send_json({
                    "type": "session_loaded",
                    "session_id": session_id,
                    "messages": messages or []
                })
            
            elif msg_type == "delete_message":
                session_id = data.get("session_id")
                msg_index = data.get("index")
                
                print(f"[Server] Delete request received: session_id={session_id}, index={msg_index}")
                
                if not session_id or msg_index is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing session_id or index for delete"
                    })
                    continue
                    
                if not agent:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Agent not initialized"
                    })
                    continue
                
                if not session_id.startswith(f"user_{user_id}_"):
                    session_id = f"user_{user_id}_{session_id}"

                if session_id not in agent.sessions:
                    loaded_msgs = session_manager.load_session(session_id)
                    if loaded_msgs:
                        print(f"[Server] Restoring session {session_id} from DB for deletion ({len(loaded_msgs)} msgs)")
                        session_obj = agent.get_session(session_id)
                        session_obj.messages = loaded_msgs
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Session {session_id} not found"
                        })
                        continue
                
                try:
                    session = agent.get_session(session_id)
                    
                    if not session or not session.messages:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Session has no messages"
                        })
                        continue
                    
                    if msg_index < 0 or msg_index >= len(session.messages):
                        print(f"[Server] Invalid index {msg_index}, session has {len(session.messages)} messages")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Invalid message index {msg_index}"
                        })
                        continue
                    
                    def get_role(msg):
                        if isinstance(msg, dict):
                            return msg.get('role', 'unknown')
                        return getattr(msg, 'role', 'unknown')
                    
                    target_role = get_role(session.messages[msg_index])
                    indices_to_delete = [msg_index]
                    
                    print(f"[Server] Request to delete message {msg_index} ({target_role})")
                    
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
                        print(f"[Server] Deleted message at index {idx} ({removed_role})")
                    
                    remaining_user_msgs = sum(1 for m in session.messages if get_role(m) == 'user')
                    
                    if remaining_user_msgs == 0:
                        print(f"[Server] No user messages left, deleting session {session_id}")
                        session_manager.delete_session(session_id)
                        
                        if session_id in agent.sessions:
                            del agent.sessions[session_id]
                        
                        await websocket.send_json({
                            "type": "session_deleted",
                            "session_id": session_id,
                            "reason": "all_messages_deleted"
                        })
                        print(f"[Server] Session {session_id} deleted (no messages remaining)")
                    else:
                        session_manager.save_session(session_id, session.messages)
                        
                        await websocket.send_json({
                            "type": "message_deleted",
                            "session_id": session_id,
                            "index": msg_index,
                            "deleted_count": len(indices_to_delete),
                            "deleted_roles": deleted_roles
                        })
                        print(f"[Server] Successfully deleted {len(indices_to_delete)} message(s)")
                    
                except Exception as e:
                    print(f"Error deleting message: {e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to delete message: {str(e)}"
                    })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"Client disconnected: {user['username'] if user else 'unknown'}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
