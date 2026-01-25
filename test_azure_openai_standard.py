import os
from openai import AzureOpenAI
import traceback

# Provided Configuration
ENDPOINT = "https://dhruv-m4ndq32p-eastus2.openai.azure.com/"
API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "PLACEHOLDER_KEY_DO_NOT_COMMIT")
API_VERSION = "2024-12-01-preview"
DEPLOYMENT = "gpt-5-mini" # Assuming deployment name from previous context

def test_standard_azure():
    print(f"\n--- Testing Standard Azure OpenAI ---")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Deployment: {DEPLOYMENT}")
    
    client = AzureOpenAI(
        api_version=API_VERSION,
        azure_endpoint=ENDPOINT,
        api_key=API_KEY
    )
    
    # 1. Simple Test
    print("\nTest 1: Simple Chat")
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role": "user", "content": "Say hello!"}]
        )
        print(f"[SUCCESS] Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"[FAILED] Simple chat failed: {e}")

    # 2. Tool Test
    print("\nTest 2: Tool Use")
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"]
            }
        }
    }]
    
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role": "user", "content": "What's the weather in San Francisco?"}],
            tools=tools,
            tool_choice="auto"
        )
        print("[SUCCESS] Model accepted tools parameter.")
        if response.choices[0].message.tool_calls:
            print(f"Tool Call: {response.choices[0].message.tool_calls[0].function.name}")
        else:
            print(f"No tool call triggered, response: {response.choices[0].message.content[:50]}...")
    except Exception as e:
        print(f"[FAILED] Tool use failed: {e}")

if __name__ == "__main__":
    test_standard_azure()
