"""cfo_platform: multi-client AI CFO data platform.

Layers, bottom to top: settings -> clients (per-client config) -> db (DuckDB
warehouse, one file per client) -> importers -> analytics -> reporting /
mcp_server. See docs/architecture/overview.md for the full picture.
"""

__version__ = "0.1.0"
