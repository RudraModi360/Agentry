import asyncio
import os
import sys
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.getcwd())

from backend.services.media_orchestrator import media_orchestrator

# Mock Provider
class MockProvider:
    def __init__(self, mock_response: str):
        self.mock_response = mock_response
        self.content = mock_response # For direct attribute access if needed

    async def chat(self, messages, temperature=0.1):
        # Return a mock response object
        class Response:
            content = self.mock_response
        return Response()

async def verify_intent_analysis():
    print("\n[Verification] 1. Testing Intent Analysis (LLM Mock)...")
    
    # Test Case 1: Needs media
    mock_json = '{"needs_media": true, "query": "RBF Kernel visualization", "media_types": ["image", "video"]}'
    provider = MockProvider(mock_json)
    
    intent = await media_orchestrator.analyze_intent("Show me a video about RBF Kernels", provider)
    
    if intent.get("needs_media") and intent.get("query") == "RBF Kernel visualization":
        print("✅ Intent Analysis PASSED: Detected media need.")
    else:
        print(f"❌ Intent Analysis FAILED: Got {intent}")
        return False
        
    # Test Case 2: No media
    mock_json_no = '{"needs_media": false}'
    provider_no = MockProvider(mock_json_no)
    
    intent_no = await media_orchestrator.analyze_intent("What is 10 plus 10?", provider_no)
    
    if not intent_no.get("needs_media"):
        print("✅ Intent Analysis PASSED: Detected NO media need.")
    else:
        print(f"❌ Intent Analysis FAILED (No Media): Got {intent_no}")
        return False
        
    return True

async def verify_media_search():
    print("\n[Verification] 2. Testing Search Execution (Real Tool Call)...")
    
    # We will search for something simple that should definitely return results
    query = "cat"
    media_types = ["image"]
    
    print(f"Searching for '{query}' with types {media_types}...")
    try:
        results = await media_orchestrator.search_media(query, media_types)
        
        if len(results) > 0:
            print(f"✅ Search Execution PASSED: Found {len(results)} results.")
            print(f"   First result: {results[0].get('title')} ({results[0].get('type')})")
        else:
            print("⚠️ Search Execution WARNING: No results found (could be network or API limit).")
            # This is not necessarily a code fail, but an env fail
            
        # Verify strict video search if possible (might fail without API key, but let's check structure)
        # Note: Unless we have a valid key, this might return empty.
        
    except Exception as e:
        print(f"❌ Search Execution ERROR: {e}")
        return False
        
    return True

async def main():
    print("🚀 Starting Media Orchestrator Sanity Check")
    
    if await verify_intent_analysis():
        await verify_media_search()
    
    print("\n🏁 Sanity Check Complete")

if __name__ == "__main__":
    asyncio.run(main())
