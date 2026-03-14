# Your First Agent: A Step-by-Step Guide

Let's build a real-world agent together.

---

## What We're Building

A **PDF Analyzer Agent** that:
1. Takes a PDF file path
2. Extracts and analyzes content  
3. Generates a summary and key insights
4. Saves results to a file

**Time:** 15 minutes | **Difficulty:** Beginner

---

## Prerequisites

```bash
# Install Logicore with tools
pip install logicore[all]

# Set up your LLM
export GROQ_API_KEY=gsk_...  # or your provider
```

---

## Step 1: Create the Agent

Create `pdf_analyzer.py`:

```python
from logicore import Agent
from logicore.providers import GroqProvider

# Create agent
agent = Agent(
    provider=GroqProvider(model="llama-3.3-70b-versatile"),
    role="document_analyst"
)

print("✓ Agent created")
```

Run it:
```bash
python pdf_analyzer.py
```

---

## Step 2: Add PDF Parsing Tool

```python
from logicore import Agent, tool
from logicore.providers import GroqProvider

@tool
def analyze_pdf(file_path: str) -> str:
    """Read and analyze a PDF file."""
    try:
        # Use built-in PDF parser
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return f"PDF Content ({len(text)} chars):\n{text[:2000]}..."
    except Exception as e:
        return f"Error reading PDF: {e}"

@tool
def save_analysis(filename: str, content: str) -> str:
    """Save analysis results to file."""
    with open(filename, 'w') as f:
        f.write(content)
    return f"Saved to {filename}"

agent = Agent(
    provider=GroqProvider(model="llama-3.3-70b-versatile"),
    role="document_analyst",
    custom_tools=[analyze_pdf, save_analysis]
)

print("✓ Tools added")
```

---

## Step 3: Process a PDF

```python
from logicore import Agent, tool
from logicore.providers import GroqProvider

@tool
def analyze_pdf(file_path: str) -> str:
    """Read and analyze a PDF file."""
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:5]:  # First 5 pages
                text += page.extract_text()
        return f"PDF Content:\n{text[:3000]}"
    except Exception as e:
        return f"Error: {e}"

@tool
def save_analysis(filename: str, content: str) -> str:
    """Save analysis results to file."""
    with open(filename, 'w') as f:
        f.write(content)
    return f"Saved analysis to {filename}"

agent = Agent(
    provider=GroqProvider(model="llama-3.3-70b-versatile"),
    role="document_analyst",
    custom_tools=[analyze_pdf, save_analysis]
)

# Process a PDF
pdf_file = "sample.pdf"  # Replace with your PDF

response = agent.chat(f"""
Please:
1. Analyze the content of {pdf_file}
2. Provide a 3-line summary
3. List 5 key insights
4. Save the analysis to 'analysis_result.txt'
""")

print(response)
```

---

## Step 4: Add Memory

Remember analyses across sessions:

```python
from logicore import Agent, tool
from logicore.providers import GroqProvider

@tool
def analyze_pdf(file_path: str) -> str:
    """Analyze a PDF file."""
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:5]:
                text += page.extract_text()
        return f"PDF Content:\n{text[:3000]}"
    except Exception as e:
        return f"Error: {e}"

@tool
def save_analysis(filename: str, content: str) -> str:
    """Save analysis to file."""
    with open(filename, 'w') as f:
        f.write(content)
    return f"Saved to {filename}"

# Enable memory
agent = Agent(
    provider=GroqProvider(model="llama-3.3-70b-versatile"),
    role="document_analyst",
    custom_tools=[analyze_pdf, save_analysis],
    memory=True  # ← New!
)

# Session 1
pdf_file = "report.pdf"
agent.chat(f"Analyze {pdf_file} please")
agent.chat("Save the results")

# Later... new Python process
agent2 = Agent(
    provider=GroqProvider(model="llama-3.3-70b-versatile"),
    role="document_analyst",
    memory=True
)

# Agent remembers!
response = agent2.chat("What PDF did I analyze before?")
print(response)  # "You analyzed report.pdf"
```

---

## Step 5: Add Error Handling

Make it production-ready:

