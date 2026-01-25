import asyncio
import os
import sys

# Ensure we can import scratchy
sys.path.insert(0, os.getcwd())

from scratchy.providers.azure_provider import AzureProvider

# Configuration 1: Anthropic
ANTHROPIC_CONFIG = {
    "model_name": "claude-opus-4-5",
    "endpoint": "https://anydoctransform-resource.services.ai.azure.com/anthropic/v1/messages",
    "api_key": os.getenv("ANTHROPIC_AXURE_API_KEY", "PLACEHOLDER_KEY"),
    "model_type": "anthropic" 
}

# Configuration 2: DeepSeek (OpenAI Compatible - MaaS)
DEEPSEEK_CONFIG = {
    "model_name": "DeepSeek-V3.2",
    "endpoint": "https://dhruv-m4ndq32p-eastus2.services.ai.azure.com/openai/v1/",
    "api_key": os.getenv("DEEPSEEK_API_KEY", "PLACEHOLDER_KEY"),
    "model_type": "openai" 
}

# Configuration 3: GPT-5 Mini (Standard Azure OpenAI)
GPT5_CONFIG = {
    "model_name": "gpt-5-mini",
    "endpoint": "https://dhruv-m4ndq32p-eastus2.openai.azure.com/",
    "api_key": os.getenv("AZURE_OPENAI_API_KEY", "PLACEHOLDER_KEY"),
    "model_type": "openai"
}

async def test_provider(name, config):
    print(f"\n--- Testing {name} ---")
    try:
        provider = AzureProvider(
            model_name=config["model_name"],
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            model_type=config.get("model_type")
        )
        print(f"Initialized provider with type: {provider.model_type}")
        
        # Test 1: Simple User Message
        print("Test 1: Simple User Message")
        msgs = [{"role": "user", "content": "Hello, simply say 'Working'"}]
        response = await provider.chat(msgs)
        print(f"Test 1 Response: {response.content}")

    except Exception as e:
        print(f"Failed: {e}")

async def main():
    await test_provider("Anthropic", ANTHROPIC_CONFIG)
    await test_provider("DeepSeek", DEEPSEEK_CONFIG)
    await test_provider("GPT-5 Mini", GPT5_CONFIG)

if __name__ == "__main__":
    asyncio.run(main())
