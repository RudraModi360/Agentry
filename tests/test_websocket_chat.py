"""
WebSocket Chat Test Script
===========================
Tests the WebSocket chat endpoint with authentication.

Run with: python tests/test_websocket_chat.py
"""

import asyncio
import json
import requests

# For websockets library
try:
    import websockets
except ImportError:
    print("Installing websockets library...")
    import subprocess
    subprocess.check_call(["pip", "install", "websockets"])
    import websockets

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"

# Credentials
USERNAME = "Rudra"
PASSWORD = "123456"


async def test_chat():
    print("=" * 60)
    print("🧪 WEBSOCKET CHAT TEST")
    print("=" * 60)
    
    # Step 1: Login to get token
    print("\n📍 Step 1: Login to get auth token...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    data = response.json()
    token = data.get("token")
    print(f"✅ Login successful! Token: {token[:20]}...")
    
    # Step 2: Connect to WebSocket
    print(f"\n📍 Step 2: Connecting to WebSocket at {WS_URL}...")
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ WebSocket connected!")
            
            # Step 3: Authenticate
            print("\n📍 Step 3: Sending authentication...")
            auth_msg = {"type": "auth", "token": token}
            await ws.send(json.dumps(auth_msg))
            print(f"📤 Sent: {auth_msg}")
            
            # Wait for auth response
            try:
                auth_response = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"📥 Auth Response: {auth_response}")
            except asyncio.TimeoutError:
                print("⏱️ No auth response (continuing...)")
            
            # Step 4: Send "Hi" message
            print("\n📍 Step 4: Sending 'Hi' message...")
            chat_msg = {
                "type": "message",
                "content": "Hi",
                "session_id": f"user_test_{USERNAME}"
            }
            await ws.send(json.dumps(chat_msg))
            print(f"📤 Sent: {chat_msg}")
            
            # Step 5: Receive response chunks
            print("\n📍 Step 5: Receiving response...")
            full_response = ""
            chunk_count = 0
            
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    chunk_count += 1
                    
                    try:
                        data = json.loads(msg)
                        msg_type = data.get("type", "")
                        
                        if msg_type == "chunk" or "content" in data:
                            content = data.get("content", data.get("chunk", ""))
                            full_response += content
                            print(f"📥 Chunk {chunk_count}: {content[:50]}..." if len(content) > 50 else f"📥 Chunk {chunk_count}: {content}")
                        
                        elif msg_type == "stream_end" or data.get("done"):
                            print(f"📥 Stream ended")
                            break
                        
                        elif msg_type == "error":
                            print(f"❌ Error: {data.get('message', data)}")
                            break
                        
                        else:
                            print(f"📥 Message: {msg[:100]}...")
                            
                    except json.JSONDecodeError:
                        print(f"📥 Raw: {msg[:100]}...")
                        
            except asyncio.TimeoutError:
                print("⏱️ Response timeout (30s)")
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 RESULT")
            print("=" * 60)
            print(f"Chunks received: {chunk_count}")
            print(f"Full response:\n{full_response[:500]}..." if len(full_response) > 500 else f"Full response:\n{full_response}")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


if __name__ == "__main__":
    asyncio.run(test_chat())
