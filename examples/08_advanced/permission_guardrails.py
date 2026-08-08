"""
Permission & Guardrails — tool approval and anti-repetition.

Shows:
  - PermissionMode: AUTO, PLAN, BYPASS
  - ToolCallGuardrailController config (warn/block thresholds)
  - Approval workflows for dangerous tools
  - Anti-repetition circuit breaker
  - auto_approve_all flag

Run:
    python examples/08_advanced/permission_guardrails.py
"""

from __future__ import annotations
import argparse, asyncio
from logicore import Agent
from logicore.agent.permissions import PermissionMode


async def run(provider: str, model: str, mode: str):
    agent = Agent(
        provider=provider,
        model=model,
        debug=True,
        max_iterations=15,
    )

    # Configure permission mode
    if mode == "auto":
        agent.tool_executor.auto_approve_all = True
        print("[permissions] AUTO mode — all tools auto-approved")
    elif mode == "bypass":
        agent.tool_executor.auto_approve_all = True
        print("[permissions] BYPASS mode — all tools auto-approved (no guardrails)")
    else:
        print("[permissions] DEFAULT mode — approval required for dangerous tools")

    # Configure guardrails
    gc = agent._chat_orchestrator.tool_guardrails
    if gc:
        print(f"[guardrails] Exact failure warn/block: {gc.config.exact_failure_warn_after}/{gc.config.exact_failure_block_after}")
        print(f"[guardrails] No-progress warn/block: {gc.config.no_progress_warn_after}/{gc.config.no_progress_block_after}")
        print(f"[guardrails] Same-tool warn/halt: {gc.config.same_tool_failure_warn_after}/{gc.config.same_tool_failure_halt_after}")

    print(f"\nAgent: permissions demo  |  Mode: {mode}")
    print("Try asking to delete/execute files to see approval flow")
    print("Type 'quit' to exit\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit"):
            break

        response = await agent.chat(msg)
        print(f"\nBot: {response}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="gpt-oss:20b-cloud")
    parser.add_argument("--mode", default="default",
                       choices=["default", "auto", "bypass"],
                       help="Permission mode")
    args = parser.parse_args()
    asyncio.run(run(args.provider, args.model, args.mode))


if __name__ == "__main__":
    main()
