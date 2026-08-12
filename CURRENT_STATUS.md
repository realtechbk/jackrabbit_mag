# CURRENT_STATUS.md

Last updated: 11 August 2026.

## The one-paragraph version

Two independent tracks live in this repo (see `ARCHITECTURE.md`). **Phase 1 — legacy analysis:**
revenue and unit counts for MAG are fully mapped and reconciled to zero variance for 2023, 2024, 2025
and 2026 YTD, delivered as Excel/Word documents in `outputs/`. Cost of Sales has not been started on
that track — it does not exist in Jackrabbit and requires coach payroll data. **Phase 2 — AI CFO
platform:** just completed. A real `JackrabbitClassImporter` now ingests the MAG source files into
DuckDB, and its output has been verified exactly against the Phase 1 validated figures — see "Phase 2
validation results" below. **Phase 3 — Payroll Management report analysis — is next** (not started):
Cost of Sales, on both tracks, needs coach payroll data that hasn't existed anywhere in this repo
until now. Read `NEXT_STEPS.md` before starting it.

---

## Phase 1 — Legacy MAG analysis (`scripts/`, `outputs/`, `data/raw/`)

**Status: revenue and unit counts done and reconciled. Cost of Sales not started.** Because Cost of
Sales is empty, every gross-profit figure in the workbook currently equals revenue and **must not be
presented to the client**.

### ✅ Completed

**Revenue mapping — done and verified**
- All four periods parsed from the Revenue Summary PDFs and mapped to 18 service rows.
- **Zero variance on all four periods.** Verified programmatically; the build script prints it.
- The `--No Activity Name--` decomposition fully explains the previously "unattributed" $94,922
  (2025) down to $0.00 residual. 2023 and 2024 leave $36.00 and $671.40, both traced to three
  specific classes with no Category 1.

**Unit counts — done for everything Jackrabbit supports**
- Class enrolments for the 7 comparable rows, de-duplicated: **5,684 / 6,199 / 6,341** (2023/2024/2025).
- Open Gym bookings, birthday parties, retail items, private lessons, gift certificates.
- Membership units as a live formula (revenue ÷ $45).

**Category / structure investigation — done**
- Cat1/Cat2/Cat3 hierarchy understood and documented (`DATA_DICTIONARY.md`).
- Category drift across years identified and quantified.
- Team's triple-enrolment structure identified; 2023 tuition-vs-meet-fee split completed.
- The eight untagged 2025 "Workshops & Class Series" classes identified by name, with their correct
  destinations ($1,364 → Tumbling, $1,770 → Girls Wings).

**Store / retail analysis — done**
- 81 item numbers classified into merchandise vs fee/service.
- Team apparel identified as posting under Cat1 Team, explaining the Pro Shop reconciliation gap.
- Destira leotard confirmed as the $42.20 SKU ($40 + 5.5% Maine tax).
- Falmouth Rec 70/30 revenue share decoded from the Note field and verified against totals.
- Private-lesson coach attribution extracted (91% coverage in 2026).

**Deliverables shipped**
| File | Status |
|---|---|
| `outputs/MAG_ServiceLinePerformance_v8.xlsx` | **Current.** 3 tabs, 4 periods, 18 rows. |
| `outputs/MAG_RevenueByService_2023-2026YTD.xlsx` | **Current.** Revenue-only view + findings + drift tabs. |
| `outputs/MAG_JackrabbitClassMapping.xlsx` | Current. 176 classes mapped, zero unmapped. |
| `outputs/MAG_CompanyProfile_v2.docx` | Current. 5-page business profile. |
| `outputs/MAG_JackrabbitCrosswalk_template.xlsx` | Reusable blank crosswalk template. |
| `outputs/superseded/` | 11 earlier versions, retained deliberately. |

### 🟡 Partially completed

**Team tuition vs meet-fee split — 2023 only.** 2023 is split: **$377,627.07 tuition / $140,104.38
meet fees & other**. The same split for 2024, 2025 and 2026 has **not** been done. Until it is, the
Team row mixes real tuition with pass-through meet entries and team gross margin cannot be calculated.
The method is established — sum the billing-group activity lines from the parsed Revenue Summary and
treat the residual as meet fees.

**Instructor attribution — current session only.** Coach-hours per service line are calculated for
the 2026-27 session from the Class List. But joining *historical revenue* to instructors via class
name covers only **58% of 2026 and 37% of 2025** revenue, because the class list holds only the
current session. Not reliable enough to build on.

**Coach identification in private lessons — extracted but not cleaned.** Coach names pulled from
free-text notes. Coverage 8% / 9% / 46% / 91%. The name list almost certainly contains duplicates
(Kel/Kjeld, Dani/Danica, Nikki/Nicole) and needs a human pass.

