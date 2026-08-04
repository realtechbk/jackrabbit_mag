"""Load and cache per-client configuration from config/clients/*.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from cfo_platform.clients.models import ClientProfile
from cfo_platform.core.exceptions import ClientNotFoundError
from cfo_platform.settings import get_settings


def _config_path(client_id: str) -> Path:
    return get_settings().clients_config_dir / f"{client_id}.yaml"


@lru_cache(maxsize=None)
def load_client(client_id: str) -> ClientProfile:
    """Load and cache one client's profile. Tests must call load_client.cache_clear()."""
    path = _config_path(client_id)
    if not path.exists():
        raise ClientNotFoundError(f"No client config at {path}")

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    return ClientProfile(
        client_id=raw["client_id"],
        display_name=raw["display_name"],
        source_system=raw["source_system"],
        timezone=raw.get("timezone", "UTC"),
        fiscal_year_start_month=raw.get("fiscal_year_start_month", 1),
        warehouse_file=raw["warehouse_file"],
        raw_data_dir=Path(raw["raw_data_dir"]),
        notes=raw.get("notes", ""),
    )


def list_clients() -> list[str]:
    """List client_ids with a config/clients/<id>.yaml, excluding _template.yaml-style files."""
    config_dir = get_settings().clients_config_dir
    if not config_dir.exists():
        return []
    return sorted(p.stem for p in config_dir.glob("*.yaml") if not p.stem.startswith("_"))
