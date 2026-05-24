"""
write.py — Step 4
Reads all mapping .json files from CACHE_DIR and writes the results into
the DNP curricular mapping Excel template.

Usage:
    python write.py [--cache-dir PATH] [--template PATH] [--output PATH]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import config
from utils.excel_writer import write_courses, build_subcomp_index
from openpyxl import load_workbook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Write mapping JSON into Excel template")
    p.add_argument("--cache-dir", type=Path, default=config.CACHE_DIR)
    p.add_argument("--template",  type=Path, default=config.TEMPLATE_PATH)
    p.add_argument("--output",    type=Path, default=config.OUTPUT_PATH)
    return p.parse_args()


def run(cache_dir: Path, template_path: Path, output_path: Path) -> None:
    json_files = sorted(cache_dir.glob("*.json"))
    if not json_files:
        log.error("No .json files in %s — run map.py first", cache_dir)
        sys.exit(1)

    if not template_path.exists():
        log.error("Template not found: %s", template_path)
        sys.exit(1)

    log.info("Loading %d mapping file(s)", len(json_files))
    mappings: list[dict] = []
    for jf in json_files:
        try:
            mappings.append(json.loads(jf.read_text(encoding="utf-8")))
            log.info("  Loaded: %s", jf.name)
        except json.JSONDecodeError as exc:
            log.warning("  Skipping malformed JSON %s: %s", jf.name, exc)

    if not mappings:
        log.error("No valid mapping files loaded.")
        sys.exit(1)

    log.info("Writing to template: %s", template_path)
    warnings = write_courses(template_path, output_path, mappings)

    if warnings:
        log.warning("%d warning(s) during write:", len(warnings))
        for w in warnings:
            log.warning("  %s", w)
    else:
        log.info("Write completed with no warnings.")

    log.info("Output saved: %s", output_path)


def main() -> None:
    args = parse_args()
    run(args.cache_dir, args.template, args.output)


if __name__ == "__main__":
    main()
