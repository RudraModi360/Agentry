import os
from ollama import Client
from openai import OpenAI

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.94.233.40:11434")
MODEL = os.getenv("OLLAMA_MODEL", "lfm2.5-thinking:latest")
QUESTION = "Why is the sky blue?"


def stream_with_ollama_sdk():
    print("=== Ollama SDK Streaming ===")
    client = Client(host=OLLAMA_HOST)
    messages = [{"role": "user", "content": QUESTION}]

    for part in client.chat(MODEL, messages=messages, stream=True):
        print(part.message.content, end="", flush=True)
    print()


def stream_with_openai_sdk():
    print("=== OpenAI SDK Streaming ===")
    client = OpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")
    messages = [{"role": "user", "content": QUESTION}]

    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()


if __name__ == "__main__":
    stream_with_ollama_sdk()
    stream_with_openai_sdk()

