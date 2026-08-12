from __future__ import annotations

import duckdb

from cfo_platform.db.migrations.runner import current_version, migrate


def test_migrate_applies_pending_migrations(tmp_warehouse: duckdb.DuckDBPyConnection) -> None:
    applied = migrate(tmp_warehouse)
    assert applied == ["0001_init", "0002_jackrabbit_raw", "0003_mag_service_line_facts"]
    assert current_version(tmp_warehouse) == "0003_mag_service_line_facts"


def test_migrate_is_idempotent(tmp_warehouse: duckdb.DuckDBPyConnection) -> None:
    migrate(tmp_warehouse)
    assert migrate(tmp_warehouse) == []
