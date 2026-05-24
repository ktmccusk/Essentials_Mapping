"""
extract.py — Step 1
Reads every .docx in SYLLABUS_DIR, extracts educationally relevant sections,
saves extracted text to CACHE_DIR/<filename>.txt, and prints a quality report.

Usage:
    python extract.py [--syllabus-dir PATH] [--cache-dir PATH]
"""

import argparse
import logging
import sys
from pathlib import Path

import config
from utils.docx_reader import extract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DIVIDER = "─" * 60


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract relevant sections from .docx syllabi")
    p.add_argument("--syllabus-dir", type=Path, default=config.SYLLABUS_DIR)
    p.add_argument("--cache-dir",    type=Path, default=config.CACHE_DIR)
    return p.parse_args()


def run(syllabus_dir: Path, cache_dir: Path) -> int:
    """Returns number of successfully extracted files."""
    cache_dir.mkdir(parents=True, exist_ok=True)

    docx_files = sorted(syllabus_dir.glob("*.docx"))
    if not docx_files:
        log.error("No .docx files found in %s", syllabus_dir)
        return 0

    log.info("Found %d .docx file(s) in %s", len(docx_files), syllabus_dir)
    print(f"\n{'='*60}")
    print(f"  EXTRACTION QUALITY REPORT")
    print(f"{'='*60}\n")

    success_count = 0

    for path in docx_files:
        print(DIVIDER)
        print(f"FILE: {path.name}")

        result = extract(path, config.SECTION_KEYWORDS, config.STOP_KEYWORDS)

        # Print section summary
        sections = {
            "Description":      result.course_description,
            "Learning Outcomes":result.learning_outcomes,
            "Assessments":      result.assessments,
            "Course Topics":    result.course_topics,
        }
        for label, content in sections.items():
            char_count = len(content)
            status = "✓" if char_count > 50 else ("⚠ SHORT" if char_count > 0 else "✗ MISSING")
            print(f"  {label:<20} {status}  ({char_count} chars)")

        if result.warnings:
            for w in result.warnings:
                print(f"  ⚠ WARNING: {w}")

        if result.is_empty():
            print("  ✗ SKIPPED — no content extracted")
            continue

        # Truncate to configured max before saving
        full_text = result.as_prompt_text()
        if len(full_text) > config.MAX_EXTRACT_CHARS:
            full_text = full_text[: config.MAX_EXTRACT_CHARS]
            print(f"  ℹ Truncated to {config.MAX_EXTRACT_CHARS} chars for API")

        out_path = cache_dir / (path.stem + ".txt")
        out_path.write_text(full_text, encoding="utf-8")
        print(f"  → Saved: {out_path.name}")
        success_count += 1

    print(f"\n{'='*60}")
    print(f"  Extracted: {success_count}/{len(docx_files)} files")
    print(f"{'='*60}\n")
    return success_count


def main() -> None:
    args = parse_args()
    count = run(args.syllabus_dir, args.cache_dir)
    if count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
