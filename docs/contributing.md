---
title: Contributing
description: Development setup and contribution guidelines
---

# Contributing to Logicore

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Ollama (for local testing)

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```env
# For testing with Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434

# For testing with cloud providers (optional)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
GROQ_API_KEY=gsk_...
```

## Project Structure

```
Agentry/
├── logicore/              # Main package
│   ├── agent/            # Agent classes
│   ├── config/           # Configuration
│   ├── gateway/          # Provider gateway
│   ├── memory/           # Memory system
│   ├── mcp/              # MCP integration
│   ├── providers/        # LLM providers
│   ├── skills/           # Skills system
│   ├── storage/          # Storage backends
│   ├── stream/           # Streaming
│   ├── tasks/            # Task management
│   ├── telemetry/        # Telemetry
│   ├── tools/            # Tool system
│   └── utils/            # Utilities
├── tests/                # Test suite
├── examples/             # Usage examples
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=logiocre

# Run specific test
pytest tests/unit/test_agent.py
```

## Code Style

### Formatting

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

```bash
# Format code
black logicore/
isort logicore/

# Check formatting
black --check logicore/
isort --check-only logicore/

# Lint
flake8 logicore/
```

### Type Hints

Use type hints for all functions:

```python
def process_data(data: List[Dict], limit: int = 10) -> str:
    """Process data and return result."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate(expression: str, precision: int = 2) -> float:
    """Calculate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
        precision: Decimal places for result
    
    Returns:
        Calculation result
    
    Raises:
        ValueError: If expression is invalid
    """
    ...
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write code following the style guidelines
- Add tests for new functionality
- Update documentation if needed

### 3. Run Tests

```bash
# Ensure all tests pass
pytest

# Check formatting
black --check logicore/
isort --check-only logicore/
```

### 4. Commit

```bash
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: resolve bug in X"
```

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Pull Request Guidelines

### PR Title

Use conventional commits format:
```
feat: add Excel skill support
fix: resolve session persistence issue
docs: update API reference
```

### PR Description

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## Adding a New Provider

1. Create `logicore/providers/your_provider.py`:

```python
from logicore.providers.base import LLMProvider

class YourProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
    
    async def complete(self, messages, model=None, **kwargs):
        # Implement completion
        ...
    
    async def stream(self, messages, model=None, **kwargs):
        # Implement streaming
        ...
```

2. Register in `logicore/providers/factory.py`:

```python
PROVIDER_REGISTRY["your_provider"] = YourProvider
```

3. Add tests in `tests/unit/test_providers.py`

4. Update documentation

## Adding a New Tool

1. Create `logicore/tools/your_tool.py`:

```python
from logicore.tools.base import BaseTool, ToolResult

class YourTool(BaseTool):
    name = "your_tool"
    description = "Description of what it does"
    
    def __init__(self, ...):
        # Initialize
        ...
    
    async def run(self, param1: str, param2: int = 10) -> ToolResult:
        """Run the tool.
        
        Args:
            param1: Description
            param2: Description (default: 10)
        """
        try:
            # Your implementation
            result = ...
            return ToolResult(success=True, content=str(result))
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def is_read_only(self) -> bool:
        return True  # or False
```

2. Register in `logicore/tools/registry.py`:

```python
TOOL_CLASSES["your_tool"] = YourTool
```

3. Add tests

4. Update documentation

## Adding a New Skill

1. Create directory `logicore/skills/defaults/your_skill/`:

```
your_skill/
├── SKILL.md
├── examples/
└── validation_rules/
```

2. Write SKILL.md with metadata and instructions

3. Add examples

4. Update skill index

5. Add tests

6. Update documentation

## Reporting Issues

### Bug Reports

Include:
- Python version
- Logicore version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error traceback

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered

## Getting Help

- **Discord**: [Join the server](https://discord.gg/Yz8yFzgQ)
- **GitHub Issues**: [Report bugs](https://github.com/RudraModi360/Agentry/issues)
- **Discussions**: [Ask questions](https://github.com/RudraModi360/Agentry/discussions)

## Code of Conduct

- Be respectful
- Be constructive
- Be inclusive
- Focus on the code

Thank you for contributing!
