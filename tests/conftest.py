from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest


@pytest.fixture()
def tmp_warehouse(tmp_path: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    """A throwaway DuckDB connection backed by a scratch file."""
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point settings/client-registry at scratch dirs so tests never touch real client data."""
    from cfo_platform.clients.registry import load_client
    from cfo_platform.settings import get_settings

    monkeypatch.setenv("CFO_WAREHOUSE_DIR", str(tmp_path / "warehouse"))
    monkeypatch.setenv("CFO_CLIENTS_CONFIG_DIR", str(tmp_path / "clients"))

    get_settings.cache_clear()
    load_client.cache_clear()
    yield
    get_settings.cache_clear()
    load_client.cache_clear()
