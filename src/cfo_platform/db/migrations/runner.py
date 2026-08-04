"""Applies pending SQL migrations from versions/*.sql to a DuckDB connection.

Deliberately dumb: no rollback, no branching, files run once in filename
order and are recorded in schema_migrations. Good enough for a per-client
DuckDB file where schema changes are additive and reviewed by hand.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from cfo_platform.core.constants import SCHEMA_MIGRATIONS_TABLE
from cfo_platform.logging_config import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "versions"

_BOOTSTRAP_SQL = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
    version    VARCHAR PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT current_timestamp
);
"""


def _applied_versions(conn: duckdb.DuckDBPyConnection) -> set[str]:
    conn.execute(_BOOTSTRAP_SQL)
    rows = conn.execute(f"SELECT version FROM {SCHEMA_MIGRATIONS_TABLE}").fetchall()
    return {row[0] for row in rows}


def _pending_migrations(applied: set[str]) -> list[Path]:
    all_migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [m for m in all_migrations if m.stem not in applied]


def migrate(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Apply every migration in versions/ not yet applied to this connection.

    Returns the version stems that were applied by this call (empty if
    already up to date).
    """
    applied = _applied_versions(conn)
    pending = _pending_migrations(applied)

    applied_now: list[str] = []
    for migration in pending:
        logger.info("Applying migration %s", migration.stem)
        conn.execute(migration.read_text(encoding="utf-8"))
        conn.execute(
            f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version) VALUES (?)",
            [migration.stem],
        )
        applied_now.append(migration.stem)

    return applied_now


def current_version(conn: duckdb.DuckDBPyConnection) -> str | None:
    """Return the most recently applied migration version, if any."""
    applied = sorted(_applied_versions(conn))
    return applied[-1] if applied else None
