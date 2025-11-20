# Contributing to Agentry

Thank you for your interest in contributing to Agentry! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- 🐛 **Report bugs** - Help us identify and fix issues
- 💡 **Suggest features** - Share ideas for new capabilities
- 📝 **Improve documentation** - Help others understand the project
- 🔧 **Submit code** - Fix bugs or implement new features
- ✅ **Write tests** - Improve code coverage and reliability

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Agentry.git
cd Agentry
```

### 2. Set Up Development Environment

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Create virtual environment and install dependencies
uv venv .venv
uv sync

# Install development dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff black mypy
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## 📝 Development Guidelines

### Code Style

We follow these standards:

- **PEP 8** for Python code style
- **Black** for automatic code formatting
- **Ruff** for fast linting
- **Type hints** for better code clarity

Before committing, run:

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Project Structure

```
src/
├── agents/          # Agent orchestration
├── providers/       # LLM provider implementations
├── tools/           # Tool implementations
│   ├── base.py      # Base tool class
│   ├── registry.py  # Tool registration
│   └── *.py         # Individual tool modules
└── config/          # Configuration management
```

### Adding a New Tool

1. Create a new file in `src/tools/`:

```python
# src/tools/my_tool.py
from typing import Any
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult

class MyToolParams(BaseModel):
    """Parameters for MyTool."""
    param1: str = Field(..., description="Description of param1")
    param2: int = Field(default=10, description="Description of param2")

class MyTool(BaseTool):
    """Description of what this tool does."""
    
    name = "my_tool"
    description = "Brief description for the LLM"
    args_schema = MyToolParams

    def run(self, param1: str, param2: int = 10) -> ToolResult:
        """
        Execute the tool logic.
        
        Args:
            param1: Description
            param2: Description
            
        Returns:
            ToolResult with success status and content/error
        """
        try:
            # Your implementation here
            result = f"Processed {param1} with {param2}"
            return ToolResult(success=True, content=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

2. Register it in `src/tools/registry.py`:

```python
from .my_tool import MyTool

class ToolRegistry:
    def _register_defaults(self):
        # ... existing tools ...
        self.register_tool(MyTool())

# Add to appropriate category
SAFE_TOOLS = [..., 'my_tool']  # or APPROVAL_REQUIRED_TOOLS or DANGEROUS_TOOLS
```

3. Write tests in `tests/tools/test_my_tool.py`:

```python
import pytest
from src.tools.my_tool import MyTool

def test_my_tool_success():
    tool = MyTool()
    result = tool.run(param1="test", param2=5)
    assert result['success'] is True
    assert "test" in result['content']

def test_my_tool_error():
    tool = MyTool()
    # Test error cases
    pass
```

### Adding a New Provider

1. Create a new file in `src/providers/`:

```python
# src/providers/my_provider.py
from typing import List, Dict, Any, Optional
from .base import LLMProvider

class MyProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        # Initialize your client here

    async def chat(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """
        Send chat request to the provider.
        
        Returns:
            Normalized message dict with 'content' and optional 'tool_calls'
        """
        # Your implementation
        pass

    def get_model_name(self) -> str:
        return self.model_name
```

2. Update `src/main.py` to include your provider in the menu.

## ✅ Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src tests/

# Run specific test file
uv run pytest tests/tools/test_my_tool.py

# Run with verbose output
uv run pytest -v
```

### Writing Tests

- Place tests in `tests/` directory mirroring `src/` structure
- Use descriptive test names: `test_<function>_<scenario>`
- Test both success and failure cases
- Use fixtures for common setup
- Mock external API calls

Example:

```python
import pytest
from unittest.mock import Mock, patch
from src.tools.web import WebSearchTool

@pytest.fixture
def web_search_tool():
    return WebSearchTool()

def test_web_search_general(web_search_tool):
    """Test general web search returns results."""
    result = web_search_tool.run(
        user_input="Python programming",
        search_type="general"
    )
    assert result['success'] is True
    assert 'content' in result

@patch('src.tools.web.DuckDuckGoSearchRun')
def test_web_search_error(mock_ddg, web_search_tool):
    """Test web search handles errors gracefully."""
    mock_ddg.return_value.invoke.side_effect = Exception("Network error")
    result = web_search_tool.run(user_input="test")
    assert result['success'] is False
    assert 'error' in result
```

## 📋 Pull Request Process

### Before Submitting

1. **Update documentation** - README, docstrings, comments
2. **Add tests** - Ensure new code is tested
3. **Run linters** - `black`, `ruff`, `mypy`
4. **Run tests** - All tests should pass
5. **Update CHANGELOG** - Add entry for your changes (if applicable)

### PR Guidelines

1. **Title**: Clear, concise description
   - ✅ `Add web scraping tool with BeautifulSoup`
   - ❌ `Update code`

2. **Description**: Include:
   - What changed and why
   - Related issue number (if applicable)
   - Testing performed
   - Screenshots (for UI changes)

3. **Commits**: 
   - Keep commits atomic and focused
   - Write clear commit messages
   - Use conventional commits format:
     ```
     feat: add new tool for X
     fix: resolve issue with Y
     docs: update README with Z
     test: add tests for W
     ```

### Example PR Description

```markdown
## Description
Adds a new web scraping tool that uses BeautifulSoup to extract structured data from HTML pages.

## Related Issue
Closes #42

## Changes
- Added `WebScrapeTool` in `src/tools/web_scrape.py`
- Registered tool in registry with SAFE_TOOLS category
- Added comprehensive tests in `tests/tools/test_web_scrape.py`
- Updated README with tool documentation

## Testing
- [x] All existing tests pass
- [x] New tests added and passing
- [x] Manually tested with multiple websites
- [x] Linting passes

## Screenshots
N/A
```

## 🐛 Reporting Bugs

Use the [GitHub Issues](https://github.com/RudraModi360/Agentry/issues) page.

Include:
- **Clear title** - Summarize the issue
- **Description** - What happened vs. what you expected
- **Steps to reproduce** - Detailed steps
- **Environment** - OS, Python version, provider used
- **Logs/Screenshots** - Any relevant output
- **Possible solution** - If you have ideas

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
1. Run command '...'
2. Select provider '...'
3. Enter prompt '...'
4. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- Provider: [e.g., Ollama with llama3.1]
- Version: [e.g., v0.1.0]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other relevant information.
```

## 💡 Suggesting Features

Use [GitHub Discussions](https://github.com/RudraModi360/Agentry/discussions) for feature ideas.

Include:
- **Use case** - Why is this needed?
- **Proposed solution** - How should it work?
- **Alternatives** - Other approaches considered
- **Additional context** - Examples, mockups, etc.


## 🎓 Learning Resources

### Python & Async
- [Python Async/Await](https://realpython.com/async-io-python/)
- [Type Hints](https://docs.python.org/3/library/typing.html)

### LLM & AI
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)

### Project Tools
- [uv Documentation](https://github.com/astral-sh/uv)
- [Pytest Guide](https://docs.pytest.org/)
- [Ruff Linter](https://docs.astral.sh/ruff/)

## 🙏 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Credited in commit history

## 📞 Questions?

- **GitHub Discussions** - For general questions
- **GitHub Issues** - For bug reports
- **Email** - [rudramodi9560@gmail.com](mailto:rudramodi9560@gmail.com)

---

Thank you for contributing to Agentry! 🚀

Every contribution, no matter how small, helps make this project better.
