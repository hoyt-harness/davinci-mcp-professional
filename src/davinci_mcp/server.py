"""
DaVinci Resolve MCP Server.

A clean, modern implementation of the Model Context Protocol server
for DaVinci Resolve integration.
"""

import logging
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

from . import __version__
from .resolve_client import DaVinciResolveClient, DaVinciResolveError
from .resources import get_all_resources
from .tools import get_all_tools

logger = logging.getLogger(__name__)


class DaVinciMCPServer:
    """
    DaVinci Resolve MCP Server.

    Provides a clean interface between MCP clients and DaVinci Resolve
    through organized tools and resources.
    """

    def __init__(self) -> None:
        self.server = Server("davinci-resolve-mcp")
        self.resolve_client = DaVinciResolveClient()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:  # type: ignore[reportUnusedFunction]
            return get_all_tools()

        @self.server.call_tool()
        async def handle_call_tool(  # type: ignore[reportUnusedFunction]
            name: str, arguments: dict[str, Any] | None = None
        ) -> list[types.TextContent]:
            if arguments is None:
                arguments = {}
            try:
                if not self.resolve_client.is_connected():
                    self.resolve_client.connect()
                result = await self._call_tool(name, arguments)
                return [types.TextContent(type="text", text=str(result))]
            except DaVinciResolveError as e:
                error_msg = f"DaVinci Resolve error: {e}"
                logger.exception(error_msg)
                return [types.TextContent(type="text", text=error_msg)]
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                logger.exception(error_msg)
                return [types.TextContent(type="text", text=error_msg)]

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:  # type: ignore[reportUnusedFunction]
            return get_all_resources()

        @self.server.read_resource()
        async def handle_read_resource(  # type: ignore[reportUnusedFunction]
            uri: AnyUrl,
        ) -> str:
            try:
                if not self.resolve_client.is_connected():
                    self.resolve_client.connect()
                result = await self._read_resource(str(uri))
                return str(result)
            except DaVinciResolveError as e:
                error_msg = f"DaVinci Resolve error: {e}"
                logger.exception(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                logger.exception(error_msg)
                return error_msg

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Dispatch a tool call to the resolve client."""
        if name == "get_version":
            return self.resolve_client.get_version()
        elif name == "get_current_page":
            return self.resolve_client.get_current_page()
        elif name == "switch_page":
            return self.resolve_client.switch_page(arguments.get("page", ""))
        elif name == "list_projects":
            return self.resolve_client.list_projects()
        elif name == "get_current_project":
            return self.resolve_client.get_current_project_name()
        elif name == "open_project":
            name_arg = arguments.get("name", "")
            result = self.resolve_client.open_project(name_arg)
            return (
                f"Successfully opened project '{name_arg}'"
                if result
                else f"Failed to open project '{name_arg}'"
            )
        elif name == "create_project":
            name_arg = arguments.get("name", "")
            result = self.resolve_client.create_project(name_arg)
            return (
                f"Successfully created project '{name_arg}'"
                if result
                else f"Failed to create project '{name_arg}'"
            )
        elif name == "list_timelines":
            return self.resolve_client.list_timelines()
        elif name == "get_current_timeline":
            return self.resolve_client.get_current_timeline_name()
        elif name == "create_timeline":
            name_arg = arguments.get("name", "")
            result = self.resolve_client.create_timeline(name_arg)
            return (
                f"Successfully created timeline '{name_arg}'"
                if result
                else f"Failed to create timeline '{name_arg}'"
            )
        elif name == "switch_timeline":
            name_arg = arguments.get("name", "")
            result = self.resolve_client.switch_timeline(name_arg)
            return (
                f"Successfully switched to timeline '{name_arg}'"
                if result
                else f"Failed to switch to timeline '{name_arg}'"
            )
        elif name == "list_media_clips":
            return self.resolve_client.list_media_clips()
        elif name == "import_media":
            file_path = arguments.get("file_path", "")
            result = self.resolve_client.import_media(file_path)
            return (
                f"Successfully imported media '{file_path}'"
                if result
                else f"Failed to import media '{file_path}'"
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _read_resource(self, uri: str) -> Any:
        """Dispatch a resource read to the resolve client."""
        if uri == "resolve://version":
            return self.resolve_client.get_version()
        elif uri == "resolve://current-page":
            return self.resolve_client.get_current_page()
        elif uri == "resolve://projects":
            return self.resolve_client.list_projects()
        elif uri == "resolve://current-project":
            name = self.resolve_client.get_current_project_name()
            return name if name else "No project open"
        elif uri == "resolve://timelines":
            return self.resolve_client.list_timelines()
        elif uri == "resolve://current-timeline":
            name = self.resolve_client.get_current_timeline_name()
            return name if name else "No timeline active"
        elif uri == "resolve://media-clips":
            return self.resolve_client.list_media_clips()
        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting DaVinci Resolve MCP Server...")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="davinci-mcp-professional",
                    server_version=__version__,
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
