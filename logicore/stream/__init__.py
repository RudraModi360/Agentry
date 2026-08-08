"""
Logicore streaming package.

Public surface:
* :class:`StreamEvent` / :class:`StreamEventType` — the typed event protocol.
* :class:`StreamEmitter` — per-run async event bus.
* :class:`AgentRunResult` — awaitable + async-iterable result of ``Agent.stream_run``.
* :func:`as_sse` / :func:`events_to_sse` — SSE serialization helpers.

See ``docs/concepts/streaming.md`` for the full event model and frontend wiring.
"""

from .events import StreamEvent, StreamEventType, get_current_emitter, set_current_emitter
from .emitter import StreamEmitter
from .result import AgentRunResult
from .sse import as_sse, events_to_sse, SSE_DONE

__all__ = [
    "StreamEvent",
    "StreamEventType",
    "StreamEmitter",
    "AgentRunResult",
    "as_sse",
    "events_to_sse",
    "SSE_DONE",
    "get_current_emitter",
    "set_current_emitter",
]
