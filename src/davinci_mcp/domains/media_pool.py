# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 3: Media Pool Operations tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


class MediaPoolDomain:
    name = "media_pool"
    description = (
        "Full media pool management: folder navigation, clip operations, "
        "timeline creation from clips, relink, mattes, and stereo clips"
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        return [
            # ----------------------------------------------------------------
            # Original migrated tools
            # ----------------------------------------------------------------
            types.Tool(
                name="list_media_clips",
                description="List all clips in the media pool root folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="import_media",
                description="Import a media file into the current media pool folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the media file",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            # ----------------------------------------------------------------
            # Folder inspection
            # ----------------------------------------------------------------
            types.Tool(
                name="get_media_pool_root_folder",
                description="Get info about the media pool root folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_media_pool_folder",
                description="Get the currently selected media pool folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="set_current_media_pool_folder",
                description="Set the currently selected media pool folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_path": {
                            "type": "string",
                            "description": "Path from root's children, slash-separated; e.g. 'B-Roll' or 'B-Roll/Outdoor'. Use 'Master' or '/' for root.",  # noqa: E501
                        },
                    },
                    "required": ["folder_path"],
                },
            ),
            types.Tool(
                name="get_folder_clips",
                description="List clips in a specific media pool folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_path": {
                            "type": "string",
                            "description": "Path from root's children, slash-separated; e.g. 'B-Roll' or 'B-Roll/Outdoor'. Use 'Master' or '/' for root.",  # noqa: E501
                        },
                    },
                    "required": ["folder_path"],
                },
            ),
            types.Tool(
                name="get_folder_subfolders",
                description="List subfolders of a media pool folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_path": {
                            "type": "string",
                            "description": "Path from root's children, slash-separated; e.g. 'B-Roll' or 'B-Roll/Outdoor'. Use 'Master' or '/' for root.",  # noqa: E501
                        },
                    },
                    "required": ["folder_path"],
                },
            ),
            types.Tool(
                name="get_selected_pool_clips",
                description="Get the clips currently selected in the media pool. Note: MediaPool.GetSelectedClips() is undocumented in FusionScript and returns empty in Resolve 21 — treat this as best-effort.",  # noqa: E501
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="set_selected_pool_clip",
                description="Set a clip as the selected clip in the media pool (sets the source viewer clip). Note: selection state cannot be verified via get_selected_pool_clips in Resolve 21.",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {
                            "type": "string",
                            "description": "UUID from get_folder_clips or list_media_clips",  # noqa: E501
                        },
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="refresh_media_pool_folders",
                description="Refresh media pool folders (use in collaboration mode)",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            # ----------------------------------------------------------------
            # Folder management
            # ----------------------------------------------------------------
            types.Tool(
                name="create_media_pool_folder",
                description="Create a subfolder inside an existing media pool folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_path": {
                            "type": "string",
                            "description": "Parent folder path (slash-separated from root)",  # noqa: E501
                        },
                        "name": {"type": "string", "description": "New subfolder name"},
                    },
                    "required": ["folder_path", "name"],
                },
            ),
            types.Tool(
                name="delete_media_pool_folders",
                description=f"{_DESTRUCTIVE}Delete media pool folders and all clips they contain. Requires confirm=true.",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of folder paths to delete",
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. Permanently deletes folders and all contained clips.",  # noqa: E501
                        },
                    },
                    "required": ["folder_paths", "confirm"],
                },
            ),
            types.Tool(
                name="move_clips_to_folder",
                description=(
                    f"{_DESTRUCTIVE}Move clips to a different media pool folder. "
                    "Re-list clips after this call — clip_id references remain valid but folder context changes. "  # noqa: E501
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to move",
                        },
                        "target_folder_path": {
                            "type": "string",
                            "description": "Destination folder path",
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_ids", "target_folder_path", "confirm"],
                },
            ),
            types.Tool(
                name="move_folders",
                description="Move media pool folders to a different parent folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Folder paths to move",
                        },
                        "target_folder_path": {
                            "type": "string",
                            "description": "Destination parent folder path",
                        },
                    },
                    "required": ["folder_paths", "target_folder_path"],
                },
            ),
            # ----------------------------------------------------------------
            # Clip operations
            # ----------------------------------------------------------------
            types.Tool(
                name="delete_media_pool_clips",
                description=f"{_DESTRUCTIVE}Permanently delete clips from the media pool. Requires confirm=true.",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to delete",
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. Deletion is permanent.",
                        },
                    },
                    "required": ["clip_ids", "confirm"],
                },
            ),
            types.Tool(
                name="append_clips_to_timeline",
                description="Append media pool clips to the current timeline",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to append",
                        },
                    },
                    "required": ["clip_ids"],
                },
            ),
            types.Tool(
                name="create_timeline_from_clips",
                description="Create a new timeline from a list of media pool clips. Timeline is placed in the current media pool folder (use set_current_media_pool_folder to control placement).",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "New timeline name"},
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to include",
                        },
                    },
                    "required": ["name", "clip_ids"],
                },
            ),
            types.Tool(
                name="import_timeline_from_file",
                description="Import a timeline from an EDL, AAF, XML, FCPXML, DRT, ADL, or OTIO file",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Source file path",
                        },
                        "import_options": {
                            "type": "object",
                            "description": "Import options dict (see DaVinci scripting docs)",  # noqa: E501
                        },
                    },
                    "required": ["file_path", "import_options"],
                },
            ),
            types.Tool(
                name="export_clip_metadata",
                description="Export clip metadata to a CSV file. Pass empty clip_ids list to export all clips.",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_name": {
                            "type": "string",
                            "description": "Destination CSV file path",
                        },
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to export; empty list exports all",  # noqa: E501
                        },
                    },
                    "required": ["file_name", "clip_ids"],
                },
            ),
            types.Tool(
                name="relink_clips",
                description="Relink offline clips to a new media folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to relink",
                        },
                        "folder_path": {
                            "type": "string",
                            "description": "Filesystem path to search for replacement media",  # noqa: E501
                        },
                    },
                    "required": ["clip_ids", "folder_path"],
                },
            ),
            types.Tool(
                name="unlink_clips",
                description=f"{_DESTRUCTIVE}Unlink clips from their source media files. Requires confirm=true.",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to unlink",
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_ids", "confirm"],
                },
            ),
            types.Tool(
                name="auto_sync_audio",
                description="Auto-sync audio clips to video clips by waveform or timecode",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UUIDs of clips to sync",
                        },
                        "audio_sync_settings": {
                            "type": "object",
                            "description": (
                                '{"syncMode": "AUDIO_SYNC_WAVEFORM"|"AUDIO_SYNC_TIMECODE", ...}'  # noqa: E501
                            ),
                        },
                    },
                    "required": ["clip_ids", "audio_sync_settings"],
                },
            ),
            types.Tool(
                name="import_folder_from_file",
                description="Import a folder from a .drb bin file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Source .drb file path",
                        },
                        "source_clips_path": {
                            "type": "string",
                            "description": "Root folder path for clip relinking",
                        },
                    },
                    "required": ["file_path", "source_clips_path"],
                },
            ),
            # ----------------------------------------------------------------
            # Mattes
            # ----------------------------------------------------------------
            types.Tool(
                name="get_clip_matte_list",
                description="Get the list of matte file paths attached to a clip",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="add_clip_mattes",
                description=(
                    f"{_DESTRUCTIVE}Add matte files to a clip. "
                    "Modifies the clip's matte list permanently. Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "file_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Matte file paths to add",
                        },
                        "stereo_eye": {
                            "type": "string",
                            "description": "Stereo eye: 'left' or 'right'",
                            "enum": ["left", "right"],
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "file_paths", "stereo_eye", "confirm"],
                },
            ),
            types.Tool(
                name="delete_clip_mattes",
                description=f"{_DESTRUCTIVE}Remove matte files from a clip. Requires confirm=true.",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "file_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Matte file paths to remove",
                        },
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "file_paths", "confirm"],
                },
            ),
            types.Tool(
                name="add_timeline_mattes",
                description="Add timeline matte files to the media pool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Timeline matte file paths to add",
                        },
                    },
                    "required": ["file_paths"],
                },
            ),
            # ----------------------------------------------------------------
            # Stereo
            # ----------------------------------------------------------------
            types.Tool(
                name="create_stereo_clip",
                description="Create a stereo clip from two existing clips (DaVinci Resolve Studio only)",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "left_clip_id": {
                            "type": "string",
                            "description": "UUID of the left-eye clip",
                        },
                        "right_clip_id": {
                            "type": "string",
                            "description": "UUID of the right-eye clip",
                        },
                    },
                    "required": ["left_clip_id", "right_clip_id"],
                },
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        # --- original migrated tools ---
        if tool_name == "list_media_clips":
            return client.list_media_clips()
        elif tool_name == "import_media":
            fp = arguments.get("file_path", "")
            result = client.import_media(fp)
            return f"Imported '{fp}'" if result else f"Failed to import '{fp}'"

        # --- folder inspection ---
        elif tool_name == "get_media_pool_root_folder":
            return client.get_media_pool_root_folder()
        elif tool_name == "get_current_media_pool_folder":
            return client.get_current_media_pool_folder()
        elif tool_name == "set_current_media_pool_folder":
            fp = arguments.get("folder_path", "")
            result = client.set_current_media_pool_folder(fp)
            return f"Current folder set to '{fp}'" if result else "Failed"
        elif tool_name == "get_folder_clips":
            return client.get_folder_clips(arguments.get("folder_path", ""))
        elif tool_name == "get_folder_subfolders":
            return client.get_folder_subfolders(arguments.get("folder_path", ""))
        elif tool_name == "get_selected_pool_clips":
            return client.get_selected_pool_clips()
        elif tool_name == "set_selected_pool_clip":
            result = client.set_selected_pool_clip(arguments.get("clip_id", ""))
            return "Clip selected" if result else "Selection failed"
        elif tool_name == "refresh_media_pool_folders":
            result = client.refresh_media_pool_folders()
            return "Folders refreshed" if result else "Refresh failed"

        # --- folder management ---
        elif tool_name == "create_media_pool_folder":
            fp = arguments.get("folder_path", "")
            name = arguments.get("name", "")
            result = client.create_media_pool_folder(fp, name)
            return f"Created folder '{name}' in '{fp}'" if result else "Failed"
        elif tool_name == "delete_media_pool_folders":
            fps = arguments.get("folder_paths", [])
            if err := _confirm_gate(
                arguments,
                f"Permanently deletes folders {fps} and all clips they contain.",
            ):
                return err
            result = client.delete_media_pool_folders(fps)
            return f"Deleted {len(fps)} folder(s)" if result else "Delete failed"
        elif tool_name == "move_clips_to_folder":
            clip_ids = arguments.get("clip_ids", [])
            target = arguments.get("target_folder_path", "")
            if err := _confirm_gate(
                arguments, f"Moves {len(clip_ids)} clip(s) to '{target}'."
            ):
                return err
            result = client.move_clips_to_folder(clip_ids, target)
            return (
                f"Moved {len(clip_ids)} clip(s) to '{target}'"
                if result
                else "Move failed"
            )
        elif tool_name == "move_folders":
            fps = arguments.get("folder_paths", [])
            target = arguments.get("target_folder_path", "")
            result = client.move_folders(fps, target)
            return (
                f"Moved {len(fps)} folder(s) to '{target}'" if result else "Move failed"
            )

        # --- clip operations ---
        elif tool_name == "delete_media_pool_clips":
            clip_ids = arguments.get("clip_ids", [])
            if err := _confirm_gate(
                arguments,
                f"Permanently deletes {len(clip_ids)} clip(s) from the media pool.",
            ):
                return err
            result = client.delete_media_pool_clips(clip_ids)
            return f"Deleted {len(clip_ids)} clip(s)" if result else "Delete failed"
        elif tool_name == "append_clips_to_timeline":
            clip_ids = arguments.get("clip_ids", [])
            result = client.append_clips_to_timeline(clip_ids)
            return (
                f"Appended {len(clip_ids)} clip(s) to timeline"
                if result
                else "Append failed"
            )
        elif tool_name == "create_timeline_from_clips":
            name = arguments.get("name", "")
            clip_ids = arguments.get("clip_ids", [])
            result = client.create_timeline_from_clips(name, clip_ids)
            return (
                f"Created timeline '{name}'" if result else "Timeline creation failed"
            )
        elif tool_name == "import_timeline_from_file":
            fp = arguments.get("file_path", "")
            opts = arguments.get("import_options", {})
            result = client.import_timeline_from_file(fp, opts)
            return f"Imported timeline from '{fp}'" if result else "Import failed"
        elif tool_name == "export_clip_metadata":
            fn = arguments.get("file_name", "")
            clip_ids = arguments.get("clip_ids", [])
            result = client.export_clip_metadata(fn, clip_ids)
            return f"Exported metadata to '{fn}'" if result else "Export failed"
        elif tool_name == "relink_clips":
            clip_ids = arguments.get("clip_ids", [])
            fp = arguments.get("folder_path", "")
            result = client.relink_clips(clip_ids, fp)
            return f"Relinked {len(clip_ids)} clip(s)" if result else "Relink failed"
        elif tool_name == "unlink_clips":
            clip_ids = arguments.get("clip_ids", [])
            if err := _confirm_gate(
                arguments, f"Unlinks {len(clip_ids)} clip(s) from their source media."
            ):
                return err
            result = client.unlink_clips(clip_ids)
            return f"Unlinked {len(clip_ids)} clip(s)" if result else "Unlink failed"
        elif tool_name == "auto_sync_audio":
            clip_ids = arguments.get("clip_ids", [])
            settings = arguments.get("audio_sync_settings", {})
            result = client.auto_sync_audio(clip_ids, settings)
            return (
                f"Audio sync completed for {len(clip_ids)} clip(s)"
                if result
                else "Sync failed"
            )
        elif tool_name == "import_folder_from_file":
            fp = arguments.get("file_path", "")
            scp = arguments.get("source_clips_path", "")
            result = client.import_folder_from_file(fp, scp)
            return f"Imported folder from '{fp}'" if result else "Import failed"

        # --- mattes ---
        elif tool_name == "get_clip_matte_list":
            return client.get_clip_matte_list(arguments.get("clip_id", ""))
        elif tool_name == "add_clip_mattes":
            clip_id = arguments.get("clip_id", "")
            if err := _confirm_gate(arguments, f"Adds mattes to clip '{clip_id}'."):
                return err
            result = client.add_clip_mattes(
                clip_id,
                arguments.get("file_paths", []),
                arguments.get("stereo_eye", "left"),
            )
            return "Mattes added" if result else "Failed to add mattes"
        elif tool_name == "delete_clip_mattes":
            clip_id = arguments.get("clip_id", "")
            fps = arguments.get("file_paths", [])
            if err := _confirm_gate(
                arguments, f"Removes {len(fps)} matte(s) from clip '{clip_id}'."
            ):
                return err
            result = client.delete_clip_mattes(clip_id, fps)
            return "Mattes removed" if result else "Failed to remove mattes"
        elif tool_name == "add_timeline_mattes":
            fps = arguments.get("file_paths", [])
            result = client.add_timeline_mattes(fps)
            return f"Added {len(fps)} timeline matte(s)" if result else "Failed"

        # --- stereo ---
        elif tool_name == "create_stereo_clip":
            result = client.create_stereo_clip(
                arguments.get("left_clip_id", ""),
                arguments.get("right_clip_id", ""),
            )
            return "Stereo clip created" if result else "Stereo clip creation failed"

        return f"Unknown tool in media_pool domain: {tool_name}"
