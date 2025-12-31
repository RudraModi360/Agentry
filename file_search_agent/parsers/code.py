"""
Code Parser - Intelligent parsing of source code files.
Extracts functions, classes, docstrings, and comments for semantic search.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from .base import BaseParser, ParsedDocument, DocumentChunk


class CodeParser(BaseParser):
    """Parser for source code files with structure-aware chunking."""
    
    supported_extensions = [
        # Python
        ".py", ".pyw", ".pyi",
        # JavaScript/TypeScript
        ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        # Web
        ".html", ".css", ".scss", ".sass", ".less",
        # Systems
        ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
        # JVM
        ".java", ".kt", ".kts", ".scala", ".groovy",
        # Other
        ".go", ".rs", ".rb", ".php", ".swift", ".m",
        ".r", ".R", ".jl", ".lua", ".pl", ".pm",
        # Shell
        ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
        # Config as code
        ".sql", ".graphql", ".gql",
    ]
    
    # Language-specific comment patterns
    COMMENT_PATTERNS = {
        "python": (r'#.*$', r'"""[\s\S]*?"""', r"'''[\s\S]*?'''"),
        "javascript": (r'//.*$', r'/\*[\s\S]*?\*/'),
        "c": (r'//.*$', r'/\*[\s\S]*?\*/'),
        "shell": (r'#.*$',),
        "sql": (r'--.*$', r'/\*[\s\S]*?\*/'),
    }
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse source code with intelligent structure detection."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read with encoding detection
        content = self._read_with_encoding(file_path)
        
        # Detect language
        language = self._detect_language(file_path)
        
        # Extract code elements
        elements = self._extract_code_elements(content, language)
        
        # Create structure-aware chunks
        chunks = self._create_code_chunks(content, elements, language)
        
        file_meta = self.get_file_metadata(file_path)
        
        return ParsedDocument(
            file_path=file_path,
            file_name=file_path.name,
            file_type=f"code/{language}",
            content=content,
            chunks=chunks,
            file_size=file_meta["file_size"],
            created_at=file_meta.get("created_at"),
            modified_at=file_meta.get("modified_at"),
            title=file_path.stem,
            metadata={
                "language": language,
                "line_count": content.count("\n") + 1,
                "elements": {
                    "functions": len(elements.get("functions", [])),
                    "classes": len(elements.get("classes", [])),
                    "imports": len(elements.get("imports", [])),
                }
            }
        )
    
    def _read_with_encoding(self, file_path: Path) -> str:
        """Read file with encoding detection."""
        import chardet
        
        with open(file_path, "rb") as f:
            raw = f.read()
            detected = chardet.detect(raw)
            encoding = detected.get("encoding", "utf-8") or "utf-8"
        
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="replace")
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()
        
        lang_map = {
            ".py": "python", ".pyw": "python", ".pyi": "python",
            ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript",
            ".java": "java", ".kt": "kotlin",
            ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
            ".go": "go", ".rs": "rust", ".rb": "ruby",
            ".php": "php", ".swift": "swift",
            ".sh": "shell", ".bash": "shell",
            ".sql": "sql",
        }
        
        return lang_map.get(ext, "unknown")
    
    def _extract_code_elements(
        self,
        content: str,
        language: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract functions, classes, imports, and comments."""
        elements = {
            "functions": [],
            "classes": [],
            "imports": [],
            "comments": [],
        }
        
        lines = content.split("\n")
        
        if language == "python":
            elements = self._extract_python_elements(lines)
        elif language in ["javascript", "typescript"]:
            elements = self._extract_js_elements(lines)
        elif language == "java":
            elements = self._extract_java_elements(lines)
        
        return elements
    
    def _extract_python_elements(self, lines: List[str]) -> Dict[str, List]:
        """Extract Python code elements."""
        elements = {"functions": [], "classes": [], "imports": [], "comments": []}
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Imports
            if stripped.startswith(("import ", "from ")):
                elements["imports"].append({"line": i + 1, "text": stripped})
            
            # Functions
            elif stripped.startswith("def "):
                match = re.match(r"def\s+(\w+)\s*\(", stripped)
                if match:
                    elements["functions"].append({
                        "line": i + 1,
                        "name": match.group(1),
                        "text": stripped
                    })
            
            # Classes
            elif stripped.startswith("class "):
                match = re.match(r"class\s+(\w+)", stripped)
                if match:
                    elements["classes"].append({
                        "line": i + 1,
                        "name": match.group(1),
                        "text": stripped
                    })
            
            # Comments
            elif stripped.startswith("#"):
                elements["comments"].append({"line": i + 1, "text": stripped})
        
        return elements
    
    def _extract_js_elements(self, lines: List[str]) -> Dict[str, List]:
        """Extract JavaScript/TypeScript elements."""
        elements = {"functions": [], "classes": [], "imports": [], "comments": []}
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Imports
            if stripped.startswith(("import ", "require(")):
                elements["imports"].append({"line": i + 1, "text": stripped})
            
            # Functions
            elif "function " in stripped or re.match(r"(const|let|var)\s+\w+\s*=\s*(async\s*)?\(", stripped):
                elements["functions"].append({"line": i + 1, "text": stripped})
            
            # Classes
            elif stripped.startswith("class "):
                elements["classes"].append({"line": i + 1, "text": stripped})
        
        return elements
    
    def _extract_java_elements(self, lines: List[str]) -> Dict[str, List]:
        """Extract Java elements."""
        elements = {"functions": [], "classes": [], "imports": [], "comments": []}
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith("import "):
                elements["imports"].append({"line": i + 1, "text": stripped})
            elif "class " in stripped:
                elements["classes"].append({"line": i + 1, "text": stripped})
            elif re.match(r"(public|private|protected|static|\s)+\w+\s+\w+\s*\(", stripped):
                elements["functions"].append({"line": i + 1, "text": stripped})
        
        return elements
    
    def _create_code_chunks(
        self,
        content: str,
        elements: Dict[str, List],
        language: str
    ) -> List[DocumentChunk]:
        """Create chunks based on code structure."""
        # For code, we create chunks around logical units (functions, classes)
        # Plus a general chunking fallback
        
        chunks = []
        chunk_index = 0
        
        # Create a summary chunk with imports and structure
        summary_parts = []
        if elements.get("imports"):
            summary_parts.append("Imports: " + ", ".join(
                imp["text"] for imp in elements["imports"][:10]
            ))
        if elements.get("classes"):
            summary_parts.append("Classes: " + ", ".join(
                cls.get("name", cls["text"]) for cls in elements["classes"]
            ))
        if elements.get("functions"):
            summary_parts.append("Functions: " + ", ".join(
                fn.get("name", fn["text"]) for fn in elements["functions"][:20]
            ))
        
        if summary_parts:
            chunks.append(DocumentChunk(
                text="FILE STRUCTURE:\n" + "\n".join(summary_parts),
                chunk_index=chunk_index,
                start_char=0,
                end_char=0,
                metadata={"type": "structure_summary", "language": language}
            ))
            chunk_index += 1
        
        # Then chunk the actual content
        content_chunks = self.chunk_text(
            content,
            metadata={"language": language}
        )
        
        for chunk in content_chunks:
            chunk.chunk_index = chunk_index
            chunks.append(chunk)
            chunk_index += 1
        
        return chunks
