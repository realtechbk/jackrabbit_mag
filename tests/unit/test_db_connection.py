from __future__ import annotations

import yaml

from cfo_platform.db.connection import get_connection
from cfo_platform.settings import get_settings


def _write_client_config(client_id: str) -> None:
    settings = get_settings()
    settings.clients_config_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "client_id": client_id,
        "display_name": "Test Client",
        "source_system": "jackrabbit_class",
        "warehouse_file": f"{client_id}.duckdb",
        "raw_data_dir": "data/raw",
    }
    path = settings.clients_config_dir / f"{client_id}.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")


def test_get_connection_creates_warehouse_file() -> None:
    _write_client_config("testclient")

    conn = get_connection("testclient")
    conn.execute("SELECT 1").fetchone()
    conn.close()

    settings = get_settings()
    assert (settings.warehouse_dir / "testclient.duckdb").exists()
