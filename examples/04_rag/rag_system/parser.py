from __future__ import annotations

import hashlib
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .logging_setup import get_logger

log = get_logger("parser")


@dataclass
class ContentBlock:
    type: Literal["text", "image", "section_header"]
    content: str
    page_number: int
    section_path: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def section_title(self) -> str:
        return ".".join(self.section_path) if self.section_path else ""


_SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s+(.+)", re.MULTILINE)
_MD_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)
_BOLD_HEADER_RE = re.compile(r"^\s*\*\*(.+?)\*\*\s*$", re.MULTILINE)

_PAGE_DPI = 150
_LAYOUT_MODEL = None
_LAYOUT_CLASS_NAMES = {
    3: "figure",   # diagrams, photos, illustrations
    5: "table",    # data tables
    8: "formula",  # isolate_formula — standalone equations
}
_LAYOUT_CONFIDENCE = 0.9
_PADDING = 5


def _get_layout_model():
    global _LAYOUT_MODEL
    if _LAYOUT_MODEL is not None:
        return _LAYOUT_MODEL
    try:
        from doclayout_yolo import YOLOv10
        from huggingface_hub import hf_hub_download

        print("  Loading DocLayout-YOLO model (first run downloads ~100MB) ...", flush=True)
        t0 = time.time()
        filepath = hf_hub_download(
            repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
            filename="doclayout_yolo_docstructbench_imgsz1024.pt",
        )
        _LAYOUT_MODEL = YOLOv10(filepath)
        print(f"  Model loaded in {time.time() - t0:.1f}s")
        return _LAYOUT_MODEL
    except Exception as e:
        print(f"  WARNING: DocLayout-YOLO load failed: {e}")
        return None


