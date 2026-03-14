# Skills: Reusable Tool Collections

A **Skill** is a bundle of related tools and domain knowledge, packaged for reuse.

Think of skills like professional certifications:
- A data scientist has the "Data Analysis" skill
- A developer has the "Code Review" skill
- A writer has the "Content Creation" skill

Logicore lets you build these and reuse them across agents.

---

## Why Skills?

### Problem: Too Many Tools

```python
agent = Agent(custom_tools=[
    read_file, write_file, list_files, delete_file,  # Files
    web_search, fetch_url, extract_images,            # Web
    run_python, run_shell, debug_code,                # Execution
    query_sql, load_csv, validate_data,               # Data
    plot_chart, generate_report, analyze_stats,       # Analysis
    # ... 30+ more tools
])

# LLM is confused! Which tool to use? What do they do?
```

### Solution: Group Into Skills

```python
file_skill = FileOperationSkill()        # Read, write, delete
web_skill = WebResearchSkill()           # Search, fetch, extract
code_skill = CodeExecutionSkill()        # Run Python, debug
data_skill = DataManipulationSkill()     # Query, load, validate
analysis_skill = AnalysisSkill()         # Plot, report, analyze

agent = Agent(skills=[
    file_skill,
    web_skill,
    code_skill,
    data_skill,
    analysis_skill
])

# Much clearer! LLM sees 5 skills instead of 30 tools
```

---

## Built-in Skills

Logicore includes pre-built skills:

### FileOperationSkill
```python
from logicore.skills import FileOperationSkill

agent = Agent(skills=[FileOperationSkill()])

# Now has: read_file, write_file, list_files, search_files, delete_file
response = agent.chat("Find all Python files and list them")
```

### WebResearchSkill
```python
from logicore.skills import WebResearchSkill

agent = Agent(skills=[WebResearchSkill()])

# Now has: web_search, fetch_url, extract_links, image_search
response = agent.chat("Search for latest AI research")
```

### CodeExecutionSkill
```python
from logicore.skills import CodeExecutionSkill

agent = Agent(skills=[CodeExecutionSkill()])

# Now has: execute_python, run_shell, debug_code
response = agent.chat("Write Python code that calculates factorial")
```

### DataAnalysisSkill
```python
from logicore.skills import DataAnalysisSkill

agent = Agent(skills=[DataAnalysisSkill()])

# Now has: load_csv, query_sql, clean_data, plot_chart, analyze_stats
response = agent.chat("Analyze this dataset and find trends")
```

### DocumentProcessingSkill
```python
from logicore.skills import DocumentProcessingSkill

agent = Agent(skills=[DocumentProcessingSkill()])

# Now has: parse_pdf, read_docx, extract_images, ocr
response = agent.chat("Extract text from this PDF")
```

---

## Creating Custom Skills

### Basic Skill

```python
from logicore.skills import Skill
from logicore import tool

class SecurityAuditSkill(Skill):
    name = "security_audit"
    description = "Security vulnerability scanning and reporting"
    
    @tool
    def scan_dependencies(self, project_path: str) -> str:
        """Scan dependencies for known vulnerabilities."""
        # Implementation
        return "Scanning complete..."
    
    @tool
    def check_secrets(self, directory: str) -> str:
        """Check for exposed secrets in code."""
        # Implementation
        return "Secret scan complete..."
    
    @tool
    def audit_permissions(self, path: str) -> str:
        """Audit file permissions for security issues."""
        # Implementation
        return "Permission audit complete..."

# Use it
agent = Agent(skills=[SecurityAuditSkill()])
response = agent.chat("Audit this project for security issues")
```

### Skill with Configuration

```python
class DataEngineeringSkill(Skill):
    name = "data_engineering"
    
    def __init__(self, database_url: str, api_key: str):
        self.db_url = database_url
        self.api_key = api_key
        super().__init__()
    
    @tool
    def query_database(self, sql: str) -> str:
        """Execute SQL query against database."""
        # Uses self.db_url
        return query_db(self.db_url, sql)
    
    @tool
    def transform_data(self, data: str, transformation: str) -> str:
        """Apply transformation to data."""
        return apply_transform(data, transformation)

# Create with config
skill = DataEngineeringSkill(
    database_url="postgres://localhost/mydb",
    api_key="sk-..."
)
agent = Agent(skills=[skill])
```

### Skill as a Collection

```python
from logicore.skills import Skill

class MarketingSkill(Skill):
    name = "marketing"
    description = "Content and campaign management"
    
    # Bundle existing tools
    def __init__(self):
        self.tools = [
            write_post_tool,
            schedule_tweet_tool,
            analyze_metrics_tool,
            generate_email_copy_tool,
        ]

agent = Agent(skills=[MarketingSkill()])
```

---

## Skill Composition

Combine skills for powerful agents:

