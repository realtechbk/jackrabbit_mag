"""Command-line entrypoint for cfo_platform (`cfo-platform` once installed).

`clients`, `db-migrate` and `db-import` work today. `report` is a stub —
reporting/analytics logic doesn't exist yet.
"""

from __future__ import annotations

import typer

from cfo_platform.clients.registry import list_clients, load_client
from cfo_platform.core.exceptions import ReconciliationError
from cfo_platform.db.connection import get_connection
from cfo_platform.db.migrations.runner import migrate
from cfo_platform.importers import jackrabbit  # noqa: F401 -- import registers JackrabbitClassImporter
from cfo_platform.importers.registry import get_importer_class
from cfo_platform.logging_config import get_logger, setup_logging
from cfo_platform.settings import REPO_ROOT

app = typer.Typer(help="AI CFO platform CLI")
logger = get_logger(__name__)


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
    """Run this client's import pipeline.

    Applies pending migrations first, then runs the Importer registered for
    the client's source_system (config/clients/<client_id>.yaml) against its
    raw_data_dir. Refuses to load (raises) if any period fails reconciliation
    -- CLAUDE.md rule 1 -- rather than loading a partially-wrong period.
    """
    setup_logging()
    profile = load_client(client_id)
    importer_cls = get_importer_class(profile.source_system.value)
    importer = importer_cls(client_id=client_id, raw_data_dir=REPO_ROOT / profile.raw_data_dir)

    conn = get_connection(client_id)
    try:
        migrate(conn)
        importer.run(conn)
    except ReconciliationError as exc:
        typer.echo(f"Reconciliation failed -- import refused: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    finally:
        conn.close()

    typer.echo(f"Import complete for {client_id}.")


@app.command()
def report(client_id: str, report_name: str) -> None:
    """Build a client deliverable. Not implemented yet."""
    raise NotImplementedError(
        "Reporting logic hasn't been built yet — see docs/architecture/overview.md"
    )


if __name__ == "__main__":
    app()