**Falmouth Rec and Visiting Team rental — quantified but not on the grid.** Both are real revenue
with full quantities and economics documented on the `Store Detail` tab. They are **not** on the main
grid because their Jackrabbit Cat1 could not be verified — see Known Problems.

### ❌ Not started

**Cost of Sales — the big one, now Phase 3.** Nothing has been done. It does not exist in Jackrabbit.
What is needed: (1) coach hourly rates from payroll or the bookkeeper — not requested yet; (2) actual
hours worked from `Reports → Clock` — not pulled. Scheduled coach-hours per service line *are*
available for the current session (see `NEXT_STEPS.md`) and can serve as a fallback if actual hours
prove hard to get. Consequence: `Cost of Sales %`, `Total Cost of Sales`, `Gross Profit` and
`Gross Profit %` are all empty or meaningless in the current workbook.

**Pro Shop cost of goods.** Pro Shop is the one row where cost of sales is inventory purchase cost,
not labour. No supplier cost data has been obtained. Destira wholesale pricing would be the place to
start.

**Price-versus-volume decomposition.** Cannot be done — historical class prices are unavailable
because the class list export covers only the current session. Fixable by re-running the Class List
with archived sessions included.

**Same-period 2026 comparison.** 2026 YTD is currently compared to full years via a straight-line
annualisation, which ignores seasonality (July sits in the summer trough). The honest version needs
Revenue Summary run for 1 Jan – 28 Jul in 2024 and 2025 so the seasonality cancels. Two reports, not
yet pulled.

**Client-facing presentation.** No deck or presentation has been built. Everything so far is working
analysis.

---

## Phase 2 — AI CFO platform (`src/cfo_platform/`)

**Status: done as of 2026-08-11.** The Jackrabbit Class importer is built, tested, and verified
against real MAG source data end to end. This closes out the platform's first concrete
importer/warehouse milestone described in `docs/architecture/overview.md`.

### What was completed

- **Warehouse schema** (migrations `0001_init`, `0002_jackrabbit_raw`, `0003_mag_service_line_facts`):
  raw landing tables per Jackrabbit report type, source-file lineage/dedupe (`source_files`, unique on
  `client_id + file_sha256`), `dim_service_line` + `dim_jackrabbit_category_map` (seeded from
  `mapping.py`, the single source of truth), `fact_revenue`, `fact_class_enrolment`.
- **`JackrabbitClassImporter`** (`src/cfo_platform/importers/jackrabbit/`): extract → transform → load
  for all four Jackrabbit exports (Revenue Summary PDF, Class/Event Revenue Summary, Sales Detail,
  Class List). The Revenue Summary parser is a faithful port of `scripts/parse_rsr.py` — same
  algorithm, same documented traps — not a rewrite.
- **Reconciliation gate**: revenue that doesn't tie to the report's stated total raises a typed
  `ReconciliationError` and is refused, never silently loaded (CLAUDE.md rule 1, enforced in code, not
  just printed as a warning).
- **Class-enrolment de-duplication** on `Class + Session + Cat3` (CLAUDE.md rule 5), implemented and
  verified exact against the Phase 1 benchmark.
- **Duplicate-import prevention** by file content hash (`source_files.file_sha256`), independent of
  filename — re-importing the same bytes under a different name is still a no-op.
- **Per-file failure isolation**: one bad file (e.g. a broken PDF render) excludes only that file and
  its report type from a run; unrelated report types still load and the run's other data is not held
  hostage.
- **`pdftotext` environment check** (`check_pdftotext_is_poppler()`): catches an incompatible
  pdftotext build with one clear, actionable error instead of a confusing reconciliation variance.
  Configurable via `CFO_PDFTOTEXT_PATH` if Poppler isn't first on PATH.
- **Wired into the CLI**: `cfo-platform db-import mag` runs the real pipeline end to end.
- **45 automated tests**, all passing — see "Test count / status" below.

Sales Detail and Class List are landed in raw tables only; no unit-level analytics (Pro Shop item
classification, coach hours) are built on them yet — that is future work, not an oversight.

### Current architecture (platform track)

