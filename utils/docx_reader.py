"""
utils/docx_reader.py
Extracts usable text from a .docx syllabus for the AI mapping step.

Strategy: extract ALL text, skipping only sections whose headings are
pure boilerplate (office hours, academic integrity, etc.), and stopping
entirely once we hit terminal boilerplate. Let the AI find the alignment
table wherever it lives — don't try to classify sections in Python.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class ExtractedSyllabus:
    filename:  str
    text:      str = ""
    warnings:  list[str] = field(default_factory=list)
    has_aacn:  bool = False   # did we spot AACN Essentials IDs?
    has_nonpf: bool = False   # did we spot NONPF IDs?

    def is_empty(self) -> bool:
        return len(self.text.strip()) < 100


def _normalize(text: str) -> str:
    """Replace non-breaking spaces and tabs with regular spaces."""
    return text.replace("\xa0", " ").replace("\t", " ").strip()


def _is_heading(para) -> bool:
    """True if paragraph uses a Word Heading style or is short and fully bold."""
    style_name = para.style.name.lower() if para.style else ""
    if "heading" in style_name:
        return True
    text = para.text.strip()
    if not text or len(text) > 120:
        return False
    runs_with_text = [r for r in para.runs if r.text.strip()]
    if not runs_with_text:
        return False
    return all(r.bold for r in runs_with_text)


def _keyword_match(text: str, keywords: list[str]) -> bool:
    t = _normalize(text).lower()
    return any(kw in t for kw in keywords)


def _table_to_text(table) -> str:
    """Flatten a Word table into pipe-delimited rows."""
    rows = []
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells if c.text.strip()]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def _iter_blocks(doc):
    """Yield all content blocks in document order as dicts."""
    body = doc.element.body
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            from docx.text.paragraph import Paragraph
            para = Paragraph(child, doc)
            yield {"is_heading": _is_heading(para), "text": _normalize(para.text)}
        elif tag == "tbl":
            from docx.table import Table
            yield {"is_heading": False, "text": _table_to_text(Table(child, doc))}


def _extract_docx(path: Path, skip_keywords: list[str],
                  stop_keywords: list[str]) -> tuple[str, list[str]]:
    """Extract text from a real binary .docx file."""
    from docx import Document
    doc = Document(str(path))
    lines: list[str] = []
    warnings: list[str] = []
    skip_section = False
    stopped = False

    for block in _iter_blocks(doc):
        if stopped:
            break
        text = block["text"]
        if not text:
            continue

        if block["is_heading"]:
            if _keyword_match(text, stop_keywords):
                stopped = True
                continue
            skip_section = _keyword_match(text, skip_keywords)
            if not skip_section:
                lines.append(text)
            continue

        if not skip_section:
            lines.append(text)

    return "\n".join(lines), warnings


def _extract_plaintext(path: Path, skip_keywords: list[str],
                       stop_keywords: list[str]) -> tuple[str, list[str]]:
    """Fallback for files stored as UTF-8 text with a .docx extension."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines: list[str] = []
    warnings = ["File is plain text (not binary .docx) — using text extractor."]
    skip_section = False

    for line in raw.splitlines():
        stripped = _normalize(line)
        if not stripped:
            continue

        is_bold = stripped.startswith("**") and stripped.endswith("**") and len(stripped) < 120
        is_heading = (
            stripped.startswith("#")
            or is_bold
            or (stripped.isupper() and 5 < len(stripped) < 80)
        )
        heading_text = stripped.lstrip("#").strip(" :*")

        if is_heading:
            if _keyword_match(heading_text, stop_keywords):
                break
            skip_section = _keyword_match(heading_text, skip_keywords)
            if not skip_section:
                lines.append(heading_text)
            continue

        if not skip_section:
            lines.append(stripped.lstrip("*_").rstrip("*_"))

    return "\n".join(lines), warnings


def extract(path: Path, skip_keywords: list[str],
            stop_keywords: list[str], max_chars: int = 8000) -> ExtractedSyllabus:
    """
    Extract all non-boilerplate text from a syllabus file.
    Returns an ExtractedSyllabus with the text ready to send to the API.
    """
    result = ExtractedSyllabus(filename=path.name)

    try:
        text, warnings = _extract_docx(path, skip_keywords, stop_keywords)
    except Exception:
        text, warnings = _extract_plaintext(path, skip_keywords, stop_keywords)

    result.warnings = warnings

    if len(text) > max_chars:
        text = text[:max_chars]
        log.info("%s: truncated to %d chars", path.name, max_chars)

    result.text     = text
    result.has_aacn  = "aacn essentials" in text.lower() or "aacn:" in text.lower()
    result.has_nonpf = "nonpf" in text.lower() or "np " in text.lower()

    if result.is_empty():
        result.warnings.append("Very little text extracted — check syllabus format.")
        log.warning("%s: minimal content extracted", path.name)
    else:
        log.info("%s: extracted %d chars (AACN=%s, NONPF=%s)",
                 path.name, len(text), result.has_aacn, result.has_nonpf)

    return result
