"""DuckDB connection handling — one warehouse file per client.

See docs/architecture/adr/0002-warehouse-per-client.md for why clients don't
share a database.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from cfo_platform.clients.registry import load_client
from cfo_platform.settings import get_settings


def warehouse_path(client_id: str) -> Path:
    """Return the DuckDB file path for a client, creating the warehouse dir if needed."""
    settings = get_settings()
    profile = load_client(client_id)
    settings.warehouse_dir.mkdir(parents=True, exist_ok=True)
    return settings.warehouse_dir / profile.warehouse_file


def get_connection(client_id: str, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection to one client's warehouse. Caller is responsible for closing it."""
    return duckdb.connect(str(warehouse_path(client_id)), read_only=read_only)
