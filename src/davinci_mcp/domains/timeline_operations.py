# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 2: Timeline Operations tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "
_COORDS_WARNING = (
    "Item coordinates ({track_type, track_index, item_index}) are invalidated by "
    "any timeline modification — re-call get_items_in_track after mutations."
)


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


def _track_type_schema() -> dict[str, Any]:
    return {
        "type": "string",
        "description": "Track type: 'video', 'audio', or 'subtitle'",
        "enum": ["video", "audio", "subtitle"],
    }


def _item_refs_schema() -> dict[str, Any]:
    return {
        "type": "array",
        "description": (f"List of item coordinates. {_COORDS_WARNING}"),
        "items": {
            "type": "object",
            "properties": {
                "track_type": _track_type_schema(),
                "track_index": {
                    "type": "integer",
                    "description": "1-based track index",
                },
                "item_index": {
                    "type": "integer",
                    "description": "1-based item index within the track",
                },
            },
            "required": ["track_type", "track_index", "item_index"],
        },
    }


class TimelineOperationsDomain:
    name = "timeline_operations"
    description = (
        "Full timeline management: settings, timecode, tracks, markers, items, "
        "export/import, generators, titles, Fusion clips, and Dolby Vision analysis"
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        return [
            # ----------------------------------------------------------------
            # Original migrated tools
            # ----------------------------------------------------------------
            types.Tool(
                name="list_timelines",
                description="List all timelines in the current project",
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_timeline",
                description="Get the name of the currently active timeline",
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="create_timeline",
                description="Create a new empty timeline with the given name",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "New timeline name"},
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="switch_timeline",
                description="Switch the current timeline by name",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Timeline name to switch to",
                        },
                    },
                    "required": ["name"],
                },
            ),
            # ----------------------------------------------------------------
            # Management
            # ----------------------------------------------------------------
            types.Tool(
                name="rename_timeline",
                description="Rename an existing timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Current timeline name",
                        },
                        "new_name": {"type": "string", "description": "New name"},
                    },
                    "required": ["name", "new_name"],
                },
            ),
            types.Tool(
                name="delete_timeline",
                description=f"{_DESTRUCTIVE}Permanently delete a timeline. Requires confirm=true.",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Timeline name to delete",
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["name", "confirm"],
                },
            ),
            types.Tool(
                name="duplicate_timeline",
                description="Duplicate a timeline with a new name",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Timeline to duplicate",
                        },
                        "new_name": {
                            "type": "string",
                            "description": "Name for the duplicate",
                        },
                    },
                    "required": ["name", "new_name"],
                },
            ),
            # ----------------------------------------------------------------
            # Settings / timecode
            # ----------------------------------------------------------------
            types.Tool(
                name="get_timeline_settings",
                description="Get one or all settings of a timeline. Omit setting_name to get all.",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Timeline name"},
                        "setting_name": {
                            "type": ["string", "null"],
                            "description": "Setting key, or null for all settings",
                        },
                    },
                    "required": ["name", "setting_name"],
                },
            ),
            types.Tool(
                name="set_timeline_setting",
                description="Set a timeline setting value. Note: Timeline.SetSetting() has very limited write support in Resolve 21 — most settings are effectively read-only via the API and will return 'Update failed'.",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Timeline name"},
                        "setting_name": {
                            "type": "string",
                            "description": "Setting key",
                        },
                        "setting_value": {"description": "New value for the setting"},
                    },
                    "required": ["name", "setting_name", "setting_value"],
                },
            ),
            types.Tool(
                name="get_start_timecode",
                description="Get the start timecode of a timeline",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="set_start_timecode",
                description="Set the start timecode of a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "timecode": {
                            "type": "string",
                            "description": "HH:MM:SS:FF format",
                        },
                    },
                    "required": ["name", "timecode"],
                },
            ),
            types.Tool(
                name="get_current_timecode",
                description="Get the current playhead timecode of a timeline",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="set_current_timecode",
                description=(
                    "Move the playhead to a timecode position. "
                    "Only works on the currently active timeline — call switch_timeline first if needed."  # noqa: E501
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "timecode": {
                            "type": "string",
                            "description": "HH:MM:SS:FF format",
                        },
                    },
                    "required": ["name", "timecode"],
                },
            ),
            types.Tool(
                name="get_timeline_start_frame",
                description="Get the start frame number of a timeline",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="get_timeline_end_frame",
                description="Get the end frame number of a timeline",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            # ----------------------------------------------------------------
            # Marks
            # ----------------------------------------------------------------
            types.Tool(
                name="get_timeline_marks",
                description="Get the in/out marks of a timeline",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="set_timeline_marks",
                description="Set in/out marks on a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "mark_in": {
                            "type": "integer",
                            "description": "In point frame number",
                        },
                        "mark_out": {
                            "type": "integer",
                            "description": "Out point frame number",
                        },
                        "mark_type": {
                            "type": "string",
                            "description": "Mark type: 'video', 'audio', or 'all'",
                        },
                    },
                    "required": ["name", "mark_in", "mark_out", "mark_type"],
                },
            ),
            types.Tool(
                name="clear_timeline_marks",
                description="Clear in/out marks from a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "mark_type": {
                            "type": "string",
                            "description": "Mark type to clear: 'video', 'audio', or 'all'",  # noqa: E501
                        },
                    },
                    "required": ["name", "mark_type"],
                },
            ),
            # ----------------------------------------------------------------
            # Tracks
            # ----------------------------------------------------------------
            types.Tool(
                name="get_track_count",
                description="Get the number of tracks of a given type in a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                    },
                    "required": ["name", "track_type"],
                },
            ),
            types.Tool(
                name="add_track",
                description="Add a new track to a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "sub_track_type": {
                            "type": "string",
                            "description": "Audio subtype: 'mono', 'stereo', '5.1', '7.1', etc. Leave empty for video/subtitle.",  # noqa: E501
                        },
                    },
                    "required": ["name", "track_type", "sub_track_type"],
                },
            ),
            types.Tool(
                name="delete_track",
                description=f"{_DESTRUCTIVE}Delete a track and all its contents. Requires confirm=true.",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {
                            "type": "integer",
                            "description": "1-based track index",
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["name", "track_type", "track_index", "confirm"],
                },
            ),
            types.Tool(
                name="get_track_name",
                description="Get the name of a timeline track",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {
                            "type": "integer",
                            "description": "1-based track index",
                        },
                    },
                    "required": ["name", "track_type", "track_index"],
                },
            ),
            types.Tool(
                name="set_track_name",
                description="Set the name of a timeline track",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {
                            "type": "integer",
                            "description": "1-based track index",
                        },
                        "new_name": {"type": "string", "description": "New track name"},
                    },
                    "required": ["name", "track_type", "track_index", "new_name"],
                },
            ),
            types.Tool(
                name="get_track_subtype",
                description="Get the audio format subtype of an audio track",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {"type": "integer"},
                    },
                    "required": ["name", "track_type", "track_index"],
                },
            ),
            types.Tool(
                name="enable_track",
                description="Enable or disable a timeline track",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {"type": "integer"},
                        "enabled": {"type": "boolean"},
                    },
                    "required": ["name", "track_type", "track_index", "enabled"],
                },
            ),
            types.Tool(
                name="get_track_enabled",
                description="Get whether a timeline track is enabled",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {"type": "integer"},
                    },
                    "required": ["name", "track_type", "track_index"],
                },
            ),
            types.Tool(
                name="lock_track",
                description="Lock or unlock a timeline track",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {"type": "integer"},
                        "locked": {"type": "boolean"},
                    },
                    "required": ["name", "track_type", "track_index", "locked"],
                },
            ),
            types.Tool(
                name="get_track_locked",
                description="Get whether a timeline track is locked",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {"type": "integer"},
                    },
                    "required": ["name", "track_type", "track_index"],
                },
            ),
            # ----------------------------------------------------------------
            # Items
            # ----------------------------------------------------------------
            types.Tool(
                name="get_items_in_track",
                description=(
                    f"List all items in a timeline track with their coordinates. "
                    f"{_COORDS_WARNING}"
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "track_type": _track_type_schema(),
                        "track_index": {"type": "integer"},
                    },
                    "required": ["name", "track_type", "track_index"],
                },
            ),
            types.Tool(
                name="get_selected_timeline_clips",
                description=(
                    "Get clips currently selected in a timeline. "
                    "Returns name and position only. For coordinate-based operations, "
                    "use get_items_in_track to obtain item references."
                ),
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="get_current_video_item",
                description="Get the current video item under the playhead",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="get_current_clip_thumbnail",
                description="Get the current clip thumbnail image data from the Color page",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="get_timeline_media_pool_item",
                description="Get the media pool item associated with a timeline",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="delete_timeline_clips",
                description=(
                    f"{_DESTRUCTIVE}Delete clips from a timeline. "
                    f"{_COORDS_WARNING} Requires confirm=true. "
                    "Note: generator clips (Solid Color, Fusion Composition) cannot be deleted via this API in Resolve 21 — only real media clips."  # noqa: E501
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "item_refs": _item_refs_schema(),
                        "ripple": {
                            "type": "boolean",
                            "description": "If true, downstream clips shift to fill the gap",  # noqa: E501
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["name", "item_refs", "ripple", "confirm"],
                },
            ),
            types.Tool(
                name="link_clips",
                description="Link or unlink video and audio clips in a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "item_refs": _item_refs_schema(),
                        "linked": {"type": "boolean"},
                    },
                    "required": ["name", "item_refs", "linked"],
                },
            ),
            # ----------------------------------------------------------------
            # Markers
            # ----------------------------------------------------------------
            types.Tool(
                name="add_timeline_marker",
                description="Add a marker to a timeline at a specific frame",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "frame_id": {
                            "type": "integer",
                            "description": "Frame number for the marker",
                        },
                        "color": {
                            "type": "string",
                            "description": "Marker color: Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia, Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream",  # noqa: E501
                        },
                        "marker_name": {"type": "string", "description": "Marker name"},
                        "note": {"type": "string", "description": "Marker note text"},
                        "duration": {
                            "type": "integer",
                            "description": "Marker duration in frames",
                        },
                        "custom_data": {
                            "type": "string",
                            "description": "Custom metadata string",
                        },
                    },
                    "required": [
                        "name",
                        "frame_id",
                        "color",
                        "marker_name",
                        "note",
                        "duration",
                        "custom_data",
                    ],
                },
            ),
            types.Tool(
                name="get_timeline_markers",
                description="Get all markers on a timeline as {frameId: {color, duration, note, name, customData}}",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="delete_timeline_markers_by_color",
                description=(
                    f"{_DESTRUCTIVE}Delete timeline markers by color. "
                    "Use 'All' to clear all markers. Requires confirm=true."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "color": {
                            "type": "string",
                            "description": "Marker color to delete, or 'All' to delete all",  # noqa: E501
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["name", "color", "confirm"],
                },
            ),
            types.Tool(
                name="delete_timeline_marker_at_frame",
                description=f"{_DESTRUCTIVE}Delete the timeline marker at a specific frame. Requires confirm=true.",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "frame_num": {"type": "integer"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["name", "frame_num", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Export / import
            # ----------------------------------------------------------------
            types.Tool(
                name="export_timeline",
                description="Export a timeline to AAF, EDL, XML, FCPXML, OTIO, DRT, ALE, HDR, or Dolby Vision",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "file_name": {
                            "type": "string",
                            "description": "Destination file path",
                        },
                        "export_type": {
                            "type": "string",
                            "description": "e.g. EXPORT_AAF, EXPORT_EDL, EXPORT_XML, EXPORT_FCPXML_1_10, EXPORT_OTIO",  # noqa: E501
                        },
                        "export_subtype": {
                            "type": "string",
                            "description": "e.g. EXPORT_AAF_NEW, EXPORT_NONE",
                        },
                    },
                    "required": ["name", "file_name", "export_type", "export_subtype"],
                },
            ),
            types.Tool(
                name="import_into_timeline",
                description="Import content into a timeline from an AAF file with remapping",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "file_path": {"type": "string"},
                        "import_options": {
                            "type": "object",
                            "description": "Import options dict (see DaVinci scripting docs)",  # noqa: E501
                        },
                    },
                    "required": ["name", "file_path", "import_options"],
                },
            ),
            # ----------------------------------------------------------------
            # Generators / titles / Fusion
            # ----------------------------------------------------------------
            types.Tool(
                name="insert_generator",
                description="Insert a generator clip into a timeline at the current playhead position",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "generator_name": {
                            "type": "string",
                            "description": "Generator name, e.g. 'Solid Color'",
                        },
                    },
                    "required": ["name", "generator_name"],
                },
            ),
            types.Tool(
                name="insert_fusion_generator",
                description="Insert a Fusion generator into a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "generator_name": {"type": "string"},
                    },
                    "required": ["name", "generator_name"],
                },
            ),
            types.Tool(
                name="insert_ofx_generator",
                description="Insert an OFX generator into a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "generator_name": {"type": "string"},
                    },
                    "required": ["name", "generator_name"],
                },
            ),
            types.Tool(
                name="insert_title",
                description="Insert a title clip into a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "title_name": {
                            "type": "string",
                            "description": "Title preset name",
                        },
                    },
                    "required": ["name", "title_name"],
                },
            ),
            types.Tool(
                name="insert_fusion_title",
                description="Insert a Fusion title into a timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "title_name": {"type": "string"},
                    },
                    "required": ["name", "title_name"],
                },
            ),
            types.Tool(
                name="insert_fusion_composition",
                description="Insert a new Fusion composition into a timeline at the current position",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="get_timeline_node_graph",
                description="Get the color node graph for a timeline (Color page)",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="create_compound_clip",
                description=(
                    f"{_DESTRUCTIVE}Create a compound clip from selected timeline items. "  # noqa: E501
                    f"{_COORDS_WARNING} Requires confirm=true."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "item_refs": _item_refs_schema(),
                        "clip_info": {
                            "type": "object",
                            "description": "Clip info dict (startTimecode, name)",
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["name", "item_refs", "clip_info", "confirm"],
                },
            ),
            types.Tool(
                name="create_fusion_clip",
                description=(
                    f"{_DESTRUCTIVE}Create a Fusion clip from selected timeline items. "
                    f"{_COORDS_WARNING} Requires confirm=true."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "item_refs": _item_refs_schema(),
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["name", "item_refs", "confirm"],
                },
            ),
            types.Tool(
                name="analyze_dolby_vision",
                description="Run Dolby Vision analysis on timeline items",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "item_refs": _item_refs_schema(),
                        "analysis_type": {
                            "type": "integer",
                            "description": "Analysis type (see DaVinci scripting docs)",
                        },
                    },
                    "required": ["name", "item_refs", "analysis_type"],
                },
            ),
        ]

    async def dispatch(  # noqa: PLR0912, PLR0915
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        name = arguments.get("name", "")

        # --- original migrated tools ---
        if tool_name == "list_timelines":
            return client.list_timelines()
        elif tool_name == "get_current_timeline":
            return client.get_current_timeline_name()
        elif tool_name == "create_timeline":
            result = client.create_timeline(name)
            return (
                f"Created timeline '{name}'" if result else f"Failed to create '{name}'"
            )
        elif tool_name == "switch_timeline":
            result = client.switch_timeline(name)
            return (
                f"Switched to '{name}'" if result else f"Failed to switch to '{name}'"
            )

        # --- management ---
        elif tool_name == "rename_timeline":
            new_name = arguments.get("new_name", "")
            result = client.rename_timeline(name, new_name)
            return f"Renamed '{name}' → '{new_name}'" if result else "Rename failed"
        elif tool_name == "delete_timeline":
            if err := _confirm_gate(
                arguments, f"Permanently deletes timeline '{name}'."
            ):
                return err
            result = client.delete_timeline(name)
            return f"Deleted timeline '{name}'" if result else "Delete failed"
        elif tool_name == "duplicate_timeline":
            new_name = arguments.get("new_name", "")
            result = client.duplicate_timeline(name, new_name)
            return (
                f"Duplicated '{name}' as '{new_name}'" if result else "Duplicate failed"
            )

        # --- settings / timecode ---
        elif tool_name == "get_timeline_settings":
            return client.get_timeline_settings(name, arguments.get("setting_name"))
        elif tool_name == "set_timeline_setting":
            result = client.set_timeline_setting(
                name, arguments.get("setting_name", ""), arguments.get("setting_value")
            )
            return "Setting updated" if result else "Update failed"
        elif tool_name == "get_start_timecode":
            return client.get_start_timecode(name)
        elif tool_name == "set_start_timecode":
            result = client.set_start_timecode(name, arguments.get("timecode", ""))
            return "Start timecode set" if result else "Failed"
        elif tool_name == "get_current_timecode":
            return client.get_current_timecode(name)
        elif tool_name == "set_current_timecode":
            result = client.set_current_timecode(name, arguments.get("timecode", ""))
            return "Playhead moved" if result else "Failed"
        elif tool_name == "get_timeline_start_frame":
            return client.get_timeline_start_frame(name)
        elif tool_name == "get_timeline_end_frame":
            return client.get_timeline_end_frame(name)

        # --- marks ---
        elif tool_name == "get_timeline_marks":
            return client.get_timeline_marks(name)
        elif tool_name == "set_timeline_marks":
            result = client.set_timeline_marks(
                name,
                int(arguments.get("mark_in", 0)),
                int(arguments.get("mark_out", 0)),
                arguments.get("mark_type", "video"),
            )
            return "Marks set" if result else "Failed"
        elif tool_name == "clear_timeline_marks":
            result = client.clear_timeline_marks(
                name, arguments.get("mark_type", "video")
            )
            return "Marks cleared" if result else "Failed"

        # --- tracks ---
        elif tool_name == "get_track_count":
            return client.get_track_count(name, arguments.get("track_type", "video"))
        elif tool_name == "add_track":
            result = client.add_track(
                name,
                arguments.get("track_type", "video"),
                arguments.get("sub_track_type", ""),
            )
            return "Track added" if result else "Failed"
        elif tool_name == "delete_track":
            if err := _confirm_gate(
                arguments,
                f"Permanently deletes {arguments.get('track_type', 'video')} track "
                f"{arguments.get('track_index', 1)} and all its clips from '{name}'.",
            ):
                return err
            result = client.delete_track(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
            )
            return "Track deleted" if result else "Delete failed"
        elif tool_name == "get_track_name":
            return client.get_track_name(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
            )
        elif tool_name == "set_track_name":
            result = client.set_track_name(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
                arguments.get("new_name", ""),
            )
            return "Track renamed" if result else "Failed"
        elif tool_name == "get_track_subtype":
            return client.get_track_subtype(
                name,
                arguments.get("track_type", "audio"),
                int(arguments.get("track_index", 1)),
            )
        elif tool_name == "enable_track":
            result = client.enable_track(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
                bool(arguments.get("enabled", True)),
            )
            return "Track enabled state set" if result else "Failed"
        elif tool_name == "get_track_enabled":
            return client.get_track_enabled(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
            )
        elif tool_name == "lock_track":
            result = client.lock_track(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
                bool(arguments.get("locked", True)),
            )
            return "Track lock state set" if result else "Failed"
        elif tool_name == "get_track_locked":
            return client.get_track_locked(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
            )

        # --- items ---
        elif tool_name == "get_items_in_track":
            return client.get_items_in_track(
                name,
                arguments.get("track_type", "video"),
                int(arguments.get("track_index", 1)),
            )
        elif tool_name == "get_selected_timeline_clips":
            return client.get_selected_timeline_clips(name)
        elif tool_name == "get_current_video_item":
            return client.get_current_video_item(name)
        elif tool_name == "get_current_clip_thumbnail":
            return client.get_current_clip_thumbnail(name)
        elif tool_name == "get_timeline_media_pool_item":
            return client.get_timeline_media_pool_item(name)
        elif tool_name == "delete_timeline_clips":
            item_refs = arguments.get("item_refs", [])
            if err := _confirm_gate(
                arguments,
                f"Permanently deletes {len(item_refs)} clip(s) from '{name}'.",
            ):
                return err
            result = client.delete_timeline_clips(
                name, item_refs, bool(arguments.get("ripple", False))
            )
            return f"Deleted {len(item_refs)} clip(s)" if result else "Delete failed"
        elif tool_name == "link_clips":
            result = client.link_clips(
                name,
                arguments.get("item_refs", []),
                bool(arguments.get("linked", True)),
            )
            return "Clip link state set" if result else "Failed"

        # --- markers ---
        elif tool_name == "add_timeline_marker":
            result = client.add_timeline_marker(
                name,
                int(arguments.get("frame_id", 0)),
                arguments.get("color", "Blue"),
                arguments.get("marker_name", ""),
                arguments.get("note", ""),
                int(arguments.get("duration", 1)),
                arguments.get("custom_data", ""),
            )
            return "Marker added" if result else "Failed"
        elif tool_name == "get_timeline_markers":
            return client.get_timeline_markers(name)
        elif tool_name == "delete_timeline_markers_by_color":
            color = arguments.get("color", "")
            if err := _confirm_gate(
                arguments, f"Deletes all '{color}' markers from '{name}'."
            ):
                return err
            result = client.delete_timeline_markers_by_color(name, color)
            return "Markers deleted" if result else "Delete failed"
        elif tool_name == "delete_timeline_marker_at_frame":
            frame = int(arguments.get("frame_num", 0))
            if err := _confirm_gate(
                arguments, f"Deletes the marker at frame {frame} in '{name}'."
            ):
                return err
            result = client.delete_timeline_marker_at_frame(name, frame)
            return "Marker deleted" if result else "Delete failed"

        # --- export / import ---
        elif tool_name == "export_timeline":
            result = client.export_timeline(
                name,
                arguments.get("file_name", ""),
                arguments.get("export_type", ""),
                arguments.get("export_subtype", ""),
            )
            return f"Exported '{name}'" if result else "Export failed"
        elif tool_name == "import_into_timeline":
            result = client.import_into_timeline(
                name,
                arguments.get("file_path", ""),
                arguments.get("import_options", {}),
            )
            return "Import complete" if result else "Import failed"

        # --- generators / titles / Fusion ---
        elif tool_name == "insert_generator":
            result = client.insert_generator(name, arguments.get("generator_name", ""))
            return "Generator inserted" if result else "Failed"
        elif tool_name == "insert_fusion_generator":
            result = client.insert_fusion_generator(
                name, arguments.get("generator_name", "")
            )
            return "Fusion generator inserted" if result else "Failed"
        elif tool_name == "insert_ofx_generator":
            result = client.insert_ofx_generator(
                name, arguments.get("generator_name", "")
            )
            return "OFX generator inserted" if result else "Failed"
        elif tool_name == "insert_title":
            result = client.insert_title(name, arguments.get("title_name", ""))
            return "Title inserted" if result else "Failed"
        elif tool_name == "insert_fusion_title":
            result = client.insert_fusion_title(name, arguments.get("title_name", ""))
            return "Fusion title inserted" if result else "Failed"
        elif tool_name == "insert_fusion_composition":
            result = client.insert_fusion_composition(name)
            return "Fusion composition inserted" if result else "Failed"
        elif tool_name == "get_timeline_node_graph":
            return client.get_timeline_node_graph(name)
        elif tool_name == "create_compound_clip":
            item_refs = arguments.get("item_refs", [])
            if err := _confirm_gate(
                arguments,
                f"Converts {len(item_refs)} clip(s) in '{name}' into a compound clip.",
            ):
                return err
            result = client.create_compound_clip(
                name, item_refs, arguments.get("clip_info", {})
            )
            return "Compound clip created" if result else "Failed"
        elif tool_name == "create_fusion_clip":
            item_refs = arguments.get("item_refs", [])
            if err := _confirm_gate(
                arguments,
                f"Converts {len(item_refs)} clip(s) in '{name}' into a Fusion clip.",
            ):
                return err
            result = client.create_fusion_clip(name, item_refs)
            return "Fusion clip created" if result else "Failed"
        elif tool_name == "analyze_dolby_vision":
            result = client.analyze_dolby_vision(
                name,
                arguments.get("item_refs", []),
                int(arguments.get("analysis_type", 0)),
            )
            return "Dolby Vision analysis complete" if result else "Analysis failed"

        return f"Unknown tool in timeline_operations domain: {tool_name}"
