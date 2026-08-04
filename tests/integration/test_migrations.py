from __future__ import annotations

import duckdb

from cfo_platform.db.migrations.runner import current_version, migrate


def test_migrate_applies_pending_migrations(tmp_warehouse: duckdb.DuckDBPyConnection) -> None:
    applied = migrate(tmp_warehouse)
    assert "0001_init" in applied
    assert current_version(tmp_warehouse) == "0001_init"


def test_migrate_is_idempotent(tmp_warehouse: duckdb.DuckDBPyConnection) -> None:
    migrate(tmp_warehouse)
    assert migrate(tmp_warehouse) == []
