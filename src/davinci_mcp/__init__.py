"""
DaVinci Resolve MCP Server

A modern, clean implementation of a Model Context Protocol server
for DaVinci Resolve integration.
"""

try:
    from ._version import __version__
except ImportError:
    from importlib.metadata import version

    __version__ = version("davinci-mcp-professional")
__author__ = "Hoyt Harness"

from .resolve_client import DaVinciResolveClient
from .server import DaVinciMCPServer

__all__ = ["DaVinciMCPServer", "DaVinciResolveClient"]
