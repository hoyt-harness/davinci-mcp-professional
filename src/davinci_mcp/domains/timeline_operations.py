# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 2: Timeline Operations tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient


class TimelineOperationsDomain:
    name = "timeline_operations"
    description = "List, create, and switch between timelines in the current project"

    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="list_timelines",
                description="List all timelines in the current project",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_timeline",
                description="Get the name of the current timeline",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="create_timeline",
                description="Create a new timeline with the given name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name for the new timeline",
                        }
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="switch_timeline",
                description="Switch to a timeline by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the timeline to switch to",
                        }
                    },
                    "required": ["name"],
                },
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        if tool_name == "list_timelines":
            return client.list_timelines()
        elif tool_name == "get_current_timeline":
            return client.get_current_timeline_name()
        elif tool_name == "create_timeline":
            name = arguments.get("name", "")
            result = client.create_timeline(name)
            return (
                f"Successfully created timeline '{name}'"
                if result
                else f"Failed to create timeline '{name}'"
            )
        elif tool_name == "switch_timeline":
            name = arguments.get("name", "")
            result = client.switch_timeline(name)
            return (
                f"Successfully switched to timeline '{name}'"
                if result
                else f"Failed to switch to timeline '{name}'"
            )
        return f"Unknown tool in timeline_operations domain: {tool_name}"
