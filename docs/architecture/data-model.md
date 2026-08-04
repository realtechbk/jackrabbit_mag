# Data model

## Today

Each client has one DuckDB file at `data/warehouse/<warehouse_file>` (per
`config/clients/<id>.yaml`). Migration `0001_init` creates only:

| Table | Purpose |
|---|---|
| `schema_migrations` | Tracks which `versions/*.sql` files have run (created by the migration runner itself, not by `0001_init`). |
| `import_runs` | One row per importer run: `client_id`, `source_system`, start/finish time, status. Bookkeeping for the import pipeline layer, not business data. |

No fact or dimension tables exist yet. There is deliberately no schema for
revenue, enrolments, cost of sales, or anything MAG-specific — designing
that now, before an `Importer` exists to populate it, would be guessing.

## What comes next (not built)

When the first `Importer`/`Analyzer` pair is built (see
`docs/architecture/overview.md`), it should add its own migration(s) after
`0001_init`. Starting points, informed by the legacy analysis in
`DATA_DICTIONARY.md` and `CLAUDE.md`:

- A revenue fact table grained at whatever level reconciles to the Jackrabbit
  Revenue Summary (`CLAUDE.md` rule 1 — reconciliation to zero variance is
  non-negotiable, so the grain should make that check a single `SUM`).
- A units/enrolment fact table at a *different* grain, since `CLAUDE.md` rule
  2 forbids summing `# Units Sold` across rows with different units, and rule
  5 requires de-duplicating on `Class + Session + Cat3` before summing
  enrolments.
- A `service_line` dimension carrying the `[Revenue Group] -- [Sub Group]`
  naming convention, including the `Review --` and `EXCLUDE --` buckets as
  first-class rows rather than special-cased strings.
- Cost-of-sales (coach payroll) has no source yet in Jackrabbit — that table
  can't be designed until a payroll data source is chosen.

## Per-client schema variation

Different clients will need different fact tables (a gym's cost of sales is
coach labour; a retail client's is inventory). The convention going forward:
migrations for one client's schema additions live under
`db/migrations/versions/` with a client-scoped prefix once more than one
client has custom tables, e.g. `0002_mag_revenue_facts.sql`. Tables genuinely
common to every client (like `import_runs`) stay unprefixed.
