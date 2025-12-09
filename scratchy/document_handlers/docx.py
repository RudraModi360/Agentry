from typing import Dict, Any
from .base import BaseDocumentHandler

class DocxHandler(BaseDocumentHandler):
    """Handler for Word documents (.docx) using python-docx."""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self._doc = None
        self._text = ""
        self._metadata = {}

    def load(self) -> None:
        """Load and parse the DOCX file."""
        try:
            import docx
        except ImportError:
            raise RuntimeError("python-docx is not installed. Please install it via 'pip install python-docx' to use DocxHandler.")

        try:
            self._doc = docx.Document(self.file_path)
            
            # Extract text from paragraphs
            self._text = "\n\n".join([para.text for para in self._doc.paragraphs])
            
            # Extract core properties
            core_props = self._doc.core_properties
            self._metadata = {
                "author": core_props.author,
                "created": str(core_props.created),
                "modified": str(core_props.modified),
                "title": core_props.title,
                "subject": core_props.subject,
                "keywords": core_props.keywords,
                "last_modified_by": core_props.last_modified_by,
            }
            # Remove None values
            self._metadata = {k: v for k, v in self._metadata.items() if v is not None}
            
        except Exception as e:
            raise RuntimeError(f"Failed to load DOCX file {self.file_path}: {e}")

    def get_text(self) -> str:
        if self._doc is None:
            self.load()
        return self._text

    def get_metadata(self) -> Dict[str, Any]:
        if self._doc is None:
            self.load()
        return self._metadata
