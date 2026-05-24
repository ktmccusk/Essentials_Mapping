"""
run_all.py — Orchestrator
Runs all four steps in sequence:
    1. extract.py  — .docx → extracted text
    2. map.py      — text → JSON via Anthropic API
    3. report.py   — JSON → audit report
    4. write.py    — JSON → Excel template

Usage:
    python run_all.py [--syllabus-dir PATH] [--template PATH] [--output PATH] [--force]

Flags:
    --force     Re-process syllabi that already have cached JSON (re-calls the API)
    --skip-to   Start from a specific step: extract | map | report | write
"""

import argparse
import logging
import sys
from pathlib import Path

import config
import extract
import map as map_step
import report
import write

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

STEPS = ["extract", "map", "report", "write"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the full DNP mapping pipeline")
    p.add_argument("--syllabus-dir", type=Path, default=config.SYLLABUS_DIR)
    p.add_argument("--cache-dir",    type=Path, default=config.CACHE_DIR)
    p.add_argument("--template",     type=Path, default=config.TEMPLATE_PATH)
    p.add_argument("--output",       type=Path, default=config.OUTPUT_PATH)
    p.add_argument("--report",       type=Path, default=config.REPORT_PATH)
    p.add_argument("--force",        action="store_true")
    p.add_argument(
        "--skip-to",
        choices=STEPS,
        default="extract",
        help="Resume from a specific step (skips earlier steps)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    start_index = STEPS.index(args.skip_to)

    log.info("=" * 60)
    log.info("DNP Mapping Pipeline")
    log.info("=" * 60)

    if start_index <= STEPS.index("extract"):
        log.info("── Step 1: Extract ──────────────────────────────────────")
        count = extract.run(args.syllabus_dir, args.cache_dir)
        if count == 0:
            log.error("Extraction produced no output. Stopping.")
            sys.exit(1)

    if start_index <= STEPS.index("map"):
        log.info("── Step 2: Map (API calls) ──────────────────────────────")
        count = map_step.run(args.cache_dir, force=args.force)
        if count == 0:
            log.error("Mapping produced no output. Stopping.")
            sys.exit(1)

    if start_index <= STEPS.index("report"):
        log.info("── Step 3: Report ───────────────────────────────────────")
        report.run(args.cache_dir, args.report)

    if start_index <= STEPS.index("write"):
        log.info("── Step 4: Write to Excel ───────────────────────────────")
        write.run(args.cache_dir, args.template, args.output)

    log.info("=" * 60)
    log.info("Pipeline complete.")
    log.info("  Excel output : %s", args.output)
    log.info("  Audit report : %s", args.report)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
