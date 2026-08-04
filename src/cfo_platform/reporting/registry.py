"""Maps a name to the ReportBuilder subclass that produces it."""

from __future__ import annotations

from cfo_platform.core.exceptions import ConfigurationError
from cfo_platform.reporting.base import ReportBuilder

_REGISTRY: dict[str, type[ReportBuilder]] = {}


def register_report_builder(name: str):
    """Class decorator: register a concrete ReportBuilder under a name."""

    def _decorator(cls: type[ReportBuilder]) -> type[ReportBuilder]:
        _REGISTRY[name] = cls
        return cls

    return _decorator


def get_report_builder_class(name: str) -> type[ReportBuilder]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise ConfigurationError(
            f"No report builder registered under name={name!r}. Registered: {sorted(_REGISTRY)}"
        ) from exc
