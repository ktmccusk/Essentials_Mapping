"""
map.py — Step 2
Reads extracted .txt files from CACHE_DIR, calls the Anthropic API with the
skill prompt, saves the mapping JSON to CACHE_DIR/<filename>.json.
Skips files that already have a .json (resume support).

Usage:
    python map.py [--cache-dir PATH] [--force]
    
    Set ANTHROPIC_API_KEY environment variable before running.
    Use --force to re-process files that already have cached JSON.
"""

import argparse
import json
import logging
import os
import re
import time
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv
load_dotenv()  # loads ANTHROPIC_API_KEY from .env if present

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Map syllabi to competencies via Anthropic API")
    p.add_argument("--cache-dir", type=Path, default=config.CACHE_DIR)
    p.add_argument("--force", action="store_true", help="Re-process already-cached JSON files")
    return p.parse_args()


def load_skill_prompt() -> str:
    if not config.SKILL_PROMPT.exists():
        log.error("Skill prompt not found: %s", config.SKILL_PROMPT)
        sys.exit(1)
    return config.SKILL_PROMPT.read_text(encoding="utf-8")


def call_api(client: anthropic.Anthropic, skill_prompt: str, syllabus_text: str) -> dict:
    """Call the API with retry logic. Returns parsed JSON dict."""
    for attempt in range(1, config.RETRY_LIMIT + 1):
        try:
            message = client.messages.create(
                model=config.MODEL,
                max_tokens=config.MAX_TOKENS,
                system=skill_prompt,
                messages=[{"role": "user", "content": syllabus_text}],
            )
            raw = message.content[0].text.strip()
            # Strip accidental markdown fences
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            return json.loads(raw)

        except anthropic.RateLimitError:
            wait = config.RETRY_DELAY * attempt
            log.warning("Rate limited — waiting %ds (attempt %d/%d)", wait, attempt, config.RETRY_LIMIT)
            time.sleep(wait)

        except anthropic.APIStatusError as exc:
            log.error("API error on attempt %d: %s", attempt, exc)
            if attempt == config.RETRY_LIMIT:
                raise
            time.sleep(config.RETRY_DELAY)

        except json.JSONDecodeError as exc:
            log.error("JSON parse error on attempt %d: %s", attempt, exc)
            if attempt == config.RETRY_LIMIT:
                raise
            time.sleep(config.RETRY_DELAY)

    raise RuntimeError("All retry attempts exhausted")


def run(cache_dir: Path, force: bool = False) -> int:
    """Returns number of successfully mapped files."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY environment variable not set.")
        log.error("Set it with: export ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)

    client      = anthropic.Anthropic(api_key=api_key)
    skill_prompt= load_skill_prompt()

    txt_files = sorted(cache_dir.glob("*.txt"))
    if not txt_files:
        log.error("No .txt files in %s — run extract.py first", cache_dir)
        return 0

    log.info("Found %d extracted file(s) to map", len(txt_files))
    success_count = 0

    for txt_path in txt_files:
        json_path = txt_path.with_suffix(".json")

        if json_path.exists() and not force:
            log.info("SKIP (cached): %s", txt_path.name)
            success_count += 1
            continue

        log.info("Mapping: %s", txt_path.name)
        syllabus_text = txt_path.read_text(encoding="utf-8")

        try:
            result = call_api(client, skill_prompt, syllabus_text)
            json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

            n_mappings = len(result.get("mappings", []))
            n_unmapped = len(result.get("unmapped_clos", []))
            n_flagged  = sum(1 for m in result.get("mappings", []) if m.get("flag") == "verify")
            log.info(
                "  ✓ %s: %d mappings, %d unmapped CLOs, %d flagged",
                result.get("course_name", "?"), n_mappings, n_unmapped, n_flagged,
            )
            success_count += 1

        except Exception as exc:
            log.error("  ✗ FAILED %s: %s", txt_path.name, exc)

        # Pause between calls to respect rate limits
        time.sleep(config.RATE_LIMIT_PAUSE)

    log.info("Mapped: %d/%d files", success_count, len(txt_files))
    return success_count


def main() -> None:
    args = parse_args()
    count = run(args.cache_dir, args.force)
    if count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
