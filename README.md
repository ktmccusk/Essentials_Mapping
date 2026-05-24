# DNP Curricular Mapping Tool

Automates extraction of competency mappings from DNP course syllabi (.docx) into the
DNP Curricular Mapping Template Excel file. Maps to both AACN Essentials 2026 and
NONPF NP Competencies, subject to track rules below.

---

## What This Tool Does and Does Not Do

**Does:**
- Reads each syllabus and extracts the AACN and NONPF subcompetency IDs already documented
  in the syllabus alignment table — it does not re-evaluate or re-interpret the mapping
- Writes **X** in both the Course Objectives/Content and Student Evaluation/Grading columns
  for each confirmed mapping (amber X for entries flagged as uncertain)
- Generates an audit report for faculty review before anything is written to Excel
- Pauses after the report and asks for confirmation before writing to the template

**Does not:**
- Assign I/R/D (Introduce/Reinforce/Demonstrate) codes — that requires full curriculum
  sequence context and is a faculty judgment made during curriculum review
- Re-evaluate whether a CLO aligns with a competency — it trusts the syllabus mapping
- Map CNS-only courses to NONPF — the CNS role has its own competency framework (NACNS)

## Track Rule — NONPF Mapping
| Course track | AACN | NONPF |
|---|---|---|
| AG-CNS only | ✓ | ✗ |
| AG-ACNP, PMHNP, FNP, Midwifery/WHNP | ✓ | ✓ |
| Core DNP / shared CNS+NP | ✓ | ✓ |

## Framework Structure

Both frameworks use a two-level hierarchy. This tool maps to the **subcompetency** level
only — the level that includes a letter suffix.

| Framework | Level NOT mapped | Level mapped |
|-----------|-----------------|--------------|
| AACN 2026 | Competency e.g. `1.3` | Subcompetency e.g. `1.3d` |
| NONPF     | Role Competency e.g. `NP 2.3` | Subcompetency e.g. `NP 2.3i` |

---

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- Your .docx syllabus files
- The DNP Curricular Mapping Template Excel file (2026 updated version)

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create a .env file in the project root with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

> **Never commit your `.env` file to GitHub.** It is listed in `.gitignore` by default.

---

## Project Folder Structure

```
Essentials_Mapping/              ← project root
├── env/                         ← Python virtual environment
├── syllabi/                     ← put your .docx files here
├── cache/                       ← created automatically (extracted text + JSON)
├── Temp/                        ← create manually (report and Excel output go here)
├── utils/
│   ├── __init__.py
│   ├── docx_reader.py
│   └── excel_writer.py
├── .env                         ← your API key (never commit this)
├── .gitignore
├── config.py
├── DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx
├── extract.py
├── map.py
├── report.py
├── run_all.py
├── skill_prompt.txt
├── requirements.txt
├── write.py
└── README.md
```

---

## Running the Pipeline

### Full pipeline (recommended):
```bash
python run_all.py
```

This runs all four steps in sequence, pausing after the audit report to ask:
```
Ok to proceed with writing to Excel? [Y]es / [N]o:
```
Review `Temp/DNP_Mapping_Report.md` before answering. If you answer N, the pipeline
stops safely — nothing is written to the template. Re-run with `--skip-to write`
when you are ready to proceed.

### Individual steps:
```bash
python extract.py    # Step 1: extract text from .docx files → cache/
python map.py        # Step 2: call API, generate JSON → cache/
python report.py     # Step 3: generate audit report → Temp/
python write.py      # Step 4: write mappings to Excel → Temp/
```

### Resume after a crash:
```bash
python run_all.py
# Already-mapped courses are cached — they are skipped automatically
```

### Re-process everything from scratch:
```bash
python run_all.py --force
```

### Skip to a specific step:
```bash
python run_all.py --skip-to map      # skips extract, runs map → report → confirm → write
python run_all.py --skip-to report   # skips extract + map, runs report → confirm → write
python run_all.py --skip-to write    # runs write only, no confirmation prompt
```

---

## Outputs

| File | Description |
|------|-------------|
| `cache/*.txt` | Extracted text from each syllabus — check these if extraction quality is poor |
| `cache/*.json` | AI-generated mapping for each course |
| `Temp/DNP_Mapping_Report.md` | Audit report — **review before proceeding to write** |
| `Temp/DNP_Mapping_Output.xlsx` | Populated mapping template |

---

## Reviewing the Output

Before finalizing:

1. Open `Temp/DNP_Mapping_Report.md` — review all ⚑ flagged entries (amber in Excel)
   and any unmapped CLOs
2. Open `Temp/DNP_Mapping_Output.xlsx` — confirm X marks appear in expected cells
3. Faculty complete the Course Objectives/Content column (I/R/D codes) during curriculum review

---

## Configuring the Tool

All settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `SYLLABUS_DIR` | `syllabi/` | Folder containing .docx files |
| `CACHE_DIR` | `cache/` | Intermediate file storage |
| `TEMPLATE_PATH` | `DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx` | Input template |
| `OUTPUT_PATH` | `Temp/DNP_Mapping_Output.xlsx` | Excel output |
| `REPORT_PATH` | `Temp/DNP_Mapping_Report.md` | Audit report output |
| `MODEL` | `claude-sonnet-4-6` | Anthropic model |
| `MAX_TOKENS` | `8192` | Max response tokens per API call |
| `MAX_EXTRACT_CHARS` | `12000` | Max chars sent to API per syllabus |

---

## Troubleshooting

**"No .docx files found"**
→ Confirm `syllabi/` folder exists at project root and contains .docx files.

**"ANTHROPIC_API_KEY not set"**
→ Check `.env` file exists at project root with `ANTHROPIC_API_KEY=your-key-here`.
  No quotes, no extra spaces.

**"Template not found"**
→ Confirm the template filename in `config.py` matches exactly, including capitalisation.

**AACN IDs not detected in extraction report**
→ The alignment table may be missing from that syllabus or use unexpected formatting.
  Open the corresponding `cache/*.txt` file to inspect what was extracted.

**Subcomp ID not found warning in write step**
→ The syllabus listed an ID that doesn't exist in the template (e.g. an old numbering).
  Check the audit report — these are logged as warnings and skipped.

**Crashed mid-run**
→ Just re-run `python run_all.py` — completed courses are cached and skipped.

---

## Cost Estimate

Each syllabus call uses approximately 8,000–12,000 tokens (input + output).
At claude-sonnet-4-6 pricing, 70 syllabi ≈ $3–8 total.
