"""
PDF Parser - Extracts text and metadata from PDF files.
Uses PyMuPDF (fitz) for fast and accurate extraction.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF

from .base import BaseParser, ParsedDocument, DocumentChunk


class PDFParser(BaseParser):
    """Parser for PDF documents."""
    
    supported_extensions = [".pdf"]
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a PDF file and extract text with page-aware chunking."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        doc = fitz.open(file_path)
        
        # Extract metadata
        metadata = doc.metadata or {}
        
        # Extract text from all pages
        all_text = ""
        page_texts: List[Dict[str, Any]] = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            all_text += text + "\n\n"
            page_texts.append({
                "page_number": page_num + 1,
                "text": text
            })
        
        # Create page-aware chunks
        chunks = self._create_page_aware_chunks(page_texts)
        
        # Get file metadata
        file_meta = self.get_file_metadata(file_path)
        
        doc.close()
        
        return ParsedDocument(
            file_path=file_path,
            file_name=file_path.name,
            file_type="pdf",
            content=all_text,
            chunks=chunks,
            file_size=file_meta["file_size"],
            created_at=file_meta.get("created_at"),
            modified_at=file_meta.get("modified_at"),
            title=metadata.get("title") or file_path.stem,
            author=metadata.get("author"),
            page_count=len(page_texts),
            metadata={
                "producer": metadata.get("producer"),
                "creator": metadata.get("creator"),
                "subject": metadata.get("subject"),
                "keywords": metadata.get("keywords"),
            }
        )
    
    def _create_page_aware_chunks(
        self,
        page_texts: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Create chunks that respect page boundaries when possible."""
        chunks = []
        chunk_index = 0
        global_char_pos = 0
        
        for page_data in page_texts:
            page_num = page_data["page_number"]
            page_text = page_data["text"]
            
            # Chunk this page's text
            page_chunks = self.chunk_text(
                page_text,
                metadata={"source_page": page_num}
            )
            
            # Update chunk indices and add page info
            for chunk in page_chunks:
                chunk.chunk_index = chunk_index
                chunk.page_number = page_num
                chunk.start_char += global_char_pos
                chunk.end_char += global_char_pos
                chunks.append(chunk)
                chunk_index += 1
            
            global_char_pos += len(page_text) + 2  # +2 for \n\n
        
        return chunks
    
    def extract_tables(self, file_path: Path) -> List[List[List[str]]]:
        """Extract tables from PDF (basic implementation)."""
        # For better table extraction, consider using tabula-py or camelot
        doc = fitz.open(file_path)
        tables = []
        
        for page in doc:
            # This is a simplified approach - real table extraction is complex
            # Consider integrating tabula-py for production use
            pass
        
        doc.close()
        return tables
    
    def extract_images(self, file_path: Path, output_dir: Optional[Path] = None) -> List[Path]:
        """Extract images from PDF."""
        doc = fitz.open(file_path)
        extracted = []
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        for page_num, page in enumerate(doc):
            images = page.get_images()
            
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                if output_dir:
                    img_path = output_dir / f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
                    with open(img_path, "wb") as f:
                        f.write(image_bytes)
                    extracted.append(img_path)
        
        doc.close()
        return extracted
