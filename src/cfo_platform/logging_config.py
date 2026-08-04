"""Logging setup for cfo_platform, driven by config/logging.yaml."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import yaml

from cfo_platform.settings import get_settings

_configured = False


def setup_logging(config_path: Path | None = None) -> None:
    """Configure logging from config/logging.yaml. Idempotent — safe to call repeatedly."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    path = config_path or settings.logging_config_path

    if path.exists():
        with open(path, encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        log_file = config.get("handlers", {}).get("file", {}).get("filename")
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=settings.log_level)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, configuring logging from config/logging.yaml on first use."""
    setup_logging()
    return logging.getLogger(name)
