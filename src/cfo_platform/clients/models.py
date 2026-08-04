"""The ClientProfile model — everything the platform needs to know about one client."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cfo_platform.core.models import SourceSystem


class ClientProfile(BaseModel):
    """Loaded from config/clients/<client_id>.yaml by cfo_platform.clients.registry."""

    client_id: str
    display_name: str
    source_system: SourceSystem
    timezone: str = "UTC"
    fiscal_year_start_month: int = 1
    warehouse_file: str
    raw_data_dir: Path
    notes: str = ""
