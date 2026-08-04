"""The Importer contract. No concrete importer exists yet — see
docs/architecture/overview.md for the planned Jackrabbit Class importer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import duckdb


class Importer(ABC):
    """One client/source-system import pipeline: extract -> transform -> load."""

    source_system: str

    def __init__(self, client_id: str, raw_data_dir: Path) -> None:
        self.client_id = client_id
        self.raw_data_dir = raw_data_dir

    @abstractmethod
    def extract(self) -> Any:
        """Read raw source files and return them in a source-native shape."""
        raise NotImplementedError

    @abstractmethod
    def transform(self, raw: Any) -> Any:
        """Convert extracted data into the platform's warehouse schema."""
        raise NotImplementedError

    @abstractmethod
    def load(self, conn: duckdb.DuckDBPyConnection, transformed: Any) -> None:
        """Write transformed data into the client's DuckDB warehouse."""
        raise NotImplementedError

    def run(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Run extract -> transform -> load in sequence."""
        raw = self.extract()
        transformed = self.transform(raw)
        self.load(conn, transformed)
