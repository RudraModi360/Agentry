"""
Skills Agent — using the logicore skills system.

Shows:
  - BasicAgent with skills=[...] parameter
  - SkillLoader discovery from ~/.agents/skills/
  - load_skill() / list_available_skills() runtime API
  - How skills inject capabilities + system prompt sections
  - The 2-tier lazy loading pattern (SKILL_INDEX.md -> SKILL.md)

Run:
    python examples/06_skills/skill_agent.py
    python examples/06_skills/skill_agent.py --list-skills
"""

from __future__ import annotations
import argparse, os, json, asyncio
from logicore import BasicAgent
from logicore.skills import SkillLoader


def list_available_skills():
    """Discover and print all available skills."""
    search_paths = []

    # Default skills directory
    defaults_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "logicore", "skills", "defaults"
    )
    if os.path.exists(defaults_dir):
        search_paths.append(defaults_dir)

    # User workspace skills
    home = os.path.expanduser("~")
    for sub in [".agents/skills", ".logicore/skills"]:
        path = os.path.join(home, sub)
        if os.path.exists(path):
            search_paths.append(path)

    print("Available Skills:")
    print("=" * 50)
    for sp in search_paths:
        if os.path.isdir(sp):
            for item in os.listdir(sp):
                skill_dir = os.path.join(sp, item)
                if os.path.isdir(skill_dir):
                    skill_file = os.path.join(skill_dir, "SKILL.md")
                    index_file = os.path.join(sp, "SKILL_INDEX.md")
                    if os.path.exists(skill_file):
                        print(f"  - {item} (from {sp})")
                    elif os.path.exists(index_file):
                        print(f"  - {item} (indexed in {sp})")
    print()


async def run_skill_agent(provider: str, model: str):
    agent = BasicAgent(
        name="SkillAgent",
        description="Agent with dynamically loaded skills",
        tools=[],  # Start with no tools, skills add capabilities
        provider=provider,
        model=model,
    )

    # Try to load skills from default location
    try:
        skills = SkillLoader.discover(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logicore", "skills", "defaults"
            )
        )
        for skill in skills[:5]:  # Load first 5
            agent.load_skill(skill)
            print(f"  Loaded skill: {skill.name}")
    except Exception as e:
        print(f"  Skill loading: {e}")

    print(f"\nAgent: {agent.name}")
    loaded = agent._agent.list_available_skills()
    print(f"Skills loaded: {len(loaded)}")
    for s in loaded:
        print(f"  - {s['name']}: {s.get('description', 'N/A')[:60]}")

    print("\nType 'quit' to exit\n")

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
    parser.add_argument("--list-skills", action="store_true", help="List available skills and exit")
    args = parser.parse_args()

    if args.list_skills:
        list_available_skills()
        return

    asyncio.run(run_skill_agent(args.provider, args.model))


if __name__ == "__main__":
    main()
