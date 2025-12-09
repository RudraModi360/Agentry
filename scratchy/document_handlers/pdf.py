from typing import Dict, Any
from .base import BaseDocumentHandler

class PDFHandler(BaseDocumentHandler):
    """Handler for PDF documents using pypdf."""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self._reader = None
        self._text = ""
        self._metadata = {}

    def load(self) -> None:
        """Load and parse the PDF file."""
        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("pypdf is not installed. Please install it via 'pip install pypdf' to use PDFHandler.")

        try:
            self._reader = PdfReader(self.file_path)
            
            # Extract text
            text_parts = []
            for page in self._reader.pages:
                text_parts.append(page.extract_text() or "")
            self._text = "\n\n".join(text_parts)
            
            # Extract metadata
            if self._reader.metadata:
                for key, value in self._reader.metadata.items():
                    # Strip the leading '/' from PDF metadata keys if present
                    clean_key = key[1:] if key.startswith('/') else key
                    self._metadata[clean_key] = value
                    
        except Exception as e:
            raise RuntimeError(f"Failed to load PDF file {self.file_path}: {e}")

    def get_text(self) -> str:
        if self._reader is None:
            self.load()
        return self._text

    def get_metadata(self) -> Dict[str, Any]:
        if self._reader is None:
            self.load()
        return self._metadata
