"""
Telemetry Monitor — token usage, cost tracking, performance metrics.

Shows:
  - Agent(telemetry=True) for full tracking
  - agent.telemetry property for usage summary
  - TelemetryTracker for per-session metrics
  - Token pricing estimation
  - Per-turn performance breakdown

Run:
    python examples/08_advanced/telemetry_monitor.py
"""

from __future__ import annotations
import argparse, asyncio, json
from logicore import Agent


def print_telemetry(agent: Agent, label: str = ""):
    """Pretty-print telemetry data."""
    t = agent.telemetry
    print(f"\n{'=' * 50}")
    if label:
        print(f"  {label}")
    print(f"  Model:          {t.get('model', '?')}")
    print(f"  Provider:       {t.get('provider', '?')}")
    print(f"  Input tokens:   {t.get('input_tokens', 0):,}")
    print(f"  Output tokens:  {t.get('output_tokens', 0):,}")
    print(f"  Total tokens:   {t.get('total_tokens', 0):,}")
    print(f"  API calls:      {t.get('api_calls', 0)}")
    if t.get("tracker_summary"):
        summary = t["tracker_summary"]
        print(f"  Sessions:       {summary.get('total_sessions', '?')}")
        print(f"  Avg tokens/turn: {summary.get('avg_tokens_per_turn', '?')}")
    print(f"{'=' * 50}")


async def run(provider: str, model: str):
    agent = Agent(
        provider=provider,
        model=model,
        telemetry=True,
        debug=False,
        tools=[],  # No tools — pure LLM telemetry
    )

    print(f"Telemetry Monitor  |  Model: {model}")
    print("Type 'quit' to exit, 'stats' to see current telemetry\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        if msg.lower() == "stats":
            print_telemetry(agent, "Current Session")
            continue

        response = await agent.chat(msg)
        print(f"\nBot: {response}")
        print_telemetry(agent, "After last turn")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    args = parser.parse_args()
    asyncio.run(run(args.provider, args.model))


if __name__ == "__main__":
    main()
