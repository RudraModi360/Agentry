# Agentry Examples

This folder contains examples for each type of agent in the Agentry framework.

## Agent Types

| Agent | File | Description |
|-------|------|-------------|
| **Agent** | `default_agent_example.py` | Full-featured agent with all default tools |
| **SmartAgent** | `smart_agent_example.py` | Enhanced reasoning, 5 tools, project memory |
| **BasicAgent** | `basic_agent_example.py` | Generic wrapper for custom tools |
| **CopilotAgent** | `copilot_agent_example.py` | Coding-focused agent |

## Quick Comparison

| Feature | Agent | SmartAgent | BasicAgent | CopilotAgent |
|---------|-------|------------|------------|--------------|
| Tools | All (30+) | 5 essential | Custom only | Coding tools |
| Memory | Basic | Project memory | None | Basic |
| Purpose | General | Reasoning + Learning | Custom use cases | Coding |
| Complexity | High | Medium | Low | Medium |

## Running Examples

```bash
# From the Scratchy directory
python examples/default_agent_example.py
python examples/smart_agent_example.py
python examples/basic_agent_example.py
python examples/copilot_agent_example.py
```

## Choosing the Right Agent

1. **Use Agent** when you need full access to filesystem, documents, office tools
2. **Use SmartAgent** when you want enhanced reasoning with persistent learning
3. **Use BasicAgent** when you want to create a custom agent with your own tools
4. **Use CopilotAgent** when working on coding tasks
