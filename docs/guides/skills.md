---
title: Skills Guide
description: Building and using reusable skill packages
---

# Skills Guide

Skills are reusable capability packages that bundle tools, instructions, and examples. This guide covers skill creation, management, and usage.

## What is a Skill?

A skill is a directory containing:

```
my-skill/
├── SKILL.md          # Instructions and metadata
├── examples/         # Example usage
├── scripts/          # Executable scripts
├── templates/        # Prompt templates
└── validation_rules/ # Validation logic
```

## Using Built-in Skills

### Loading Skills

```python
# Load single skill
agent.load_skill("excel_operations")

# Load multiple skills
agent.load_skills(["excel_operations", "pdf_operations"])

# Load from skill index
agent.load_skill_from_index("excel")
```

### Managing Skills

```python
# List available skills
skills = agent.list_available_skills()

# Enable/disable
agent.disable_skill("excel_operations")
agent.enable_skill("excel_operations")

# Unload
agent.unload_skill("excel_operations")
```

### Available Built-in Skills

| Skill | Description |
|-------|-------------|
| `excel_operations` | Read/write Excel files |
| `pdf_operations` | PDF manipulation |
| `powerpoint_operations` | PowerPoint presentations |
| `word_operations` | Word documents |

## Creating Custom Skills

### Step 1: Create Directory

```bash
mkdir my-custom-skill
cd my-custom-skill
```

### Step 2: Create SKILL.md

```markdown
---
name: web-research
description: Web research and information gathering
version: 1.0.0
author: Your Name
tags:
  - research
  - web
  - information
trigger: "when the user asks to research a topic"
cost_tier: medium
min_framework_version: "1.0.0"
requires: []
conflicts_with: []
---

# Web Research Skill

This skill enables agents to research topics using web search.

## Capabilities

### search_web
Search the web for information.

**Usage:**
```
search_web(query="python asyncio tutorial")
```

**Parameters:**
- `query` (string): Search query
- `num_results` (integer): Number of results (default: 5)

### fetch_url
Fetch content from a URL.

**Usage:**
```
fetch_url(url="https://example.com")
```

## Examples

### Basic Research
```
User: Research Python async frameworks
Agent: [uses search_web] Found 5 relevant articles...
```

### Deep Dive
```
User: Get detailed information from this article: https://...
Agent: [uses fetch_url] The article discusses...
```

## Validation Rules

- URLs must be valid HTTP/HTTPS
- Search queries must be at least 3 characters
- Maximum 10 results per search
```

### Step 3: Create Examples Directory

```bash
mkdir examples
```

Create example files:

```python
# examples/basic_research.py
"""Example: Basic web research"""

query = "Python asyncio tutorial"
num_results = 5

# Expected behavior:
# 1. Agent calls search_web with query
# 2. Returns list of relevant URLs
# 3. Agent summarizes findings
```

### Step 4: Create Scripts Directory (Optional)

```bash
mkdir scripts
```

```python
# scripts/validate_url.py
"""Validate a URL before fetching"""
import re

def validate_url(url: str) -> bool:
    """Validate HTTP/HTTPS URL."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))
```

## Skill Structure

### SKILL.md Frontmatter

```yaml
---
name: skill-name
description: Brief description
version: 1.0.0
author: Author Name
tags:
  - tag1
  - tag2
trigger: "when to use this skill"
cost_tier: low|medium|high
min_framework_version: "1.0.0"
requires:
  - other-skill
conflicts_with:
  - conflicting-skill
---
```

### Capabilities Section

Document each tool/capability:

```markdown
## Capabilities

### tool_name
Description of what this tool does.

**Usage:**
```
tool_name(param1="value1", param2="value2")
```

**Parameters:**
- `param1` (type): Description
- `param2` (type): Description (default: value)
```

### Examples Section

Provide usage examples:

```markdown
## Examples

### Example 1: Title
```
User: User input
Agent: [tool_call] Tool output
Agent: Final response
```
```

## Skill Loader

### Discovery

```python
from logicore.skills import SkillLoader

# Discover all skills in a directory
skills = SkillLoader.discover("/path/to/skills")

# Load specific skill
skill = SkillLoader.load("/path/to/skills/my-skill")

# Load with dependencies
skills = SkillLoader.load_skill_graph("/path/to/skills/my-skill")
```

### Skill Index

Create a `SKILL_INDEX.md` for fast discovery:

```markdown
# Skill Index

## Available Skills

### excel_operations
- **Path**: defaults/excel_operations
- **Tags**: excel, spreadsheet, data
- **Trigger**: when user asks to work with Excel files

### pdf_operations
- **Path**: defaults/pdf_operations
- **Tags**: pdf, document, manipulation
- **Trigger**: when user asks to work with PDF files
```

## Agent-Skill Integration

### Automatic Tool Registration

When a skill is loaded, its tools are automatically registered:

```python
agent.load_skill("excel_operations")

# Tools from the skill are now available
# Agent can call them without explicit registration
```

### Skill Prompt Injection

Skills inject instructions into the system prompt:

```python
# The agent's system prompt is automatically updated
# with skill instructions when loaded
```

### Skill Dependencies

```yaml
requires:
  - base-tools  # Must load base-tools first
conflicts_with:
  - legacy-excel  # Cannot use with legacy-excel
```

## Skill Management

### Listing Skills

```python
# List loaded skills
loaded = agent.list_available_skills()

# List by tag
excel_skills = [s for s in loaded if "excel" in s.tags]
```

### Toggling Skills

```python
# Disable without unloading
agent.disable_skill("excel_operations")

# Re-enable
agent.enable_skill("excel_operations")
```

### Dependency Resolution

```python
# Load with automatic dependency resolution
skills = SkillLoader.load_skill_graph("my-skill")

# Check dependencies
skill = SkillLoader.load("my-skill")
if skill.dependencies_met:
    agent.load_skill(skill)
```

## Best Practices

1. **Clear Trigger**: Define when the skill should be used
2. **Good Examples**: Provide realistic usage examples
3. **Validation**: Include validation rules for inputs
4. **Documentation**: Document all parameters and return values
5. **Dependencies**: Declare required skills
6. **Versioning**: Use semantic versioning

## Next Steps

- [Built-in Skills Reference](../api/skills.md)
- [Skill Examples](../examples/skills/)
- [Custom Skill Tutorial](../tutorials/custom-skill.md)
- [Skills API](../api/skills.md)
