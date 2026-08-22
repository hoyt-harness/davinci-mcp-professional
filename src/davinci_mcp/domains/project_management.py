# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 1: Project Management tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient


class ProjectManagementDomain:
    name = "project_management"
    description = "List, open, and create DaVinci Resolve projects"

    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="list_projects",
                description="List all available projects in the current database",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_project",
                description="Get the name of the currently open project",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="open_project",
                description="Open a project by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the project to open",
                        }
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="create_project",
                description="Create a new project with the given name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name for the new project",
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
        if tool_name == "list_projects":
            return client.list_projects()
        elif tool_name == "get_current_project":
            return client.get_current_project_name()
        elif tool_name == "open_project":
            name = arguments.get("name", "")
            result = client.open_project(name)
            return (
                f"Successfully opened project '{name}'"
                if result
                else f"Failed to open project '{name}'"
            )
        elif tool_name == "create_project":
            name = arguments.get("name", "")
            result = client.create_project(name)
            return (
                f"Successfully created project '{name}'"
                if result
                else f"Failed to create project '{name}'"
            )
        return f"Unknown tool in project_management domain: {tool_name}"
