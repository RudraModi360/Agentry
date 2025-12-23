# Contributing to Agentry

Thank you for your interest in contributing to Agentry! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- **Bug Reports**: Report bugs via [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)
- **Feature Requests**: Suggest new features or improvements
- **Documentation**: Improve or add documentation
- **Code**: Submit bug fixes or new features
- **Examples**: Add usage examples and tutorials

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/Agentry.git
cd Agentry
```

### 2. Set Up Development Environment

```bash
# Install dependencies
uv sync  # or: pip install -r requirements.txt

# Run tests to ensure everything works
python test_Agentry_suite.py
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where possible
- Write docstrings for all public functions and classes
- Keep functions focused and modular

### Example:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    # Implementation
    return True
```

### Testing

- Add tests for new features
- Ensure all existing tests pass
- Test with different LLM providers (Ollama, Groq, Gemini)

```bash
# Run test suite
python test_Agentry_suite.py

# Run command tests
python test_commands.py

# Run robust tests
python check.py
```

### Documentation

- Update relevant documentation in `docs/`
- Add docstrings to new code
- Update README.md if adding major features
- Include usage examples

## 🔄 Pull Request Process

### 1. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature" # or "fix: fix bug"
```

Use conventional commit messages:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to the [original repository](https://github.com/RudraModi360/Agentry)
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:
   - **Description**: What does this PR do?
   - **Motivation**: Why is this change needed?
   - **Testing**: How was this tested?
   - **Screenshots**: If applicable

### 4. Code Review

- Address review comments
- Make requested changes
- Push updates to your branch (PR will update automatically)

## 🎨 Areas for Contribution

### High Priority

- [ ] Additional LLM provider support
- [ ] More built-in tools
- [ ] Performance optimizations
- [ ] Better error messages
- [ ] More examples and tutorials

### Documentation

- [ ] Video tutorials
- [ ] More code examples
- [ ] Architecture deep-dive
- [ ] Best practices guide
- [ ] Troubleshooting guide

### Features

- [ ] Tool marketplace/registry
- [ ] Agent templates
- [ ] Multi-agent orchestration
- [ ] Streaming responses
- [ ] Voice integration

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal code to reproduce the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - OS (Windows/Mac/Linux)
   - Python version
   - Agentry version
   - LLM provider and model

## 💡 Feature Requests

When requesting features:

1. **Use Case**: Describe the problem you're trying to solve
2. **Proposed Solution**: How you envision the feature working
3. **Alternatives**: Other solutions you've considered
4. **Additional Context**: Any other relevant information

## 📞 Questions?

- **Discussions**: [GitHub Discussions](https://github.com/RudraModi360/Agentry/discussions)
- **Email**: rudramodi9560@gmail.com

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards others

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## 🙏 Thank You!

Your contributions make Agentry better for everyone. We appreciate your time and effort!

---

**Built with ❤️ by [Rudra Modi](mailto:rudramodi9560@gmail.com)**

*Evolving towards the future of voice-driven AI assistants*
