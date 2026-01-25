import asyncio
import os
import sys
import logging

# Setup Paths
sys.path.insert(0, os.getcwd())

# Mocking the database and auth for environmentless testing if needed, 
# but ideally we test the actual logic class.
from scratchy.providers.azure_provider import AzureProvider

# Credentials
DEEPSEEK_CONFIG = {
    "model": "DeepSeek-V3.2",
    "endpoint": "https://dhruv-m4ndq32p-eastus2.services.ai.azure.com/openai/v1/",
    "api_key": os.getenv("DEEPSEEK_API_KEY", "PLACEHOLDER_KEY")
}

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deepseek_detection():
    print(f"\n[TEST] Testing DeepSeek Detection Logic")
    print(f"Input Endpoint: {DEEPSEEK_CONFIG['endpoint']}")
    
    # 1. Initialize Provider (simulating backend creation)
    try:
        provider = AzureProvider(
            model_name=DEEPSEEK_CONFIG["model"],
            api_key=DEEPSEEK_CONFIG["api_key"],
            endpoint=DEEPSEEK_CONFIG["endpoint"],
            model_type=None # Force autodetection
        )
        
        print(f"[SUCCESS] Provider Initialized")
        print(f"Detected Type: {provider.model_type}")
        print(f"Final Endpoint: {provider.endpoint}")
        
        # Verify it detected 'inference'
        if provider.model_type != "inference":
            print(f"[FAILURE] Expected 'inference' type, got '{provider.model_type}'")
            return False
            
        # 2. Test Chat
        print("\n[TEST] Sending Chat Request...")
        msgs = [{"role": "user", "content": "Hello DeepSeek, are you online?"}]
        start_t = asyncio.get_running_loop().time()
        response = await provider.chat(msgs)
        duration = asyncio.get_running_loop().time() - start_t
        
        print(f"[SUCCESS] Response Received in {duration:.2f}s")
        content = getattr(response, "content", str(response))
        print(f"Content: {content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        asyncio.run(test_deepseek_detection())
    except KeyboardInterrupt:
        pass
