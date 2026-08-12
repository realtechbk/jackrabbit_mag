"""Process-wide settings for cfo_platform.

Per-client settings (source system, warehouse file, fiscal calendar, ...) are
deliberately NOT part of this class — they live in config/clients/*.yaml and
are loaded via cfo_platform.clients.registry. This class only holds settings
that are the same for every client: where things live on disk, and how
verbose to be.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Sourced from CFO_-prefixed environment variables and .env. See .env.example."""

    model_config = SettingsConfigDict(
        env_prefix="CFO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"

    data_root: Path = REPO_ROOT / "data"
    warehouse_dir: Path = REPO_ROOT / "data" / "warehouse"
    config_dir: Path = REPO_ROOT / "config"
    clients_config_dir: Path = REPO_ROOT / "config" / "clients"
    logging_config_path: Path = REPO_ROOT / "config" / "logging.yaml"

    default_client: str | None = "mag"

    # Revenue Summary parsing requires Poppler's pdftotext specifically --
    # see importers/jackrabbit/revenue_summary_parser.py's module docstring.
    # None means "resolve 'pdftotext' from PATH"; set CFO_PDFTOTEXT_PATH to
    # point at a specific binary when the right build isn't (or shouldn't be)
    # first on PATH.
    pdftotext_path: Path | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached process-wide Settings instance.

    Tests that change CFO_* environment variables must call
    get_settings.cache_clear() first — see tests/conftest.py.
    """
    return Settings()
