---
layout: default
title: Contributing
nav_order: 10
description: "Guidelines for contributing to Agentry"
---

# Contributing to Agentry

Guidelines for contributing to the Agentry project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Commit Guidelines](#commit-guidelines)
4. [Pull Request Process](#pull-request-process)
5. [Adding New Features](#adding-new-features)
6. [Documentation](#documentation)
7. [Testing Guidelines](#testing-guidelines)
8. [Issue Guidelines](#issue-guidelines)
9. [Code of Conduct](#code-of-conduct)
10. [License](#license)
11. [Contact](#contact)

---

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR-USERNAME/Agentry.git
cd Agentry
```

### Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

---

## Development Workflow

### Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Make Changes

1. Write your code
2. Add tests for new functionality
3. Ensure all tests pass
4. Update documentation if needed

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=agentry
```

### Code Style

Follow PEP 8 guidelines:

```bash
# Format code
black agentry/

# Check style
flake8 agentry/

# Type checking
mypy agentry/
```

---

## Commit Guidelines

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**

| Type | Description |
|:-----|:------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting) |
| `refactor` | Code refactoring |
| `test` | Test additions or changes |
| `chore` | Build process or auxiliary changes |

**Examples:**

```
feat(agent): add streaming response support

fix(ollama): handle connection timeout errors

docs(readme): update installation instructions
```

---

## Pull Request Process

1. **Update your fork:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what was changed and why
   - Link to any related issues

4. **Address review feedback** if requested

5. **Merge** once approved by maintainers

---

## Adding New Features

### Adding a New Provider

1. Create provider file in `agentry/providers/`:

```python
# agentry/providers/new_provider.py
from .base import LLMProvider

class NewProvider(LLMProvider):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
    
    async def chat(self, messages, tools=None):
        # Implementation
        pass
```

2. Add to `agentry/providers/__init__.py`

3. Update agent initialization in `agentry/agents/agent.py`

4. Add tests in `tests/test_providers.py`

5. Update documentation

### Adding a New Tool

1. Create tool file in `agentry/tools/`:

```python
# agentry/tools/new_tool.py

def new_tool(param: str) -> str:
    """Description of what the tool does.
    
    Use this when [describe use case].
    """
    # Implementation
    return result
```

2. Register in `agentry/tools/__init__.py`

3. Add tests in `tests/test_tools.py`

4. Update documentation

---

## Documentation

### Building Docs Locally

```bash
cd docs

# Install Jekyll (requires Ruby)
bundle install

# Serve locally
bundle exec jekyll serve

# Open http://localhost:4000/Agentry/
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Use tables for structured information
- Add images for complex concepts
- Avoid emojis in technical documentation

---

## Testing Guidelines

### Test Structure

```python
import pytest
from agentry import Agent

class TestAgent:
    def test_initialization(self):
        agent = Agent(llm="ollama")
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_chat(self):
        agent = Agent(llm="ollama")
        response = await agent.chat("Hello")
        assert response is not None
```

### Test Categories

| Category | Location | Description |
|:---------|:---------|:------------|
| Unit | `tests/unit/` | Test individual functions |
| Integration | `tests/integration/` | Test component interactions |
| E2E | `tests/e2e/` | Test full workflows |

---

## Issue Guidelines

### Reporting Bugs

Include:
- Python version
- Agentry version
- Operating system
- LLM provider and model
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error traceback

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative approaches considered
- Any related issues

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Report unacceptable behavior to maintainers

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Contact

- **GitHub Issues:** [Report issues](https://github.com/RudraModi360/Agentry/issues)
- **Discussions:** [Community discussions](https://github.com/RudraModi360/Agentry/discussions)
- **Email:** rudramodi9560@gmail.com
