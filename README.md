# DNP Curricular Mapping Tool

Automates mapping of DNP course syllabi (.docx) to AACN Essentials 2026 and NONPF competencies,
populating the DNP Curricular Mapping Template Excel file.

---

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- Your .docx syllabus files
- The updated DNP mapping template Excel file

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key (do this once per terminal session)
# Mac/Linux:
export ANTHROPIC_API_KEY=your-key-here

# Windows (Command Prompt):
set ANTHROPIC_API_KEY=your-key-here

# Windows (PowerShell):
$env:ANTHROPIC_API_KEY="your-key-here"
```

## Directory Layout

```
your-project/
├── syllabi/                          ← Put your .docx files here
├── DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx
├── cache/                            ← Created automatically (extracted text + JSON)
├── dnp_mapper/                       ← This tool
│   ├── run_all.py
│   ├── extract.py
│   ├── map.py
│   ├── report.py
│   ├── write.py
│   ├── config.py
│   ├── skill_prompt.txt
│   └── utils/
└── DNP_Mapping_Output.xlsx           ← Created automatically
```

## Running the Full Pipeline

From inside the `dnp_mapper/` directory:

```bash
python run_all.py
```

This runs all four steps in sequence.

## Running Individual Steps

```bash
# Step 1 only: extract relevant sections from syllabi
python extract.py

# Step 2 only: call the API and generate JSON mappings
python map.py

# Step 3 only: generate the audit report
python report.py

# Step 4 only: write mappings into the Excel template
python write.py
```

## Resuming After a Crash

The tool caches each course's JSON after a successful API call.
If the pipeline crashes mid-run, simply run again — already-mapped courses are skipped.

To **re-process everything** from scratch:
```bash
python run_all.py --force
```

To **resume from a specific step**:
```bash
python run_all.py --skip-to report   # skips extract and map, runs report + write
python run_all.py --skip-to write    # runs write only
```

## Outputs

| File | Description |
|------|-------------|
| `cache/*.txt` | Extracted sections from each syllabus |
| `cache/*.json` | AI-generated mapping for each course |
| `DNP_Mapping_Output.xlsx` | Populated mapping template |
| `DNP_Mapping_Report.md` | Audit report — review before finalizing |

## Framework Structure

Both frameworks use a two-level hierarchy in the mapping template. This tool maps to the
**subcompetency** level only — the more specific level that includes a letter suffix.

| Framework | Level NOT mapped | Level mapped (letter suffix required) |
|-----------|-----------------|---------------------------------------|
| AACN 2026 | Competency e.g. `1.3` | Subcompetency e.g. `1.3d` |
| NONPF     | Role Competency e.g. `NP 2.3` | Subcompetency e.g. `NP 2.3i` |

In the Excel template, NONPF sheets label column 2 as **"Role Competency"** rather than
"Competency Name" — but the mapping target is always column 3 (Subcomp #) in both frameworks.

## What This Tool Does and Does Not Do

**Does:** Identify which AACN 2026 and NONPF subcompetencies each course explicitly addresses,
and record the assessment methods (eval codes) associated with each mapping. Confirmed mappings
appear as **X** in the Course Objectives/Content column; flagged uncertain mappings appear in amber.

**Does not:** Assign I/R/D (Introduce/Reinforce/Demonstrate) faculty codes. That designation
requires knowledge of the full curriculum sequence — where a course sits relative to others,
what content comes before and after — and is a faculty judgment that belongs in a separate
curriculum review process. The Course Objectives/Content column is left blank for faculty to complete.

## Reviewing the Output

**Before accepting the Excel output as final:**

1. Open `DNP_Mapping_Report.md` in any Markdown viewer (VS Code, Typora, GitHub)
2. Review all **⚑ Flagged entries** — these are mappings the AI was uncertain about (shown in amber in the Excel)
3. Review any **Unmapped CLOs** — course objectives that couldn't be matched
4. Spot-check a few courses against the source syllabi

## Configuring Paths

Edit `config.py` to change default directories, model name, or extraction behavior.

## Cost Estimate

Each syllabus call uses approximately 6,000–10,000 tokens (input + output).
At claude-sonnet-4 pricing, 70 syllabi ≈ $3–7 total.
