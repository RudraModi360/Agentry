"""
OllamaVisionService: VLM-powered image understanding via local Ollama.

Uses jpmarindiaz/lfm2.5-vl-450m:latest for:
- Structured OCR text extraction with preprocessing
- Task-specific reasoning (tables, forms, diagrams)
- Document page analysis with retry logic

Preprocessing pipeline:
- Resize large images (small model benefits from smaller inputs)
- Enhance contrast for better OCR accuracy
- Convert to grayscale when appropriate (reduces noise)

Prompt design:
- Structured output formats for reliable extraction
- Task-specific instructions avoid ambiguity
- Explicit format constraints reduce small-model hallucination
"""

from io import BytesIO
import logging
from typing import Optional, Literal

logger = logging.getLogger(__name__)

try:
    from ollama import Client
    from PIL import Image, ImageEnhance, ImageFilter
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


# ── Image preprocessing constants ──────────────────────────

MAX_IMAGE_DIM = 1024
OCR_PREVIEW_WIDTH = 1200
MIN_IMAGE_DIM = 50
RESIZE_QUALITY = 92

# ── Shared system prompt prefix ────────────────────────────

_SYSTEM_PREFIX = (
    "You are a precise document analysis engine. "
    "Extract information accurately and return it in the exact format requested. "
    "Do not add extra commentary, introductions, or conclusions. "
    "If information is not visible or extractable, state exactly what is missing."
)


