"""Document parsers for various file formats."""

from pathlib import Path
from typing import Optional

from .base import BaseParser, ParsedDocument, DocumentChunk
from .pdf import PDFParser
from .docx import DocxParser
from .excel import ExcelParser
from .text import TextParser
from .code import CodeParser
from .image import ImageParser

__all__ = [
    "BaseParser", "ParsedDocument", "DocumentChunk",
    "PDFParser", "DocxParser", "ExcelParser", 
    "TextParser", "CodeParser", "ImageParser",
    "get_parser"
]

# Registry of parsers
_PARSERS = [
    PDFParser(),
    DocxParser(),
    ExcelParser(),
    TextParser(),
    CodeParser(),
    ImageParser(),
]


def get_parser(file_path: Path) -> Optional[BaseParser]:
    """
    Get the appropriate parser for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Parser instance if found, None otherwise
    """
    file_path = Path(file_path)
    
    for parser in _PARSERS:
        if parser.can_parse(file_path):
            return parser
    
    return None


def register_parser(parser: BaseParser):
    """Register a custom parser."""
    _PARSERS.append(parser)
