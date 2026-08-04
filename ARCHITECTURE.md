# Architecture

This repo now holds two things:

| | Location | Status |
|---|---|---|
| **Legacy MAG analysis** | `scripts/`, `outputs/`, `data/raw/` | Done for revenue/units; see `CURRENT_STATUS.md`. One-off, hardcoded-figures pipeline described in `CLAUDE.md`. |
| **AI CFO platform** | `src/cfo_platform/` | Architecture only — see below. Not yet wired to the legacy analysis. |

The platform is designed to serve multiple clients; MAG is the first. It does
not replace the legacy analysis yet — that migration is future work, not
done as part of this scaffold.

Full design detail: [`docs/architecture/overview.md`](docs/architecture/overview.md).

## Quick orientation

```
config/                   Non-secret defaults + per-client YAML config
src/cfo_platform/
├── settings.py            Env-driven process settings (pydantic-settings)
├── logging_config.py      dictConfig logging, driven by config/logging.yaml
├── core/                  Shared exceptions, domain models, constants
├── clients/               Per-client config loading (ClientProfile, registry)
├── db/                    DuckDB connection (one file per client) + migrations
├── importers/             Importer contract + registry — NO concrete importer yet
├── analytics/             Analyzer contract + registry — NO concrete analyzer yet
├── reporting/              ReportBuilder contract + registry — NO concrete builder yet
├── mcp_server/            MCP server skeleton (health-check tool only)
└── cli.py                 `cfo-platform` CLI (clients, db-migrate work; db-import/report stub)
tests/                     unit/ + integration/, pytest
docs/architecture/         Overview, data model, ADRs, client-onboarding guide
```

## Why nothing here computes anything yet

By design, this pass built the seams (config, settings, logging, DuckDB
warehousing, migrations, and the three plugin contracts — Importer, Analyzer,
ReportBuilder) without filling in any importer, analytics, or reporting
logic. That's the next phase of work, informed by `CLAUDE.md`'s existing
rules (reconciliation to zero variance, units-basis vs revenue-basis, etc.),
which still apply and should inform the first concrete Jackrabbit importer
and MAG analyzer built on top of this.

`CLAUDE.md`'s "There is no application here" line predates this platform and
is now only true of `scripts/`/`outputs/`. Consider updating it once the
first importer/analyzer lands here.
