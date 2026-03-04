"""
Agentry Telemetry Module
Comprehensive token usage tracking with detailed breakdown per session.

Features:
- Token counting per request and session
- Detailed token breakdown (system, tools, files, messages, tool_results)
- Context window usage percentage calculation
- Response time tracking and percentiles
- Tool call monitoring
- Per-session isolation
- Detailed metrics export

Usage:
    tracker = TelemetryTracker(enabled=True)
    tracker.record_request(
        session_id="user123",
        input_tokens=150,
        output_tokens=75,
        model="gpt-4",
        provider="openai",
        duration_ms=1200,
        token_breakdown=TokenBreakdown(
            system_instructions=50,
            tool_definitions=30,
            messages=70
        )
    )
    summary = tracker.get_session_summary("user123")
    print(summary["token_breakdown"]["percentages"])
"""

import statistics
from typing import Dict, Set, Optional, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime


class ContextWindowFetcher:
    """
    Fetches context window sizes from cloud providers dynamically.
    Caches results to avoid repeated API calls.
    """
    
    def __init__(self):
        self._cache: Dict[str, int] = {}
        self._fetchers: Dict[str, Callable] = {}
        self._setup_default_fetchers()
    
    def _setup_default_fetchers(self):
        """Setup default fetcher functions for known providers."""
        self._fetchers["openai"] = self._fetch_openai
        self._fetchers["anthropic"] = self._fetch_anthropic
        self._fetchers["google"] = self._fetch_google
        self._fetchers["groq"] = self._fetch_groq
        self._fetchers["ollama"] = self._fetch_ollama
    
    def register_fetcher(self, provider: str, fetcher: Callable[[str], Optional[int]]):
        """Register a custom context window fetcher for a provider."""
        self._fetchers[provider] = fetcher
    
    def get_context_window(self, model: str, provider: str) -> int:
        """
        Get context window for a model from cache or by fetching from provider.
        
        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-opus")
            provider: Provider name (e.g., "openai", "anthropic")
        
        Returns:
            Context window size in tokens, or 4096 as fallback
        """
        cache_key = f"{provider}:{model}"
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try to fetch from provider
        if provider in self._fetchers:
            try:
                context_size = self._fetchers[provider](model)
                if context_size:
                    self._cache[cache_key] = context_size
                    return context_size
            except Exception as e:
                print(f"Warning: Failed to fetch context window for {model} from {provider}: {e}")
        
        # Fallback to default
        return 4096
    
    def _fetch_openai(self, model: str) -> Optional[int]:
        """Fetch OpenAI model context window from API."""
        try:
            import openai
            client = openai.OpenAI()
            mod = client.models.retrieve(model)
            # OpenAI typically provides context_window in model object
            if hasattr(mod, 'context_window'):
                return mod.context_window
            # Fallback to known values
            openai_windows = {
                "gpt-4o": 128000,
                "gpt-4-turbo": 128000,
                "gpt-4": 8192,
                "gpt-4-32k": 32768,
                "gpt-3.5-turbo": 4096,
            }
            return openai_windows.get(model)
        except Exception as e:
            # Fallback: return known values
            openai_windows = {
                "gpt-4o": 128000,
                "gpt-4-turbo": 128000,
                "gpt-4": 8192,
                "gpt-4-32k": 32768,
                "gpt-3.5-turbo": 4096,
            }
            return openai_windows.get(model)
    
    def _fetch_anthropic(self, model: str) -> Optional[int]:
        """Fetch Anthropic model context window from API."""
        try:
            import anthropic
            client = anthropic.Anthropic()
            # Anthropic publishes model capabilities
            # Use their known model specs
            anthropic_windows = {
                "claude-3-opus": 200000,
                "claude-3-opus-20240229": 200000,
                "claude-3-sonnet": 200000,
                "claude-3-sonnet-20240229": 200000,
                "claude-3-haiku": 200000,
                "claude-3-haiku-20240307": 200000,
                "claude-2.1": 100000,
                "claude-2": 100000,
                "claude-instant-1.2": 100000,
            }
            return anthropic_windows.get(model)
        except Exception as e:
            # Fallback
            anthropic_windows = {
                "claude-3-opus": 200000,
                "claude-3-sonnet": 200000,
                "claude-3-haiku": 200000,
                "claude-2": 100000,
                "claude-instant": 100000,
            }
            return anthropic_windows.get(model)
    
    def _fetch_google(self, model: str) -> Optional[int]:
        """Fetch Google Gemini model context window from API."""
        try:
            import google.generativeai as genai
            # List available models and get their specs
            models = genai.list_models()
            for m in models:
                model_name = m.name.split('/')[-1]  # Extract model ID from 'models/gemini-pro'
                if model_name == model or m.name == model:
                    # Try to get input token limit
                    if hasattr(m, 'input_token_limit'):
                        return m.input_token_limit
            
            # Fallback to known values
            google_windows = {
                "gemini-pro": 32000,
                "gemini-1.5-pro": 1000000,
                "gemini-1.5-flash": 1000000,
                "gemini-2.0-flash": 1000000,
            }
            return google_windows.get(model)
        except Exception as e:
            # Fallback to known values
            google_windows = {
                "gemini-pro": 32000,
                "gemini-1.5-pro": 1000000,
                "gemini-1.5-flash": 1000000,
                "gemini-2.0-flash": 1000000,
            }
            return google_windows.get(model)
    
    def _fetch_groq(self, model: str) -> Optional[int]:
        """
        Fetch Groq model context window from API.
        
        Uses Groq's models API: https://console.groq.com/docs/models#get-all-available-models
        """
        try:
            from groq import Groq
            client = Groq()
            # Get list of all available models from Groq API
            models_response = client.models.list()
            
            # Iterate through available models
            for m in models_response.data:
                if m.id == model:
                    # Try to get context window from model info
                    if hasattr(m, 'context_window'):
                        return m.context_window
                    # Some models might have context_length instead
                    if hasattr(m, 'context_length'):
                        return m.context_length
            
            # Fallback to known values if not found in API response
            groq_windows = {
                "mixtral-8x7b-32768": 32768,
                "llama-3-70b-8192": 8192,
                "llama-3.1-70b-versatile": 131072,
                "llama-2-7b-chat": 4096,
                "llama-2-13b-chat": 4096,
                "llama-2-70b-chat": 4096,
            }
            return groq_windows.get(model)
        except Exception as e:
            # Fallback to known values if API call fails
            groq_windows = {
                "mixtral-8x7b-32768": 32768,
                "llama-3-70b-8192": 8192,
                "llama-3.1-70b-versatile": 131072,
                "llama-2-7b-chat": 4096,
            }
            return groq_windows.get(model)
    
    def _fetch_ollama(self, model: str) -> Optional[int]:
        """Fetch Ollama model context window from local instance."""
        try:
            import ollama
            # Get model info from local Ollama instance
            info = ollama.show(model)
            # Extract context window from parameters
            if "parameters" in info and "num_ctx" in info["parameters"]:
                return info["parameters"]["num_ctx"]
            return None
        except Exception as e:
            # Fallback: return default, Ollama is local
            return 4096
    
    def clear_cache(self):
        """Clear the context window cache."""
        self._cache.clear()


