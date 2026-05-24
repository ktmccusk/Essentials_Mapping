"""
report.py — Step 3
Reads all .json files from CACHE_DIR and generates a Markdown audit report
showing mappings per domain, flagged entries, and unmapped CLOs.

Usage:
    python report.py [--cache-dir PATH] [--output PATH]
"""

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate audit report from mapping JSON cache")
    p.add_argument("--cache-dir", type=Path, default=config.CACHE_DIR)
    p.add_argument("--output",    type=Path, default=config.REPORT_PATH)
    return p.parse_args()


def _domain_from_id(subcomp_id: str, framework: str) -> str:
    sid = subcomp_id.strip()
    if framework.upper() == "NONPF" or sid.upper().startswith("NP "):
        try:
            num = sid.replace("NP ", "").replace("NP", "").split(".")[0].strip()
            return f"NONPF Domain {num}"
        except Exception:
            return "NONPF Unknown"
    try:
        return f"AACN Domain {sid.split('.')[0].strip()}"
    except Exception:
        return "AACN Unknown"


def build_report(json_files: list[Path]) -> str:
    lines: list[str] = []
    lines.append("# DNP Curricular Mapping — Audit Report\n")
    lines.append(f"**Courses processed:** {len(json_files)}\n")
    lines.append(
        "> **Note:** The Course Objectives/Content column (I/R/D faculty code) is left blank "
        "intentionally. Introduce/Reinforce/Demonstrate designations require full curriculum "
        "sequence context and should be assigned by faculty during curriculum review.\n"
    )

    total_mappings = 0
    total_flagged  = 0
    total_unmapped = 0
    domain_counts: defaultdict[str, int] = defaultdict(int)
    flagged_entries:  list[dict] = []
    unmapped_entries: list[dict] = []
    course_summaries: list[dict] = []

    for jf in sorted(json_files):
        data       = json.loads(jf.read_text(encoding="utf-8"))
        course     = data.get("course_name", jf.stem)
        course_num = data.get("course_number", "")
        track      = data.get("track", "")
        mappings   = data.get("mappings", [])
        unmapped   = data.get("unmapped_clos", [])
        notes      = data.get("notes", "")
        flagged    = [m for m in mappings if m.get("flag") == "verify"]

        total_mappings += len(mappings)
        total_flagged  += len(flagged)
        total_unmapped += len(unmapped)

        for m in mappings:
            domain_counts[_domain_from_id(m["subcomp_id"], m.get("framework", "AACN"))] += 1

        for m in flagged:
            flagged_entries.append({
                "course":    f"{course_num} {course}".strip(),
                "subcomp":   m["subcomp_id"],
                "rationale": m.get("rationale", ""),
            })

        for u in unmapped:
            unmapped_entries.append({
                "course": f"{course_num} {course}".strip(),
                "clo":    u.get("clo_text", ""),
                "reason": u.get("reason", ""),
            })

        course_summaries.append({
            "display":  f"{course_num} {course}".strip(),
            "track":    track,
            "mapped":   len(mappings),
            "flagged":  len(flagged),
            "unmapped": len(unmapped),
            "notes":    notes,
        })

    # ── Summary ──────────────────────────────────────────────────────────────
    lines.append("## Summary\n")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Total subcompetency mappings | {total_mappings} |")
    lines.append(f"| Flagged for faculty review ⚑ | {total_flagged} |")
    lines.append(f"| Unmapped CLOs               | {total_unmapped} |")
    lines.append("")

    # ── Per-course table ─────────────────────────────────────────────────────
    lines.append("## Per-Course Summary\n")
    lines.append("| Course | Track | Mapped | Flagged | Unmapped CLOs |")
    lines.append("|--------|-------|--------|---------|---------------|")
    for cs in course_summaries:
        lines.append(
            f"| {cs['display']} | {cs['track']} | {cs['mapped']} "
            f"| {cs['flagged']} | {cs['unmapped']} |"
        )
    lines.append("")

    # ── Domain coverage ──────────────────────────────────────────────────────
    lines.append("## Domain Coverage (total mapping entries per domain)\n")
    lines.append("| Domain | Entries |")
    lines.append("|--------|---------|")
    for domain in sorted(domain_counts):
        lines.append(f"| {domain} | {domain_counts[domain]} |")
    lines.append("")

    # ── Flagged entries ──────────────────────────────────────────────────────
    if flagged_entries:
        lines.append("## ⚑ Flagged Entries — Require Faculty Review\n")
        lines.append(
            "These mappings were marked uncertain by the AI. "
            "Faculty should verify before finalizing.\n"
        )
        for fe in flagged_entries:
            lines.append(f"**{fe['course']}** — `{fe['subcomp']}`")
            lines.append(f"> {fe['rationale']}\n")
    else:
        lines.append("## ⚑ Flagged Entries\n_None — all mappings are confident._\n")

    # ── Unmapped CLOs ─────────────────────────────────────────────────────────
    if unmapped_entries:
        lines.append("## Unmapped CLOs\n")
        lines.append(
            "These course-level outcomes could not be matched to any subcompetency. "
            "Faculty should review.\n"
        )
        for ue in unmapped_entries:
            lines.append(f"**{ue['course']}**")
            lines.append(f"- CLO: _{ue['clo']}_")
            lines.append(f"- Reason: {ue['reason']}\n")
    else:
        lines.append("## Unmapped CLOs\n_None — all CLOs were mapped._\n")

    # ── Course notes ──────────────────────────────────────────────────────────
    notes_exist = [cs for cs in course_summaries if cs["notes"]]
    if notes_exist:
        lines.append("## AI Notes by Course\n")
        for cs in notes_exist:
            lines.append(f"**{cs['display']}:** {cs['notes']}\n")

    return "\n".join(lines)


def run(cache_dir: Path, output: Path) -> None:
    json_files = sorted(cache_dir.glob("*.json"))
    if not json_files:
        log.error("No .json files in %s — run map.py first", cache_dir)
        return

    log.info("Building report from %d mapping file(s)", len(json_files))
    report_text = build_report(json_files)
    output.write_text(report_text, encoding="utf-8")
    log.info("Report saved: %s", output)

    print(f"\n{'='*60}")
    print("  AUDIT REPORT SUMMARY")
    print(f"{'='*60}")
    for line in report_text.split("\n"):
        if line.startswith(("## ", "| ", "**", "> **Note")):
            print(line)
    print(f"\nFull report: {output}\n")


def main() -> None:
    args = parse_args()
    run(args.cache_dir, args.output)


if __name__ == "__main__":
    main()
