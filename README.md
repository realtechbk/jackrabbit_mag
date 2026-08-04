# Maine Academy of Gymnastics — Service Line Profitability Analysis

Analysis of MAG's revenue and unit economics by service line, built from Jackrabbit Class exports.
Client engagement run by RealTech (Al, al@realtechbk.com).

**Status:** revenue and unit counts complete and reconciled for 2023, 2024, 2025 and 2026 YTD.
Cost of Sales not started — needs coach payroll. See `CURRENT_STATUS.md`.

---

## Read these first, in this order

| File | What it gives you |
|---|---|
| **`CLAUDE.md`** | Operating rules. **Read before touching anything.** The reconciliation gate and the units rule are non-negotiable. |
| **`CURRENT_STATUS.md`** | What is done, partly done, not started, and what is broken. |
| **`PROJECT_CONTEXT.md`** | The business, the reports, the findings, the numbers. |
| **`DATA_DICTIONARY.md`** | Column definitions, parsing traps, join reliability. |
| **`DECISIONS.md`** | Why things are the way they are — including three reversed decisions. |
| **`NEXT_STEPS.md`** | Prioritised task list. Start at Priority 1. |

---

## Folder layout

```
jackrabbit-mag/
├── CLAUDE.md · CURRENT_STATUS.md · PROJECT_CONTEXT.md
├── DATA_DICTIONARY.md · DECISIONS.md · NEXT_STEPS.md · README.md
├── data/raw/            Source Jackrabbit exports, unmodified
├── scripts/             Build scripts and the PDF parser
├── outputs/             Current deliverables
│   └── superseded/      Earlier versions, retained deliberately
└── docs/                Supporting notes
```

### `data/raw/` — source exports (all run 28 July 2026)

| File | Report | Notes |
|---|---|---|
| `RevenueSummary_2023.pdf` … `_2026YTD.pdf` | Revenue Summary | **Authoritative revenue.** PDF. |
| `ClassEventRevenue_2023.xlsx` … `_2026.xlsx` | Class/Event Revenue Summary | Class enrolments. **2026 file is defective** — 19-month enrolment window. |
| `SalesDetail_2023.xls` … `_2026.xls` | Store Sales Detail | Item-level units. Note field carries coach names and contract terms. |
| `ClassList_2026-27session.xls` | Class List | Instructors, duration, price, capacity. **Current session only.** |

### `scripts/`

| Script | Builds / does |
|---|---|
| `parse_rsr.py` | Parses Revenue Summary PDFs → Cat1/Cat2/activity records. The only real engineering here. |
| `build_perf_v8.py` | **The main deliverable.** `MAG_ServiceLinePerformance_v8.xlsx` — 3 tabs, 4 periods, 18 rows. |
| `build_3yr.py` | `MAG_RevenueByService_2023-2026YTD.xlsx` — revenue-only view, findings, category drift. |
| `build_mapped.py` | `MAG_JackrabbitClassMapping.xlsx` — all 176 classes mapped to service rows. |
| `build_crosswalk.py` | Blank reusable crosswalk template. |
| `build_2023.py` | 2023-only deep dive incl. the Team tuition/meet-fee split. Superseded but the Team method lives here. |
| `build_mag_doc.js` | `MAG_CompanyProfile_v2.docx` — the business profile. |

---

## Setup

### Python
```bash
pip install openpyxl pandas
```

### Node (only for the Word document)
```bash
npm install docx
```

### System tools
```bash
# Debian/Ubuntu
sudo apt-get install poppler-utils libreoffice
```
- `pdftotext` (poppler) — **required** by `parse_rsr.py`
- `soffice` (LibreOffice) — recalculates workbooks and renders PDFs for visual checks
- `pdftoppm` (poppler) — renders PDF pages to images

---

## Usage

