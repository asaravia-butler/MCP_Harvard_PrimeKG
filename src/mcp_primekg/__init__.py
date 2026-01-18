"""MCP Server for Harvard PrimeKG Knowledge Graph."""

import asyncio
from .server import main

__version__ = "0.1.0"
__all__ = ["main"]


def entry_point():
    """Entry point for the mcp-primekg command."""
    asyncio.run(main())