# Global context window fetcher instance
_context_fetcher = ContextWindowFetcher()


@dataclass
class TokenBreakdown:
    """Token distribution across different components."""
    system_instructions: int = 0  # System prompts and instructions
    tool_definitions: int = 0      # Tool/function definitions
    file_content: int = 0           # Files uploaded or included
    messages: int = 0               # Chat messages
    tool_results: int = 0           # Results from tool calls
    other: int = 0                  # Any other tokens

    @property
    def total(self) -> int:
        """Total tokens across all categories."""
        return (
            self.system_instructions
            + self.tool_definitions
            + self.file_content
            + self.messages
            + self.tool_results
            + self.other
        )

    def to_dict(self) -> dict:
        """Export as dictionary with percentages."""
        total = self.total
        if total == 0:
            return {
                "system_instructions": 0,
                "tool_definitions": 0,
                "file_content": 0,
                "messages": 0,
                "tool_results": 0,
                "other": 0,
                "total": 0,
                "percentages": {
                    "system_instructions": 0.0,
                    "tool_definitions": 0.0,
                    "file_content": 0.0,
                    "messages": 0.0,
                    "tool_results": 0.0,
                    "other": 0.0,
                }
            }

        return {
            "system_instructions": self.system_instructions,
            "tool_definitions": self.tool_definitions,
            "file_content": self.file_content,
            "messages": self.messages,
            "tool_results": self.tool_results,
            "other": self.other,
            "total": total,
            "percentages": {
                "system_instructions": round(
                    (self.system_instructions / total) * 100, 1
                ),
                "tool_definitions": round(
                    (self.tool_definitions / total) * 100, 1
                ),
                "file_content": round(
                    (self.file_content / total) * 100, 1
                ),
                "messages": round(
                    (self.messages / total) * 100, 1
                ),
                "tool_results": round(
                    (self.tool_results / total) * 100, 1
                ),
                "other": round(
                    (self.other / total) * 100, 1
                ),
            }
        }


