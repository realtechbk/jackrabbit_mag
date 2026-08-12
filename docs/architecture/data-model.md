# Data model

## Today

Each client has one DuckDB file at `data/warehouse/<warehouse_file>` (per
`config/clients/<id>.yaml`). Three migrations have run for MAG:

| Migration | Tables |
|---|---|
| `0001_init` | `schema_migrations` (tracks applied migrations), `import_runs` (one row per importer run: `client_id`, `source_system`, start/finish time, status). |
| `0002_jackrabbit_raw` | `source_files` (lineage + dedupe spine, unique on `client_id, file_sha256`), and one raw landing table per Jackrabbit report: `raw_revenue_summary_activities` / `_cat1_totals` / `_cat2_totals` / `_totals`, `raw_class_event_revenue_rows`, `raw_sales_detail_rows`, `raw_class_list_rows`. |
| `0003_mag_service_line_facts` | `dim_service_line`, `dim_jackrabbit_category_map` (both seeded at import time from `importers/jackrabbit/mapping.py`, not by the migration itself), `fact_revenue`, `fact_class_enrolment`. |

Populated by `JackrabbitClassImporter` (`importers/jackrabbit/`), registered
for `source_system: jackrabbit_class` and run via `cfo-platform db-import
<client_id>`. See that package's module docstrings for the extract/transform/
load split and `tests/integration/test_jackrabbit_importer.py` for the
end-to-end reconciliation proof.

**What's covered:** revenue (`fact_revenue`, reconciled to the Revenue
Summary's stated total — CLAUDE.md rule 1, enforced as a typed
`ReconciliationError` at load time, not a printed warning) and class
enrolment (`fact_class_enrolment`, de-duplicated per rule 5; verified exact
against `CURRENT_STATUS.md`'s 5,684 / 6,199 / 6,341 for 2023-2025). Sales
Detail and Class List are landed raw only — no unit/cost-of-sales analytics
are built on them yet (Pro Shop units, coach hours); that's future work, not
a Phase 2 gap in the sense of being unconsidered.

**Known limitation:** Revenue Summary parsing depends on `pdftotext -layout`
producing single-line rows exactly as Poppler renders them. This
environment's `pdftotext` is an Xpdf build, which wraps this report's
columns differently and breaks that assumption — the importer's
reconciliation gate correctly refuses to load the real PDFs here rather than
produce a wrong number, but that means revenue import currently only proves
out end-to-end against fixture text, not the real files, in this specific
environment. Installing Poppler's `pdftotext` should resolve it without any
code change; the parser itself is a faithful, tested port of
`scripts/parse_rsr.py`.

## What comes next (not built)

- **Cost of sales (coach payroll).** No source yet in Jackrabbit — can't be
  designed until a payroll data source is chosen (CLAUDE.md, Phase 2 scope
  explicitly excludes this).
- **Sales Detail / Class List analytics.** Raw rows are landed; item
  classification (Pro Shop units, team apparel exclusion) and coach-hours
  extraction are not yet built into fact tables.
- **`ServiceLineProfitabilityAnalyzer`.** The `analytics/` layer that would
  reproduce `outputs/MAG_ServiceLinePerformance_v8.xlsx`'s grid from these
  facts hasn't been built — Phase 2 stopped at the warehouse, per scope.
- **Team tuition vs. meet-fee split**, **Falmouth Rec / Visiting Team
  rental category verification**, and other open items in `NEXT_STEPS.md`
  are unaffected by this layer and still require the underlying Jackrabbit
  data/category questions to be resolved first.

## Per-client schema variation

Different clients will need different fact tables (a gym's cost of sales is
coach labour; a retail client's is inventory). The convention going forward:
migrations for one client's schema additions live under
`db/migrations/versions/` with a client-scoped prefix once more than one
client has custom tables, e.g. `0002_mag_revenue_facts.sql`. Tables genuinely
common to every client (like `import_runs`) stay unprefixed.
