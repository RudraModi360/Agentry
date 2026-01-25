
import asyncio
import os
import sys

# Ensure we can import scratchy
sys.path.insert(0, os.getcwd())

from scratchy.providers.azure_provider import AzureProvider

# Configuration 3: GPT-5 Mini (Standard Azure OpenAI)
GPT5_CONFIG = {
    "model_name": "gpt-5-mini",
    "endpoint": "https://dhruv-m4ndq32p-eastus2.openai.azure.com/",
    "api_key": os.getenv("AZURE_OPENAI_API_KEY", "PLACEHOLDER_KEY"),
    "model_type": "openai"
}

PROMPT = """
Here is the topic list of my syllabus for given chapter now I have exam tomorrow and I have to prepare for it .

I have zero knowledge on this subject so help me .
Give the same in question answer format important topics u explain in detail rest in short.
Give the same in english first then explain same in gujarati too .
Keep answer in simple words , normal english itself .

Introduction to Cybersecurity
● Introduction to Cyber Space - Computers, Internet &
World Wide Web :- Definition, Use, Advantages
● Need & Importance of Cyber Security in daily life
● Cyber Ethics :- Definition, Key Principal
● Digital Citizenship :- Definition, Key Components
● Cyber Threats
○ Phishing
○ Malware :- Virus, Worm, Trojan
○ Fake Messages and Scams
○ Identity Theft
○ Social Engineering
○ Juice Jacking
● CIA Triad- Confidentiality, Integrity, Availability
● Current Issues and challenges of cyber security

give hte answer into the gujarati + english mix language tiself
"""

async def test_provider(name, config, prompt):
    print(f"\n--- Testing {name} with Syllabus Prompt ---")
    try:
        provider = AzureProvider(
            model_name=config["model_name"],
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            model_type=config.get("model_type")
        )
        print(f"Initialized provider with type: {provider.model_type}")
        
        msgs = [{"role": "user", "content": prompt}]
        
        # We will iterate safely as it's async generator if 'stream' is default, 
        # but here the provider.chat() usually returns a complete response object in non-streaming mode if implemented that way or we assume we await it.
        # Checking AzureProvider.chat implementation: it's async and returns ChatResponse.
        
        response = await provider.chat(msgs)
        
        print(f"\nResponse Length: {len(response.content)} chars")
        print("\n--- RESPONSE START ---\n")
        print(response.content[:2000] + "... [TRUNCATED] ..." if len(response.content) > 2000 else response.content)
        print("\n--- RESPONSE END ---\n")

    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_provider("GPT-5 Mini", GPT5_CONFIG, PROMPT)

if __name__ == "__main__":
    asyncio.run(main())
