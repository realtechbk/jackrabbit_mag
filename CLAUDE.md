# CLAUDE.md — Operating instructions for this project

## Project purpose

Build a defensible service-line profitability analysis for **Maine Academy of Gymnastics (MAG)**, a
family-owned gymnastics club in Westbrook, Maine, from data exported out of **Jackrabbit Class**
(their practice-management SaaS).

The deliverable the client asked for is a grid with, per service line and per year:
`# Units Sold · Revenue per Unit · Total Revenue · Total Cost of Sales · Cost of Sales % · Total Gross Profit`.

The consultant is **Al (al@realtechbk.com), RealTech**. MAG is his client. Deliverables are
client-facing, so numbers must reconcile and claims must be sourced.

## Current status in one line

Revenue and unit counts are **done and reconciled** for 2023, 2024, 2025 and 2026 YTD on both the
legacy analysis and the AI CFO platform (which now has a working Jackrabbit importer — see
Architecture decisions below). **Cost of Sales is not started on either track** — it does not exist
in Jackrabbit and needs coach payroll data. This is Phase 3, the current priority.

Read `CURRENT_STATUS.md` before doing anything — it has the exact validation numbers, test status and
latest commits. This file has the rules that don't change from session to session.

## Important business context

- MAG has been trading since 1991. ~$2.0–2.3M annual revenue. 176 active class records.
- Revenue is dominated by recreational girls' gymnastics (43.5% of 2025) and competitive team (25.2%).
- Staffing, not demand or floor space, is the binding constraint on the business. They advertise for
  coaches on the homepage and run an internal "Coach in Training" pipeline.
- **Cost of sales in a gym is coach labour.** There is no cost-of-goods concept in Jackrabbit.
  The single exception is Pro Shop, where cost of sales is inventory purchase cost.
- The 2026 fiscal picture is a part year (1 Jan – 28 Jul 2026) and is **not** comparable to full years.

## Architecture decisions

**This repo now holds two tracks.** Read `ARCHITECTURE.md` for the split.

| Track | Location | State |
|---|---|---|
| **Legacy MAG analysis** | `scripts/`, `outputs/`, `data/raw/` | Revenue and units complete. A one-off pipeline with hardcoded figures. Everything under "The legacy analysis track" below describes this track. |
| **AI CFO platform** | `src/cfo_platform/`, `config/`, `tests/` | **`JackrabbitClassImporter` is built, tested (45 tests) and verified against real MAG data** — revenue and class-enrolment facts in DuckDB, reconciled exactly to the legacy analysis. No `Analyzer` or `ReportBuilder` yet, and no payroll/cost-of-sales anything. See `CURRENT_STATUS.md` for the numbers and `ARCHITECTURE.md` for the layout. |

The rules in this file were written for the legacy analysis but **apply equally to the platform** —
the reconciliation gate is enforced in code there as a typed `ReconciliationError`
(`src/cfo_platform/core/exceptions.py`), not just a printed warning, and the units-basis rule shapes
`dim_service_line`/`fact_class_enrolment`'s design. They should shape the payroll importer and MAG
analyzer that come next (Phase 3 — see `NEXT_STEPS.md`).

### The legacy analysis track

An **analysis pipeline**: Jackrabbit exports in, Python transforms, Excel/Word deliverables out.

- `scripts/parse_rsr.py` — the only non-trivial piece of engineering. Parses the Jackrabbit Revenue
  Summary **PDF** (via `pdftotext -layout`) into Cat1/Cat2/activity records. Exits non-zero on a
  non-zero variance or a zero report total. Everything else reads `.xls`/`.xlsx` with pandas.
- `scripts/build_*.py` — each builds one deliverable with `openpyxl`. Figures are **hardcoded
  constants at the top of each script**, not re-derived at build time. This is deliberate: the
  numbers were verified once against the source reports, and hardcoding them makes the build
  reproducible and reviewable. If you change a figure, you must re-verify it.
