"""MCP server entrypoint.

Only a health-check tool is registered so far. Real tools (querying a
client's warehouse, running analytics, building reports) belong in
mcp_server/tools/*.py and are not implemented yet — see
docs/architecture/overview.md.
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from cfo_platform.logging_config import get_logger

logger = get_logger(__name__)

mcp = MCPServer("cfo-platform")


@mcp.tool()
def ping() -> str:
    """Health check so MCP clients can confirm the server is reachable."""
    return "pong"


def main() -> None:
    """Entrypoint for `python -m cfo_platform.mcp_server.server`."""
    logger.info("Starting cfo-platform MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
