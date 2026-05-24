"""
utils/docx_reader.py
Extracts the educationally relevant sections from a .docx syllabus.
Returns structured text ready for the AI mapping step.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from docx import Document
from docx.oxml.ns import qn

log = logging.getLogger(__name__)


@dataclass
class ExtractedSyllabus:
    filename: str
    course_description: str = ""
    learning_outcomes:  str = ""
    assessments:        str = ""
    course_topics:      str = ""
    warnings:           list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([
            self.course_description, self.learning_outcomes,
            self.assessments, self.course_topics,
        ])

    def as_prompt_text(self) -> str:
        """Concatenate sections into a single string for the API."""
        parts = []
        if self.course_description:
            parts.append(f"## COURSE DESCRIPTION\n{self.course_description}")
        if self.learning_outcomes:
            parts.append(f"## LEARNING OUTCOMES / OBJECTIVES\n{self.learning_outcomes}")
        if self.assessments:
            parts.append(f"## ASSESSMENTS / GRADING\n{self.assessments}")
        if self.course_topics:
            parts.append(f"## COURSE TOPICS / CONTENT\n{self.course_topics}")
        return "\n\n".join(parts)


def _is_heading(para) -> bool:
    """True if paragraph uses a Word Heading style or is short and bold."""
    style_name = para.style.name.lower() if para.style else ""
    if "heading" in style_name:
        return True
    text = para.text.strip()
    if not text or len(text) > 120:
        return False
    runs_bold = [r for r in para.runs if r.bold and r.text.strip()]
    return len(runs_bold) > 0 and len(runs_bold) == len([r for r in para.runs if r.text.strip()])


def _keyword_match(text: str, keywords: list[str]) -> bool:
    t = text.lower().replace(' ', ' ').replace('	', ' ')
    return any(kw in t for kw in keywords)


def _extract_table_text(table) -> str:
    """Flatten a Word table into readable text."""
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def _classify_section(heading_text: str) -> Optional[str]:
    """Map a heading to one of our four buckets, or None to skip."""
    t = heading_text.lower()
    if any(k in t for k in ["description", "rationale", "overview", "introduction", "about this"]):
        return "description"
    if any(k in t for k in ["learning outcome", "course objective", "student learning",
                              "program outcome", "clo", "competenc"]):
        return "outcomes"
    if any(k in t for k in ["assignment", "grading", "evaluation", "assessment"]):
        return "assessments"
    if any(k in t for k in ["topic", "content", "schedule", "weekly", "module", "unit"]):
        return "topics"
    return None


def extract(path: Path, section_keywords: list[str], stop_keywords: list[str], skip_keywords: list[str] | None = None) -> ExtractedSyllabus:
    """
    Read a .docx file and return an ExtractedSyllabus with the four
    educationally relevant sections populated.
    """
    result = ExtractedSyllabus(filename=path.name)

    try:
        doc = Document(str(path))
    except Exception:
        # File is likely plain text with a .docx extension — use text fallback
        return _extract_plain_text(path, section_keywords, stop_keywords, skip_keywords or [])

    buckets: dict[str, list[str]] = {
        "description": [], "outcomes": [], "assessments": [], "topics": []
    }
    current_bucket: Optional[str] = None
    past_stop = False

    for block in _iter_blocks(doc):
        is_hdg  = block["is_heading"]
        text    = block["text"].strip()
        raw     = block["raw"]

        if not text:
            continue

        if is_hdg:
            if _keyword_match(text, stop_keywords):
                past_stop = True
                current_bucket = None
                continue
            if past_stop:
                continue
            if skip_keywords and _keyword_match(text, skip_keywords):
                current_bucket = None  # skip this section but keep scanning
                continue
            bucket = _classify_section(text)
            current_bucket = bucket
            continue

        if current_bucket and not past_stop:
            buckets[current_bucket].append(raw)

    result.course_description = "\n".join(buckets["description"]).strip()
    result.learning_outcomes  = "\n".join(buckets["outcomes"]).strip()
    result.assessments        = "\n".join(buckets["assessments"]).strip()
    result.course_topics      = "\n".join(buckets["topics"]).strip()

    if result.is_empty():
        result.warnings.append("No relevant sections found — syllabus may use unexpected heading styles.")
        log.warning("%s: no sections extracted", path.name)
    else:
        found = [k for k, v in {
            "description": result.course_description,
            "outcomes":    result.learning_outcomes,
            "assessments": result.assessments,
            "topics":      result.course_topics,
        }.items() if v]
        log.info("%s: extracted sections: %s", path.name, ", ".join(found))

    return result


def _iter_blocks(doc):
    """
    Yield all content blocks (paragraphs and tables) in document order.
    Each block is a dict with keys: is_heading, text, raw.
    """
    # Walk the document body XML to preserve paragraph/table order
    body = doc.element.body
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            from docx.text.paragraph import Paragraph
            para = Paragraph(child, doc)
            yield {
                "is_heading": _is_heading(para),
                "text": para.text,
                "raw":  para.text,
            }
        elif tag == "tbl":
            from docx.table import Table
            table = Table(child, doc)
            table_text = _extract_table_text(table)
            yield {
                "is_heading": False,
                "text": table_text,
                "raw":  table_text,
            }


# ── Plain-text fallback (for files stored as UTF-8 text with .docx extension) ──

def _extract_plain_text(path: Path, section_keywords: list[str], stop_keywords: list[str], skip_keywords: list[str] | None = None) -> ExtractedSyllabus:
    """
    Fallback extractor for files that are plain text (Markdown-style) despite
    having a .docx extension. Uses heading-line detection via '#' prefixes and
    bold markers.
    """
    result = ExtractedSyllabus(filename=path.name)
    result.warnings.append("File is plain text (not binary .docx) — using text extractor.")

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    buckets: dict[str, list[str]] = {
        "description": [], "outcomes": [], "assessments": [], "topics": []
    }
    current_bucket: Optional[str] = None
    past_stop = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect headings: Markdown #/##, **bold**, ALL CAPS, or lines ending with ':'
        is_bold_line = stripped.startswith("**") and stripped.endswith("**") and len(stripped) < 120
        is_hdg = (
            stripped.startswith("#")
            or is_bold_line
            or (stripped.isupper() and 5 < len(stripped) < 80)
            or (stripped.endswith(":") and len(stripped) < 80 and "*" not in stripped)
        )
        heading_text = stripped.lstrip("#").strip(" :*").replace('\xa0', ' ').strip()

        if is_hdg:
            if _keyword_match(heading_text, stop_keywords):
                past_stop = True
                current_bucket = None
                continue
            if past_stop:
                continue
            if skip_keywords and _keyword_match(heading_text, skip_keywords):
                current_bucket = None  # skip this section but keep scanning
                continue
            bucket = _classify_section(heading_text)
            current_bucket = bucket
            continue

        if current_bucket and not past_stop:
            # Strip markdown formatting for cleanliness
            clean = stripped.lstrip("*_").rstrip("*_").strip("|").strip()
            if clean:
                buckets[current_bucket].append(clean)

    result.course_description = "\n".join(buckets["description"]).strip()
    result.learning_outcomes  = "\n".join(buckets["outcomes"]).strip()
    result.assessments        = "\n".join(buckets["assessments"]).strip()
    result.course_topics      = "\n".join(buckets["topics"]).strip()

    if result.is_empty():
        result.warnings.append("No relevant sections found in plain text either.")

    return result
