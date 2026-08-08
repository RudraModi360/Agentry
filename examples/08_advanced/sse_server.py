"""
SSE Server — Server-Sent Events streaming for web frontends.

Shows:
  - as_sse() converting StreamEvent to SSE frames
  - events_to_sse() for batch conversion
  - SSE_DONE sentinel frame
  - StreamEmitter usage pattern
  - How to integrate with any HTTP framework

Run:
    python examples/08_advanced/sse_server.py
    # Then open browser to http://localhost:8000

Requires: pip install aiohttp
"""

from __future__ import annotations
import argparse, asyncio, json, os
from aiohttp import web

from logicore import Agent
from logicore.stream.sse import as_sse, events_to_sse, SSE_DONE
from logicore.stream.events import StreamEventType


# ── Agent setup ────────────────────────────────────────────────────────────

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = Agent(provider="ollama", model="gpt-oss:20b-cloud")
    return _agent


# ── SSE endpoint ───────────────────────────────────────────────────────────

async def handle_chat(request):
    """SSE endpoint: GET /chat?message=hello"""
    message = request.query.get("message", "")
    if not message:
        return web.Response(text="Missing 'message' parameter", status=400)

    agent = get_agent()
    run_result = await agent.stream_run(message)

    async def event_stream():
        async for ev in run_result.stream_events():
            yield as_sse(ev)
        yield SSE_DONE

    return web.StreamResponse(
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def handle_chat_page(request):
    """Simple HTML page for testing SSE."""
    html = """<!DOCTYPE html>
<html><head><title>Logicore SSE Test</title></head>
<body>
<h1>Logicore SSE Streaming Test</h1>
<input id="msg" placeholder="Type a message..." style="width:400px" />
<button onclick="send()">Send</button>
<pre id="output"></pre>
<script>
function send() {
    const msg = document.getElementById('msg').value;
    const output = document.getElementById('output');
    output.textContent = '';
    const es = new EventSource('/chat?message=' + encodeURIComponent(msg));
    es.onmessage = (e) => {
        if (e.data === '[DONE]') { es.close(); return; }
        try {
            const ev = JSON.parse(e.data);
            if (ev.type === 'token') output.textContent += ev.data.delta || '';
            else if (ev.type === 'tool_call_start') output.textContent += '\\n[tool] ' + (ev.data.name || '') + '\\n';
        } catch(err) { output.textContent += e.data; }
    };
    es.onerror = () => { es.close(); output.textContent += '\\n[connection closed]'; };
}
</script></body></html>"""
    return web.Response(text=html, content_type="text/html")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    app = web.Application()
    app.router.add_get("/", handle_chat_page)
    app.router.add_get("/chat", handle_chat)

    print(f"SSE Server running at http://{args.host}:{args.port}")
    print(f"  Open http://localhost:{args.port} in browser")
    print(f"  Or curl: curl -N 'http://localhost:{args.port}/chat?message=hello'")
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
