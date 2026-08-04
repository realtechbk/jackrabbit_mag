"""Domain models shared across every client and every layer.

Client-specific taxonomies (e.g. MAG's Recreational / Competitive / Ancillary
/ Review / EXCLUDE service-line groups) do not belong here — they belong in
that client's config or in analytics code scoped to that client, so this
module stays reusable across clients with different business models.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel


class SourceSystem(str, Enum):
    """Practice-management / accounting systems the platform knows how to import from."""

    JACKRABBIT_CLASS = "jackrabbit_class"


class FiscalPeriod(BaseModel):
    """A reporting period for one client; may be a full year or a partial year."""

    client_id: str
    label: str
    start_date: date
    end_date: date
    is_full_year: bool
