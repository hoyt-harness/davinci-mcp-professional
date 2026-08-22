# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 3: Media Pool Operations tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient


class MediaPoolDomain:
    name = "media_pool"
    description = "List clips and import media into the DaVinci Resolve media pool"

    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="list_media_clips",
                description="List all clips in the media pool",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="import_media",
                description="Import a media file into the media pool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the media file to import",
                        }
                    },
                    "required": ["file_path"],
                },
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        if tool_name == "list_media_clips":
            return client.list_media_clips()
        elif tool_name == "import_media":
            file_path = arguments.get("file_path", "")
            result = client.import_media(file_path)
            return (
                f"Successfully imported media '{file_path}'"
                if result
                else f"Failed to import media '{file_path}'"
            )
        return f"Unknown tool in media_pool domain: {tool_name}"
