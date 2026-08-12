# Architecture

This repo now holds two things:

| | Location | Status |
|---|---|---|
| **Legacy MAG analysis** | `scripts/`, `outputs/`, `data/raw/` | Done for revenue/units; see `CURRENT_STATUS.md`. One-off, hardcoded-figures pipeline described in `CLAUDE.md`. |
| **AI CFO platform** | `src/cfo_platform/` | Warehouse + `JackrabbitClassImporter` built and verified (Phase 2, see `CURRENT_STATUS.md`). `Analyzer`/`ReportBuilder` still not built. |

The platform is designed to serve multiple clients; MAG is the first. It does
not replace the legacy analysis yet — the importer proves out against the same
numbers, but nothing yet renders a client deliverable from the warehouse, and
retiring the legacy scripts is still future work.

Full design detail: [`docs/architecture/overview.md`](docs/architecture/overview.md).

## Quick orientation

```
config/                   Non-secret defaults + per-client YAML config
src/cfo_platform/
├── settings.py            Env-driven process settings (pydantic-settings)
├── logging_config.py      dictConfig logging, driven by config/logging.yaml
├── core/                  Shared exceptions, domain models, constants
├── clients/               Per-client config loading (ClientProfile, registry)
├── db/                    DuckDB connection (one file per client) + migrations (0001-0003)
├── importers/jackrabbit/  JackrabbitClassImporter — extract/transform/load, DONE and verified
├── analytics/             Analyzer contract + registry — NO concrete analyzer yet
├── reporting/              ReportBuilder contract + registry — NO concrete builder yet
├── mcp_server/            MCP server skeleton (health-check tool only)
└── cli.py                 `cfo-platform` CLI (clients, db-migrate, db-import work; report stub)
tests/                     unit/ + integration/ (incl. a `regression` marker), 45 tests, pytest
docs/architecture/         Overview, data model, ADRs, client-onboarding guide
```

## What computes now, and what still doesn't

Phase 2 (see `CURRENT_STATUS.md` for the full validation results) filled in the first concrete
`Importer`: `JackrabbitClassImporter` reads all four Jackrabbit exports, applies the reconciliation
gate and enrolment de-duplication from `CLAUDE.md`, and writes revenue/class-enrolment facts to
DuckDB — verified to reconcile exactly against the legacy analysis's validated numbers.

Still not built: any `Analyzer` (service-line profitability, cost-of-sales allocation — blocked on
payroll data, see `NEXT_STEPS.md` Phase 3), any `ReportBuilder`, and any payroll/cost-of-sales schema
or importer. Those remain informed by `CLAUDE.md`'s existing rules the same way the Jackrabbit
importer was.

## Relationship to `CLAUDE.md`

`CLAUDE.md` has been updated to describe both tracks — its Architecture section now names the split
explicitly, so the old "There is no application here" line is gone.

Its analysis rules were written for the legacy scripts but **apply to the platform too**. Status
against the Jackrabbit importer:

- reconciliation to zero variance (rule 1) — **done**: `ReconciliationError` refuses to load a period
  whose revenue doesn't match the reported total, rather than printing a warning.
- revenue-basis vs units-basis must stay distinguishable in the data model (rule 4) — **done**:
  `fact_revenue` and `fact_class_enrolment` are separate tables at separate grains.
- enrolment de-duplication on `Class + Session + Cat3` (rule 5) — **done**, verified exact against the
  legacy benchmark.
- never sum mixed units (rule 2) — **done**: `dim_service_line.is_class_enrolment_comparable` marks
  exactly the 7 comparable rows; nothing sums the whole `fact_class_enrolment` table.

The same rules apply to the payroll importer that hasn't been built yet (`NEXT_STEPS.md` Phase 3) —
build order and traps to carry forward are there under "Platform track".
