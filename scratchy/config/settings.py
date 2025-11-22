import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key(provider: str):
    if provider == "groq":
        return os.getenv("GROQ_API_KEY")
    elif provider == "gemini":
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    elif provider == "openai":
        return os.getenv("OPENAI_API_KEY")
    return None
