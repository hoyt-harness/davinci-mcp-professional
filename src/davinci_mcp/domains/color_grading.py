# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 6: Color Grading tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


class ColorGradingDomain:
    name = "color_grading"
    description = (
        "Color node graph inspection and LUT management, gallery stills "
        "(albums, grab, export, import, labels), color groups, and LUT list refresh"
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        _tl = {"timeline_name": {"type": "string", "description": "Timeline name"}}
        _alb = {"album_name": {"type": "string", "description": "Album name"}}
        _ni = {"node_index": {"type": "integer", "description": "Node index (1-based)"}}  # noqa: E501
        _si = {
            "still_index": {"type": "integer", "description": "Still index (1-based)"}
        }  # noqa: E501
        _req_tl = ["timeline_name"]
        _req_alb = ["album_name"]

        return [
            # ----------------------------------------------------------------
            # Graph / node operations
            # ----------------------------------------------------------------
            types.Tool(
                name="get_graph_node_count",
                description="Get the number of nodes in the current timeline's node graph",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": _tl,
                    "required": _req_tl,
                },
            ),
            types.Tool(
                name="get_graph_node_label",
                description="Get the label of a node in the timeline's node graph",
                inputSchema={
                    "type": "object",
                    "properties": {**_tl, **_ni},
                    "required": _req_tl + ["node_index"],
                },
            ),
            types.Tool(
                name="get_graph_node_tools",
                description="Get the list of tool names active in a graph node",
                inputSchema={
                    "type": "object",
                    "properties": {**_tl, **_ni},
                    "required": _req_tl + ["node_index"],
                },
            ),
            types.Tool(
                name="get_graph_node_lut",
                description="Get the LUT path assigned to a graph node",
                inputSchema={
                    "type": "object",
                    "properties": {**_tl, **_ni},
                    "required": _req_tl + ["node_index"],
                },
            ),
            types.Tool(
                name="set_graph_node_lut",
                description="Assign a LUT file to a graph node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl,
                        **_ni,
                        "lut_path": {"type": "string", "description": "LUT file path"},
                    },
                    "required": _req_tl + ["node_index", "lut_path"],
                },
            ),
            types.Tool(
                name="get_graph_node_cache_mode",
                description="Get the cache mode of a graph node",
                inputSchema={
                    "type": "object",
                    "properties": {**_tl, **_ni},
                    "required": _req_tl + ["node_index"],
                },
            ),
            types.Tool(
                name="set_graph_node_enabled",
                description="Enable or disable a node in the timeline's node graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl,
                        **_ni,
                        "enabled": {"type": "boolean", "description": "Enabled state"},
                    },
                    "required": _req_tl + ["node_index", "enabled"],
                },
            ),
            types.Tool(
                name="set_graph_node_cache_mode",
                description="Set the cache mode of a graph node",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl,
                        **_ni,
                        "cache_mode": {
                            "type": "integer",
                            "description": "Cache mode value",
                        },
                    },
                    "required": _req_tl + ["node_index", "cache_mode"],
                },
            ),
            types.Tool(
                name="apply_grade_from_drx",
                description=(
                    "Apply a grade from a .drx file to the timeline's node graph. "
                    "grade_mode: 0=no keyframes, 1=source TC aligned, 2=start frames aligned."  # noqa: E501
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl,
                        "drx_path": {"type": "string", "description": ".drx file path"},
                        "grade_mode": {
                            "type": "integer",
                            "description": "0=no keyframes, 1=source TC, 2=start",
                        },
                    },
                    "required": _req_tl + ["drx_path", "grade_mode"],
                },
            ),
            types.Tool(
                name="apply_arri_cdl_lut",
                description="Apply ARRI CDL LUT to the timeline's node graph",
                inputSchema={
                    "type": "object",
                    "properties": _tl,
                    "required": _req_tl,
                },
            ),
            types.Tool(
                name="reset_all_grades",
                description=(
                    f"{_DESTRUCTIVE}Reset all grades in the timeline's node graph. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl,
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": _req_tl + ["confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Gallery stills — albums
            # ----------------------------------------------------------------
            types.Tool(
                name="get_gallery_albums",
                description="Get the list of gallery still album names",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_gallery_powergrade_albums",
                description="Get the list of gallery PowerGrade album names",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_still_album",
                description="Get the name of the currently active still album",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="create_still_album",
                description="Create a new gallery still album",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="create_powergrade_album",
                description="Create a new gallery PowerGrade album",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            # ----------------------------------------------------------------
            # Gallery stills — grab / list
            # ----------------------------------------------------------------
            types.Tool(
                name="grab_still",
                description="Grab a still from the current clip on the Color page",
                inputSchema={
                    "type": "object",
                    "properties": _tl,
                    "required": _req_tl,
                },
            ),
            types.Tool(
                name="grab_all_stills",
                description=(
                    "Grab stills from all clips in the timeline. "
                    "still_frame_source: 1=first frame, 2=middle frame."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl,
                        "still_frame_source": {
                            "type": "integer",
                            "description": "1=first frame, 2=middle frame",
                        },
                    },
                    "required": _req_tl + ["still_frame_source"],
                },
            ),
            types.Tool(
                name="get_stills",
                description=(
                    "Get stills in an album as [{still_index, label}]. "
                    "Use still_index to reference a still in subsequent calls."
                ),
                inputSchema={
                    "type": "object",
                    "properties": _alb,
                    "required": _req_alb,
                },
            ),
            types.Tool(
                name="export_stills",
                description=(
                    "Export stills from an album to a folder. "
                    "format: dpx, cin, tif, jpg, png, ppm, bmp, xpm, drx, srgb."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_alb,
                        "still_indices": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "1-based still indices to export",
                        },
                        "folder_path": {
                            "type": "string",
                            "description": "Destination folder",
                        },
                        "file_prefix": {
                            "type": "string",
                            "description": "Filename prefix",
                        },
                        "format": {"type": "string", "description": "Export format"},
                    },
                    "required": _req_alb
                    + ["still_indices", "folder_path", "file_prefix", "format"],  # noqa: E501
                },
            ),
            types.Tool(
                name="import_stills",
                description="Import still files into a gallery album",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_alb,
                        "file_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Still file paths to import",
                        },
                    },
                    "required": _req_alb + ["file_paths"],
                },
            ),
            types.Tool(
                name="delete_stills",
                description=(
                    f"{_DESTRUCTIVE}Delete stills from an album by index. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_alb,
                        "still_indices": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "1-based still indices to delete",
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": _req_alb + ["still_indices", "confirm"],
                },
            ),
            types.Tool(
                name="get_still_label",
                description="Get the label of a still by index within an album",
                inputSchema={
                    "type": "object",
                    "properties": {**_alb, **_si},
                    "required": _req_alb + ["still_index"],
                },
            ),
            types.Tool(
                name="set_still_label",
                description="Set the label of a still by index within an album",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_alb,
                        **_si,
                        "label": {"type": "string", "description": "New label"},
                    },
                    "required": _req_alb + ["still_index", "label"],
                },
            ),
            # ----------------------------------------------------------------
            # Color groups
            # ----------------------------------------------------------------
            types.Tool(
                name="get_color_groups",
                description="Get the list of color group names in the current project",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="create_color_group",
                description="Create a new color group in the current project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string", "description": "Group name"},
                    },
                    "required": ["group_name"],
                },
            ),
            types.Tool(
                name="delete_color_group",
                description=(
                    f"{_DESTRUCTIVE}Delete a color group (clips become ungrouped). "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string", "description": "Group name"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["group_name", "confirm"],
                },
            ),
            types.Tool(
                name="rename_color_group",
                description="Rename a color group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string", "description": "Current name"},
                        "new_name": {"type": "string", "description": "New name"},
                    },
                    "required": ["group_name", "new_name"],
                },
            ),
            types.Tool(
                name="get_clips_in_color_group",
                description="Get the timeline items assigned to a color group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string", "description": "Group name"},
                        "timeline_name": {"type": "string", "description": "Timeline"},
                    },
                    "required": ["group_name", "timeline_name"],
                },
            ),
            types.Tool(
                name="get_color_group_pre_graph",
                description="Get node-count info for a color group's pre-clip node graph",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string", "description": "Group name"},
                    },
                    "required": ["group_name"],
                },
            ),
            types.Tool(
                name="get_color_group_post_graph",
                description="Get node-count info for a color group's post-clip node graph",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string", "description": "Group name"},
                    },
                    "required": ["group_name"],
                },
            ),
            # ----------------------------------------------------------------
            # Project-level color utilities
            # ----------------------------------------------------------------
            types.Tool(
                name="refresh_lut_list",
                description="Refresh the LUT list from disk",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="export_current_frame_as_still",
                description="Export the current frame as a still image file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Output path"},
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
        tl = arguments.get("timeline_name", "")
        alb = arguments.get("album_name", "")

        # --- graph / node operations ---
        if tool_name == "get_graph_node_count":
            return client.get_graph_node_count(tl)
        elif tool_name == "get_graph_node_label":
            return client.get_graph_node_label(tl, int(arguments.get("node_index", 1)))
        elif tool_name == "get_graph_node_tools":
            return client.get_graph_node_tools(tl, int(arguments.get("node_index", 1)))
        elif tool_name == "get_graph_node_lut":
            return client.get_graph_node_lut(tl, int(arguments.get("node_index", 1)))
        elif tool_name == "set_graph_node_lut":
            result = client.set_graph_node_lut(
                tl,
                int(arguments.get("node_index", 1)),
                arguments.get("lut_path", ""),
            )
            return "LUT set" if result else "Failed to set LUT"
        elif tool_name == "get_graph_node_cache_mode":
            return client.get_graph_node_cache_mode(
                tl, int(arguments.get("node_index", 1))
            )  # noqa: E501
        elif tool_name == "set_graph_node_enabled":
            result = client.set_graph_node_enabled(
                tl,
                int(arguments.get("node_index", 1)),
                bool(arguments.get("enabled", True)),
            )
            return "Node state set" if result else "Failed to set node state"
        elif tool_name == "set_graph_node_cache_mode":
            result = client.set_graph_node_cache_mode(
                tl,
                int(arguments.get("node_index", 1)),
                int(arguments.get("cache_mode", 0)),
            )
            return "Cache mode set" if result else "Failed to set cache mode"
        elif tool_name == "apply_grade_from_drx":
            result = client.apply_grade_from_drx(
                tl,
                arguments.get("drx_path", ""),
                int(arguments.get("grade_mode", 0)),
            )
            return "Grade applied" if result else "Failed to apply grade"
        elif tool_name == "apply_arri_cdl_lut":
            result = client.apply_arri_cdl_lut(tl)
            return "ARRI CDL LUT applied" if result else "Failed"
        elif tool_name == "reset_all_grades":
            if err := _confirm_gate(
                arguments, f"Resets all grades in timeline '{tl}'."
            ):
                return err
            result = client.reset_all_grades(tl)
            return "All grades reset" if result else "Failed to reset grades"

        # --- gallery stills — albums ---
        elif tool_name == "get_gallery_albums":
            return client.get_gallery_albums()
        elif tool_name == "get_gallery_powergrade_albums":
            return client.get_gallery_powergrade_albums()
        elif tool_name == "get_current_still_album":
            return client.get_current_still_album()
        elif tool_name == "create_still_album":
            result = client.create_still_album()
            return "Still album created" if result else "Failed to create album"
        elif tool_name == "create_powergrade_album":
            result = client.create_powergrade_album()
            return "PowerGrade album created" if result else "Failed to create album"

        # --- gallery stills — grab / list ---
        elif tool_name == "grab_still":
            result = client.grab_still(tl)
            return "Still grabbed" if result else "Failed to grab still"
        elif tool_name == "grab_all_stills":
            result = client.grab_all_stills(
                tl, int(arguments.get("still_frame_source", 1))
            )
            return "Stills grabbed" if result else "Failed to grab stills"
        elif tool_name == "get_stills":
            return client.get_stills(alb)
        elif tool_name == "export_stills":
            result = client.export_stills(
                alb,
                [int(i) for i in arguments.get("still_indices", [])],
                arguments.get("folder_path", ""),
                arguments.get("file_prefix", ""),
                arguments.get("format", "dpx"),
            )
            return "Stills exported" if result else "Export failed"
        elif tool_name == "import_stills":
            result = client.import_stills(alb, arguments.get("file_paths", []))
            return "Stills imported" if result else "Import failed"
        elif tool_name == "delete_stills":
            indices = [int(i) for i in arguments.get("still_indices", [])]
            if err := _confirm_gate(
                arguments, f"Permanently deletes stills {indices} from album '{alb}'."
            ):
                return err
            result = client.delete_stills(alb, indices)
            return "Stills deleted" if result else "Delete failed"
        elif tool_name == "get_still_label":
            return client.get_still_label(alb, int(arguments.get("still_index", 1)))
        elif tool_name == "set_still_label":
            result = client.set_still_label(
                alb,
                int(arguments.get("still_index", 1)),
                arguments.get("label", ""),
            )
            return "Label set" if result else "Failed to set label"

        # --- color groups ---
        elif tool_name == "get_color_groups":
            return client.get_color_groups()
        elif tool_name == "create_color_group":
            group_name = arguments.get("group_name", "")
            result = client.create_color_group(group_name)
            return f"Color group '{group_name}' created" if result else "Failed"
        elif tool_name == "delete_color_group":
            group_name = arguments.get("group_name", "")
            if err := _confirm_gate(
                arguments,
                f"Permanently deletes color group '{group_name}'; clips become ungrouped.",  # noqa: E501
            ):
                return err
            result = client.delete_color_group(group_name)
            return f"Color group '{group_name}' deleted" if result else "Delete failed"
        elif tool_name == "rename_color_group":
            group_name = arguments.get("group_name", "")
            new_name = arguments.get("new_name", "")
            result = client.rename_color_group(group_name, new_name)
            return f"Renamed to '{new_name}'" if result else "Rename failed"
        elif tool_name == "get_clips_in_color_group":
            return client.get_clips_in_color_group(arguments.get("group_name", ""), tl)
        elif tool_name == "get_color_group_pre_graph":
            return client.get_color_group_pre_graph(arguments.get("group_name", ""))
        elif tool_name == "get_color_group_post_graph":
            return client.get_color_group_post_graph(arguments.get("group_name", ""))

        # --- project-level ---
        elif tool_name == "refresh_lut_list":
            result = client.refresh_lut_list()
            return "LUT list refreshed" if result else "Failed"
        elif tool_name == "export_current_frame_as_still":
            file_path = arguments.get("file_path", "")
            result = client.export_current_frame_as_still(file_path)
            return f"Frame exported to {file_path}" if result else "Export failed"

        return f"Unknown tool in color_grading domain: {tool_name}"
