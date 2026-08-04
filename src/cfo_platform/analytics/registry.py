"""Maps a name to the Analyzer subclass that computes it."""

from __future__ import annotations

from cfo_platform.analytics.base import Analyzer
from cfo_platform.core.exceptions import ConfigurationError

_REGISTRY: dict[str, type[Analyzer]] = {}


def register_analyzer(name: str):
    """Class decorator: register a concrete Analyzer under a name."""

    def _decorator(cls: type[Analyzer]) -> type[Analyzer]:
        _REGISTRY[name] = cls
        return cls

    return _decorator


def get_analyzer_class(name: str) -> type[Analyzer]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise ConfigurationError(
            f"No analyzer registered under name={name!r}. Registered: {sorted(_REGISTRY)}"
        ) from exc