class PDFParser:

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="rag_images_")
        os.makedirs(self.output_dir, exist_ok=True)

    def parse(self, file_path: str) -> List[ContentBlock]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF not found: {file_path}")

        blocks: List[ContentBlock] = []
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        print(f"  Opening PDF: {os.path.basename(file_path)} ...", flush=True)
        t0 = time.time()

        try:
            import pymupdf
        except ImportError:
            raise RuntimeError("pymupdf is required. pip install pymupdf")

        model = _get_layout_model()

        doc = pymupdf.open(file_path)
        total_pages = len(doc)
        print(f"  PDF has {total_pages} pages")

        current_section: List[str] = []
        images_extracted = 0
        text_blocks_count = 0
        section_headers_count = 0

        for page_num_idx in range(total_pages):
            page_num = page_num_idx + 1
            t_page = time.time()
            print(f"    Page {page_num}/{total_pages} ...", flush=True)

            page = doc[page_num_idx]

            page_text_blocks: List[ContentBlock] = []
            page_text = page.get_text() or ""
            if page_text.strip():
                text_blocks = self._split_page_text(page_text, page_num, base_name)
                for tb in text_blocks:
                    if tb.type == "section_header" and tb.section_path:
                        current_section = tb.section_path
                        section_headers_count += 1
                    if not tb.section_path and current_section:
                        tb.section_path = list(current_section)
                    if tb.type == "text":
                        text_blocks_count += 1
                    page_text_blocks.append(tb)
                    blocks.append(tb)

            try:
                page_img = self._render_page(page, pymupdf)

                if page_img is not None and model is not None:
                    crops = self._extract_layout_regions(
                        page_img, page_num, base_name, model,
                        current_section=list(current_section),
                        page_text_blocks=page_text_blocks,
                    )
                    images_extracted += len(crops)
                    for crop_block in crops:
                        blocks.append(crop_block)
            except Exception as e:
                print(f"  WARNING: Page {page_num}: failed ({e})")

            page_elapsed = time.time() - t_page
            print(
                f"    Page {page_num}/{total_pages} done ({page_elapsed:.1f}s) | "
                f"{text_blocks_count} text, {images_extracted} regions",
                flush=True,
            )

        doc.close()
        elapsed = time.time() - t0
        print(
            f"  PDF parsed: {len(blocks)} blocks "
            f"({text_blocks_count} text, {section_headers_count} sections, "
            f"{images_extracted} regions) in {elapsed:.1f}s"
        )
        return blocks

    def _render_page(self, page, pymupdf):
        import numpy as np

        mat = pymupdf.Matrix(_PAGE_DPI / 72, _PAGE_DPI / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        w = pix.width
        h = pix.height
        samples = pix.samples
        img_array = np.frombuffer(samples, dtype=np.uint8).reshape(h, w, 3)
        return img_array

    def _extract_layout_regions(
        self,
        page_img,
        page_num: int,
        source_name: str,
        model,
        current_section: Optional[List[str]] = None,
        page_text_blocks: Optional[List[ContentBlock]] = None,
    ) -> List[ContentBlock]:
        import numpy as np
        from PIL import Image

        t0 = time.time()
        pil_img = Image.fromarray(page_img)
        h, w = page_img.shape[:2]

        det_res = model.predict(
            page_img,
            imgsz=1024,
            conf=0.15,
            device="cpu",
        )

        if not det_res or len(det_res) == 0:
            return []

        result = det_res[0]
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return []

        # Pass 1: collect figure_caption regions (class 4) — bbox only, no crop
        captions: List[Dict[str, Any]] = []
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            if cls_id != 4:
                continue
            xyxy = boxes.xyxy[i].cpu().numpy()
            cx1, cy1, cx2, cy2 = [int(v) for v in xyxy]
            caption_cy = (cy1 + cy2) // 2
            captions.append({
                "bbox": [cx1, cy1, cx2, cy2],
                "center_y": caption_cy,
            })

        # Pass 2: extract figure/table/formula regions (classes 3,5,8) at 90%+
        blocks: List[ContentBlock] = []
        crop_count = 0

        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            if cls_id not in _LAYOUT_CLASS_NAMES:
                continue

            conf = float(boxes.conf[i].item())
            if conf < _LAYOUT_CONFIDENCE:
                continue

            label = _LAYOUT_CLASS_NAMES[cls_id]

            xyxy = boxes.xyxy[i].cpu().numpy()
            x1, y1, x2, y2 = xyxy

            x1 = max(0, int(x1) - _PADDING)
            y1 = max(0, int(y1) - _PADDING)
            x2 = min(w, int(x2) + _PADDING)
            y2 = min(h, int(y2) + _PADDING)

            if (x2 - x1) < 20 or (y2 - y1) < 20:
                continue

            crop = pil_img.crop((x1, y1, x2, y2))

            # Find nearest caption by vertical distance
            region_cy = (y1 + y2) // 2
            nearest_caption = None
            min_dist = float("inf")
            for cap in captions:
                dist = abs(cap["center_y"] - region_cy)
                if dist < min_dist:
                    min_dist = dist
                    nearest_caption = cap

            # Build section slug for filename
            section_slug = ""
            if current_section:
                section_slug = "_".join(current_section)

            crop_hash = hashlib.md5(crop.tobytes()).hexdigest()[:12]
            conf_pct = int(conf * 100)
            sec_part = f"_{section_slug}" if section_slug else ""
            filename = f"{source_name}_p{page_num}{sec_part}_{label}_conf{conf_pct}_{crop_hash}.png"
            filepath = os.path.join(self.output_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            crop.save(filepath, "PNG")

            cw, ch = crop.size
            print(
                f"      {label}: {cw}x{ch} conf={conf:.2f} -> {filename}",
                flush=True,
            )

            blocks.append(ContentBlock(
                type="image",
                content=filepath,
                page_number=page_num,
                section_path=list(current_section) if current_section else [],
                metadata={
                    "source": source_name,
                    "page": page_num,
                    "section": ".".join(current_section) if current_section else "",
                    "type": label,
                    "confidence": round(conf, 3),
                    "bbox": [x1, y1, x2, y2],
                    "width": cw,
                    "height": ch,
                    "filename": filename,
                },
            ))
            crop_count += 1

        elapsed = time.time() - t0
        print(f"      layout: {crop_count} regions detected ({elapsed:.2f}s)", flush=True)
        return blocks

    def _split_page_text(
        self, text: str, page_num: int, source_name: str
    ) -> List[ContentBlock]:
        blocks: List[ContentBlock] = []
        lines = text.split("\n")

        current_text: List[str] = []
        current_section: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_text.append("")
                continue

            m = _SECTION_RE.match(stripped)
            if m:
                if current_text:
                    text_content = "\n".join(current_text).strip()
                    if text_content:
                        blocks.append(ContentBlock(
                            type="text",
                            content=text_content,
                            page_number=page_num,
                            section_path=list(current_section),
                            metadata={"source": source_name},
                        ))
                    current_text = []

                section_path = m.group(1).split(".")
                current_section = section_path
                blocks.append(ContentBlock(
                    type="section_header",
                    content=stripped,
                    page_number=page_num,
                    section_path=section_path,
                    metadata={"source": source_name, "title": m.group(2)},
                ))
                continue

            mmd = _MD_HEADER_RE.match(stripped)
            if mmd:
                if current_text:
                    text_content = "\n".join(current_text).strip()
                    if text_content:
                        blocks.append(ContentBlock(
                            type="text",
                            content=text_content,
                            page_number=page_num,
                            section_path=list(current_section),
                            metadata={"source": source_name},
                        ))
                    current_text = []

                blocks.append(ContentBlock(
                    type="section_header",
                    content=stripped,
                    page_number=page_num,
                    section_path=list(current_section),
                    metadata={"source": source_name, "title": mmd.group(2)},
                ))
                continue

            current_text.append(stripped)

        if current_text:
            text_content = "\n".join(current_text).strip()
            if text_content:
                blocks.append(ContentBlock(
                    type="text",
                    content=text_content,
                    page_number=page_num,
                    section_path=list(current_section),
                    metadata={"source": source_name},
                ))

        return blocks

    def extract_text_only(self, file_path: str) -> str:
        try:
            import pymupdf
        except ImportError:
            raise RuntimeError("pymupdf is required. pip install pymupdf")

        doc = pymupdf.open(file_path)
        parts = []
        for page in doc:
            text = page.get_text()
            if text:
                parts.append(text)
        doc.close()
        return "\n\n".join(parts)