def _preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Preprocess image for optimal OCR with a small VLM."""
    img = image.convert("RGB")

    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIM:
        ratio = min(MAX_IMAGE_DIM / w, MAX_IMAGE_DIM / h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    img = img.convert("L")
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.3)

    return img


def _preprocess_for_reasoning(image: Image.Image) -> Image.Image:
    """Preprocess image for visual reasoning (keep color, resize)."""
    img = image.convert("RGB")

    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIM:
        ratio = min(MAX_IMAGE_DIM / w, MAX_IMAGE_DIM / h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)

    return img


def _pil_to_bytes(image: Image.Image, fmt: str = "PNG") -> bytes:
    """Convert PIL Image to bytes."""
    buffered = BytesIO()
    image.save(buffered, format=fmt, quality=RESIZE_QUALITY)
    return buffered.getvalue()


def _build_user_message(prompt: str, image_data: bytes, system: Optional[str] = None) -> dict:
    """Build a structured user message for Ollama chat API."""
    content_parts = [{"text": prompt}]
    content_parts[0]["text"] = f"{_SYSTEM_PREFIX}\n\n{prompt}" if system else prompt
    content_parts.append({"image": image_data})
    return {"role": "user", "content": content_parts}


class OllamaVisionService:
    """VLM service for OCR and visual reasoning via local Ollama."""

    _client = None
    _model = "jpmarindiaz/lfm2.5-vl-450m:latest"

    @classmethod
    def _get_client(cls):
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("ollama library is not installed.")
        if cls._client is None:
            cls._client = Client(host='http://localhost:11434', timeout=120)
        return cls._client

    # ── Public API ──────────────────────────────────────────────

    @classmethod
    def get_text_from_image(cls, image_source: str) -> str:
        """Extract all visible text from an image file path."""
        return cls._process_image(
            image_source,
            cls._build_ocr_prompt(),
            preprocess=_preprocess_for_ocr,
        )

    @classmethod
    def get_text_from_pil_image(cls, image: Image.Image) -> str:
        """Extract all visible text from a PIL Image."""
        return cls._process_image(
            _pil_to_bytes(_preprocess_for_ocr(image)),
            cls._build_ocr_prompt(),
        )

    @classmethod
    def extract_text_structured(cls, image: Image.Image) -> dict:
        """
        Extract text with structure: headings, paragraphs, lists.
        Returns a dict with 'headings', 'paragraphs', 'lists', 'raw_text'.
        """
        raw = cls._process_image(
            _pil_to_bytes(_preprocess_for_ocr(image)),
            cls._build_structured_ocr_prompt(),
        )
        return cls._parse_structured_ocr(raw)

    @classmethod
    def extract_tables(cls, image: Image.Image) -> list:
        """Extract all tables from an image as a list of row lists."""
        raw = cls._process_image(
            _pil_to_bytes(_preprocess_for_reasoning(image)),
            cls._build_table_extraction_prompt(),
        )
        return cls._parse_table_output(raw)

    @classmethod
    def extract_forms(cls, image: Image.Image) -> dict:
        """Extract structured form fields from an image."""
        raw = cls._process_image(
            _pil_to_bytes(_preprocess_for_ocr(image)),
            cls._build_form_extraction_prompt(),
        )
        return cls._parse_form_output(raw)

    @classmethod
    def extract_metadata(cls, image: Image.Image) -> dict:
        """Extract document metadata: title, author, date, page number, language."""
        raw = cls._process_image(
            _pil_to_bytes(_preprocess_for_reasoning(image)),
            cls._build_metadata_extraction_prompt(),
        )
        return cls._parse_metadata_output(raw)

    @classmethod
    def describe_image(cls, image: Image.Image, focus: str = "") -> str:
        """Generate a detailed description of what is in the image."""
        prompt = (
            "Describe this image in detail. Focus on:"
            f" {focus}" if focus else "Describe this image in detail."
        )
        return cls._process_image(
            _pil_to_bytes(_preprocess_for_reasoning(image)),
            prompt,
        )

    @classmethod
    def reason_about_image(cls, image: Image.Image, prompt: str) -> str:
        """Send an image + custom reasoning prompt to the VLM."""
        return cls._process_image(
            _pil_to_bytes(_preprocess_for_reasoning(image)),
            prompt,
        )

    @classmethod
    def reason_about_image_bytes(cls, image_bytes: bytes, prompt: str) -> str:
        """Send raw image bytes + a custom reasoning prompt to the VLM."""
        return cls._process_image(image_bytes, prompt)

    @classmethod
    def get_ocr_confidence(cls, image: Image.Image) -> dict:
        """
        Run OCR and return confidence assessment about the result quality.
        Useful for deciding whether to trust the OCR output or re-process.
        """
        raw = cls._process_image(
            _pil_to_bytes(_preprocess_for_ocr(image)),
            cls._build_confidence_check_prompt(),
        )
        return cls._parse_confidence_output(raw)

    # ── Retry methods ───────────────────────────────────────────

    @classmethod
    def get_text_from_image_with_retry(cls, image_source: str, max_retries: int = 2) -> str:
        """OCR with retry and preprocessing fallback."""
        return cls._process_image_with_retry(
            image_source,
            cls._build_ocr_prompt(),
            preprocess=_preprocess_for_ocr,
            max_retries=max_retries,
        )

    # ── Internal ────────────────────────────────────────────────

    @classmethod
    def _build_ocr_prompt(cls) -> str:
        return (
            "OCR task — extract all visible text from this image.\n"
            "Rules:\n"
            "- Extract EVERY piece of text, including headers, footers, page numbers, and watermarks.\n"
            "- Preserve the original reading order (top to bottom, left to right).\n"
            "- Preserve line breaks between different lines of text.\n"
            "- Do not add commentary, summaries, or explanations.\n"
            "- If text is partially obscured, include what you can read and wrap uncertain characters in [].\n"
            "- Output ONLY the extracted text — nothing else."
        )

    @classmethod
    def _build_structured_ocr_prompt(cls) -> str:
        return (
            "Structured OCR task — analyze this document page and extract its structure.\n"
            "Return the content organized by type.\n"
            "Output format (JSON object with keys: headings, paragraphs, lists, raw_text):\n"
            "- 'headings': array of all headings/subheadings found\n"
            "- 'paragraphs': array of all body text paragraphs\n"
            "- 'lists': array of all list items found\n"
            "- 'raw_text': the complete raw text as extracted\n"
            "Preserve the order of elements as they appear on the page."
        )

    @classmethod
    def _build_table_extraction_prompt(cls) -> str:
        return (
            "Table extraction task — find all tables in this image.\n"
            "For each table, extract rows and columns exactly as they appear.\n"
            "Output format (JSON array of objects):\n"
            "[\n"
            "  {\n"
            "    'table_id': 1,\n"
            "    'headers': ['col1', 'col2', ...],\n"
            "    'rows': [['cell1', 'cell2', ...], ...]\n"
            "  }\n"
            "]\n"
            "Rules:\n"
            "- If a table has no clear headers, use empty strings for header names.\n"
            "- If rows have different column counts, pad with empty strings.\n"
            "- Include ALL tables found in the image.\n"
            "- Output ONLY valid JSON."
        )

    @classmethod
    def _build_form_extraction_prompt(cls) -> str:
        return (
            "Form extraction task — find all form fields in this image.\n"
            "For each field, identify the label and the value.\n"
            "Output format (JSON object):\n"
            "{\n"
            "  'fields': [\n"
            "    {'label': 'field name', 'value': 'field value'},\n"
            "    ...\n"
            "  ]\n"
            "}\n"
            "Rules:\n"
            "- If a field has no value, use an empty string.\n"
            "- If you cannot determine the label, use 'unknown' as the label.\n"
            "- Include ALL form fields found.\n"
            "- Output ONLY valid JSON."
        )

    @classmethod
    def _build_metadata_extraction_prompt(cls) -> str:
        return (
            "Metadata extraction task — extract document metadata from this image.\n"
            "Look for: title, author, date, page number, document type.\n"
            "Output format (JSON object with keys: title, author, date, page_number, document_type, language).\n"
            "If a field is not found, use null for its value.\n"
            "Output ONLY valid JSON."
        )

    @classmethod
    def _build_confidence_check_prompt(cls) -> str:
        return (
            "OCR quality check task — review the text in this image and assess extraction quality.\n"
            "Output format (JSON object):\n"
            "{\n"
            "  'confidence': 0.0-1.0,\n"
            "  'issues': ['list of issues found'],\n"
            "  'recommendation': 'use_this' or 'reprocess_with_higher_quality'\n"
            "}\n"
            "Output ONLY valid JSON."
        )

    @classmethod
    def _process_image(cls, image_data, prompt: str) -> str:
        """Core VLM call with error handling."""
        try:
            client = cls._get_client()
            response = client.chat(
                model=cls._model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_data],
                }],
            )
            return response['message']['content'].strip()
        except Exception as e:
            logger.error(f"Ollama vision call failed: {e}")
            return f"[Vision Failed] {type(e).__name__}: {e}"

    @classmethod
    def _process_image_with_retry(cls, image_source, prompt: str,
                                  preprocess=_preprocess_for_ocr,
                                  max_retries: int = 2) -> str:
        """Process image with retry logic."""
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                if isinstance(image_source, str):
                    with Image.open(image_source) as img:
                        processed = preprocess(img)
                        image_bytes = _pil_to_bytes(processed)
                elif isinstance(image_source, bytes):
                    image_bytes = image_source
                else:
                    processed = preprocess(image_source)
                    image_bytes = _pil_to_bytes(processed)

                result = cls._process_image(image_bytes, prompt)

                if result.startswith("[Vision Failed]"):
                    last_error = result
                    logger.warning(f"Vision attempt {attempt + 1}/{max_retries + 1} failed: {result}")
                    continue

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Vision attempt {attempt + 1}/{max_retries + 1} failed: {e}")
                continue

        return f"[Vision Failed after {max_retries + 1} attempts] {last_error}"

    @classmethod
    def _parse_structured_ocr(cls, raw: str) -> dict:
        """Parse structured OCR output into a dict."""
        result = {"headings": [], "paragraphs": [], "lists": [], "raw_text": raw}
        lines = raw.split("\n")

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if cls._is_heading(stripped):
                result["headings"].append(stripped)
            elif cls._is_list_item(stripped):
                result["lists"].append(stripped)
            else:
                result["paragraphs"].append(stripped)

        return result

    @classmethod
    def _parse_table_output(cls, raw: str) -> list:
        """Parse table extraction output."""
        try:
            import json
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "tables" in data:
                return data["tables"]
        except (json.JSONDecodeError, ValueError):
            pass
        logger.warning("Table extraction output was not valid JSON")
        return []

    @classmethod
    def _parse_form_output(cls, raw: str) -> dict:
        """Parse form extraction output."""
        try:
            import json
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError):
            pass
        logger.warning("Form extraction output was not valid JSON")
        return {"fields": []}

    @classmethod
    def _parse_metadata_output(cls, raw: str) -> dict:
        """Parse metadata extraction output."""
        try:
            import json
            data = json.loads(raw)
            if isinstance(data, dict):
                defaults = {"title": None, "author": None, "date": None,
                            "page_number": None, "document_type": None, "language": None}
                defaults.update(data)
                return defaults
        except (json.JSONDecodeError, ValueError):
            pass
        logger.warning("Metadata extraction output was not valid JSON")
        return {"title": None, "author": None, "date": None,
                "page_number": None, "document_type": None, "language": None}

    @classmethod
    def _parse_confidence_output(cls, raw: str) -> dict:
        """Parse OCR confidence check output."""
        try:
            import json
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError):
            pass
        return {
            "confidence": 0.5,
            "issues": ["Could not parse confidence assessment"],
            "recommendation": "reprocess_with_higher_quality",
        }

    @staticmethod
    def _is_heading(text: str) -> bool:
        """Heuristic for detecting headings."""
        if not text:
            return False
        if text.startswith("#") or text.startswith("##") or text.startswith("###"):
            return True
        if text.isupper() and len(text.split()) <= 8:
            return True
        lines = text.split("\n")
        return len(lines) <= 3 and len(text) > 5

    @staticmethod
    def _is_list_item(text: str) -> bool:
        """Heuristic for detecting list items."""
        stripped = text.strip()
        if not stripped:
            return False
        return stripped[0] in "-•*123456789" and len(stripped) > 2