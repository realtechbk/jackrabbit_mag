"""The Analyzer contract. No concrete analyzer exists yet — service-line
profitability, cost-of-sales allocation, etc. are future work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import duckdb
import pandas as pd


class Analyzer(ABC):
    """One analytics computation over a client's warehouse."""

    name: str

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

    @abstractmethod
    def run(self, conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
        """Compute this analysis against the client's warehouse and return a DataFrame."""
        raise NotImplementedError
