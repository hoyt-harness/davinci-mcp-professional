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

from .server import DaVinciMCPServer
from .resolve_client import DaVinciResolveClient

__all__ = ["DaVinciMCPServer", "DaVinciResolveClient"]