```python
from logicore import Agent, tool
from pathlib import Path

@tool
def analyze_pdf(file_path: str) -> str:
    """Analyze a PDF file with validation."""
    # Validate path
    path = Path(file_path)
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if not path.suffix.lower() == '.pdf':
        return f"Error: File is not a PDF: {file_path}"
    
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) == 0:
                return "Error: PDF has no pages"
            
            text = ""
            for page in reader.pages[:5]:
                text += page.extract_text()
        
        return f"PDF Analysis:\n{text[:3000]}"
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

@tool
def save_analysis(filename: str, content: str) -> str:
    """Save analysis with validation."""
    try:
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully saved to {filename}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

from logicore import Agent
from logicore.providers import GroqProvider

agent = Agent(
    provider=GroqProvider(model="llama-3.3-70b-versatile"),
    role="document_analyst",
    custom_tools=[analyze_pdf, save_analysis],
    memory=True,
    debug=True  # Show tool calls
)

# Safe usage
try:
    response = agent.chat("""
    Analyze 'sample.pdf' and save insights to 'results.txt'
    """)
    print(response)
except Exception as e:
    print(f"Agent error: {e}")
```

---

## Step 6: Test Different Providers

```python
from logicore import Agent
from logicore.providers import GroqProvider, OllamaProvider, GeminiProvider

# Same tools work with any provider
def create_analyzer(provider_name: str):
    providers = {
        "groq": GroqProvider(model="llama-3.3-70b-versatile"),
        "ollama": OllamaProvider(model="llama3.2"),
        "gemini": GeminiProvider(model="gemini-2.0-flash"),
    }
    
    agent = Agent(
        provider=providers[provider_name],
        role="document_analyst",
        custom_tools=[analyze_pdf, save_analysis]
    )
    return agent

# Try different providers
for provider in ["groq", "ollama", "gemini"]:
    try:
        agent = create_analyzer(provider)
        response = agent.chat("Sample PDF analysis request")
        print(f"✓ {provider}: Works!")
    except Exception as e:
        print(f"✗ {provider}: {e}")
```

---

## Complete Example

Here's the full, production-ready agent:

```python
#!/usr/bin/env python3
"""PDF Analyzer Agent - Complete Example"""

from pathlib import Path
from logicore import Agent, tool
from logicore.providers import GroqProvider

class PDFAnalyzerAgent:
    def __init__(self, provider_name="groq"):
        """Initialize PDF analyzer agent."""
        self.agent = Agent(
            provider=GroqProvider(model="llama-3.3-70b-versatile") 
                if provider_name == "groq" else None,
            role="document_analyst",
            custom_tools=[self.analyze_pdf, self.save_analysis],
            memory=True,
            debug=False
        )
    
    @staticmethod
    @tool
    def analyze_pdf(file_path: str) -> str:
        """Analyze PDF content."""
        path = Path(file_path)
        
        if not path.exists():
            return f"Error: File not found"
        if path.suffix.lower() != '.pdf':
            return f"Error: Not a PDF file"
        
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join(
                    page.extract_text() 
                    for page in reader.pages[:10]
                )
            return f"Extracted {len(text)} characters from PDF"
        except Exception as e:
            return f"Error: {e}"
    
    @staticmethod
    @tool
    def save_analysis(filename: str, content: str) -> str:
        """Save analysis results."""
        try:
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Saved to {filename}"
        except Exception as e:
            return f"Error: {e}"
    
    def analyze(self, pdf_path: str, output_file: str = None):
        """Analyze a PDF and optionally save results."""
        prompt = f"Analyze {pdf_path} and provide summary and key insights"
        
        if output_file:
            prompt += f". Then save to {output_file}"
        
        return self.agent.chat(prompt)

# Usage
if __name__ == "__main__":
    analyzer = PDFAnalyzerAgent()
    
    result = analyzer.analyze(
        pdf_path="document.pdf",
        output_file="analysis.txt"
    )
    
    print(result)
```

---

## Next Steps

- **Multi-Provider**: [Run same agent with different LLMs](multi-provider-patterns.md)
- **Tool Integration**: [Create more specialized tools](tool-integration.md)
- **Production**: [Deploy your agent](../guides/production-deployment.md)
- **Memory**: [Advanced memory management](../concepts/memory.md)

---

## Common Issues

**"Module not found: PyPDF2"**
```bash
pip install PyPDF2
```

**"API key not found"**
```bash
export GROQ_API_KEY=gsk_...
```

**"Tool not called by agent"**
→ Make sure tool description is clear (agent needs to understand what it does)

**"Memory not persisting"**
→ Make sure `memory=True` is set and you're using same `role`

---

## Need Help?

- 💬 [Discord Community](https://discord.gg/logicore)
- 🐛 [GitHub Issues](https://github.com/RudraModi360/Logicore/issues)
