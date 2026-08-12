# NEXT_STEPS.md

Phase 1 (legacy revenue/units analysis) and Phase 2 (AI CFO platform ingestion) are done — see
`CURRENT_STATUS.md`. **Phase 3 — Payroll Management report analysis — is the next major task**, on
both tracks at once: the Phase 1 grid's Cost of Sales columns are empty, and the platform has no
payroll schema or importer yet. Everything below Phase 3 is either supplementary (cheap wins that can
run in parallel) or was already true before Phase 2 and is reordered accordingly.

---

## Phase 3 — Payroll Management report analysis (NEXT MAJOR TASK)

This is the whole right-hand half of the client's requested grid (`Total Cost of Sales`,
`Cost of Sales %`, `Total Gross Profit`) and **nothing has been done** on either track. Cost of sales
in a gym is coach labour — there is no cost-of-goods concept in Jackrabbit except Pro Shop. Start the
data request now; the analysis follows once payroll data exists.

### 3a. Pull `Reports → Clock`
The time clock gives **actual hours worked per staff member**. This is the single highest-value
dataset still outstanding. Actual beats scheduled, and captures the gap every gym has between the two.

### 3b. Obtain coach hourly rates
From payroll or MAG's bookkeeper. Likely the longest lead time in the project — request early. A
blended rate by seniority tier is acceptable if individual rates are sensitive. **Check first whether
Susan (the entire premium ancillary line — private lessons + Xcel clinic) is an employee or a
contractor** — if a contractor, she may not appear in a payroll report at all and needs a separate
data source.

### 3c. Fall back to scheduled hours if 3a or 3b stall
Already computed for the current session from the Class List:

| Service | Coach hrs/wk | Enrolled | Coach hrs per student |
|---|---|---|---|
| Girls Wings | 266.2 | 411 | 0.65 |
| Preschool | 74.0 | 211 | 0.35 |
| Team | 60.0 | ~77 unique | — |
| Boys Wings | 25.5 | 34 | **0.75** |
| Tumbling | 18.0 | 62 | 0.29 |

Caveats: assumes every listed instructor works the full class duration; `MAG A.` is a generic account
and must be excluded.

### 3d. Pro Shop is separate
Its cost of sales is **inventory purchase cost**, not labour. Destira wholesale pricing is the
starting point. Do not apply a labour percentage to this row.

### 3e. Platform-track payroll ingestion
Once a payroll data source is chosen (3a/3b), it needs the same treatment the Jackrabbit exports got
in Phase 2: a raw landing table with source-file lineage, a fact table at whatever grain reconciles
cleanly (coach × pay-period, most likely), and a reconciliation check before it's trusted — same
discipline as `CLAUDE.md` rule 1, same as `fact_revenue`'s gate. This is new schema (a migration after
`0003_mag_service_line_facts`), not an extension of the Jackrabbit importer — payroll is a different
source system. Only after that exists does a `ServiceLineProfitabilityAnalyzer` (`analytics/`) make
sense, since it needs both revenue and cost-of-sales facts to compute gross profit.

**Do not present gross profit to the client until this is populated** — every gross-profit figure
currently equals revenue on both tracks.

---

## Supplementary — cheap wins that can run in parallel with Phase 3

### P-A. Two five-minute Jackrabbit lookups

