"""
MCP resources for DaVinci Resolve integration.
"""

from typing import cast

import mcp.types as types
from pydantic import AnyUrl


def get_all_resources() -> list[types.Resource]:
    """Get all available MCP resources."""
    return [
        # System resources
        types.Resource(
            uri=cast(AnyUrl, "resolve://version"),
            name="DaVinci Resolve Version",
            description="Current version of DaVinci Resolve",
            mimeType="text/plain",
        ),
        types.Resource(
            uri=cast(AnyUrl, "resolve://current-page"),
            name="Current Page",
            description="The currently active page in DaVinci Resolve",
            mimeType="text/plain",
        ),
        # Project resources
        types.Resource(
            uri=cast(AnyUrl, "resolve://projects"),
            name="Available Projects",
            description="List of all available projects in the current database",
            mimeType="application/json",
        ),
        types.Resource(
            uri=cast(AnyUrl, "resolve://current-project"),
            name="Current Project",
            description="Name of the currently open project",
            mimeType="text/plain",
        ),
        # Timeline resources
        types.Resource(
            uri=cast(AnyUrl, "resolve://timelines"),
            name="Available Timelines",
            description="List of all timelines in the current project",
            mimeType="application/json",
        ),
        types.Resource(
            uri=cast(AnyUrl, "resolve://current-timeline"),
            name="Current Timeline",
            description="Name of the current timeline",
            mimeType="text/plain",
        ),
        # Media resources
        types.Resource(
            uri=cast(AnyUrl, "resolve://media-clips"),
            name="Media Pool Clips",
            description="List of all clips in the media pool",
            mimeType="application/json",
        ),
    ]