```
config/clients/mag.yaml               Client profile (source_system: jackrabbit_class)
src/cfo_platform/
├── settings.py                        Env-driven settings (+ CFO_PDFTOTEXT_PATH)
├── db/migrations/versions/
│   ├── 0001_init.sql                   import_runs, schema_migrations
│   ├── 0002_jackrabbit_raw.sql          source_files + raw_* landing tables
│   └── 0003_mag_service_line_facts.sql  dim_service_line, dim_jackrabbit_category_map,
│                                        fact_revenue, fact_class_enrolment
├── importers/jackrabbit/
│   ├── importer.py                     JackrabbitClassImporter (extract/transform/load)
│   ├── revenue_summary_parser.py       ported PDF parser + check_pdftotext_is_poppler()
│   ├── readers.py                      xlsx/xls readers (Class/Event Revenue, Sales Detail, Class List)
│   ├── dedupe.py                       Class+Session+Cat3 de-dup (CLAUDE.md rule 5)
│   ├── mapping.py                      Cat1/Cat2 -> service_line_key (single source of truth)
│   └── validation.py                   reconciliation checks (typed ReconciliationError)
├── analytics/, reporting/              STILL contracts only — no concrete Analyzer/ReportBuilder yet
├── mcp_server/                         STILL skeleton — health-check tool only, out of scope for now
└── cli.py                              `clients`, `db-migrate`, `db-import` work; `report` still a stub
tests/
├── unit/                               parser, mapping, dedupe, pdftotext-check (fast, fixture-based)
└── integration/                        real-file tests + the revenue regression suite (`-m regression`)
```

`analytics/` (a `ServiceLineProfitabilityAnalyzer` reproducing the Phase 1 grid from the warehouse),
`reporting/` (an Excel/Word `ReportBuilder`), and any payroll/cost-of-sales schema are **not built** —
none of that was in scope for Phase 2.

### Phase 2 validation results

Revenue Summary PDFs processed successfully using **Poppler** pdftotext 24.09.0 (see "Environment
considerations" below for why the specific build mattered).

| Period | DB-computed revenue | Report's stated total | Variance |
|---|---|---|---|
| 2023 | $1,996,290.52 | $1,996,290.52 | **$0.00** |
| 2024 | $2,297,353.81 | $2,297,353.81 | **$0.00** |
| 2025 | $2,241,034.37 | $2,241,034.37 | **$0.00** |
| 2026 YTD | $1,126,223.32 | $1,126,223.32 | **$0.00** |
| **Combined, all four periods** | **$7,660,902.02** | | |

- **Service-line revenue**: every one of the 18 service lines × 4 periods matches
  `scripts/build_perf_v8.py`'s validated legacy `ROWS` figures exactly — zero mismatches, cell for
  cell.
- **Class enrolment** (de-duplicated, 7 comparable rows): **5,684 / 6,199 / 6,341** for
  2023/2024/2025, matching the Phase 1 figures above exactly. 2026 is intentionally excluded from this
  benchmark — its Class/Event export's enrolment window is defective (19 months vs 7 months of
  revenue), same limitation as on the legacy track.
- All of the above is proven by a **permanent regression test**
  (`tests/integration/test_revenue_regression.py`, marked `regression`) that runs the real
  `JackrabbitClassImporter` against the real `data/raw/*.pdf` files — not a fixture — so this exact
  result is re-verified on every full test run, not just asserted once by hand.

### Test count / status

**45/45 passing** (`pytest tests/`, ~40s):
- Unit (fast, fixture-based): Revenue Summary parser traps, Cat1/Cat2 mapping, enrolment de-dup,
  pdftotext-environment-check.
- Integration (real files): import correctness, re-import idempotency, duplicate-file detection,
  broken-pdftotext isolation behaviour.
- Regression (`pytest -m regression`; 4 of the 45, also included in a full `pytest tests/` run): the
  real-PDF revenue reconciliation in the table above. Exclude from a fast local loop with
  `pytest -m "not regression"`.

### Environment considerations

- **Poppler is required, not just "a" pdftotext.** This machine's `pdftotext` was originally an Xpdf
  clone (bundled with Git for Windows/MSYS2) — it renders this report's `-layout` column alignment
  differently from Poppler and silently broke the parser (looked like a data reconciliation failure,
  not an environment problem, until diagnosed). Installed via `conda install -c conda-forge poppler`;
  now resolves at `.../conda3/Library/bin/pdftotext.exe`, version 24.09.0, ahead of the old Xpdf build
  already on PATH.
- **A fresh environment must have Poppler's pdftotext on PATH** (or point `CFO_PDFTOTEXT_PATH` at it)
  before running `cfo-platform db-import` or the regression test. `check_pdftotext_is_poppler()`
  raises a clear `ConfigurationError` naming the exact fix if it's missing or the wrong build, rather
  than failing mysteriously — see `src/cfo_platform/importers/jackrabbit/revenue_summary_parser.py`.
- `xlrd` is now an explicit dependency (was previously used transitively but undeclared) — needed for
  the legacy `.xls` exports (Sales Detail, Class List).

### Latest relevant commits

- `5ccc6ba` — feat: complete Jackrabbit ingestion pipeline. Migrations `0002`/`0003`, the importer,
  CLI wiring, initial 35 tests.