```python
from logicore.skills import (
    FileOperationSkill,
    CodeExecutionSkill,
    WebResearchSkill,
    DataAnalysisSkill,
)

# Software engineer agent
dev_agent = Agent(
    role="software_engineer",
    skills=[
        FileOperationSkill(),
        CodeExecutionSkill(),
        WebResearchSkill(),  # Search for solutions
    ]
)

# Data analyst agent
analyst_agent = Agent(
    role="data_analyst",
    skills=[
        FileOperationSkill(),
        DataAnalysisSkill(),
        WebResearchSkill(),  # Search for context
    ]
)

# DevOps agent
devops_agent = Agent(
    role="devops_engineer",
    skills=[
        FileOperationSkill(),
        CodeExecutionSkill(),
        # Custom: infrastructure tools
    ]
)
```

---

## Skill Packages (Sharing Skills)

Package and distribute skills:

```python
# mycompany_skills/__init__.py

from logicore.skills import Skill

class CompanyDataSkill(Skill):
    """Access internal company data systems."""
    name = "company_data"
    
    @tool
    def query_crm(self, query: str) -> str:
        """Query company CRM."""
        return query_crm_api(query)
    
    @tool
    def get_employee_info(self, employee_id: str) -> str:
        """Get employee information."""
        return employees_service.get(employee_id)

class CompanyAuthSkill(Skill):
    """Handle company authentication."""
    name = "company_auth"
    
    @tool
    def authenticate_user(self, username: str) -> str:
        """Authenticate user against company directory."""
        return auth_service.authenticate(username)

__all__ = ["CompanyDataSkill", "CompanyAuthSkill"]
```

Use in your agents:

```python
from mycompany_skills import CompanyDataSkill, CompanyAuthSkill

agent = Agent(
    skills=[
        CompanyDataSkill(api_key="..."),
        CompanyAuthSkill(domain="company.com"),
    ]
)
```

---

## Skill Discovery

List available skills:

```python
from logicore.skills import BUILTIN_SKILLS

for skill_name, skill_class in BUILTIN_SKILLS.items():
    print(f"{skill_name}: {skill_class.description}")

# Output:
# file_operations: Read, write, and manage files
# web_research: Search the web and fetch URLs
# code_execution: Execute Python and shell code
# data_analysis: Analyze and visualize data
# document_processing: Parse PDFs and documents
```

Dynamic skill loading:

```python
from logicore.skills import load_skill

# Load skill by name
skill = load_skill("data_analysis")

agent = Agent(skills=[skill])
```

---

## Best Practices

✅ **DO:**
- Group related tools into one skill
- Give skills clear, descriptive names
- Document what each skill does
- Keep skills focused (do one thing well)
- Reuse built-in skills when possible
- Share skills with your team

❌ **DON'T:**
- Mix unrelated tools in one skill
- Create nested skills (skills of skills)
- Give skills vague names
- Put 100 tools in one skill
- Duplicate built-in skills
- Leave skills undocumented

---

## Example: Complete Skill

```python
from logicore.skills import Skill
from logicore import tool

class BlogAuthorSkill(Skill):
    """Complete skill for blog authoring and publishing."""
    
    name = "blog_author"
    description = "Write, edit, and publish blog posts"
    version = "1.0.0"
    
    def __init__(self, wordpress_api_key: str):
        self.api_key = wordpress_api_key
        super().__init__()
    
    @tool
    def search_topic(self, topic: str) -> str:
        """Research a topic for blog post."""
        results = google_search(topic)
        return format_results(results)
    
    @tool
    def write_draft(self, topic: str, outline: str) -> str:
        """Write initial blog post draft."""
        # Use LLM to write
        draft = generate_blog_draft(topic, outline)
        return draft
    
    @tool
    def edit_post(self, content: str, style: str) -> str:
        """Edit post for grammar, tone, and style."""
        edited = grammar_check(content)
        styled = apply_style(edited, style)
        return styled
    
    @tool
    def add_images(self, post_id: str, topic: str) -> str:
        """Add relevant images to post."""
        images = search_images(topic)
        add_to_post(post_id, images)
        return "Images added"
    
    @tool
    def publish(self, post_id: str) -> str:
        """Publish post to WordPress."""
        result = wordpress_api.publish(post_id, self.api_key)
        return f"Published: {result['url']}"

# Use it
skill = BlogAuthorSkill(wordpress_api_key="...")
agent = Agent(role="blog_writer", skills=[skill])

response = agent.chat("""
Write and publish a blog post about:
- Topic: "The Future of AI"
- Target audience: Tech enthusiasts
- Length: ~1500 words
- Style: Professional but accessible
""")
```

---

## Next Steps

- [Memory](memory.md) — Persistent learning
- [Tools](tools.md) — Deep dive into tool creation
- [Guides: Custom Skills](../../guides/custom-skills.md) — Build your own
