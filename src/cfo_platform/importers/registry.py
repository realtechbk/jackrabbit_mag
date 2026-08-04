"""Maps a source_system key to the Importer subclass that handles it."""

from __future__ import annotations

from cfo_platform.core.exceptions import ConfigurationError
from cfo_platform.importers.base import Importer

_REGISTRY: dict[str, type[Importer]] = {}


def register_importer(source_system: str):
    """Class decorator: register a concrete Importer for a source_system key."""

    def _decorator(cls: type[Importer]) -> type[Importer]:
        _REGISTRY[source_system] = cls
        return cls

    return _decorator


def get_importer_class(source_system: str) -> type[Importer]:
    try:
        return _REGISTRY[source_system]
    except KeyError as exc:
        raise ConfigurationError(
            f"No importer registered for source_system={source_system!r}. "
            f"Registered: {sorted(_REGISTRY)}"
        ) from exc