- `a68301e` — fix: resolve Poppler pdftotext dependency and add revenue regression test. The
  `pdftotext`/Poppler environment check, per-file failure isolation fix, CLI error handling, and the
  permanent real-PDF regression suite — brings the count to 45 tests.

Five documentation files (`CLAUDE.md`, `ARCHITECTURE.md`, `CURRENT_STATUS.md` (this file),
`NEXT_STEPS.md`, `README.md`) had pre-Phase-2 edits sitting uncommitted before this update; that
predates the Phase 2 coding session and is being reconciled with the Phase 2 status separately — see
the session's own notes for exactly what changed.

---

## Phase 3 — next phase: Payroll Management report analysis

**Not started.** This is Cost of Sales, on both tracks at once: the Phase 1 grid's Cost of Sales
columns are still empty, and nothing in `src/cfo_platform/` ingests payroll data yet (no schema, no
importer). See `NEXT_STEPS.md` for the task breakdown — coach hourly rates, actual hours from
`Reports → Clock`, and the Pro Shop exception (inventory cost, not labour). Do not begin without
reading `NEXT_STEPS.md` and this file first.

---

## Known problems and unresolved questions

*(Phase 1 / data-quality findings — unaffected by the Phase 2 platform work above.)*

### Data problems

1. **The 2026 Class/Event export is defective.** Enrolment column covers `1/1/2025 – 7/28/2026`
   (19 months) against 7 months of revenue. 2026 class-enrolment units are therefore blank. Its
   revenue also differs from the Revenue Summary by $775. **Needs re-running with matching dates.**
2. **$12,817.63 of unapplied payments by July 2026**, up from $172 in 2023 — and *worsening*. Real
   cash sitting unallocated on family accounts. Independent of the analysis; an operational item.
3. **Late fees rising sharply** — 8 → 7 → 24 → 46 charges. Same underlying story as #2: collections
   are drifting.
4. **$24,120 of unlinked tuition in 2025** (Recreational $16,503 + Team $7,617). Preventable going
   forward by posting tuition through the class-linked routine and inactivating rather than deleting
   classes. Not economically recoverable retroactively (~100 transactions/year at 0.7% of revenue).
   Trend is strongly positive: down 54% from the 2024 peak.
5. **Eight 2025 classes have no Category 2** ("Workshops & Class Series"), plus three classes across
   2023/2024 with no Category 1 at all. All identified by name. Fixing them in Jackrabbit corrects
   every historical report automatically, because the reports read each class's *current* category.
6. **Staff category spiked to $10,226.82 in 2024** from $2,660 the prior year and $3,825 after. No
   explanation found.

### Unresolved questions — for the client

1. **Which Cat1 do `FALREC` and `VTM` post to?** One lookup in Jackrabbit (`Store` → item setup →
   revenue category). This both unblocks promoting them to the grid **and** may explain a large share
   of the unlinked tuition bucket — Falmouth Rec alone is $8,258 in 2023, about 38% of that year's
   unlinked total.
2. **Was Birthday Parties a deliberate exit?** $45,767 → $19,038 → nil, with almost no coach cost
   attached. The website still shows party photographs but has no Parties page.
3. **Did Falmouth Rec end, or did MAG end it?** $8,258 → $8,201 → $4,242 → nil.
4. **Is the American Flyers Cup on MAG's books or the Booster Club's?** Partially answered — Cup
   revenue *does* appear under Cat1 Team ($9,445 for the 2023 and 2024 editions). But the American
   Flyers Booster Club is a separate 501(c)(3) and may hold other Cup revenue.
5. **What is "Non-Instructional time"?** New Cat1 in 2025, $340. Small, but worth knowing before it
   grows.
6. **Is Susan an employee or a contractor?** She is the entire premium ancillary line — private
   lessons plus the Xcel clinic. A material concentration risk either way. **Directly relevant to
   Phase 3** if she's a contractor: contractor payments may not appear in a payroll report at all.

### Methodological caveats to preserve

1. **The membership-fee student proxy is wrong.** Revenue ÷ $45 implies 1,295 / 1,370 / 1,173
   students, i.e. a 14% fall in 2025. Class enrolments went the *other way* (+2.3%). Treat the
   membership figure as a billing-timing artefact. It is flagged in the workbook — keep it flagged.
   An earlier draft of the analysis led with the 14% figure; that was wrong and was retracted.
2. **Revenue and units come from different reports** with a ~1–2% attribution difference. Documented
   on the sheet. Never silently mix them.
3. **Girls Wings' +33.6% in 2024 is overstated** by roughly the $26,248 of Pre-Team revenue that
   folded into it when the `Pre-Team (Invite Only)` Cat2 disappeared.
4. **Coach-hours assume each listed instructor works the full class duration**, which overstates
   hours where a coach floats between groups. **Directly relevant to Phase 3.**