- `scripts/build_mag_doc.js` — the Word company profile, built with the `docx` npm package.

## Naming conventions

**Service rows use `[Revenue Group] -- [Sub Group]`** with a space-hyphen-hyphen-space separator.
The four groups, in this order, reflect economic character rather than marketing:

1. `Recreational -- ...` — monthly tuition, coach-hours cost base
2. `Competitive -- ...` — monthly, hour-tier billing
3. `Ancillary -- ...` — transactional, little or no coach cost
4. `Review -- ...` — data-quality buckets, **not services**
5. `EXCLUDE -- ...` — not customer revenue at all

Files: `MAG_<Thing>_<version>.<ext>`. Superseded outputs go to `outputs/superseded/`, never deleted
silently.

## Which tool to use for what

This project is worked in **both Claude Code (VS Code) and Claude Cowork**. Same rules apply to both.

- **Claude Code** — anything involving the platform scaffold, git, tests, refactoring, or editing
  scripts. It has the repo, the venv and the test runner.
- **Cowork** — building or reviewing client-facing Excel/Word deliverables, reading source PDFs,
  visual checks. It has the document skills and can render files for inspection.
- **Either** — analysis, reading these docs, answering questions about the data.

One difference that matters: the `recalc.py` helper referenced below is a **Cowork skill script** and
does not exist in a VS Code checkout. The portable equivalent is given in `README.md`.

## Rules for any Claude session (Code or Cowork)

1. **Every revenue figure must reconcile to the source report total with zero variance.** Each build
   script prints the variance. If it is not `0.00`, stop and fix it before shipping anything. This is
   the project's single most important rule — a quiet mapping error becomes a wrong number in a
   client deck. On the platform track this is a typed `ReconciliationError` raised at load time, not
   a printed warning — the importer refuses to load a period that doesn't reconcile.
2. **Never sum the `# Units Sold` column across rows.** The unit differs by row: class enrolments,
   Open Gym bookings, birthday parties, leotards, memberships. The TOTAL row deliberately shows a
   dash. Only the class-enrolment subtotal is additive.
3. **Do not present the membership-fee student proxy as a headcount.** Membership revenue ÷ $45
   implies students fell 14% in 2025. The class enrolment data contradicts this. It is a
   billing-timing artefact. It is already flagged in the workbook; keep it flagged.
4. **Distinguish "revenue basis" from "units basis" and say which you used.** Revenue comes from the
   Revenue Summary; units come from the Class/Event Revenue Summary and Sales Detail. The two
   attribute revenue ~1–2% differently. Never silently mix them.
5. **De-duplicate before summing enrolments.** The Class/Event report splits some classes across
   multiple revenue rows and *repeats* the enrolment figure on each. De-duplicate on
   `Class + Session + Cat3`, then sum. Revenue still sums across all rows. In 2023 a naive sum gives
   10,691 against a true 8,159.
6. **Do not promote a line to the main grid unless its Jackrabbit revenue category is verified.**
   Falmouth Rec and Visiting Team rental are real revenue but their Cat1 is unknown, so they live on
   the `Store Detail` tab. Guessing would break the reconciliation.
7. **Do not dress up data-quality problems as services.** `Review -- ` rows stay visibly separate.
   Presenting them neutrally on the grid is fine; leaving them undocumented is not.
8. **Recalculate after writing any xlsx.** `openpyxl` writes formulas with no cached values, so until
   recalculated every formula cell reads back as `None`. In Cowork use the `xlsx` skill's
   `recalc.py` and require `status: success` with `total_errors: 0`. In VS Code use LibreOffice
   directly — see `README.md`. A green recalc proves formulas *evaluate*, not that they are *right* —
   spot check two or three values.
9. **Verify visually before shipping.** Convert to PDF, render to image, and actually look at it.
   Two real bugs were caught this way (a summary block overlapping a header row; a label beginning
   with `=` being parsed as a formula).
10. **Cite the report and date for any figure that reaches a client document.** All source reports
    were run 28 July 2026.

