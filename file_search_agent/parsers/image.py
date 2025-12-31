"""
Image Parser - Extract text from images using OCR.
Supports various image formats with multiple OCR backends.
"""

from pathlib import Path
from typing import Optional, Literal
from PIL import Image

from .base import BaseParser, ParsedDocument


class ImageParser(BaseParser):
    """Parser for images using OCR."""
    
    supported_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        ocr_engine: Literal["tesseract", "easyocr"] = "tesseract",
        languages: Optional[list] = None
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.ocr_engine = ocr_engine
        self.languages = languages or ["en"]
        self._ocr = None
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def _get_ocr(self):
        """Lazy load OCR engine."""
        if self._ocr is not None:
            return self._ocr
        
        if self.ocr_engine == "tesseract":
            import pytesseract
            self._ocr = pytesseract
        elif self.ocr_engine == "easyocr":
            import easyocr
            self._ocr = easyocr.Reader(self.languages)
        
        return self._ocr
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse an image file using OCR."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Open image
        image = Image.open(file_path)
        
        # Get image metadata
        image_info = {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
        }
        
        # Perform OCR
        if self.ocr_engine == "tesseract":
            content = self._ocr_tesseract(image)
        else:
            content = self._ocr_easyocr(file_path)
        
        # Create chunks
        chunks = self.chunk_text(
            content,
            metadata={"source": "ocr", "engine": self.ocr_engine}
        )
        
        file_meta = self.get_file_metadata(file_path)
        
        return ParsedDocument(
            file_path=file_path,
            file_name=file_path.name,
            file_type="image",
            content=content,
            chunks=chunks,
            file_size=file_meta["file_size"],
            created_at=file_meta.get("created_at"),
            modified_at=file_meta.get("modified_at"),
            title=file_path.stem,
            metadata={
                "ocr_engine": self.ocr_engine,
                "languages": self.languages,
                **image_info
            }
        )
    
    def _ocr_tesseract(self, image: Image.Image) -> str:
        """Extract text using Tesseract OCR."""
        ocr = self._get_ocr()
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Configure Tesseract
        lang = "+".join(self.languages)
        
        # Perform OCR
        text = ocr.image_to_string(image, lang=lang)
        
        return text.strip()
    
    def _ocr_easyocr(self, file_path: Path) -> str:
        """Extract text using EasyOCR."""
        ocr = self._get_ocr()
        
        # EasyOCR returns list of (bbox, text, confidence)
        results = ocr.readtext(str(file_path))
        
        # Sort by vertical position (top to bottom, left to right)
        results.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
        
        # Extract text
        texts = [r[1] for r in results]
        
        return "\n".join(texts)
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        import numpy as np
        
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")
        
        # Increase contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        return image
    
    def detect_text_regions(self, file_path: Path) -> list:
        """Detect regions containing text in an image."""
        if self.ocr_engine == "tesseract":
            ocr = self._get_ocr()
            image = Image.open(file_path)
            data = ocr.image_to_data(image, output_type=ocr.Output.DICT)
            
            regions = []
            for i, text in enumerate(data["text"]):
                if text.strip():
                    regions.append({
                        "text": text,
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i],
                        "confidence": data["conf"][i]
                    })
            return regions
        
        elif self.ocr_engine == "easyocr":
            ocr = self._get_ocr()
            results = ocr.readtext(str(file_path))
            
            return [
                {
                    "text": text,
                    "bbox": bbox,
                    "confidence": conf
                }
                for bbox, text, conf in results
            ]
