"""
extract.py — Step 1
Reads every .docx in SYLLABUS_DIR, extracts all non-boilerplate text,
saves to CACHE_DIR/<filename>.txt, and prints a quality report.

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
    p = argparse.ArgumentParser(description="Extract text from .docx syllabi")
    p.add_argument("--syllabus-dir", type=Path, default=config.SYLLABUS_DIR)
    p.add_argument("--cache-dir",    type=Path, default=config.CACHE_DIR)
    return p.parse_args()


def run(syllabus_dir: Path, cache_dir: Path) -> int:
    cache_dir.mkdir(parents=True, exist_ok=True)

    docx_files = sorted(syllabus_dir.glob("*.docx"))
    if not docx_files:
        log.error("No .docx files found in %s", syllabus_dir)
        return 0

    log.info("Found %d .docx file(s) in %s", len(docx_files), syllabus_dir)
    print(f"\n{'='*60}")
    print("  EXTRACTION QUALITY REPORT")
    print(f"{'='*60}\n")

    success_count = 0

    for path in docx_files:
        print(DIVIDER)
        print(f"FILE: {path.name}")

        result = extract(
            path,
            skip_keywords=config.SKIP_KEYWORDS,
            stop_keywords=config.STOP_KEYWORDS,
            max_chars=config.MAX_EXTRACT_CHARS,
        )

        char_count = len(result.text)
        status = "✓" if char_count > 200 else "⚠ VERY SHORT"
        print(f"  Extracted:          {status}  ({char_count} chars)")
        print(f"  AACN IDs detected:  {'✓' if result.has_aacn  else '✗ NOT FOUND'}")
        print(f"  NONPF IDs detected: {'✓' if result.has_nonpf else '✗ NOT FOUND'}")

        for w in result.warnings:
            print(f"  ⚠ {w}")

        if result.is_empty():
            print("  ✗ SKIPPED — insufficient content")
            continue

        if not result.has_aacn:
            print("  ⚠ No AACN Essentials IDs found in extracted text —")
            print("    the alignment table may be missing or use unexpected formatting.")

        out_path = cache_dir / (path.stem + ".txt")
        out_path.write_text(result.text, encoding="utf-8")
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
