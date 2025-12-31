"""
Text Parser - Handles plain text, markdown, JSON, XML, and similar text files.
Includes encoding detection for various file encodings.
"""

from pathlib import Path
from typing import List, Optional
import json
import chardet

from .base import BaseParser, ParsedDocument


class TextParser(BaseParser):
    """Parser for plain text and structured text files."""
    
    supported_extensions = [
        ".txt", ".md", ".markdown", ".rst",  # Plain/markdown
        ".json", ".jsonl",                    # JSON
        ".xml", ".html", ".htm",              # Markup
        ".yaml", ".yml",                      # Config
        ".csv", ".tsv",                       # Tabular
        ".log", ".ini", ".conf", ".cfg",      # Config/logs
    ]
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a text file with automatic encoding detection."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect encoding
        with open(file_path, "rb") as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected.get("encoding", "utf-8") or "utf-8"
        
        # Read content with detected encoding
        try:
            content = raw_data.decode(encoding)
        except UnicodeDecodeError:
            # Fallback to utf-8 with error handling
            content = raw_data.decode("utf-8", errors="replace")
        
        # Process based on file type
        file_ext = file_path.suffix.lower()
        
        if file_ext in [".json", ".jsonl"]:
            content = self._format_json(content)
        elif file_ext in [".xml", ".html", ".htm"]:
            content = self._extract_text_from_markup(content)
        elif file_ext == ".csv":
            content = self._format_csv(content)
        
        # Create chunks
        chunks = self.chunk_text(
            content,
            metadata={"file_type": file_ext, "encoding": encoding}
        )
        
        file_meta = self.get_file_metadata(file_path)
        
        return ParsedDocument(
            file_path=file_path,
            file_name=file_path.name,
            file_type=file_ext.lstrip("."),
            content=content,
            chunks=chunks,
            file_size=file_meta["file_size"],
            created_at=file_meta.get("created_at"),
            modified_at=file_meta.get("modified_at"),
            title=file_path.stem,
            metadata={
                "encoding": encoding,
                "confidence": detected.get("confidence", 0),
                "line_count": content.count("\n") + 1,
            }
        )
    
    def _format_json(self, content: str) -> str:
        """Format JSON for better readability and searchability."""
        try:
            # Try parsing as JSON
            data = json.loads(content)
            
            # Flatten nested structures for better search
            def flatten(obj, prefix=""):
                lines = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        new_key = f"{prefix}.{k}" if prefix else k
                        lines.extend(flatten(v, new_key))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        lines.extend(flatten(item, f"{prefix}[{i}]"))
                else:
                    lines.append(f"{prefix}: {obj}")
                return lines
            
            flattened = flatten(data)
            return "\n".join(flattened)
        except json.JSONDecodeError:
            # Return as-is if not valid JSON
            return content
    
    def _extract_text_from_markup(self, content: str) -> str:
        """Extract readable text from HTML/XML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            
            # Remove script and style elements
            for element in soup(["script", "style", "meta", "link"]):
                element.decompose()
            
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            # Fallback: simple regex-based tag removal
            import re
            text = re.sub(r"<[^>]+>", " ", content)
            text = re.sub(r"\s+", " ", text)
            return text.strip()
    
    def _format_csv(self, content: str) -> str:
        """Format CSV for better searchability."""
        import csv
        from io import StringIO
        
        try:
            reader = csv.reader(StringIO(content))
            rows = list(reader)
            
            if not rows:
                return content
            
            headers = rows[0]
            lines = [f"Headers: {', '.join(headers)}"]
            
            for row in rows[1:]:
                parts = []
                for i, value in enumerate(row):
                    if value.strip() and i < len(headers):
                        parts.append(f"{headers[i]}: {value}")
                if parts:
                    lines.append("; ".join(parts))
            
            return "\n".join(lines)
        except Exception:
            return content
