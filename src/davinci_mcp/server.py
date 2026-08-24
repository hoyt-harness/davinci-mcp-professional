# SPDX-License-Identifier: GPL-3.0-or-later
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
from mcp.server.lowlevel.server import request_ctx
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

from . import __version__
from .domains.registry import DOMAIN_REGISTRY, DomainModule
from .resolve_client import DaVinciResolveClient, DaVinciResolveError
from .resources import get_all_resources
from .tools import get_all_tools

logger = logging.getLogger(__name__)

_KERNEL_TOOLS: frozenset[str] = frozenset(
    {
        "activate_domain",
        "deactivate_domain",
        "list_domains",
        "get_version",
        "get_current_page",
        "switch_page",
    }
)


class DaVinciMCPServer:
    """
    DaVinci Resolve MCP Server.

    Provides a clean interface between MCP clients and DaVinci Resolve
    through a kernel + domain architecture. The kernel exposes a fixed
    set of tools at session start; domain tools are registered dynamically
    via activate_domain.
    """

    def __init__(self) -> None:
        self.server = Server("davinci-resolve-mcp")
        self.resolve_client = DaVinciResolveClient()
        self._active_domains: dict[str, DomainModule] = {}
        self._tool_to_domain: dict[str, str] = {}
        self._inactive_tool_to_domain: dict[str, str] = {}
        self._rebuild_routing_tables()
        self._register_handlers()

    # ------------------------------------------------------------------
    # Routing table management
    # ------------------------------------------------------------------

    def _rebuild_routing_tables(self) -> None:
        """Rebuild tool→domain maps from the current active-domains set.

        Called once on __init__ and after every activation/deactivation.
        Not called on every tool call — the maps are stable between changes.
        """
        self._tool_to_domain = {
            tool.name: domain_name
            for domain_name, domain in self._active_domains.items()
            for tool in domain.get_tools()
        }
        self._inactive_tool_to_domain = {
            tool.name: domain_name
            for domain_name, domain in DOMAIN_REGISTRY.items()
            if domain_name not in self._active_domains
            for tool in domain.get_tools()
        }

    # ------------------------------------------------------------------
    # Kernel tool handlers (called from _call_kernel_tool)
    # ------------------------------------------------------------------

    async def _activate_domain(self, domain_name: str) -> dict[str, Any]:
        if domain_name not in DOMAIN_REGISTRY:
            return {
                "error": (
                    f"Unknown domain: '{domain_name}'. "
                    f"Available: {sorted(DOMAIN_REGISTRY)}"
                )
            }
        if domain_name in self._active_domains:
            return {"status": "already_active", "domain": domain_name}

        self._active_domains[domain_name] = DOMAIN_REGISTRY[domain_name]
        self._rebuild_routing_tables()
        await request_ctx.get().session.send_tool_list_changed()
        return {
            "status": "activated",
            "domain": domain_name,
            "tools_added": [t.name for t in DOMAIN_REGISTRY[domain_name].get_tools()],
        }

    async def _deactivate_domain(self, domain_name: str) -> dict[str, Any]:
        if domain_name not in self._active_domains:
            return {
                "error": (
                    f"Domain '{domain_name}' is not active. "
                    f"Active domains: {sorted(self._active_domains)}"
                )
            }
        del self._active_domains[domain_name]
        self._rebuild_routing_tables()
        await request_ctx.get().session.send_tool_list_changed()
        return {"status": "deactivated", "domain": domain_name}

    def _list_domains(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "description": domain.description,
                "active": name in self._active_domains,
                "tool_count": len(domain.get_tools()),
            }
            for name, domain in DOMAIN_REGISTRY.items()
        ]

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    async def _call_kernel_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "activate_domain":
            return await self._activate_domain(arguments.get("domain", ""))
        elif name == "deactivate_domain":
            return await self._deactivate_domain(arguments.get("domain", ""))
        elif name == "list_domains":
            return self._list_domains()
        elif name == "get_version":
            return self.resolve_client.get_version()
        elif name == "get_current_page":
            return self.resolve_client.get_current_page()
        elif name == "switch_page":
            return self.resolve_client.switch_page(arguments.get("page", ""))
        return f"Unknown kernel tool: {name}"

    async def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Route a tool call through the four-case dispatch (FR-008)."""
        if name in _KERNEL_TOOLS:
            return await self._call_kernel_tool(name, arguments)
        elif name in self._tool_to_domain:
            domain = self._active_domains[self._tool_to_domain[name]]
            return await domain.dispatch(name, arguments, self.resolve_client)
        elif name in self._inactive_tool_to_domain:
            domain_name = self._inactive_tool_to_domain[name]
            return (
                f"Tool '{name}' is in domain '{domain_name}'. "
                f"Call activate_domain('{domain_name}') first."
            )
        else:
            return f"Unknown tool: {name}"

    # ------------------------------------------------------------------
    # Tool list
    # ------------------------------------------------------------------

    async def _handle_list_tools(self) -> list[types.Tool]:
        return get_all_tools() + [
            tool
            for domain in self._active_domains.values()
            for tool in domain.get_tools()
        ]

    # ------------------------------------------------------------------
    # MCP handler registration
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:  # type: ignore
            return await self._handle_list_tools()

        @self.server.call_tool()
        async def handle_call_tool(  # type: ignore
            name: str, arguments: dict[str, Any] | None = None
        ) -> list[types.TextContent]:
            if arguments is None:
                arguments = {}
            try:
                if name not in _KERNEL_TOOLS or name in (
                    "get_version",
                    "get_current_page",
                    "switch_page",
                ):
                    if not self.resolve_client.is_connected():
                        self.resolve_client.connect()
                result = await self._dispatch_tool(name, arguments)
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
        async def handle_list_resources() -> list[types.Resource]:  # type: ignore
            return get_all_resources()

        @self.server.list_resource_templates()
        async def handle_list_resource_templates() -> list[types.ResourceTemplate]:  # type: ignore  # noqa: E501
            return []

        @self.server.read_resource()
        async def handle_read_resource(  # type: ignore
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
                        notification_options=NotificationOptions(tools_changed=True),
                        experimental_capabilities={},
                    ),
                ),
            )
