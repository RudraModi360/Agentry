"""
LLM Engine - Handles interactions with various LLM providers.
Supports OpenAI, Anthropic, Azure OpenAI, and Ollama (local).
"""

from typing import List, Optional, Dict, Any, Literal, Generator
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    """A chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a response from a prompt."""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate a response from a chat history."""
        pass
    
    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Stream a response token by token."""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI GPT models."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return self.chat([Message("user", prompt)], **kwargs)
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            **kwargs
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            tokens_used=response.usage.total_tokens if response.usage else None,
            finish_reason=response.choices[0].finish_reason
        )
    
    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicLLM(BaseLLM):
    """Anthropic Claude models."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return self.chat([Message("user", prompt)], **kwargs)
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        # Anthropic requires system message separately
        system_msg = ""
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_msgs.append({"role": m.role, "content": m.content})
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_msg if system_msg else None,
            messages=chat_msgs
        )
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason
        )
    
    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text


class OllamaLLM(BaseLLM):
    """Local LLM using Ollama (free, private)."""
    
    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        import ollama
        self.client = ollama.Client(host=host)
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        response = self.client.generate(model=self.model, prompt=prompt, **kwargs)
        return LLMResponse(
            content=response["response"],
            model=self.model,
            tokens_used=response.get("eval_count"),
            finish_reason="stop"
        )
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        response = self.client.chat(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            **kwargs
        )
        return LLMResponse(
            content=response["message"]["content"],
            model=self.model,
            tokens_used=response.get("eval_count"),
            finish_reason="stop"
        )
    
    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        for chunk in self.client.generate(model=self.model, prompt=prompt, stream=True):
            yield chunk["response"]


class LLMEngine:
    """
    Unified LLM engine supporting multiple providers.
    
    Usage:
        engine = LLMEngine(provider="openai", api_key="...")
        response = engine.generate("Explain quantum computing")
        
        # Streaming
        for token in engine.stream("Tell me a story"):
            print(token, end="")
    """
    
    def __init__(
        self,
        provider: Literal["openai", "anthropic", "ollama"] = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        self.provider = provider
        
        if provider == "openai":
            if not api_key:
                raise ValueError("API key required for OpenAI")
            self._engine = OpenAILLM(api_key, model or "gpt-4o-mini")
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("API key required for Anthropic")
            self._engine = AnthropicLLM(api_key, model or "claude-3-haiku-20240307")
        elif provider == "ollama":
            self._engine = OllamaLLM(model or "llama3.2", kwargs.get("host", "http://localhost:11434"))
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a response from a prompt."""
        return self._engine.generate(prompt, **kwargs)
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate a response from chat messages."""
        return self._engine.chat(messages, **kwargs)
    
    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Stream a response token by token."""
        yield from self._engine.stream(prompt, **kwargs)
    
    def answer_with_context(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Answer a question using provided context (RAG pattern)."""
        default_system = """You are a helpful assistant that answers questions based on the provided context.
If the answer cannot be found in the context, say "I couldn't find this information in the documents."
Always cite which document or section you found the information in."""
        
        messages = [
            Message("system", system_prompt or default_system),
            Message("user", f"""Context:
{context}

Question: {question}

Please answer based on the context above.""")
        ]
        return self._engine.chat(messages)
