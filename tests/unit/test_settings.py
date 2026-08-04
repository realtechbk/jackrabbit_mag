from __future__ import annotations

from cfo_platform.settings import get_settings


def test_settings_read_env_overrides() -> None:
    settings = get_settings()
    assert settings.warehouse_dir.name == "warehouse"
    assert settings.clients_config_dir.name == "clients"


def test_settings_default_client() -> None:
    assert get_settings().default_client == "mag"
