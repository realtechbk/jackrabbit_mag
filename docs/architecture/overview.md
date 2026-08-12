# cfo_platform — architecture overview

## Goal

A multi-client "AI CFO" platform: pull financial/operational data out of
whatever practice-management or accounting system a client uses, land it in
a queryable warehouse, compute profitability analytics on top, and expose
both the raw data and the analytics to (a) generated report deliverables and
(b) an MCP server so an LLM client (e.g. Claude) can answer ad-hoc questions
about a client's numbers.

MAG (Maine Academy of Gymnastics) is the first client, importing from
Jackrabbit Class. The platform is built so the second client — different
source system, different service-line taxonomy — is a config + one new
`Importer`/`Analyzer` subclass, not a fork of the codebase.

## Layers

```
config/clients/<id>.yaml   <-- one file per client: source system, warehouse
                                file, fiscal calendar, raw data location
        |
        v
clients.registry           <-- loads + caches ClientProfile
        |
        v
db.connection               <-- one DuckDB file per client (see ADR 0002)
        |
        v
db.migrations                <-- schema evolves via versions/NNNN_*.sql,
                                 tracked in schema_migrations
        |
        v
importers.*                <-- Importer subclasses: extract (read source
                                files) -> transform (source shape -> warehouse
                                schema) -> load (write to DuckDB)
        |
        v
analytics.*                 <-- Analyzer subclasses: SQL/pandas over the
                                warehouse -> a result DataFrame
        |
        v
reporting.* / mcp_server.*  <-- ReportBuilder subclasses render analyzer
                                output to client deliverables (Excel/Word);
                                MCP tools expose the same data/analytics to
                                an LLM client interactively
```

`cli.py` is the operator-facing entrypoint: `cfo-platform clients`,
`db-migrate <client_id>` work today; `db-import` and `report` are stubs
until the layers above them exist.

## Why this shape

- **Config, not code, varies per client.** `ClientProfile` covers what
  differs between clients (source system, timezone, fiscal year, file
  locations). Anything that would require an `if client_id == "mag"` in
  shared code instead becomes a new `Importer`/`Analyzer` registered for
  that client's `source_system`, or a value in that client's YAML.
- **Registries over hardcoded dispatch.** `importers.registry`,
  `analytics.registry`, `reporting.registry` all follow the same
  `register_x(key)` decorator + `get_x_class(key)` lookup pattern, so a new
  client's plugins are additive — no shared file needs editing to add one.
- **DuckDB, one file per client.** Embedded (no server to run or secure),
  fast for the OLAP-shaped queries a profitability grid needs, and trivial to
  hand pandas/Arrow data to from `importers`/`analytics`. See ADR 0001 for
  why DuckDB and ADR 0002 for why one file per client rather than a shared,
  multi-tenant database.
- **The reconciliation discipline from `CLAUDE.md` is a first-class
  exception, not a comment.** `core.exceptions.ReconciliationError` exists so
  that when analytics/reporting code is written, "this doesn't tie back to
  the source report" is a typed failure, not a printed variance someone can
  ignore.

## What's built (Phase 2) and what's still NOT here

- **`JackrabbitClassImporter`** (`importers/jackrabbit/`) — extract/transform/
  load for all four Jackrabbit exports, registered for
  `source_system: jackrabbit_class`. The Revenue Summary PDF parsing is a
  faithful port of `scripts/parse_rsr.py` (same algorithm, same documented
  traps), not a rewrite. Runs via `cfo-platform db-import <client_id>`.
- **Warehouse schema for revenue and class enrolment** exists (migrations
  `0002_jackrabbit_raw`, `0003_mag_service_line_facts` — see
  `docs/architecture/data-model.md`). Reconciliation to the Revenue Summary's
  stated total is enforced as a typed `ReconciliationError` at load time
  (CLAUDE.md rule 1), and de-duplication of class enrolment on
  `Class + Session + Cat3` (rule 5) is verified exact against the legacy
  analysis's 5,684 / 6,199 / 6,341 totals for 2023-2025 — see
  `tests/integration/test_jackrabbit_importer.py`.
- Still **no concrete `Analyzer`** (service-line profitability, cost-of-sales
  allocation) — the warehouse has revenue and enrolment facts, but nothing
  yet computes the grid in `outputs/MAG_ServiceLinePerformance_v8.xlsx` from
  them.
- Still **no concrete `ReportBuilder`** (the legacy `scripts/build_*.py`
  outputs are not wired in).
- Still **no cost-of-sales / payroll** anything — out of scope until a
  payroll data source is chosen (unchanged from before Phase 2).
- Still **no real MCP tools** beyond a `ping` health check — explicitly out
  of scope for this phase.
- Sales Detail and Class List land in raw tables only; no unit-level
  analytics (Pro Shop item classification, coach hours) are built on them
  yet.

## Migrating the legacy MAG analysis

Partially done (Phase 2, above): the importer and warehouse schema exist.
What's left:

1. ~~Write a `JackrabbitClassImporter(Importer)`~~ — done.
2. ~~Design the warehouse schema~~ — done for revenue and class enrolment;
   Sales Detail / Class List unit analytics still to design.
3. Write a `ServiceLineProfitabilityAnalyzer(Analyzer)` that reproduces the
   grid in `outputs/MAG_ServiceLinePerformance_v8.xlsx` from the warehouse.
4. Only then does a `ReportBuilder` or MCP tool make sense — they render or
   serve the analyzer's output, they don't compute it themselves.

## See also

- `docs/architecture/data-model.md` — what's in the warehouse today and what
  isn't yet.
- `docs/architecture/adr/` — decision records (DuckDB, warehouse-per-client).
- `docs/architecture/onboarding-new-client.md` — steps to add client #2.
