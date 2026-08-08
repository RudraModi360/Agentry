"""
Final demo: Agent + persisted session management + persistent memory.

What this shows
--------------
- Session management: chat history is saved to the 3-tier storage under
  ~/.logicore (DB + snapshot). Re-running the script RESUMES the same session
  automatically (memories of past turns are restored).
- Persistent memory: the MemoryManager learns from each conversation and
  recalls relevant past context on future turns (stored under ~/.logicore/memory).
- Live streaming: TOKEN, REASONING, TOOL_CALL_START, TOOL_CALL_END, and
  TOOL_OUTPUT events are printed in real time with color formatting.

How to run
----------
    # Local Ollama
    python scripts/smart_agent_demo.py --provider ollama --model qwen3:0.6b

    # Groq (API key from env or --api-key)
    python scripts/smart_agent_demo.py --provider groq --model llama-3.3-70b-versatile

    # Custom endpoint (e.g. OpenAI-compatible proxy)
    python scripts/smart_agent_demo.py --provider openai --model gpt-4 \
        --api-key sk-... --endpoint https://my-proxy.com/v1

Type `quit` to exit.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logicore import Agent
from logicore.storage import create_storage
from logicore.memory.manager import MemoryManager
from logicore.stream.events import StreamEventType
from logicore.utils.colors import (
    colored, error, tool_call, tool_result, info,
    DIM, RESET, GRAY, BLUE, GREEN, RED,
)


# ── Streaming event handler ────────────────────────────────────────────────

def make_stream_handler():
    """Returns an on_event callback that prints streaming events nicely."""
    in_thinking = [False]

    def on_event(ev):
        if ev.type == StreamEventType.TOKEN:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False
            print(ev.data.get("delta", ""), end="", flush=True)

        elif ev.type == StreamEventType.REASONING:
            if not in_thinking[0]:
                print(GRAY, end="", flush=True)
                in_thinking[0] = True
            print(ev.data.get("delta", ""), end="", flush=True)

        elif ev.type == StreamEventType.TOOL_CALL_START:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False
            name = ev.data.get("name", "?")
            args = ev.data.get("args", {})
            print(f"\n{tool_call(name)}({json.dumps(args)[:100]})", flush=True)

        elif ev.type == StreamEventType.TOOL_CALL_END:
            preview = str(ev.data.get("preview", ""))[:280]
            print(f" {tool_result(ev.data.get('success'), preview)}", flush=True)

        elif ev.type == StreamEventType.TOOL_OUTPUT:
            stream = ev.data.get("stream", "stdout")
            line = ev.data.get("line", "")
            if stream == "stderr":
                print(f"{DIM}[stderr]{RESET} {line}", flush=True)
            else:
                print(line, flush=True)

        elif ev.type == StreamEventType.ERROR:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False
            print(f"\n{error('[error]')} {ev.data.get('message')}", flush=True)

        elif ev.type == StreamEventType.DONE:
            if in_thinking[0]:
                print(RESET, end="", flush=True)
                in_thinking[0] = False

    return on_event


# ── Main ───────────────────────────────────────────────────────────────────

async def main(provider: str, model: str, api_key: str = None, endpoint: str = None):
    # (1) Storage-backed persistence (sessions live under ~/.logicore)
    storage = create_storage()
    agent = Agent(
        provider=provider,
        model=model or None,
        api_key=api_key,
        endpoint=endpoint,
        storage=storage,
        debug=True,
        max_iterations=100,
        telemetry=True,
    )

    # (2) Resume an existing persisted session if present
    SESSION_ID = agent.create_session()
    print(f"[session] using session '{SESSION_ID}'")

    # (3) Attach persistent memory (standalone subsystem, driven per turn)
    memory = MemoryManager(
        llm_provider=provider,
        llm_model=model,
    )
    await memory.start()

    on_event = make_stream_handler()

    try:
        while True:
            try:
                msg = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not msg or msg.lower() in ("quit", "exit"):
                break

            # Recall relevant past memories, then run the turn
            messages = [{"role": "user", "content": msg}]
            messages = await memory.inject_context(
                messages, user_input=msg, use_llm_selection=True
            )

            run = await agent.stream_run(
                messages,
                session_id=SESSION_ID,
            )
            try:
                async for ev in run.stream_events():
                    on_event(ev)
            except asyncio.CancelledError:
                pass
            resp = await run
            print()

            # Persist what we learned from this turn
            await memory.submit_for_extraction(
                messages + [{"role": "assistant", "content": resp}],
                session_id=SESSION_ID,
            )
            if memory.worker:
                await memory.worker._extraction_queue.join()
    finally:
        await memory.stop()
        storage.shutdown()
        print("\n[done] session + memory state saved under ~/.logicore")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agent demo with sessions + persistent memory"
    )
    parser.add_argument("--provider", default=os.environ.get("PROVIDER", "ollama"))
    parser.add_argument("--model", default=os.environ.get("MODEL", "gemma4:cloud"))
    parser.add_argument("--api-key", default=os.environ.get("API_KEY"),
                        help="API key for cloud providers (or set API_KEY env var)")
    parser.add_argument("--endpoint", default=os.environ.get("ENDPOINT"),
                        help="Custom endpoint URL for providers (or set ENDPOINT env var)")
    args = parser.parse_args()
    asyncio.run(main(args.provider, args.model, args.api_key, args.endpoint))