**Find the revenue category for `FALREC` and `VTM`.** Where: Jackrabbit → `Store` → item setup / item
list → check the revenue category mapped to item numbers `FALREC` and `VTM`. Why: cheapest task with
the largest payoff — unblocks two service rows *and* probably explains a large slice of the
unlinked-tuition bucket (Falmouth Rec alone is $8,258 in 2023, ~38% of that year's unlinked total).
Then: promote `Ancillary -- Falmouth Rec (70/30 contract)` and `Ancillary -- Visiting Team Rental` to
the main grid, reducing whichever row currently absorbs them, and re-run the reconciliation gate.

**Fix eleven class records.** Where: Jackrabbit → Classes → each class → set Category 2 (and
Category 1 where missing).
- Eight 2025 classes missing Category 2 (the Summer Tumble/Wings series and Bar Workshops) →
  correct destinations: $1,364 to Tumbling, $1,770 to Girls Wings.
- Three classes missing Category 1 entirely: White Wings/Intermediate F 4:00p (2023, $36), Gold
  Wings/Elite Plus F 5:30p (2024, $190), Tumbling Class - Su 3:00p (2024, $481.40).

Why: the reports read each class's *current* category, so fixing these corrects every historical
report automatically. Fifteen minutes of work makes 2023 and 2024 reconcile perfectly rather than
nearly, and removes the need for the Workshops row entirely.

### P-B. Re-run three defective or missing reports

- **Class/Event Revenue Summary for 2026, matching dates.** Current export's enrolment window is
  `1/1/2025 – 7/28/2026` (19 months) against 7 months of revenue. Re-run both windows as
  `1/1/2026 – <today>`. Also check whether the $775 revenue gap against the Revenue Summary closes.
- **Revenue Summary for 1 Jan – 28 Jul in 2024 and 2025.** The honest way to assess 2026 — same-period
  comparison makes seasonality cancel out, replacing the straight-line annualisation currently exposed
  as an editable assumption because it's weak.
- **Class List including archived sessions.** Unlocks historical prices, the only way to decompose
  revenue movements into price versus volume.

### P-C. Finish the Team split for 2024, 2025, 2026

2023 is done: $377,627 tuition / $140,104 meet fees. Method: from the parsed Revenue Summary, sum the
Cat1 Team activity lines matching the billing-group pattern (`Team Billing Group N hrs`, etc.);
everything else in Cat1 Team is meet entries, apparel and the unnamed residual. Team apparel
(~$5,329 in 2025) should come out as a third slice. Matters because Team is 25.2% of revenue and team
gross margin is uncalculable until this is separated — directly feeds Phase 3's cost-of-sales work for
the Team row.

### P-D. Operational findings to raise with the client now

No further analysis needed:
1. **Boys Wings is the clearest opportunity in the business** — 51.6% fill, three years of declining
   enrolments (277 → 247 → 239), flat revenue, highest coach-hours per student (0.75).
2. **Unapplied payments have grown to $12,818** (from $172 in 2023); late fees 8 → 46 charges.
3. **Preschool is shrinking** — 1,151 → 1,119 → 1,071, down 7%. The funnel feeder for every other line.
4. **Susan is a concentration risk** — see Phase 3's 3b note above.
5. **Four questions for MAG**: Birthday Parties exit? Falmouth Rec end? What is "Non-Instructional
   time"? Why did Staff spike to $10,227 in 2024?
6. **Website gaps**: stale COVID-19 notices, Super Flyers showing no classes, no published pricing,
   broken footer links, no Parties page.

### P-E. Build the client deliverable

No presentation has been built. Once Phase 3 lands, the deck writes itself around: revenue mix, the
enrolment-versus-yield story, Boys Wings, and the data-hygiene wins (unlinked tuition down 54%).

---

## Platform track (`src/cfo_platform/`) — status and next build step

Phase 2 completed the Jackrabbit importer and warehouse schema for revenue and class enrolment (see
`CURRENT_STATUS.md`) — items 1–2 below are **done**:

1. ~~Jackrabbit importer~~ — done (`importers/jackrabbit/`).
2. ~~Reconciliation as a first-class check~~ — done (`ReconciliationError`, enforced at load time).
3. **Payroll importer + schema** — not started. This is Phase 3's platform-track counterpart (see
   3e above). New source system, new migration, new raw/fact tables.
4. **`ServiceLineProfitabilityAnalyzer`** (`analytics/`) — not started. Needs both `fact_revenue` and
   a payroll-derived cost-of-sales fact table, so it waits on item 3. Mapping tables to reuse:
   `importers/jackrabbit/mapping.py` (already the single source of truth) and `DATA_DICTIONARY.md` §5.
5. **Report builder** (`reporting/`) — not started; can lift the openpyxl layout wholesale from
   `build_perf_v8.py`.
6. Only then consider retiring the legacy scripts.

**Housekeeping:** `.claude/settings.local.json` is untracked — commit it or add it to `.gitignore`.

---

## Explicitly NOT worth doing

- **Manual recovery of unlinked tuition transactions.** ~100 rows a year for 0.7% of revenue.
  Fix the posting habit instead.
- **Chasing true transaction counts.** Decided against (see DECISIONS D7) — it measures billing cadence,
  not demand.
- **Instructor-to-historical-revenue attribution via class name.** Tested: only 58% / 37% revenue
  coverage. Wait for `Reports → Staff` instead.
