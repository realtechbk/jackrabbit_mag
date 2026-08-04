# ADR 0002: One DuckDB file per client, not a shared multi-tenant database

## Status

Accepted.

## Context

Given DuckDB as the engine (ADR 0001), client data could live in one shared
database (tables carrying a `client_id` column) or in one DuckDB file per
client.

## Decision

One DuckDB file per client: `data/warehouse/<client's warehouse_file>`,
resolved from that client's `config/clients/<id>.yaml` via
`db.connection.warehouse_path`.

- **Isolation.** A bug in one client's importer/analyzer query can't leak or
  corrupt another client's data — there's no shared table to get a `WHERE
  client_id = ...` filter wrong on.
- **Offboarding is a file delete.** Client data can be handed back or
  destroyed independently, which matters for a consultancy with per-client
  engagements.
- **MCP server safety.** An MCP tool connects to exactly one client's file
  per session; there's no query shape that could accidentally return another
  client's numbers to an LLM conversation scoped to a different client.
- **Matches actual usage.** RealTech's engagements are analyzed one client at
  a time; there's no current need for a single query spanning clients.

## Consequences

- Cross-client reporting (e.g. "compare MAG to client #2") requires
  `ATTACH`-ing both files in one DuckDB session — not implemented, and not
  needed yet. If it becomes a real requirement, it's a few lines in a new
  analyzer, not a schema migration.
- Each client's schema can diverge (see `docs/architecture/data-model.md`)
  since migrations run per-file. This is treated as a feature, not a risk:
  different clients have different cost structures.
