"""
MCP tools for DaVinci Resolve integration.
"""

import mcp.types as types


def get_all_tools() -> list[types.Tool]:
    """Get all available MCP tools."""
    return [
        # System tools
        types.Tool(
            name="get_version",
            description="Get DaVinci Resolve version information",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_current_page",
            description=(
                "Get the current page open in DaVinci Resolve"
                " (Edit, Color, Fusion, etc.)"
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="switch_page",
            description="Switch to a specific page in DaVinci Resolve",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "string",
                        "description": "The page to switch to",
                        "enum": [
                            "media",
                            "cut",
                            "edit",
                            "fusion",
                            "color",
                            "fairlight",
                            "deliver",
                        ],
                    }
                },
                "required": ["page"],
            },
        ),
        # Project tools
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
        # Timeline tools
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
        # Media tools
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
