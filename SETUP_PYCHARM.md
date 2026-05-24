# Running DNP Mapper in PyCharm

## 1. Get the repo into PyCharm

If the code is already on GitHub:
- Open PyCharm → **Get from VCS** → paste your GitHub repo URL → Clone

If you're starting fresh:
- Open PyCharm → **New Project** → choose a location
- Copy all project files into that folder
- Use **VCS → Enable Version Control Integration** → Git, then push to GitHub

---

## 2. Set up your project folder structure

Your project root should look like this before running:

```
Essentials_Mapping/              ← PyCharm project root
├── env/                         ← virtual environment (created by PyCharm)
├── syllabi/                     ← CREATE THIS — put all .docx files here
├── Temp/                        ← CREATE THIS — report and Excel output go here
├── cache/                       ← created automatically on first run
├── utils/
│   ├── __init__.py
│   ├── docx_reader.py
│   └── excel_writer.py
├── .env                         ← CREATE THIS — see Step 3
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

> `syllabi/`, `Temp/`, and `.env` all sit at the **project root** — same level as the scripts.

---

## 3. Create your .env file (API key)

In your project root, create a plain text file named exactly `.env` (no other extension).
Add this single line:

```
ANTHROPIC_API_KEY=your-key-here
```

Replace `your-key-here` with your actual key from https://console.anthropic.com/

> Your `.env` file is listed in `.gitignore` — it will never be committed to GitHub.
> Never paste your API key directly into any script file.

---

## 4. Create a virtual environment in PyCharm

- Go to **PyCharm → Settings → Project → Python Interpreter**
- Click the gear icon → **Add Interpreter → Add Local Interpreter**
- Choose **Virtualenv** → confirm the location → OK
- PyCharm will create an `env/` folder in your project

---

## 5. Install dependencies

Open PyCharm's built-in **Terminal** (bottom toolbar) and run:

```bash
pip install -r requirements.txt
```

---

## 6. Working directory

All scripts use relative paths and must be run from the **project root**.
PyCharm's Terminal opens at the project root by default, so just run scripts directly:

```bash
python run_all.py
```

If using PyCharm's Run Configuration instead of the Terminal:
- Open **Run → Edit Configurations** → **+** → **Python**
- Set **Script path** to the script file
- Set **Working directory** to your project root
- Click OK

---

## 7. Run the pipeline

**Full pipeline — recommended:**
```bash
python run_all.py
```

This runs all four steps in sequence. After the audit report is generated it pauses and asks:
```
Ok to proceed with writing to Excel? [Y]es / [N]o:
```
Open `Temp/DNP_Mapping_Report.md` and review it before answering.
- **Y** → writes mappings to the Excel template
- **N** → stops safely; re-run with `--skip-to write` when ready

**Individual steps:**
```bash
python extract.py    # Step 1: extract text from .docx files → cache/
python map.py        # Step 2: call API, generate JSON → cache/
python report.py     # Step 3: generate audit report → Temp/
python write.py      # Step 4: write mappings to Excel → Temp/
```

**Resume after a crash:**
```bash
python run_all.py
# Already-mapped courses are cached and skipped automatically
```

**Re-process everything from scratch:**
```bash
python run_all.py --force
```

**Resume from a specific step:**
```bash
python run_all.py --skip-to map      # skips extract only
python run_all.py --skip-to report   # skips extract + map
python run_all.py --skip-to write    # runs write only, no confirmation prompt
```

---

## 8. Check your outputs

| File | What to do with it |
|------|--------------------|
| `cache/*.txt` | Spot-check a few to confirm extraction quality — look for AACN IDs |
| `cache/*.json` | AI-generated mapping per course — source of truth before write |
| `Temp/DNP_Mapping_Report.md` | **Review this before proceeding to Excel** — check ⚑ flagged entries and unmapped CLOs |
| `Temp/DNP_Mapping_Output.xlsx` | Populated template — X in both columns per mapping; amber = needs faculty review |

> **I/R/D codes are not populated by this tool.** That designation requires knowledge of
> the full curriculum sequence and is completed by faculty during curriculum review.

---

## Troubleshooting

**"No .docx files found"**
→ Confirm `syllabi/` exists at the project root and contains .docx files.

**"ANTHROPIC_API_KEY environment variable not set"**
→ Check your `.env` file exists at the project root with `ANTHROPIC_API_KEY=your-key-here`.
  No quotes, no extra spaces around the value.

**"Template not found"**
→ Confirm `DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx` is at the project root
  and the filename in `config.py` matches exactly.

**"No module named utils"**
→ Confirm the `utils/` folder exists at the project root and contains `__init__.py`.

**AACN IDs not detected in extraction report**
→ Open the corresponding `cache/*.txt` file — check whether the alignment table was
  captured. The syllabus may use unexpected headings.

**Crashed mid-run**
→ Just re-run `python run_all.py` — completed courses are cached and skipped.
