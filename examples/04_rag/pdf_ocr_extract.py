import base64
import os
import re
import tempfile
import time
from collections import defaultdict

import fitz
from openai import OpenAI
from PIL import Image

PDF_PATH = r"C:\Users\rudra\Downloads\jesc105.pdf"
RAG_INDEX_DIR = (
    r"C:\Users\rudra\Desktop\Scratchy\examples\04_rag\rag_index\extracted_images"
)
OUTPUT_MD = r"C:\Users\rudra\Desktop\Scratchy\examples\04_rag\extracted_content.md"
MODEL = "mimo-v2.5-free"
BASE_URL = "https://opencode.ai/zen/v1"
API_KEY = ""
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds; waits 2, 4, 8 ...
MAX_IMAGE_DIM = 1280

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

INSTRUCTION = """You are an OCR engine. Transcribe ONLY the main body content of the given page into clean, well-structured markdown.

STRICT OUTPUT RULES:
- Output ONLY the page's actual body text: paragraphs, real headings (e.g. "5.1 What are Life Processes?"), bullet/numbered lists, tables, and figure captions.
- NEVER add meta text of any kind: no "This page contains...", no "Main Text:", no "Footer:", no "QR Code Text:", no "Page X" labels, no summaries, no explanations, no commentary.
- OMIT page furniture: page numbers, running heads (e.g. "Science", "80"), reprint notices (e.g. "Reprint 2026-27"), decorative separators (***), watermarks, QR codes, and anything outside the body content.
- Transcribe text verbatim and accurately, preserving original headings and paragraph structure as markdown.
- Do not reference or embed any images in the output. Text transcription only."""


def _page_number(filename: str) -> int | None:
    match = re.search(r"_p(\d+)_", filename)
    return int(match.group(1)) if match else None


def _images_by_page(index_dir: str) -> dict[int, list[str]]:
    pages: dict[int, list[str]] = defaultdict(list)
    for name in sorted(os.listdir(index_dir)):
        if not name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        page = _page_number(name)
        if page is not None:
            pages[page].append(os.path.join(index_dir, name))
    return pages


def _render_full_page(doc: fitz.Document, page_index: int, page_number: int) -> str:
    pix = doc[page_index].get_pixmap(dpi=120)
    path = os.path.join(tempfile.gettempdir(), f"jesc105_page_{page_number}.png")
    pix.save(path)
    return path


def _downscale_for_vision(path: str) -> tuple[str, bool]:
    """Downscale large images so the vision encoder processes fewer tokens (faster).
    Returns (path_to_send, is_temp_copy). Keeps the original if already small."""
    with Image.open(path) as img:
        if max(img.size) <= MAX_IMAGE_DIM:
            return path, False
        img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        out = os.path.join(tempfile.gettempdir(), f"viz_{os.path.basename(path)}")
        img.save(out, format="PNG", optimize=True)
        return out, True


def _image_data_url(path: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        ext, "image/png"
    )
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def _ocr_page(page: int, clips: list[str], rendered: list[str]) -> str:
    images = clips + rendered
    print(f"\n--- Page {page} ({len(images)} image(s)) ---", flush=True)
    content: list[dict] = [{"type": "text", "text": f"Page {page}. {INSTRUCTION}"}]
    temp_copies: list[str] = []
    for image in images:
        send_path, is_temp = _downscale_for_vision(image)
        if is_temp:
            temp_copies.append(send_path)
        content.append(
            {"type": "image_url", "image_url": {"url": _image_data_url(send_path)}}
        )
    tokens: list[str] = []
    try:
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                stream = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": content}],
                    stream=True,
                )
                for chunk in stream:
                    if (
                        chunk.choices
                        and chunk.choices[0].delta
                        and chunk.choices[0].delta.content
                    ):
                        token = chunk.choices[0].delta.content
                        tokens.append(token)
                        print(token, end="", flush=True)
                break
            except Exception as exc:
                if attempt > MAX_RETRIES:
                    tokens.append(f"\n[ERROR] Page {page}: {exc}\n")
                    break
                wait = RETRY_BACKOFF**attempt
                print(
                    f"\n[RETRY {attempt}/{MAX_RETRIES}] Page {page}: {exc} (waiting {wait}s)",
                    flush=True,
                )
                time.sleep(wait)
    finally:
        for path in temp_copies:
            try:
                os.remove(path)
            except OSError:
                pass
    return "".join(tokens)


def extract_content_to_markdown(pdf_path: str, index_dir: str, output_md: str) -> None:
    figures = _images_by_page(index_dir)
    doc = fitz.open(pdf_path)
    try:
        total_pages = len(doc)
        with open(output_md, "w", encoding="utf-8") as md:
            md.write("# Extracted Content\n")
        for page in range(1, total_pages + 1):
            clips = figures.get(page, [])
            rendered = _render_full_page(doc, page - 1, page)
            page_text = _ocr_page(page, clips, [rendered])
            with open(output_md, "a", encoding="utf-8") as md:
                md.write(f"\n## Page {page}\n\n")
                for image in clips:
                    md.write(f"![]({image.replace(os.sep, '/')})\n")
                md.write("\n")
                md.write(page_text)
                md.write("\n\n")
            try:
                os.remove(rendered)
            except OSError:
                pass
    finally:
        doc.close()


if __name__ == "__main__":
    extract_content_to_markdown(PDF_PATH, RAG_INDEX_DIR, OUTPUT_MD)
