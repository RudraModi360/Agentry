"""SmartAgent with persistent memory across sessions."""
import asyncio
import json
from logicore import BasicAgent
from logicore.memory.manager import MemoryManager
from logicore.stream.events import StreamEventType
from logicore.utils.colors import (
    error, tool_call, tool_result,
    DIM, RESET, GRAY,
)


def make_stream_handler():
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
            preview = str(ev.data.get("preview", ""))[:120]
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


async def main():
    memory = MemoryManager(
        llm_provider="ollama",
        llm_model="smollm2:135m",
        throttle_interval=1.0,
        debug=True,
    )
    await memory.start()

    agent = BasicAgent(provider="ollama", model="gpt-oss:20b-cloud", debug=False)
    on_event = make_stream_handler()

    print("SmartAgent with memory ready. Type 'quit' to exit.\n")

    while (msg := input("You: ").strip()) and msg != "quit":
        messages = [{"role": "user", "content": msg}]
        messages = await memory.inject_context(messages, user_input=msg, use_llm_selection=True)
        print(messages)  # --- IGNORE ---

        run = await agent.stream_run(messages)
        try:
            async for ev in run.stream_events():
                on_event(ev)
        except asyncio.CancelledError:
            pass
        resp = await run
        print()

        await memory.submit_for_extraction(
            messages + [{"role": "assistant", "content": resp}],
            session_id="default",
        )
        if memory.worker:
            await memory.worker._extraction_queue.join()
        print("[Memory] Extraction complete.")

    print("[Memory] Flushing pending extractions...")
    if memory.worker:
        await memory.worker._extraction_queue.join()
    await memory.stop()
    print("[Memory] Done.")

asyncio.run(main())
