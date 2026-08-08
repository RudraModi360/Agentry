"""
End-to-end test: Agent runs code_execute, TOOL_OUTPUT events reach consumer.

Simulates the full pipeline:
  LLM returns code_execute tool call → agent executes → prints "hi" →
  TOOL_OUTPUT events emitted → consumer sees them → final result contains output.
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logicore.stream.events import StreamEvent, StreamEventType
from logicore.stream.emitter import StreamEmitter
from logicore.gateway.base import NormalizedMessage, ProviderGateway
from logicore.agent.chat_orchestrator import ChatOrchestrator


# ── Fake Gateway: returns code_execute tool call, then final answer ────────

class FakeGateway(ProviderGateway):
    """Returns a code_execute tool call on first turn, final answer on second."""

    def __init__(self):
        self._turn = 0

    async def chat(self, messages, tools=None, max_tokens=None):
        return await self.chat_stream(messages, tools=tools)

    async def chat_stream(self, messages, tools=None, on_token=None, on_event=None, max_tokens=None):
        self._turn += 1
        if self._turn == 1:
            # First turn: call code_execute with a simple print
            code = 'print("hi from subprocess")'
            return NormalizedMessage(
                role="assistant",
                content="",
                tool_calls=[{
                    "id": "call_001",
                    "type": "function",
                    "function": {
                        "name": "code_execute",
                        "arguments": json.dumps({"code": code}),
                    },
                }],
            )
        else:
            # Second turn: final answer
            return NormalizedMessage(
                role="assistant",
                content="Done. The subprocess printed successfully.",
                tool_calls=[],
            )


# ── Fake Agent (minimal, just enough for ChatOrchestrator) ─────────────────

class FakeSession:
    def __init__(self):
        self.messages = []
        self.metadata = {}
        self.corrections_made = []
        self.tool_results_history = []
        self.recovery_state = type("RS", (), {"reset_for_turn": lambda s: None})()

    def add_message(self, msg):
        self.messages.append(msg)

    def add_tool_result(self, *a, **kw):
        pass


class FakeAgent:
    def __init__(self):
        self.gateway = FakeGateway()
        self.callbacks = {
            "on_token": None, "on_tool_start": None,
            "on_tool_end": None, "on_final_message": None,
        }
        self.supports_tools = True
        self.disabled_tools = set()
        self.internal_tools = []
        self.tool_executor = None  # set below
        self.context_engine = None  # set below
        self._reasoning_controller = None
        self.telemetry_enabled = False
        self.execution_log = []
        self._task_manager = None
        self.provider = type("P", (), {"provider_name": "fake"})()
        self.model_name = "fake-model"
        self.max_iterations = 10
        self._sessions = {}
        self._loop_engine = None

    def get_session(self, sid):
        if sid not in self._sessions:
            self._sessions[sid] = FakeSession()
        return self._sessions[sid]

    def _serialize_tool_result_for_model(self, name, result):
        return str(result.get("content", ""))

    def _build_reminder_routing_hint(self, *a):
        return None

    def _normalize_tool_paths(self, session, name, args):
        return args

    def _is_reminder_like_request(self, *a):
        return False

    def _has_unverified_reminder_claim(self, *a):
        return False

    def _update_tool_directory_context(self, *a):
        return None

    def _generate_execution_summary(self):
        return "summary"


class FakeContextEngine:
    def inject_hint(self, messages, hint):
        pass

    def remove_hint(self, messages, hint):
        pass

    async def prepare_messages(self, messages, session_id=None):
        return None, messages

    @property
    def token_estimator(self):
        class _Est:
            def count_messages_tokens(self, msgs):
                return 1000
        return _Est()


# ── Test ────────────────────────────────────────────────────────────────────

async def test_tool_output_events():
    print("=" * 60)
    print("E2E TEST: Agent runs code_execute, TOOL_OUTPUT events flow")
    print("=" * 60)

    # Wire up real tool executor with the real code_execute tool
    from logicore.tools.registry import registry
    from logicore.agent.tool_executor import ToolExecutor
    from logicore.tools.execution import CodeExecuteTool

    agent = FakeAgent()
    agent.context_engine = FakeContextEngine()

    tool_executor = ToolExecutor(debug=True)
    tool_executor.set_auto_approve(True)  # skip approval prompt
    agent.tool_executor = tool_executor

    # Register the REAL CodeExecuteTool directly (not via lambda wrapper)
    real_tool = CodeExecuteTool()
    tool_executor.custom_tool_executors["code_execute"] = lambda **kw: real_tool.run(**kw)

    orchestrator = ChatOrchestrator(agent=agent, debug=True)

    # Collect events
    collected = []
    em = StreamEmitter(session_id="test-e2e")

    orig_emit = em.emit
    def record(ev):
        collected.append(ev)
        orig_emit(ev)
    em.emit = record

    # Run
    final = await orchestrator.run(
        user_input="run a python print",
        session_id="test-e2e",
        emitter=em,
    )

    # Analyze
    event_types = [e.type for e in collected]
    tool_output_events = [e for e in collected if e.type == StreamEventType.TOOL_OUTPUT]

    print(f"\nFinal result: {final!r}")
    print(f"Total events: {len(collected)}")
    print(f"Event types: {[str(t) for t in event_types]}")
    print(f"TOOL_OUTPUT events: {len(tool_output_events)}")
    for ev in tool_output_events:
        print(f"  [{ev.data.get('stream')}] {ev.data.get('line')}")

    # Assertions
    assert StreamEventType.RUN_START in event_types, "RUN_START missing"
    assert StreamEventType.TOOL_CALL_START in event_types, "TOOL_CALL_START missing"
    assert StreamEventType.TOOL_OUTPUT in event_types, "TOOL_OUTPUT missing — events not reaching consumer!"
    assert StreamEventType.TOOL_CALL_END in event_types, "TOOL_CALL_END missing"
    assert StreamEventType.DONE in event_types, "DONE missing"
    assert len(tool_output_events) >= 1, f"Expected >= 1 TOOL_OUTPUT, got {len(tool_output_events)}"

    # Verify the subprocess output was captured
    all_output = " ".join(e.data.get("line", "") for e in tool_output_events)
    assert "hi from subprocess" in all_output, f"Expected 'hi from subprocess' in output, got: {all_output!r}"

    print("\n" + "=" * 60)
    print("ALL ASSERTIONS PASSED — TOOL_OUTPUT events flow end-to-end!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tool_output_events())
