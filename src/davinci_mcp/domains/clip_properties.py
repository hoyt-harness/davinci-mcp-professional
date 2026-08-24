# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 4: Clip Properties & Metadata tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


class ClipPropertiesDomain:
    name = "clip_properties"
    description = (
        "Clip name, properties, metadata, third-party metadata, color labels, "
        "flags, markers, audio mapping, mark in/out, proxy links, and clip UUID"
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        return [
            # ----------------------------------------------------------------
            # Name
            # ----------------------------------------------------------------
            types.Tool(
                name="get_clip_name",
                description="Get the name of a media pool clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="set_clip_name",
                description="Set the name of a media pool clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "name": {"type": "string", "description": "New name"},
                    },
                    "required": ["clip_id", "name"],
                },
            ),
            # ----------------------------------------------------------------
            # Properties
            # ----------------------------------------------------------------
            types.Tool(
                name="get_clip_properties",
                description=(
                    "Get clip properties. Returns all properties when property_key is "
                    "omitted. Keys include: Alpha Mode, Bit Depth, Camera #, Clip Color, "  # noqa: E501
                    "Clip Name, Comments, Data Level, Description, Drop Frame, Duration, "  # noqa: E501
                    "End, End TC, FPS, Flags, Format, Frames, Good Take, H-FLIP, IDT, "
                    "Input Color Space, Keyword, Noise Reduction, Offline Reference, "
                    "PAR, Proxy, Proxy Media Path, Reel Name, Resolution, Roll/Card, "
                    "S3D Sync, Scene, Sharpness, Shot, Slate TC, Start, Start TC, "
                    "Super Scale, Take, V-FLIP, Video Codec, Camera Type."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "property_key": {
                            "type": "string",
                            "description": "Property key, or omit for all",
                        },
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="set_clip_property",
                description="Set a single clip property by key",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "property_key": {"type": "string", "description": "Key"},
                        "property_value": {"type": "string", "description": "Value"},
                    },
                    "required": ["clip_id", "property_key", "property_value"],
                },
            ),
            # ----------------------------------------------------------------
            # Metadata
            # ----------------------------------------------------------------
            types.Tool(
                name="get_clip_metadata",
                description=(
                    "Get clip metadata. Returns all metadata when metadata_type is omitted."  # noqa: E501
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "metadata_type": {
                            "type": "string",
                            "description": "Metadata key, or omit for all",
                        },
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="set_clip_metadata",
                description="Set a clip metadata field",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "metadata_type": {"type": "string", "description": "Key"},
                        "metadata_value": {"type": "string", "description": "Value"},
                    },
                    "required": ["clip_id", "metadata_type", "metadata_value"],
                },
            ),
            types.Tool(
                name="get_clip_third_party_metadata",
                description="Get third-party metadata from a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="set_clip_third_party_metadata",
                description="Set a third-party metadata field on a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "metadata_type": {"type": "string", "description": "Key"},
                        "metadata_value": {"type": "string", "description": "Value"},
                    },
                    "required": ["clip_id", "metadata_type", "metadata_value"],
                },
            ),
            # ----------------------------------------------------------------
            # Color label
            # ----------------------------------------------------------------
            types.Tool(
                name="get_clip_color",
                description="Get the color label of a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="set_clip_color",
                description="Set the color label of a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "color_name": {"type": "string", "description": "Color name"},
                    },
                    "required": ["clip_id", "color_name"],
                },
            ),
            types.Tool(
                name="clear_clip_color",
                description="Clear the color label of a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            # ----------------------------------------------------------------
            # Flags
            # ----------------------------------------------------------------
            types.Tool(
                name="add_clip_flag",
                description="Add a color flag to a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "color": {"type": "string", "description": "Flag color"},
                    },
                    "required": ["clip_id", "color"],
                },
            ),
            types.Tool(
                name="get_clip_flags",
                description="Get the list of color flags on a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="clear_clip_flags",
                description='Clear clip flags by color. Use "All" to clear all.',
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "color": {"type": "string", "description": 'Color or "All"'},
                    },
                    "required": ["clip_id", "color"],
                },
            ),
            # ----------------------------------------------------------------
            # Markers
            # ----------------------------------------------------------------
            types.Tool(
                name="add_clip_marker",
                description="Add a marker to a clip at a specific source frame",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "frame_id": {"type": "integer", "description": "Frame"},
                        "color": {"type": "string", "description": "Marker color"},
                        "marker_name": {"type": "string", "description": "Name"},
                        "note": {"type": "string", "description": "Note text"},
                        "duration": {"type": "integer", "description": "Frames"},
                        "custom_data": {"type": "string", "description": "Data"},
                    },
                    "required": [
                        "clip_id",
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
                name="get_clip_markers",
                description=(
                    "Get all markers on a clip as "
                    "{frameId: {color, duration, note, name, customData}}"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="delete_clip_markers_by_color",
                description=(
                    f'{_DESTRUCTIVE}Delete clip markers by color. '
                    'Use "All" to delete all. Requires confirm=true.'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "color": {"type": "string", "description": 'Color or "All"'},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "color", "confirm"],
                },
            ),
            types.Tool(
                name="delete_clip_marker_at_frame",
                description=(
                    f"{_DESTRUCTIVE}Delete the clip marker at a specific frame. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "frame_num": {"type": "integer", "description": "Frame"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "frame_num", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Audio mapping / mark in-out
            # ----------------------------------------------------------------
            types.Tool(
                name="get_clip_audio_mapping",
                description=(
                    "Get the audio channel mapping for a clip as a JSON string: "
                    "embedded channels, linked audio, and track mapping."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="get_clip_mark_in_out",
                description="Get the in/out marks set on a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="set_clip_mark_in_out",
                description="Set in/out marks on a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "mark_in": {"type": "integer", "description": "In frame"},
                        "mark_out": {"type": "integer", "description": "Out frame"},
                        "mark_type": {
                            "type": "string",
                            "description": "video or audio",
                        },
                    },
                    "required": ["clip_id", "mark_in", "mark_out", "mark_type"],
                },
            ),
            types.Tool(
                name="clear_clip_mark_in_out",
                description="Clear in/out marks from a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "mark_type": {
                            "type": "string",
                            "description": "video or audio",
                        },
                    },
                    "required": ["clip_id", "mark_type"],
                },
            ),
            # ----------------------------------------------------------------
            # Proxy / full-resolution links
            # ----------------------------------------------------------------
            types.Tool(
                name="link_proxy_media",
                description="Link a proxy media file to a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "file_path": {"type": "string", "description": "Proxy path"},
                    },
                    "required": ["clip_id", "file_path"],
                },
            ),
            types.Tool(
                name="unlink_proxy_media",
                description="Unlink the proxy media from a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="link_full_resolution_media",
                description="Link a full-resolution media file to a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "file_path": {"type": "string", "description": "Full-res path"},
                    },
                    "required": ["clip_id", "file_path"],
                },
            ),
            types.Tool(
                name="replace_clip",
                description=(
                    f"{_DESTRUCTIVE}Replace the underlying asset of a clip. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "file_path": {"type": "string", "description": "New path"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "file_path", "confirm"],
                },
            ),
            types.Tool(
                name="replace_clip_preserve_subclip",
                description=(
                    f"{_DESTRUCTIVE}Replace a clip's asset, preserving subclip marks. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "file_path": {"type": "string", "description": "New path"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "file_path", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Unique ID / timeline association
            # ----------------------------------------------------------------
            types.Tool(
                name="get_clip_unique_id",
                description="Get the UUID of a clip (stable identifier for subsequent calls)",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="get_clip_timeline",
                description="Get the timeline associated with a clip (if it is a timeline clip)",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        clip_id = arguments.get("clip_id", "")

        # --- name ---
        if tool_name == "get_clip_name":
            return client.get_clip_name(clip_id)
        elif tool_name == "set_clip_name":
            result = client.set_clip_name(clip_id, arguments.get("name", ""))
            return "Name updated" if result else "Failed to update name"

        # --- properties ---
        elif tool_name == "get_clip_properties":
            return client.get_clip_properties(clip_id)
        elif tool_name == "set_clip_property":
            result = client.set_clip_property(
                clip_id,
                arguments.get("property_key", ""),
                arguments.get("property_value", ""),
            )
            return "Property set" if result else "Failed to set property"

        # --- metadata ---
        elif tool_name == "get_clip_metadata":
            return client.get_clip_metadata(clip_id)
        elif tool_name == "set_clip_metadata":
            result = client.set_clip_metadata(
                clip_id,
                arguments.get("metadata_type", ""),
                arguments.get("metadata_value", ""),
            )
            return "Metadata set" if result else "Failed to set metadata"
        elif tool_name == "get_clip_third_party_metadata":
            return client.get_clip_third_party_metadata(clip_id)
        elif tool_name == "set_clip_third_party_metadata":
            result = client.set_clip_third_party_metadata(
                clip_id,
                arguments.get("metadata_type", ""),
                arguments.get("metadata_value", ""),
            )
            return "Metadata set" if result else "Failed to set metadata"

        # --- color label ---
        elif tool_name == "get_clip_color":
            return client.get_clip_color(clip_id)
        elif tool_name == "set_clip_color":
            result = client.set_clip_color(clip_id, arguments.get("color_name", ""))
            return "Color set" if result else "Failed to set color"
        elif tool_name == "clear_clip_color":
            result = client.clear_clip_color(clip_id)
            return "Color cleared" if result else "Failed to clear color"

        # --- flags ---
        elif tool_name == "add_clip_flag":
            result = client.add_clip_flag(clip_id, arguments.get("color", ""))
            return "Flag added" if result else "Failed to add flag"
        elif tool_name == "get_clip_flags":
            return client.get_clip_flags(clip_id)
        elif tool_name == "clear_clip_flags":
            result = client.clear_clip_flags(clip_id, arguments.get("color", "All"))
            return "Flags cleared" if result else "Failed to clear flags"

        # --- markers ---
        elif tool_name == "add_clip_marker":
            result = client.add_clip_marker(
                clip_id,
                int(arguments.get("frame_id", 0)),
                arguments.get("color", ""),
                arguments.get("marker_name", ""),
                arguments.get("note", ""),
                int(arguments.get("duration", 1)),
                arguments.get("custom_data", ""),
            )
            return "Marker added" if result else "Failed to add marker"
        elif tool_name == "get_clip_markers":
            return client.get_clip_markers(clip_id)
        elif tool_name == "delete_clip_markers_by_color":
            color = arguments.get("color", "")
            if err := _confirm_gate(
                arguments, f"Permanently deletes clip markers with color '{color}'."
            ):
                return err
            result = client.delete_clip_markers_by_color(clip_id, color)
            return "Markers deleted" if result else "Delete failed"
        elif tool_name == "delete_clip_marker_at_frame":
            frame_num = int(arguments.get("frame_num", 0))
            if err := _confirm_gate(
                arguments, f"Permanently deletes clip marker at frame {frame_num}."
            ):
                return err
            result = client.delete_clip_marker_at_frame(clip_id, frame_num)
            return "Marker deleted" if result else "Delete failed"

        # --- audio / mark in-out ---
        elif tool_name == "get_clip_audio_mapping":
            return client.get_clip_audio_mapping(clip_id)
        elif tool_name == "get_clip_mark_in_out":
            return client.get_clip_mark_in_out(clip_id)
        elif tool_name == "set_clip_mark_in_out":
            result = client.set_clip_mark_in_out(
                clip_id,
                int(arguments.get("mark_in", 0)),
                int(arguments.get("mark_out", 0)),
                arguments.get("mark_type", "video"),
            )
            return "Mark in/out set" if result else "Failed to set marks"
        elif tool_name == "clear_clip_mark_in_out":
            result = client.clear_clip_mark_in_out(
                clip_id, arguments.get("mark_type", "video")
            )
            return "Marks cleared" if result else "Failed to clear marks"

        # --- proxy / full-res links ---
        elif tool_name == "link_proxy_media":
            result = client.link_proxy_media(clip_id, arguments.get("file_path", ""))
            return "Proxy linked" if result else "Failed to link proxy"
        elif tool_name == "unlink_proxy_media":
            result = client.unlink_proxy_media(clip_id)
            return "Proxy unlinked" if result else "Failed to unlink proxy"
        elif tool_name == "link_full_resolution_media":
            result = client.link_full_resolution_media(
                clip_id, arguments.get("file_path", "")
            )
            return "Full-resolution media linked" if result else "Failed to link"
        elif tool_name == "replace_clip":
            file_path = arguments.get("file_path", "")
            if err := _confirm_gate(
                arguments, f"Replaces the underlying asset of clip with '{file_path}'."
            ):
                return err
            result = client.replace_clip(clip_id, file_path)
            return "Clip replaced" if result else "Replace failed"
        elif tool_name == "replace_clip_preserve_subclip":
            file_path = arguments.get("file_path", "")
            if err := _confirm_gate(
                arguments,
                f"Replaces clip asset with '{file_path}', preserving subclip marks.",
            ):
                return err
            result = client.replace_clip_preserve_subclip(clip_id, file_path)
            return "Clip replaced (subclip preserved)" if result else "Replace failed"

        # --- unique id / timeline ---
        elif tool_name == "get_clip_unique_id":
            return client.get_clip_unique_id(clip_id)
        elif tool_name == "get_clip_timeline":
            return client.get_clip_timeline(clip_id)

        return f"Unknown tool in clip_properties domain: {tool_name}"
