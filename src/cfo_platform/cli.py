"""Command-line entrypoint for cfo_platform (`cfo-platform` once installed).

`clients` and `db-migrate` work today. `db-import` and `report` are stubs —
importer and analytics logic don't exist yet.
"""

from __future__ import annotations

import typer

from cfo_platform.clients.registry import list_clients, load_client
from cfo_platform.db.connection import get_connection
from cfo_platform.db.migrations.runner import migrate
from cfo_platform.logging_config import setup_logging

app = typer.Typer(help="AI CFO platform CLI")


@app.command()
def clients() -> None:
    """List configured clients."""
    for client_id in list_clients():
        profile = load_client(client_id)
        typer.echo(f"{client_id}\t{profile.display_name}\t{profile.source_system.value}")


@app.command(name="db-migrate")
def db_migrate(client_id: str) -> None:
    """Apply pending DuckDB migrations for one client."""
    setup_logging()
    conn = get_connection(client_id)
    try:
        applied = migrate(conn)
    finally:
        conn.close()

    if applied:
        typer.echo(f"Applied: {', '.join(applied)}")
    else:
        typer.echo("Already up to date.")


@app.command(name="db-import")
def db_import(client_id: str) -> None:
    """Run this client's import pipeline. Not implemented yet."""
    raise NotImplementedError(
        "Importer logic hasn't been built yet — see docs/architecture/overview.md"
    )


@app.command()
def report(client_id: str, report_name: str) -> None:
    """Build a client deliverable. Not implemented yet."""
    raise NotImplementedError(
        "Reporting logic hasn't been built yet — see docs/architecture/overview.md"
    )


if __name__ == "__main__":
    app()