### Regenerate the main deliverable
```bash
python scripts/build_perf_v8.py outputs/MAG_ServiceLinePerformance_v8.xlsx
```
The script prints a reconciliation line per period. **All four must read `var=0.00`.**
```
2023      rev=    1996290.52 target=    1996290.52 var=0.00
2024      rev=    2297353.81 target=    2297353.81 var=-0.00
2025      rev=    2241034.37 target=    2241034.37 var=0.00
2026 YTD  rev=    1126223.32 target=    1126223.32 var=0.00
```

### Recalculate (mandatory after writing any xlsx)
`openpyxl` writes formulas with **no cached values** — until recalculated, every formula cell reads
back as `None` to pandas and to most previewers.
```bash
python <path-to>/xlsx/scripts/recalc.py outputs/MAG_ServiceLinePerformance_v8.xlsx
```
Require `"status": "success"` and `"total_errors": 0`. A green recalc proves formulas *evaluate*, not
that they are *right* — spot-check two or three values.

If that helper is unavailable, LibreOffice will do it:
```bash
soffice --headless --convert-to xlsx --outdir /tmp outputs/MAG_ServiceLinePerformance_v8.xlsx
```

### Visual check before shipping
Two real bugs were caught this way — a summary block overlapping a header row, and a label starting
with `=` being parsed as a formula.
```bash
soffice --headless --convert-to pdf --outdir /tmp outputs/MAG_ServiceLinePerformance_v8.xlsx
pdftoppm -jpeg -r 100 /tmp/MAG_ServiceLinePerformance_v8.pdf /tmp/page
# then open /tmp/page-1.jpg and actually look at it
```

### Parse a new Revenue Summary period
```bash
pdftotext -layout data/raw/RevenueSummary_2027.pdf /tmp/y2027.txt
python scripts/parse_rsr.py /tmp/y2027.txt
# prints: period, reported total, sum of Cat1 totals, variance
# writes /tmp/parsed.json with cat1, cat2 and activity records
```
The parser **exits non-zero** if the variance is not zero, or if the report total is zero (which is
what an inverted date range produces). You can pass several files at once:
```bash
python scripts/parse_rsr.py /tmp/rs_2023.txt /tmp/rs_2024.txt /tmp/rs_2025.txt /tmp/rs_2026YTD.txt
```
Then update the `ROWS` and `TARGETS` constants at the top of `build_perf_v8.py`.
**Figures are hardcoded by design** — see `DECISIONS.md` D3.

### Rebuild the Word profile
```bash
node scripts/build_mag_doc.js outputs/MAG_CompanyProfile_v2.docx
```

---

## The three rules that matter most

1. **Zero variance or stop.** Every revenue figure reconciles to its source report total. The build
   scripts print it. If it is not `0.00`, do not ship.
2. **Never sum the Units column.** The unit differs by row — enrolments, bookings, parties, leotards,
   memberships. Only the class-enrolment subtotal is additive. The TOTAL row shows a dash deliberately.
3. **Do not present the membership-fee student proxy as a headcount.** It implies a 14% student loss in
   2025; the enrolment data says the opposite. It is a billing-timing artefact and is flagged as such
   in the workbook.

Full rules in `CLAUDE.md`.

---

## Known gotchas

- **Jackrabbit's help site renders client-side.** A plain HTTP fetch returns only the navigation shell.
  Use a real browser for their documentation.
- **An inverted date range in a Jackrabbit report returns $0.00 with no error.** Always check the
  parsed period.
- **A Cat2 can share its Cat1's name** (e.g. `Open Gym`), producing duplicate subtotal labels. The Cat1
  subtotal is the **last** one in the section. Handled in `parse_rsr.py`; do not "simplify" it.
- **Class/Event enrolments repeat across split revenue rows.** De-duplicate on
  `Class + Session + Cat3` before summing. Raw 2023 sum 10,691 vs true 8,159.
- **The OneDrive-synced folder may refuse overwrites from the shell.** Write a new versioned filename
  and move the old one to `outputs/superseded/`.
- **`MAG A.` in the instructor field is a generic/admin account**, not a person.
- Excel labels beginning with `=` are parsed as formulas by openpyxl. Avoid, or prefix.
