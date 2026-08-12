"""Jackrabbit Class importer for the AI CFO platform.

Importing this subpackage registers JackrabbitClassImporter under the
'jackrabbit_class' source_system key (see importers.registry).
"""

from __future__ import annotations

from cfo_platform.importers.jackrabbit.importer import JackrabbitClassImporter

__all__ = ["JackrabbitClassImporter"]
