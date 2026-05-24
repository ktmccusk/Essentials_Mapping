# Running DNP Mapper in PyCharm

## 1. Get the repo into PyCharm

If the code is already on GitHub:
- Open PyCharm → **Get from VCS** → paste your GitHub repo URL → Clone

If you're starting fresh:
- Open PyCharm → **New Project** → choose a location
- Copy the `dnp_mapper/` folder into that project
- Use **VCS → Enable Version Control Integration** → Git, then push to GitHub

---

## 2. Set up your project folder structure

Inside your project root, create this layout before running anything:

```
your-project/              ← PyCharm project root
├── dnp_mapper/            ← the tool (already exists)
├── syllabi/               ← CREATE THIS — put all .docx files here
├── cache/                 ← created automatically when you run
├── DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx  ← copy here
├── .env                   ← CREATE THIS — see Step 3
├── DNP_Mapping_Output.xlsx     ← created automatically
└── DNP_Mapping_Report.md       ← created automatically
```

> The `syllabi/` folder and `.env` file sit at the **project root**, not inside `dnp_mapper/`.

---

## 3. Create your .env file (API key)

In your project root, create a plain text file named exactly `.env` (no other extension).
Add this single line:

```
ANTHROPIC_API_KEY=your-key-here
```

Replace `your-key-here` with your actual key from https://console.anthropic.com/

> PyCharm may warn that `.env` is not tracked — that is correct. Add `.env` to your
> `.gitignore` file so your API key is never committed to GitHub.

Add this line to `.gitignore`:
```
.env
```

---

## 4. Create a virtual environment in PyCharm

- Go to **PyCharm → Settings → Project → Python Interpreter**
- Click the gear icon → **Add Interpreter → Add Local Interpreter**
- Choose **Virtualenv** → confirm the location → OK
- PyCharm will create a `venv/` folder in your project

---

## 5. Install dependencies

Open PyCharm's built-in **Terminal** (bottom toolbar) and run:

```bash
pip install -r dnp_mapper/requirements.txt
```

---

## 6. Set the working directory

This is the most important PyCharm setting — the scripts use relative paths,
so they must run from the **project root**, not from inside `dnp_mapper/`.

- Open **Run → Edit Configurations**
- Click **+** → **Python**
- Set **Script path** to your `run_all.py` file
- Set **Working directory** to your **project root** (the folder containing `syllabi/`)
- Click OK

Alternatively, just use the Terminal for everything (recommended — simpler):

```bash
# From the PyCharm terminal, which opens at project root by default:
python dnp_mapper/run_all.py
```

---

## 7. Run the pipeline

**Option A — Full pipeline (recommended first run):**
```bash
python dnp_mapper/run_all.py
```

**Option B — Run individual steps:**
```bash
python dnp_mapper/extract.py    # Step 1: extract from .docx files
python dnp_mapper/map.py        # Step 2: call API, generate JSON
python dnp_mapper/report.py     # Step 3: generate audit report
python dnp_mapper/write.py      # Step 4: write to Excel template
```

**Option C — Resume after a crash (skips already-cached courses):**
```bash
python dnp_mapper/run_all.py
# Just re-run the same command — cached JSON files are skipped automatically
```

**Option D — Re-process everything from scratch:**
```bash
python dnp_mapper/run_all.py --force
```

**Option E — Resume from a specific step:**
```bash
python dnp_mapper/run_all.py --skip-to report   # runs report + write only
python dnp_mapper/run_all.py --skip-to write    # runs write only
```

---

## 8. Check your outputs

After a successful run:

| File | What to do with it |
|------|--------------------|
| `cache/*.txt` | Spot-check a few to confirm extraction quality |
| `cache/*.json` | Review any flagged entries before writing to Excel |
| `DNP_Mapping_Report.md` | Open in PyCharm or any Markdown viewer — review all ⚑ flagged items and unmapped CLOs |
| `DNP_Mapping_Output.xlsx` | Your populated template — amber cells need faculty review; Course Objectives/Content (I/R/D) column is blank for faculty to complete |

---

## Troubleshooting

**"No .docx files found"**
→ Check that your `syllabi/` folder is in the project root (same level as `dnp_mapper/`),
  and that you're running from the project root as your working directory.

**"ANTHROPIC_API_KEY environment variable not set"**
→ Check that your `.env` file exists at the project root and contains the key with no
  extra spaces or quotes around the value.

**"Template not found"**
→ Confirm `DNP_Curricular_Mapping_Template_2026_UPDATED.xlsx` is in the project root.

**Crashed mid-run at course 40**
→ Just re-run `python dnp_mapper/run_all.py` — the first 39 courses are cached and skipped.
