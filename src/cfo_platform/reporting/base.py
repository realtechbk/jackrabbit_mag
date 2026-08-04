"""The ReportBuilder contract. No concrete builder exists yet.

The existing one-off MAG builders in scripts/build_*.py predate this
platform and are not wired into this layer — see
docs/architecture/overview.md for the migration plan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class ReportBuilder(ABC):
    """Renders one or more analysis DataFrames into a client-facing deliverable."""

    name: str

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

    @abstractmethod
    def build(self, data: dict[str, pd.DataFrame], output_path: Path) -> Path:
        """Render data into a deliverable file at output_path and return that path."""
        raise NotImplementedError