## Execution Policy

The assistant may execute without confirmation:

- Read files
- Search the repository
- Run Python scripts
- Run tests
- Query SQLite/DuckDB
- Inspect Git status/log/diff
- Generate documentation
- Analyze project files

The assistant must request confirmation before:

- Deleting files
- Rewriting Git history
- Force pushing
- Committing changes
- Pushing to GitHub
- Installing software
- Modifying production data
- Accessing external services
- Any irreversible action

## Current assumptions and limitations

- **Cost of Sales % cells are empty by design.** They are inputs awaiting payroll data. Every
  gross-profit figure therefore currently equals revenue. Do not present gross profit until coach
  costs are entered.
- **2026 class-enrolment units are blank on purpose.** The 2026 Class/Event export's enrolment
  column covers `1/1/2025 – 7/28/2026` (19 months) against 7 months of revenue. Unusable. Only Pro
  Shop, private lessons and membership have valid 2026 units.
- **Team enrolment double-counts athletes.** Team records include both hour-tier billing groups and
  zero-dollar practice/roster containers. Summing across all 18 gives 288 for roughly 77 people.
  Team *revenue* is safe; team *headcount* is not.
- **Team revenue cannot be split by gender.** Billing groups are priced by training hours and are
  gender-blind.
- **Meet entry fees are largely pass-through.** In 2023, $140,104 of the $517,731 Team total was meet
  entries collected on behalf of host gyms. Team gross margin is meaningless until this is separated.
  The 2024/2025/2026 splits have **not** been done.
- **Coach names in private-lesson notes are free text** and probably contain duplicates
  (Kel/Kjeld, Dani/Danica, Nikki/Nicole). Needs a human pass before use.
- **`MAG A.` in the instructor field is a generic/admin account**, not a person. Exclude it.
- Historical class prices are unavailable — the class list export covers the current session only.
  So revenue movements cannot be decomposed into price versus volume effects without re-running the
  class list with archived sessions included.

## Environment

**Legacy analysis track** — Python 3 with `openpyxl` and `pandas`; Node with `docx`
(`npm install docx`) for the Word profile.

**Platform track** — Python **≥ 3.11**, installed with `pip install -e .` (or
`pip install -r requirements.txt`). Dependencies: `duckdb`, `pandas`, `openpyxl`, `xlrd` (for the
legacy `.xls` exports), `pydantic`, `pydantic-settings`, `PyYAML`, `typer`, `mcp`. Dev extras in
`requirements-dev.txt`. Package is `cfo-platform` v0.1.0, CLI entry point `cfo-platform`.
`pyproject.toml` is the source of truth for dependencies — keep `requirements.txt` in sync.

**System tools** — `pdftotext` is required by `parse_rsr.py` (legacy track) and by
`JackrabbitClassImporter` (platform track), and it must specifically be a **Poppler** build, not
Xpdf or any Xpdf-derived clone (this includes the `pdftotext` bundled with Git for Windows/MSYS2,
which many Windows dev machines have on PATH already). Xpdf renders this report's `-layout` column
alignment differently and silently breaks the parser — it looks like a reconciliation failure, not an
environment problem. The platform track detects this automatically
(`check_pdftotext_is_poppler()` in `importers/jackrabbit/revenue_summary_parser.py`) and raises a
clear, actionable error; the legacy `parse_rsr.py` does not, so if its numbers look wrong, check this
first. Point `CFO_PDFTOTEXT_PATH` at a specific binary if Poppler isn't first on PATH. LibreOffice
(`soffice`) recalculates workbooks and renders for visual checks. `pdftoppm` renders PDF pages to
images.

**Git** — repo is on `main`; run `git log` for history rather than trusting a commit list in this
file, which would go stale. `.claude/` is currently untracked; add it to `.gitignore` or commit it
deliberately.

**External gotcha** — Jackrabbit's help site renders client-side; a plain HTTP fetch returns only the
nav shell. Use a real browser if you need their documentation.
