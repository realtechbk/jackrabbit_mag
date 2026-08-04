"""Generic schema-introspection helpers. No business schema is defined here —
the tables a client's warehouse actually needs (facts, dimensions) will be
added as migrations once importers and analytics are built.
"""

from __future__ import annotations

import duckdb


def list_tables(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """List user tables in the connected DuckDB warehouse."""
    rows = conn.execute("SHOW TABLES").fetchall()
    return sorted(row[0] for row in rows)


def table_exists(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    return name in list_tables(conn)
