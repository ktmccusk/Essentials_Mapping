"""
config.py — Central configuration for dnp_mapper.
Edit paths, model name, and keyword lists here.
"""

from pathlib import Path

# ── Directories ──────────────────────────────────────────────────────────────
SYLLABUS_DIR  = Path("syllabi")
CACHE_DIR     = Path("cache")
TEMPLATE_PATH = Path("DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx")
OUTPUT_PATH   = Path("DNP_Mapping_Output.xlsx")
REPORT_PATH   = Path("DNP_Mapping_Report.md")
SKILL_PROMPT  = Path(__file__).parent / "skill_prompt.txt"

# ── Anthropic API ────────────────────────────────────────────────────────────
MODEL            = "claude-sonnet-4-6"
MAX_TOKENS       = 8192
RETRY_LIMIT      = 3
RETRY_DELAY      = 5
RATE_LIMIT_PAUSE = 2

# ── Extraction — sections to SKIP entirely (boilerplate before relevant content)
SKIP_KEYWORDS = [
    "instructor information",
    "instructor info",
    "office hours",
    "office (student)",
    "response time",
    "email",
    "welcome",
    "introductory",
    "course information",
    "required text",
    "course material",
    "technical requirement",
    "prerequisites",
]

# ── Extraction — headings that mark the END of relevant content (stop here)
STOP_KEYWORDS = [
    "academic integrity",
    "disability",
    "accessibility",
    "generative ai",
    "attendance",
    "late work",
    "classroom norm",
    "how class will work",
    "workload",
    "bibliography",
    "university policy",
]

# ── Maximum characters to send to the API per syllabus
MAX_EXTRACT_CHARS = 12_000   # increased — send more, let AI find the table

# ── Track identifiers for CNS-only courses (AACN only, no NONPF)
CNS_ONLY_TRACKS = [
    "ag-cns",
    "agcns",
    "cns only",
    "clinical nurse specialist",
]
