-- 0001_init: platform bookkeeping tables. No client business schema (facts,
-- dimensions for revenue/cost-of-sales) is defined yet — that arrives with
-- the first real importer + analyzer, as later migrations.

CREATE TABLE IF NOT EXISTS import_runs (
    run_id        VARCHAR PRIMARY KEY,
    client_id     VARCHAR NOT NULL,
    source_system VARCHAR NOT NULL,
    started_at    TIMESTAMP NOT NULL,
    finished_at   TIMESTAMP,
    status        VARCHAR NOT NULL,
    notes         VARCHAR
);
