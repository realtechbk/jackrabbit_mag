# Onboarding a new client

Steps to add client #2 (or any client after MAG). None of steps 3-5 have
tooling built yet — they're the manual work each new client currently
requires; the goal over time is to shrink them.

1. **Copy the template config.**
   `cp config/clients/_template.yaml config/clients/<client_id>.yaml` and
   fill in every `CHANGE_ME`: `source_system`, `warehouse_file`,
   `raw_data_dir`, timezone, fiscal year start month.

2. **Drop raw source exports** wherever `raw_data_dir` points (convention:
   `data/clients/<client_id>/raw/`, kept out of `data/raw/` which is MAG's).

3. **Bootstrap the warehouse.**
   `cfo-platform db-migrate <client_id>` creates `data/warehouse/<warehouse_file>`
   and applies every migration in `db/migrations/versions/`.

4. **Write an `Importer` for the client's source system** (if one doesn't
   already exist for that `source_system` — see
   `cfo_platform.importers.registry`). Subclass `Importer`, implement
   `extract`/`transform`/`load`, register it with `@register_importer(...)`.

5. **Write an `Analyzer`** for whatever profitability question this client
   needs answered — subclass `Analyzer`, implement `run`, register with
   `@register_analyzer(...)`. Reuse an existing analyzer only if the client's
   business model and warehouse schema genuinely match; gyms and (say) a
   retail client will not share one.

6. Optionally, a `ReportBuilder` to render that analyzer's output into a
   client deliverable, and/or an MCP tool in `mcp_server/tools/` to expose it
   interactively.

See `docs/architecture/overview.md` for how these pieces fit together, and
`docs/architecture/data-model.md` for why no shared business schema is
assumed across clients.
