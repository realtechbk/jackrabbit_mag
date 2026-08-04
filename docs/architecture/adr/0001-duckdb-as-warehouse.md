# ADR 0001: DuckDB as the warehouse engine

## Status

Accepted.

## Context

The platform needs somewhere to land imported client data and run
analytical (aggregate, group-by-heavy) queries over it, then hand results to
pandas for reporting and to an MCP server for ad-hoc LLM queries. Candidates
considered: SQLite, Postgres, DuckDB.

## Decision

Use DuckDB.

- **Embedded, zero-ops.** No server process to run, deploy, or secure per
  client — a hard requirement for a consultant running this locally against
  many small clients' data.
- **OLAP-shaped.** Columnar execution suits the aggregate-heavy queries a
  profitability grid needs (sums/group-by over revenue, units, cost) far
  better than SQLite's row store.
- **First-class pandas/Arrow interop.** Importers and analyzers already work
  in pandas (existing `scripts/` use it); DuckDB reads/writes DataFrames
  without a serialization step.
- **SQL for reporting and for MCP tools.** Both the reporting layer and MCP
  tools can express what they need as SQL against the warehouse rather than
  bespoke Python aggregation code.

## Consequences

- No concurrent-writer story (DuckDB's single-writer model). Acceptable: each
  client's data is imported by one process at a time, not written to
  concurrently by multiple users.
- Cross-client queries require `ATTACH`-ing multiple files (see ADR 0002) —
  acceptable since analysis is per-client, and this platform doesn't yet do
  cross-client aggregate reporting.
