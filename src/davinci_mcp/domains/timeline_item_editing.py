# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 5: Timeline Item Editing tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "

_ITEM_REF_SCHEMA = {
    "type": "object",
    "description": "Item address: {track_type, track_index, item_index}",
    "properties": {
        "track_type": {"type": "string", "description": "video/audio/subtitle"},
        "track_index": {"type": "integer", "description": "1-based track index"},
        "item_index": {"type": "integer", "description": "1-based item index"},
    },
    "required": ["track_type", "track_index", "item_index"],
}


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


def _ref(arguments: dict[str, Any]) -> dict[str, Any]:
    return arguments.get("item_ref", {})


class TimelineItemEditingDomain:
    name = "timeline_item_editing"
    description = (
        "Timeline item name, timing, spatial/composite properties, enable/color/flags, "
        "markers, takes, color versions, Fusion comps, node graph, grade copy, CDL/LUT, "  # noqa: E501
        "sidecar, linked items, track info, color group assignment, and cache control"
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        _tl_props = {
            "timeline_name": {"type": "string", "description": "Timeline name"},
            "item_ref": _ITEM_REF_SCHEMA,
        }
        _req = ["timeline_name", "item_ref"]

        def _tool(
            name: str,
            desc: str,
            extra: dict | None = None,
            req_extra: list | None = None,
        ) -> types.Tool:  # noqa: E501
            props = dict(_tl_props)
            if extra:
                props.update(extra)
            return types.Tool(
                name=name,
                description=desc,
                inputSchema={
                    "type": "object",
                    "properties": props,
                    "required": _req + (req_extra or []),
                },
            )

        return [
            # ----------------------------------------------------------------
            # Name
            # ----------------------------------------------------------------
            _tool("get_item_name", "Get the name of a timeline item"),
            _tool(
                "set_item_name",
                "Set the name of a timeline item",
                {"name": {"type": "string", "description": "New name"}},
                ["name"],
            ),
            # ----------------------------------------------------------------
            # Timing
            # ----------------------------------------------------------------
            _tool(
                "get_item_duration",
                "Get the duration of a timeline item in frames",
                {"subframe_precision": {"type": "boolean", "description": "Sub-frame"}},
                ["subframe_precision"],
            ),
            _tool(
                "get_item_start",
                "Get the timeline start position of a timeline item",
                {"subframe_precision": {"type": "boolean", "description": "Sub-frame"}},
                ["subframe_precision"],
            ),
            _tool(
                "get_item_end",
                "Get the timeline end position of a timeline item",
                {"subframe_precision": {"type": "boolean", "description": "Sub-frame"}},
                ["subframe_precision"],
            ),
            _tool(
                "get_item_source_start", "Get the source media start frame of an item"
            ),  # noqa: E501
            _tool("get_item_source_end", "Get the source media end frame of an item"),
            _tool(
                "get_item_left_offset",
                "Get the left (head) trim headroom of an item",
                {"subframe_precision": {"type": "boolean", "description": "Sub-frame"}},
                ["subframe_precision"],
            ),
            _tool(
                "get_item_right_offset",
                "Get the right (tail) trim headroom of an item",
                {"subframe_precision": {"type": "boolean", "description": "Sub-frame"}},
                ["subframe_precision"],
            ),
            # ----------------------------------------------------------------
            # Properties (spatial / composite)
            # ----------------------------------------------------------------
            _tool(
                "get_item_properties",
                (
                    "Get all properties of a timeline item. Keys include: "
                    "Pan, Tilt, ZoomX, ZoomY, ZoomGang, RotationAngle, "
                    "AnchorPointX, AnchorPointY, Pitch, Yaw, FlipX, FlipY, "
                    "CropLeft, CropRight, CropTop, CropBottom, CropSoftness, "
                    "CropRetain, DynamicZoomEase, CompositeMode, Opacity, "
                    "Distortion, RetimeProcess, MotionEstimation, Scaling, ResizeFilter."  # noqa: E501
                ),
            ),
            _tool(
                "set_item_property",
                "Set a single property on a timeline item (spatial transforms, composite, etc.)",  # noqa: E501
                {
                    "property_key": {"type": "string", "description": "Property key"},
                    "property_value": {"description": "Property value"},
                },
                ["property_key", "property_value"],
            ),
            # ----------------------------------------------------------------
            # Enabled / color label
            # ----------------------------------------------------------------
            _tool("get_item_enabled", "Check whether a timeline item is enabled"),
            _tool(
                "set_item_enabled",
                "Enable or disable a timeline item",
                {"enabled": {"type": "boolean", "description": "Enabled state"}},
                ["enabled"],
            ),
            _tool("get_item_color", "Get the color label of a timeline item"),
            _tool(
                "set_item_color",
                "Set the color label of a timeline item",
                {"color_name": {"type": "string", "description": "Color name"}},
                ["color_name"],
            ),
            _tool("clear_item_color", "Clear the color label of a timeline item"),
            # ----------------------------------------------------------------
            # Flags
            # ----------------------------------------------------------------
            _tool(
                "add_item_flag",
                "Add a color flag to a timeline item",
                {"color": {"type": "string", "description": "Flag color"}},
                ["color"],
            ),
            _tool("get_item_flags", "Get the list of color flags on a timeline item"),
            _tool(
                "clear_item_flags",
                'Clear flags from a timeline item. Use "All" to clear all.',
                {"color": {"type": "string", "description": 'Color or "All"'}},
                ["color"],
            ),
            # ----------------------------------------------------------------
            # Markers
            # ----------------------------------------------------------------
            types.Tool(
                name="add_item_marker",
                description="Add a marker to a timeline item at a source frame",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "frame_id": {"type": "integer", "description": "Frame"},
                        "color": {"type": "string", "description": "Color"},
                        "marker_name": {"type": "string", "description": "Name"},
                        "note": {"type": "string", "description": "Note"},
                        "duration": {"type": "integer", "description": "Frames"},
                        "custom_data": {"type": "string", "description": "Data"},
                    },
                    "required": _req
                    + [
                        "frame_id",
                        "color",
                        "marker_name",
                        "note",
                        "duration",
                        "custom_data",
                    ],  # noqa: E501
                },
            ),
            _tool(
                "get_item_markers",
                "Get all markers on a timeline item as {frameId: {color, duration, note, name, customData}}",  # noqa: E501
            ),
            types.Tool(
                name="delete_item_markers_by_color",
                description=(
                    f"{_DESTRUCTIVE}Delete item markers by color. "
                    'Use "All" to delete all. Requires confirm=true.'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "color": {"type": "string", "description": 'Color or "All"'},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": _req + ["color", "confirm"],
                },
            ),
            types.Tool(
                name="delete_item_marker_at_frame",
                description=(
                    f"{_DESTRUCTIVE}Delete item marker at a specific frame. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "frame_num": {"type": "integer", "description": "Frame"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": _req + ["frame_num", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Takes
            # ----------------------------------------------------------------
            types.Tool(
                name="add_take",
                description="Add a media pool clip as a take to a timeline item",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "start_frame": {
                            "type": "integer",
                            "description": "Start frame",
                        },  # noqa: E501
                        "end_frame": {"type": "integer", "description": "End frame"},
                    },
                    "required": _req + ["clip_id", "start_frame", "end_frame"],
                },
            ),
            _tool("get_take_count", "Get the number of takes on a timeline item"),
            _tool(
                "get_take_by_index",
                "Get take info (startFrame, endFrame, mediaPoolItem) by 1-based index",
                {
                    "take_index": {
                        "type": "integer",
                        "description": "Take index (1-based)",
                    }
                },  # noqa: E501
                ["take_index"],
            ),
            _tool(
                "select_take",
                "Select the active take by 1-based index",
                {
                    "take_index": {
                        "type": "integer",
                        "description": "Take index (1-based)",
                    }
                },  # noqa: E501
                ["take_index"],
            ),
            types.Tool(
                name="delete_take",
                description=(
                    f"{_DESTRUCTIVE}Delete a take by 1-based index. Requires confirm=true."  # noqa: E501
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "take_index": {"type": "integer", "description": "Take index"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": _req + ["take_index", "confirm"],
                },
            ),
            _tool("finalize_take", "Finalize the current take on a timeline item"),
            # ----------------------------------------------------------------
            # Color versions
            # ----------------------------------------------------------------
            _tool(
                "get_current_color_version",
                "Get the current color version (name and type)",
            ),  # noqa: E501
            _tool(
                "get_color_version_list",
                "Get color version names for an item (version_type: 0=local, 1=remote)",
                {
                    "version_type": {
                        "type": "integer",
                        "description": "0=local, 1=remote",
                    }
                },  # noqa: E501
                ["version_type"],
            ),
            types.Tool(
                name="add_color_version",
                description="Add a new color version to a timeline item",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "version_name": {
                            "type": "string",
                            "description": "Version name",
                        },  # noqa: E501
                        "version_type": {
                            "type": "integer",
                            "description": "0=local, 1=remote",
                        },  # noqa: E501
                    },
                    "required": _req + ["version_name", "version_type"],
                },
            ),
            types.Tool(
                name="load_color_version",
                description="Load a color version by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "version_name": {
                            "type": "string",
                            "description": "Version name",
                        },  # noqa: E501
                        "version_type": {
                            "type": "integer",
                            "description": "0=local, 1=remote",
                        },  # noqa: E501
                    },
                    "required": _req + ["version_name", "version_type"],
                },
            ),
            types.Tool(
                name="delete_color_version",
                description=(
                    f"{_DESTRUCTIVE}Delete a color version by name. Requires confirm=true."  # noqa: E501
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "version_name": {
                            "type": "string",
                            "description": "Version name",
                        },  # noqa: E501
                        "version_type": {
                            "type": "integer",
                            "description": "0=local, 1=remote",
                        },  # noqa: E501
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": _req + ["version_name", "version_type", "confirm"],
                },
            ),
            types.Tool(
                name="rename_color_version",
                description="Rename a color version",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "old_name": {"type": "string", "description": "Current name"},
                        "new_name": {"type": "string", "description": "New name"},
                        "version_type": {
                            "type": "integer",
                            "description": "0=local, 1=remote",
                        },  # noqa: E501
                    },
                    "required": _req + ["old_name", "new_name", "version_type"],
                },
            ),
            # ----------------------------------------------------------------
            # Fusion comps
            # ----------------------------------------------------------------
            _tool(
                "list_fusion_comps", "List Fusion composition names on a timeline item"
            ),  # noqa: E501
            _tool("add_fusion_comp", "Add a new Fusion composition to a timeline item"),
            _tool(
                "load_fusion_comp",
                "Load a Fusion composition by name on a timeline item",
                {"comp_name": {"type": "string", "description": "Comp name"}},
                ["comp_name"],
            ),
            _tool(
                "import_fusion_comp",
                "Import a Fusion composition from a file onto a timeline item",
                {"file_path": {"type": "string", "description": "Source path"}},
                ["file_path"],
            ),
            types.Tool(
                name="export_fusion_comp",
                description="Export a Fusion composition to a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "file_path": {"type": "string", "description": "Destination"},
                        "comp_index": {
                            "type": "integer",
                            "description": "Comp index (0-based)",
                        },  # noqa: E501
                    },
                    "required": _req + ["file_path", "comp_index"],
                },
            ),
            types.Tool(
                name="delete_fusion_comp",
                description=(
                    f"{_DESTRUCTIVE}Delete a Fusion comp by name. Requires confirm=true."  # noqa: E501
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "comp_name": {"type": "string", "description": "Comp name"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": _req + ["comp_name", "confirm"],
                },
            ),
            types.Tool(
                name="rename_fusion_comp",
                description="Rename a Fusion composition on a timeline item",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "old_name": {"type": "string", "description": "Current name"},
                        "new_name": {"type": "string", "description": "New name"},
                    },
                    "required": _req + ["old_name", "new_name"],
                },
            ),
            # ----------------------------------------------------------------
            # Node graph / grade
            # ----------------------------------------------------------------
            _tool(
                "get_item_node_graph",
                "Get node-count info for a timeline item's color node graph",
                {"layer_index": {"type": "integer", "description": "Layer (1-based)"}},
                ["layer_index"],
            ),
            types.Tool(
                name="set_item_node_lut",
                description="Assign a LUT file to a specific node on a timeline item",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "node_index": {
                            "type": "integer",
                            "description": "Node index (1-based)",
                        },
                        "lut_path": {
                            "type": "string",
                            "description": "Absolute path to the .cube LUT file",
                        },
                    },
                    "required": _req + ["node_index", "lut_path"],
                },
            ),
            types.Tool(
                name="copy_grades",
                description="Copy grades from one timeline item to others",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "target_item_refs": {
                            "type": "array",
                            "items": _ITEM_REF_SCHEMA,
                            "description": "Target item references",
                        },
                    },
                    "required": _req + ["target_item_refs"],
                },
            ),
            types.Tool(
                name="set_cdl",
                description=(
                    "Set CDL values on a timeline item. "
                    "cdl_map keys: NodeIndex, Slope, Offset, Power, Saturation."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "cdl_map": {
                            "type": "object",
                            "description": "CDL parameters dict",
                        },
                    },
                    "required": _req + ["cdl_map"],
                },
            ),
            types.Tool(
                name="export_item_lut",
                description=(
                    "Export the LUT for a timeline item. "
                    "export_type: 0=17pt cube, 1=33pt cube, 2=65pt cube, "
                    "3=Panasonic VLUT."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        **_tl_props,
                        "export_type": {
                            "type": "integer",
                            "description": "LUT type (0-3)",
                        },  # noqa: E501
                        "file_path": {"type": "string", "description": "Output path"},
                    },
                    "required": _req + ["export_type", "file_path"],
                },
            ),
            _tool(
                "update_sidecar",
                "Sync BRAW/R3D sidecar file for a timeline item",
            ),
            # ----------------------------------------------------------------
            # Linked items / track info
            # ----------------------------------------------------------------
            _tool("get_linked_items", "Get items linked to a timeline item"),
            _tool("get_item_track", "Get the track type and index of a timeline item"),
            _tool(
                "get_item_audio_channel_mapping",
                "Get audio channel mapping for a timeline item as a JSON string",
            ),
            # ----------------------------------------------------------------
            # Color group
            # ----------------------------------------------------------------
            _tool(
                "get_item_color_group",
                "Get the color group assigned to a timeline item",
            ),  # noqa: E501
            _tool(
                "assign_to_color_group",
                "Assign a timeline item to a color group",
                {"group_name": {"type": "string", "description": "Group name"}},
                ["group_name"],
            ),
            _tool(
                "remove_from_color_group", "Remove a timeline item from its color group"
            ),  # noqa: E501
            # ----------------------------------------------------------------
            # Cache control
            # ----------------------------------------------------------------
            _tool(
                "get_item_color_cache_enabled",
                "Check whether color output cache is enabled for a timeline item",
            ),
            _tool(
                "set_item_color_cache",
                "Set color output cache mode for a timeline item",
                {"cache_value": {"type": "integer", "description": "Cache mode value"}},
                ["cache_value"],
            ),
            _tool(
                "get_item_fusion_cache_enabled",
                "Check whether Fusion output cache is enabled for a timeline item",
            ),
            _tool(
                "set_item_fusion_cache",
                "Set Fusion output cache mode for a timeline item",
                {"cache_value": {"type": "integer", "description": "Cache mode value"}},
                ["cache_value"],
            ),
            # ----------------------------------------------------------------
            # Media pool item / node colors
            # ----------------------------------------------------------------
            _tool(
                "get_item_media_pool_item",
                "Get the media pool item associated with a timeline item",
            ),
            _tool(
                "reset_item_node_colors",
                "Reset all node colors on a timeline item's color graph",
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        tl = arguments.get("timeline_name", "")
        item_ref = _ref(arguments)

        # --- name ---
        if tool_name == "get_item_name":
            return client.get_item_name(tl, item_ref)
        elif tool_name == "set_item_name":
            result = client.set_item_name(tl, item_ref, arguments.get("name", ""))
            return "Name set" if result else "Failed to set name"

        # --- timing ---
        elif tool_name == "get_item_duration":
            return client.get_item_duration(
                tl, item_ref, bool(arguments.get("subframe_precision", False))
            )  # noqa: E501
        elif tool_name == "get_item_start":
            return client.get_item_start(
                tl, item_ref, bool(arguments.get("subframe_precision", False))
            )  # noqa: E501
        elif tool_name == "get_item_end":
            return client.get_item_end(
                tl, item_ref, bool(arguments.get("subframe_precision", False))
            )  # noqa: E501
        elif tool_name == "get_item_source_start":
            return client.get_item_source_start(tl, item_ref)
        elif tool_name == "get_item_source_end":
            return client.get_item_source_end(tl, item_ref)
        elif tool_name == "get_item_left_offset":
            return client.get_item_left_offset(
                tl, item_ref, bool(arguments.get("subframe_precision", False))
            )  # noqa: E501
        elif tool_name == "get_item_right_offset":
            return client.get_item_right_offset(
                tl, item_ref, bool(arguments.get("subframe_precision", False))
            )  # noqa: E501

        # --- properties ---
        elif tool_name == "get_item_properties":
            return client.get_item_properties(tl, item_ref)
        elif tool_name == "set_item_property":
            result = client.set_item_property(
                tl,
                item_ref,
                arguments.get("property_key", ""),
                arguments.get("property_value"),
            )
            return "Property set" if result else "Failed to set property"

        # --- enabled / color ---
        elif tool_name == "get_item_enabled":
            return client.get_item_enabled(tl, item_ref)
        elif tool_name == "set_item_enabled":
            result = client.set_item_enabled(
                tl, item_ref, bool(arguments.get("enabled", True))
            )  # noqa: E501
            return "Item enabled state set" if result else "Failed"
        elif tool_name == "get_item_color":
            return client.get_item_color(tl, item_ref)
        elif tool_name == "set_item_color":
            result = client.set_item_color(
                tl, item_ref, arguments.get("color_name", "")
            )  # noqa: E501
            return "Color set" if result else "Failed to set color"
        elif tool_name == "clear_item_color":
            result = client.clear_item_color(tl, item_ref)
            return "Color cleared" if result else "Failed"

        # --- flags ---
        elif tool_name == "add_item_flag":
            result = client.add_item_flag(tl, item_ref, arguments.get("color", ""))
            return "Flag added" if result else "Failed to add flag"
        elif tool_name == "get_item_flags":
            return client.get_item_flags(tl, item_ref)
        elif tool_name == "clear_item_flags":
            result = client.clear_item_flags(
                tl, item_ref, arguments.get("color", "All")
            )  # noqa: E501
            return "Flags cleared" if result else "Failed"

        # --- markers ---
        elif tool_name == "add_item_marker":
            result = client.add_item_marker(
                tl,
                item_ref,
                int(arguments.get("frame_id", 0)),
                arguments.get("color", ""),
                arguments.get("marker_name", ""),
                arguments.get("note", ""),
                int(arguments.get("duration", 1)),
                arguments.get("custom_data", ""),
            )
            return "Marker added" if result else "Failed to add marker"
        elif tool_name == "get_item_markers":
            return client.get_item_markers(tl, item_ref)
        elif tool_name == "delete_item_markers_by_color":
            color = arguments.get("color", "")
            if err := _confirm_gate(
                arguments, f"Permanently deletes item markers with color '{color}'."
            ):
                return err
            result = client.delete_item_markers_by_color(tl, item_ref, color)
            return "Markers deleted" if result else "Delete failed"
        elif tool_name == "delete_item_marker_at_frame":
            frame_num = int(arguments.get("frame_num", 0))
            if err := _confirm_gate(
                arguments, f"Permanently deletes item marker at frame {frame_num}."
            ):
                return err
            result = client.delete_item_marker_at_frame(tl, item_ref, frame_num)
            return "Marker deleted" if result else "Delete failed"

        # --- takes ---
        elif tool_name == "add_take":
            result = client.add_take(
                tl,
                item_ref,
                arguments.get("clip_id", ""),
                int(arguments.get("start_frame", 0)),
                int(arguments.get("end_frame", 0)),
            )
            return "Take added" if result else "Failed to add take"
        elif tool_name == "get_take_count":
            return client.get_take_count(tl, item_ref)
        elif tool_name == "get_take_by_index":
            return client.get_take_by_index(
                tl, item_ref, int(arguments.get("take_index", 1))
            )  # noqa: E501
        elif tool_name == "select_take":
            result = client.select_take(
                tl, item_ref, int(arguments.get("take_index", 1))
            )  # noqa: E501
            return "Take selected" if result else "Failed to select take"
        elif tool_name == "delete_take":
            take_index = int(arguments.get("take_index", 1))
            if err := _confirm_gate(
                arguments, f"Permanently deletes take {take_index}."
            ):
                return err
            result = client.delete_take(tl, item_ref, take_index)
            return "Take deleted" if result else "Delete failed"
        elif tool_name == "finalize_take":
            result = client.finalize_take(tl, item_ref)
            return "Take finalized" if result else "Failed to finalize"

        # --- color versions ---
        elif tool_name == "get_current_color_version":
            return client.get_current_color_version(tl, item_ref)
        elif tool_name == "get_color_version_list":
            return client.get_color_version_list(
                tl, item_ref, int(arguments.get("version_type", 0))
            )
        elif tool_name == "add_color_version":
            result = client.add_color_version(
                tl,
                item_ref,
                arguments.get("version_name", ""),
                int(arguments.get("version_type", 0)),
            )
            return "Version added" if result else "Failed to add version"
        elif tool_name == "load_color_version":
            result = client.load_color_version(
                tl,
                item_ref,
                arguments.get("version_name", ""),
                int(arguments.get("version_type", 0)),
            )
            return "Version loaded" if result else "Failed to load version"
        elif tool_name == "delete_color_version":
            version_name = arguments.get("version_name", "")
            if err := _confirm_gate(
                arguments, f"Permanently deletes color version '{version_name}'."
            ):
                return err
            result = client.delete_color_version(
                tl, item_ref, version_name, int(arguments.get("version_type", 0))
            )
            return "Version deleted" if result else "Delete failed"
        elif tool_name == "rename_color_version":
            result = client.rename_color_version(
                tl,
                item_ref,
                arguments.get("old_name", ""),
                arguments.get("new_name", ""),
                int(arguments.get("version_type", 0)),
            )
            return "Version renamed" if result else "Failed to rename"

        # --- Fusion comps ---
        elif tool_name == "list_fusion_comps":
            return client.list_fusion_comps(tl, item_ref)
        elif tool_name == "add_fusion_comp":
            result = client.add_fusion_comp(tl, item_ref)
            return "Fusion comp added" if result else "Failed to add comp"
        elif tool_name == "load_fusion_comp":
            result = client.load_fusion_comp(
                tl, item_ref, arguments.get("comp_name", "")
            )  # noqa: E501
            return "Comp loaded" if result else "Failed to load comp"
        elif tool_name == "import_fusion_comp":
            result = client.import_fusion_comp(
                tl, item_ref, arguments.get("file_path", "")
            )  # noqa: E501
            return "Comp imported" if result else "Failed to import comp"
        elif tool_name == "export_fusion_comp":
            result = client.export_fusion_comp(
                tl,
                item_ref,
                arguments.get("file_path", ""),
                int(arguments.get("comp_index", 0)),
            )
            return "Comp exported" if result else "Failed to export comp"
        elif tool_name == "delete_fusion_comp":
            comp_name = arguments.get("comp_name", "")
            if err := _confirm_gate(
                arguments, f"Permanently deletes Fusion comp '{comp_name}'."
            ):
                return err
            result = client.delete_fusion_comp(tl, item_ref, comp_name)
            return "Comp deleted" if result else "Delete failed"
        elif tool_name == "rename_fusion_comp":
            result = client.rename_fusion_comp(
                tl,
                item_ref,
                arguments.get("old_name", ""),
                arguments.get("new_name", ""),
            )
            return "Comp renamed" if result else "Failed to rename comp"

        # --- node graph / grade ---
        elif tool_name == "get_item_node_graph":
            return client.get_item_node_graph(
                tl, item_ref, int(arguments.get("layer_index", 1))
            )  # noqa: E501
        elif tool_name == "set_item_node_lut":
            result = client.set_item_node_lut(
                tl,
                item_ref,
                int(arguments.get("node_index", 1)),
                arguments.get("lut_path", ""),
            )
            return "LUT set" if result else "Failed to set LUT"
        elif tool_name == "copy_grades":
            result = client.copy_grades(
                tl, item_ref, arguments.get("target_item_refs", [])
            )
            return "Grades copied" if result else "Failed to copy grades"
        elif tool_name == "set_cdl":
            result = client.set_cdl(tl, item_ref, arguments.get("cdl_map", {}))
            return "CDL set" if result else "Failed to set CDL"
        elif tool_name == "export_item_lut":
            result = client.export_item_lut(
                tl,
                item_ref,
                int(arguments.get("export_type", 0)),
                arguments.get("file_path", ""),
            )
            return "LUT exported" if result else "Failed to export LUT"
        elif tool_name == "update_sidecar":
            result = client.update_sidecar(tl, item_ref)
            return "Sidecar updated" if result else "Failed to update sidecar"

        # --- linked items / track info ---
        elif tool_name == "get_linked_items":
            return client.get_linked_items(tl, item_ref)
        elif tool_name == "get_item_track":
            return client.get_item_track(tl, item_ref)
        elif tool_name == "get_item_audio_channel_mapping":
            return client.get_item_audio_channel_mapping(tl, item_ref)

        # --- color group ---
        elif tool_name == "get_item_color_group":
            return client.get_item_color_group(tl, item_ref)
        elif tool_name == "assign_to_color_group":
            result = client.assign_to_color_group(
                tl, item_ref, arguments.get("group_name", "")
            )
            return "Assigned to color group" if result else "Failed to assign"
        elif tool_name == "remove_from_color_group":
            result = client.remove_from_color_group(tl, item_ref)
            return "Removed from color group" if result else "Failed to remove"

        # --- cache ---
        elif tool_name == "get_item_color_cache_enabled":
            return client.get_item_color_cache_enabled(tl, item_ref)
        elif tool_name == "set_item_color_cache":
            result = client.set_item_color_cache(
                tl, item_ref, int(arguments.get("cache_value", 0))
            )
            return "Color cache set" if result else "Failed"
        elif tool_name == "get_item_fusion_cache_enabled":
            return client.get_item_fusion_cache_enabled(tl, item_ref)
        elif tool_name == "set_item_fusion_cache":
            result = client.set_item_fusion_cache(
                tl, item_ref, int(arguments.get("cache_value", 0))
            )
            return "Fusion cache set" if result else "Failed"

        # --- media pool item / node colors ---
        elif tool_name == "get_item_media_pool_item":
            return client.get_item_media_pool_item(tl, item_ref)
        elif tool_name == "reset_item_node_colors":
            result = client.reset_item_node_colors(tl, item_ref)
            return "Node colors reset" if result else "Failed"

        return f"Unknown tool in timeline_item_editing domain: {tool_name}"
