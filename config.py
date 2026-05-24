"""
config.py — Central configuration for dnp_mapper.
Edit the paths and model name here; nothing else should need changing.
"""

from pathlib import Path

# ── Directories (relative to wherever you run the scripts) ──────────────────
SYLLABUS_DIR  = Path("syllabi")          # folder containing your .docx files
CACHE_DIR     = Path("cache")            # intermediate extracted text + JSON
TEMPLATE_PATH = Path("DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx")
OUTPUT_PATH   = Path("DNP_Mapping_Output.xlsx")
REPORT_PATH   = Path("DNP_Mapping_Report.md")
SKILL_PROMPT  = Path(__file__).parent / "skill_prompt.txt"

# ── Anthropic API ────────────────────────────────────────────────────────────
MODEL         = "claude-sonnet-4-20250514"
MAX_TOKENS    = 4096
RETRY_LIMIT   = 3          # retries on transient API errors
RETRY_DELAY   = 5          # seconds between retries
RATE_LIMIT_PAUSE = 2       # seconds between successive API calls

# ── Section extraction — heading keywords (case-insensitive, partial match) ──
# Extract text under headings that contain ANY of these phrases.
SECTION_KEYWORDS = [
    "course description",
    "course rationale",
    "rationale",
    "learning outcome",
    "course objective",
    "student learning",
    "program outcome",
    "clo",
    "assignment",
    "grading",
    "evaluation",
    "assessment",
    "course topic",
    "course content",
    "content outline",
    "schedule",
    "weekly",
]

# Headings where we SKIP content but keep scanning (often appear before CLOs)
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

# Headings that mark the END of relevant content — stop scanning entirely after these
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

# Maximum characters to send to the API per syllabus
MAX_EXTRACT_CHARS = 8_000