@dataclass
class RequestMetrics:
    """Metrics for a single LLM request."""
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    provider: str
    duration_ms: float
    token_breakdown: TokenBreakdown = field(default_factory=TokenBreakdown)
    tool_calls: int = 0
    error: Optional[str] = None


@dataclass
class SessionMetrics:
    """Cumulative metrics for a session."""
    session_id: str
    model: str = "unknown"
    provider: str = "unknown"
    context_window: int = 0
    
    # Token totals
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    cumulative_token_breakdown: TokenBreakdown = field(default_factory=TokenBreakdown)
    
    # Request metrics
    total_requests: int = 0
    total_tool_calls: int = 0
    total_errors: int = 0
    
    # Timing metrics
    total_duration_ms: float = 0.0
    response_times_ms: List[float] = field(default_factory=list)
    
    # Session tracking
    started_at: Optional[datetime] = None
    last_request_at: Optional[datetime] = None
    requests: List[RequestMetrics] = field(default_factory=list)

    def _get_context_window(self) -> int:
        """Get context window for the model by fetching from provider."""
        return _context_fetcher.get_context_window(self.model, self.provider)

    @property
    def context_used_percent(self) -> float:
        """Percentage of context window used."""
        window = self._get_context_window()
        if window == 0:
            return 0.0
        return round((self.total_tokens / window) * 100, 2)

    @property
    def avg_response_time_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests

    @property
    def median_response_time_ms(self) -> float:
        if not self.response_times_ms:
            return 0.0
        return statistics.median(self.response_times_ms)

    @property
    def p95_response_time_ms(self) -> float:
        if len(self.response_times_ms) < 2:
            return self.avg_response_time_ms
        sorted_times = sorted(self.response_times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def avg_tokens_per_request(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_tokens / self.total_requests

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.total_errors / self.total_requests) * 100

    def to_dict(self) -> dict:
        """Export session metrics as a dictionary."""
        duration_secs = round(self.total_duration_ms / 1000, 1) if self.total_duration_ms else 0
        context_window = self._get_context_window()
        
        return {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            
            # Context Information
            "context": {
                "window_size": context_window,
                "used_tokens": self.total_tokens,
                "used_percent": self.context_used_percent,
                "remaining_tokens": max(0, context_window - self.total_tokens),
            },
            
            # Token Breakdown & Percentages
            "token_breakdown": self.cumulative_token_breakdown.to_dict(),
            
            # Token Metrics
            "tokens": {
                "input": self.total_input_tokens,
                "output": self.total_output_tokens,
                "total": self.total_tokens,
                "avg_per_request": round(self.avg_tokens_per_request, 1),
            },
            
            # Request Metrics
            "requests": {
                "total": self.total_requests,
                "tool_calls": self.total_tool_calls,
                "errors": self.total_errors,
                "error_rate_percent": round(self.error_rate, 2),
            },
            
            # Performance Metrics
            "performance": {
                "total_duration_seconds": duration_secs,
                "avg_response_time_ms": round(self.avg_response_time_ms, 1),
                "median_response_time_ms": round(self.median_response_time_ms, 1),
                "p95_response_time_ms": round(self.p95_response_time_ms, 1),
            },
            
            # Timestamps
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None,
        }



class TelemetryTracker:
    """
    Tracks token usage with detailed breakdown per session.
    
    Usage:
        tracker = TelemetryTracker(enabled=True)
        breakdown = TokenBreakdown(
            system_instructions=50,
            tool_definitions=30,
            messages=70,
            file_content=0,
            tool_results=0
        )
        tracker.record_request(
            session_id="session1",
            input_tokens=100,
            output_tokens=50,
            model="gpt-4o",
            provider="openai",
            duration_ms=1200,
            token_breakdown=breakdown
        )
        summary = tracker.get_session_summary("session1")
        print(summary["token_breakdown"]["percentages"])
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sessions: Dict[str, SessionMetrics] = {}

    def register_context_fetcher(self, provider: str, fetcher: Callable[[str], Optional[int]]):
        """
        Register a custom context window fetcher for a provider.
        
        Args:
            provider: Provider name (e.g., "custom_provider")
            fetcher: Function that takes model name and returns context window size
                    Should return None if model not found
        
        Example:
            def fetch_custom_context(model: str) -> Optional[int]:
                '''Fetch from your cloud provider API'''
                response = requests.get(f'https://api.provider.com/models/{model}')
                return response.json().get('context_window')
            
            tracker.register_context_fetcher('custom_provider', fetch_custom_context)
        """
        _context_fetcher.register_fetcher(provider, fetcher)

    def _get_session(self, session_id: str) -> SessionMetrics:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMetrics(
                session_id=session_id,
                started_at=datetime.now()
            )
        return self.sessions[session_id]

    def record_request(
        self,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "unknown",
        provider: str = "unknown",
        duration_ms: float = 0.0,
        token_breakdown: Optional[TokenBreakdown] = None,
        tool_calls: int = 0,
        error: Optional[str] = None,
    ):
        """
        Record metrics for a single LLM request.
        
        Args:
            session_id: Unique session identifier
            input_tokens: Total input tokens
            output_tokens: Total output tokens
            model: Model name (used to determine context window)
            provider: Provider name (openai, anthropic, etc.)
            duration_ms: Request duration in milliseconds
            token_breakdown: TokenBreakdown object with category breakdown
            tool_calls: Number of tool calls made
            error: Error message if request failed
        """
        if not self.enabled:
            return

        now = datetime.now()
        total = input_tokens + output_tokens

        if token_breakdown is None:
            token_breakdown = TokenBreakdown(messages=total)

        request = RequestMetrics(
            timestamp=now,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            model=model,
            provider=provider,
            duration_ms=duration_ms,
            token_breakdown=token_breakdown,
            tool_calls=tool_calls,
            error=error,
        )

        session = self._get_session(session_id)
        session.model = model
        session.provider = provider
        session.total_input_tokens += input_tokens
        session.total_output_tokens += output_tokens
        session.total_tokens += total
        session.total_requests += 1
        session.total_tool_calls += tool_calls
        session.total_duration_ms += duration_ms
        session.response_times_ms.append(duration_ms)
        session.last_request_at = now

        if error:
            session.total_errors += 1

        # Accumulate token breakdown
        session.cumulative_token_breakdown.system_instructions += (
            token_breakdown.system_instructions
        )
        session.cumulative_token_breakdown.tool_definitions += (
            token_breakdown.tool_definitions
        )
        session.cumulative_token_breakdown.file_content += token_breakdown.file_content
        session.cumulative_token_breakdown.messages += token_breakdown.messages
        session.cumulative_token_breakdown.tool_results += token_breakdown.tool_results
        session.cumulative_token_breakdown.other += token_breakdown.other

        session.requests.append(request)

    def get_session_summary(self, session_id: str) -> dict:
        """Get detailed telemetry summary for a specific session."""
        if session_id not in self.sessions:
            return {
                "session_id": session_id,
                "total_requests": 0,
                "message": "Session not found"
            }
        return self.sessions[session_id].to_dict()

    def get_total_summary(self) -> dict:
        """Get aggregate telemetry across all sessions."""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "total_requests": 0,
                "total_tokens": 0,
                "message": "No sessions recorded"
            }

        total_breakdown = TokenBreakdown()
        aggregate = {
            "total_sessions": len(self.sessions),
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "total_requests": 0,
            "total_tool_calls": 0,
            "total_duration_ms": 0.0,
            "models_used": set(),
            "providers_used": set(),
        }

        for session in self.sessions.values():
            aggregate["total_input_tokens"] += session.total_input_tokens
            aggregate["total_output_tokens"] += session.total_output_tokens
            aggregate["total_tokens"] += session.total_tokens
            aggregate["total_requests"] += session.total_requests
            aggregate["total_tool_calls"] += session.total_tool_calls
            aggregate["total_duration_ms"] += session.total_duration_ms
            aggregate["models_used"].add(session.model)
            aggregate["providers_used"].add(session.provider)

            total_breakdown.system_instructions += (
                session.cumulative_token_breakdown.system_instructions
            )
            total_breakdown.tool_definitions += (
                session.cumulative_token_breakdown.tool_definitions
            )
            total_breakdown.file_content += (
                session.cumulative_token_breakdown.file_content
            )
            total_breakdown.messages += session.cumulative_token_breakdown.messages
            total_breakdown.tool_results += (
                session.cumulative_token_breakdown.tool_results
            )
            total_breakdown.other += session.cumulative_token_breakdown.other

        aggregate["models_used"] = list(aggregate["models_used"])
        aggregate["providers_used"] = list(aggregate["providers_used"])
        aggregate["avg_response_time_ms"] = round(
            aggregate["total_duration_ms"] / aggregate["total_requests"], 1
        ) if aggregate["total_requests"] > 0 else 0.0
        aggregate["total_duration_ms"] = round(aggregate["total_duration_ms"], 1)
        aggregate["token_breakdown"] = total_breakdown.to_dict()

        return aggregate

    def get_session_ids(self) -> List[str]:
        """Get list of all session IDs."""
        return list(self.sessions.keys())

    def reset(self, session_id: str = None):
        """Reset telemetry data for a session or all sessions."""
        if session_id:
            self.sessions.pop(session_id, None)
        else:
            self.sessions.clear()
