"""
Markdown Topic-Aware Chunker — Parse markdown, detect NCERT section structure,
produce topic-based chunks with associated images.

Strategy:
  1. Parse markdown line-by-line
  2. SKIP page markers (## Page N) — these are just page numbers, not sections
  3. Detect actual section headers by numbered pattern (5.1, 5.2, 5.2.1, etc.)
  4. Group ALL content under each section until next section header
  5. Map images to sections using filename metadata
  6. Produce one ChunkRecord per topic with text + image_paths
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .chunker import ChunkRecord
from .logging_setup import get_logger

log = get_logger("md_chunker")

# ── Patterns ───────────────────────────────────────────────────────────

# Page markers to SKIP: "## Page 1", "## Page 2", etc.
_PAGE_MARKER_RE = re.compile(r"^##\s+Page\s+\d+\s*$")

# Major sections: "## 5.2 NUTRITION" or "### 5.1 WHAT ARE LIFE PROCESSES?"
_MAJOR_SECTION_RE = re.compile(r"^#{2,3}\s+(\d+\.\d+)\s+(.*)")

# Sub-sections: "### 5.2.1 Autotrophic Nutrition"
_SUB_SECTION_RE = re.compile(r"^###\s+(\d+\.\d+\.\d+)\s+(.*)")

# Activities: "### Activity 5.1" or "## Activity 5.3"
_ACTIVITY_RE = re.compile(r"^#{2,3}\s+Activity\s+(\d+\.\d+)", re.IGNORECASE)

# Special blocks: "### QUESTIONS", "## EXERCISES", "## What You Have Learnt"
_SPECIAL_BLOCK_RE = re.compile(
    r"^#{2,3}\s+(QUESTIONS|EXERCISES|What You Have Learnt|REVISION|What you have learnt)",
    re.IGNORECASE,
)

# Image filename: jesc105_p4_5_2_1_figure_conf91_hash.png
_IMAGE_FILENAME_RE = re.compile(r"_p(\d+)_(\d+(?:_\d+)*)_figure")

# Figure references in text: "Figure 5.1", "Fig. 5.3"
_FIGURE_REF_RE = re.compile(r"(?:Figure|Fig\.?)\s+(\d+\.\d+)")


@dataclass
class _Section:
    """Internal section boundary."""
    level: int
    section_id: str
    title: str
    line_idx: int
    chunk_type: str = "topic"
    parent_id: str = ""


class MarkdownTopicChunker:
    """
    Parse markdown, detect NCERT section structure, produce topic-based chunks
    with associated images.

    Key behavior:
    - SKIPS ## Page N markers (page numbers are not sections)
    - Groups ALL content under each section until next section header
    - Attaches images to their parent sections
    """

    def __init__(
        self,
        images_dir: str,
        max_chunk_size: int = 8000,
        min_chunk_size: int = 200,
    ):
        self.images_dir = images_dir
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self._image_map: Dict[str, List[str]] = {}
        if images_dir and os.path.isdir(images_dir):
            self._image_map = self._build_image_map()
            log.info("Image map: %d sections with images", len(self._image_map))

    def chunk_markdown(
        self,
        md_path: str,
        source_file: str = "",
    ) -> List[ChunkRecord]:
        """Main entry: parse markdown → topic chunks with images."""
        t0 = time.time()
        log.info("Processing %s", md_path)

        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into logical lines (preserving blank lines for paragraph detection)
        lines = content.split("\n")

        # Step 1: Find section boundaries (SKIP page markers)
        sections = self._find_sections(lines)
        log.info("Found %d section boundaries (skipped page markers)", len(sections))

        # Step 2: Group content between section boundaries
        chunks = self._group_content(lines, sections, source_file)

        # Step 3: Renumber
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i

        elapsed = time.time() - t0
        total_images = sum(len(c.image_paths) for c in chunks)
        log.info(
            "Done: %d chunks (%d with images, %d total images) in %.1fs",
            len(chunks), sum(1 for c in chunks if c.image_paths), total_images, elapsed,
        )
        return chunks

    # ── Step 1: Find section boundaries ────────────────────────────────

    def _find_sections(self, lines: List[str]) -> List[_Section]:
        """
        Find section boundaries. SKIPS page markers.
        Returns list of _Section with line_idx indicating where each section starts.
        """
        sections: List[_Section] = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # SKIP page markers — they are NOT sections
            if _PAGE_MARKER_RE.match(stripped):
                continue

            # Check for activity
            m = _ACTIVITY_RE.match(stripped)
            if m:
                sections.append(_Section(
                    level=2,
                    section_id=f"activity_{m.group(1)}",
                    title=stripped.lstrip("#").strip(),
                    line_idx=i,
                    chunk_type="activity",
                    parent_id=m.group(1),
                ))
                continue

            # Check for special blocks (questions, exercises)
            m = _SPECIAL_BLOCK_RE.match(stripped)
            if m:
                sections.append(_Section(
                    level=2,
                    section_id=f"special_{i}",
                    title=stripped.lstrip("#").strip(),
                    line_idx=i,
                    chunk_type="question",
                ))
                continue

            # Check for major section: ## 5.2 Title or ### 5.1 Title
            m = _MAJOR_SECTION_RE.match(stripped)
            if m:
                sections.append(_Section(
                    level=len(stripped) - len(stripped.lstrip("#")),
                    section_id=m.group(1),
                    title=m.group(2).strip(),
                    line_idx=i,
                    chunk_type="topic",
                ))
                continue

            # Check for sub-section: ### 5.2.1 Title
            m = _SUB_SECTION_RE.match(stripped)
            if m:
                parent_id = ".".join(m.group(1).split(".")[:2])
                sections.append(_Section(
                    level=3,
                    section_id=m.group(1),
                    title=m.group(2).strip(),
                    line_idx=i,
                    chunk_type="topic",
                    parent_id=parent_id,
                ))
                continue

        return sections

    # ── Step 2: Group content ──────────────────────────────────────────

    def _group_content(
        self,
        lines: List[str],
        sections: List[_Section],
        source_file: str,
    ) -> List[ChunkRecord]:
        """Group lines between section boundaries into chunks."""
        if not sections:
            # No sections found — treat entire file as one chunk
            text = "\n".join(lines).strip()
            if len(text) >= self.min_chunk_size:
                return [ChunkRecord(
                    text=text[:self.max_chunk_size],
                    section_path="full_document",
                    source_file=source_file,
                    chunk_type="topic",
                )]
            return []

        chunks: List[ChunkRecord] = []

        # Add implicit "preamble" section before first detected section
        if sections[0].line_idx > 0:
            preamble_lines = lines[:sections[0].line_idx]
            preamble_text = self._clean_text(preamble_lines)
            if len(preamble_text) >= self.min_chunk_size:
                # Detect chapter title from preamble
                chapter_title = self._extract_chapter_title(preamble_lines)
                chunks.append(ChunkRecord(
                    text=preamble_text,
                    section_path=chapter_title or "preamble",
                    page_number=self._extract_page_num(preamble_lines),
                    source_file=source_file,
                    chunk_type="topic",
                ))

        # Process each section
        for idx, section in enumerate(sections):
            # End line is start of next section (or end of file)
            end_line = sections[idx + 1].line_idx if idx + 1 < len(sections) else len(lines)

            # Extract lines for this section
            section_lines = lines[section.line_idx:end_line]
            section_text = self._clean_text(section_lines)

            if not section_text or len(section_text) < self.min_chunk_size:
                continue

            # Find images for this section
            image_paths = self._attach_images(section.section_id)
            page_num = self._extract_page_num(section_lines)

            # If section fits in one chunk, keep it together
            if len(section_text) <= self.max_chunk_size:
                chunks.append(ChunkRecord(
                    text=section_text,
                    section_path=section.section_id,
                    page_number=page_num,
                    source_file=source_file,
                    chunk_type=section.chunk_type,
                    image_paths=image_paths,
                    image_ids=[self._path_to_id(p) for p in image_paths],
                ))
            else:
                # Section too long — split at sub-section boundaries or paragraphs
                sub_chunks = self._split_section(
                    section, section_lines, source_file, image_paths, page_num
                )
                chunks.extend(sub_chunks)

        return chunks

    def _split_section(
        self,
        section: _Section,
        lines: List[str],
        source_file: str,
        image_paths: List[str],
        page_num: int,
    ) -> List[ChunkRecord]:
        """Split a long section at sub-section or paragraph boundaries."""
        # Find sub-sections within this section
        sub_sections = []
        for i, line in enumerate(lines):
            m = _SUB_SECTION_RE.match(line.strip())
            if m:
                sub_sections.append((i, m.group(1), m.group(2).strip()))

        if sub_sections:
            # Split at sub-section boundaries
            return self._split_at_sub_sections(section, lines, sub_sections, source_file, image_paths, page_num)

        # No sub-sections — split at paragraph boundaries
        return self._split_at_paragraphs(section, lines, source_file, image_paths, page_num)

    def _split_at_sub_sections(
        self,
        section: _Section,
        lines: List[str],
        sub_sections: List[Tuple[int, str, str]],
        source_file: str,
        image_paths: List[str],
        page_num: int,
    ) -> List[ChunkRecord]:
        """Split at sub-section boundaries."""
        chunks = []

        # Content before first sub-section (intro)
        if sub_sections[0][0] > 1:
            intro_text = self._clean_text(lines[1:sub_sections[0][0]])
            if len(intro_text) >= self.min_chunk_size:
                chunks.append(ChunkRecord(
                    text=intro_text[:self.max_chunk_size],
                    section_path=section.section_id,
                    page_number=page_num,
                    source_file=source_file,
                    chunk_type="topic",
                    image_paths=image_paths,
                    image_ids=[self._path_to_id(p) for p in image_paths],
                ))

        # Each sub-section
        for idx, (offset, sub_id, title) in enumerate(sub_sections):
            start = offset
            end = sub_sections[idx + 1][0] if idx + 1 < len(sub_sections) else len(lines)
            sub_text = self._clean_text(lines[start:end])

            if len(sub_text) < self.min_chunk_size:
                continue

            sub_images = self._attach_images(sub_id)
            if not sub_images:
                sub_images = image_paths  # Inherit parent images

            chunks.append(ChunkRecord(
                text=sub_text[:self.max_chunk_size],
                section_path=sub_id,
                page_number=page_num,
                source_file=source_file,
                chunk_type="topic",
                image_paths=sub_images,
                image_ids=[self._path_to_id(p) for p in sub_images],
            ))

        return chunks

    def _split_at_paragraphs(
        self,
        section: _Section,
        lines: List[str],
        source_file: str,
        image_paths: List[str],
        page_num: int,
    ) -> List[ChunkRecord]:
        """Split at paragraph boundaries (fallback)."""
        text = self._clean_text(lines)
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 > self.max_chunk_size and current:
                chunks.append(ChunkRecord(
                    text=current.strip(),
                    section_path=section.section_id,
                    page_number=page_num,
                    source_file=source_file,
                    chunk_type=section.chunk_type,
                    image_paths=image_paths,
                    image_ids=[self._path_to_id(p) for p in image_paths],
                ))
                current = ""
            current += para + "\n\n"

        if current.strip() and len(current.strip()) >= self.min_chunk_size:
            chunks.append(ChunkRecord(
                text=current.strip()[:self.max_chunk_size],
                section_path=section.section_id,
                page_number=page_num,
                source_file=source_file,
                chunk_type=section.chunk_type,
                image_paths=image_paths,
                image_ids=[self._path_to_id(p) for p in image_paths],
            ))

        return chunks

    # ── Helpers ────────────────────────────────────────────────────────

    def _clean_text(self, lines: List[str]) -> str:
        """Clean lines: skip page markers, remove excessive blank lines."""
        cleaned = []
        for line in lines:
            stripped = line.strip()
            # Skip page markers
            if _PAGE_MARKER_RE.match(stripped):
                continue
            cleaned.append(stripped)

        text = "\n\n".join(cleaned)
        # Collapse 3+ blank lines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_page_num(self, lines: List[str]) -> int:
        """Extract page number from ## Page N markers."""
        for line in lines:
            m = re.match(r"##\s+Page\s+(\d+)", line.strip())
            if m:
                return int(m.group(1))
        return 0

    def _extract_chapter_title(self, lines: List[str]) -> str:
        """Extract chapter title from preamble lines."""
        for line in lines:
            m = re.match(r"^#\s+(CHAPTER\s+\d+\s+.*)", line.strip(), re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    # ── Image mapping ──────────────────────────────────────────────────

    def _build_image_map(self) -> Dict[str, List[str]]:
        """
        Parse image filenames → {section_id: [image_paths]}.
        Filename: jesc105_p4_5_2_1_figure_conf91_hash.png → section "5.2.1"
        """
        image_map: Dict[str, List[str]] = {}

        if not self.images_dir or not os.path.isdir(self.images_dir):
            return image_map

        for fname in os.listdir(self.images_dir):
            if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
                continue

            m = _IMAGE_FILENAME_RE.search(fname)
            if not m:
                continue

            # Convert "5_2_1" → "5.2.1"
            section_id = m.group(2).replace("_", ".")
            parts = section_id.split(".")
            parent_id = ".".join(parts[:2]) if len(parts) >= 2 else section_id

            full_path = os.path.join(self.images_dir, fname)

            # Map to exact section
            image_map.setdefault(section_id, []).append(full_path)
            # Map to parent section
            if parent_id != section_id:
                image_map.setdefault(parent_id, []).append(full_path)

        return image_map

    def _attach_images(self, section_id: str) -> List[str]:
        """Find images for this section (exact + child sections)."""
        if not section_id or section_id.startswith("activity_") or section_id.startswith("special_"):
            return []

        images = list(self._image_map.get(section_id, []))

        # Include child sections
        prefix = section_id + "."
        for key, paths in self._image_map.items():
            if key.startswith(prefix):
                images.extend(paths)

        # Deduplicate
        seen = set()
        unique = []
        for p in images:
            if p not in seen:
                seen.add(p)
                unique.append(p)

        return unique

    def _path_to_id(self, path: str) -> str:
        """Short ID from image path."""
        return os.path.splitext(os.path.basename(path))[0][:16]
