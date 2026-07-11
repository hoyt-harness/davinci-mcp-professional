#!/usr/bin/env python3
"""
Pure MCP server entry point for DaVinci Resolve.
This version outputs no console messages - only JSON-RPC.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from davinci_mcp.server import DaVinciMCPServer


async def main():
    """Run the MCP server with no console output."""
    server = DaVinciMCPServer()
    await server.run()


if __name__ == "__main__":
    # Suppress all output except JSON-RPC
    try:
        asyncio.run(main())
    except Exception:
        # Exit silently on any error to avoid polluting JSON-RPC
        sys.exit(1)
