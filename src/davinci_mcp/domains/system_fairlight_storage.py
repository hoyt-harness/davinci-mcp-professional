# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 9: System, Fairlight & Storage tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


class SystemFairlightStorageDomain:
    name = "system_fairlight_storage"
    description = (
        "UI layout presets, Fairlight audio presets, keyframe mode, "
        "Fairlight audio insertion, media storage browsing, and background tasks"
    )

    def get_tools(self) -> list[types.Tool]:
        return [
            # ----------------------------------------------------------------
            # Layout presets
            # ----------------------------------------------------------------
            types.Tool(
                name="get_layout_presets",
                description="Get the list of available UI layout preset names",
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="load_layout_preset",
                description="Load a UI layout preset by name",
                input_schema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name"},
                    },
                    "required": ["preset_name"],
                },
            ),
            types.Tool(
                name="save_layout_preset",
                description="Save the current UI layout as a named preset",
                input_schema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name"},
                    },
                    "required": ["preset_name"],
                },
            ),
            types.Tool(
                name="delete_layout_preset",
                description=(
                    f"{_DESTRUCTIVE}Delete a layout preset. Requires confirm=true."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["preset_name", "confirm"],
                },
            ),
            types.Tool(
                name="export_layout_preset",
                description="Export a layout preset to a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name"},
                        "file_path": {"type": "string", "description": "Destination"},
                    },
                    "required": ["preset_name", "file_path"],
                },
            ),
            types.Tool(
                name="import_layout_preset",
                description="Import a layout preset from a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Source file"},
                        "preset_name": {"type": "string", "description": "Name to use"},
                    },
                    "required": ["file_path", "preset_name"],
                },
            ),
            # ----------------------------------------------------------------
            # Fairlight presets
            # ----------------------------------------------------------------
            types.Tool(
                name="get_fairlight_presets",
                description="Get the list of available Fairlight audio preset names",
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="apply_fairlight_preset",
                description="Apply a Fairlight preset to the current timeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name"},
                    },
                    "required": ["preset_name"],
                },
            ),
            # ----------------------------------------------------------------
            # Keyframe mode
            # ----------------------------------------------------------------
            types.Tool(
                name="get_keyframe_mode",
                description="Get the current keyframe mode (0=all, 1=color, 2=sizing)",
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="set_keyframe_mode",
                description="Set keyframe mode (0=all, 1=color, 2=sizing)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "keyframe_mode": {
                            "type": "integer",
                            "description": "0=all, 1=color, 2=sizing",
                        },
                    },
                    "required": ["keyframe_mode"],
                },
            ),
            # ----------------------------------------------------------------
            # Fairlight audio insertion
            # ----------------------------------------------------------------
            types.Tool(
                name="insert_audio_at_playhead",
                description=(
                    "Insert audio from a file at the current playhead position "
                    "on the Fairlight page. Requires the Fairlight page to be active."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "media_path": {"type": "string", "description": "Audio path"},
                        "start_offset": {
                            "type": "integer",
                            "description": "Start offset in samples",
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in samples",
                        },
                    },
                    "required": ["media_path", "start_offset", "duration"],
                },
            ),
            # ----------------------------------------------------------------
            # Media storage
            # ----------------------------------------------------------------
            types.Tool(
                name="get_mounted_volumes",
                description="Get the list of mounted volumes visible to Resolve",
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_storage_subfolders",
                description="List subfolders in a media storage path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path"},
                    },
                    "required": ["folder_path"],
                },
            ),
            types.Tool(
                name="get_storage_files",
                description="List files in a media storage path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path"},
                    },
                    "required": ["folder_path"],
                },
            ),
            types.Tool(
                name="add_storage_items_to_pool",
                description="Add files or folders from media storage to the media pool",
                input_schema={
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File or folder paths to add",
                        },
                    },
                    "required": ["items"],
                },
            ),
            # ----------------------------------------------------------------
            # Background tasks
            # ----------------------------------------------------------------
            types.Tool(
                name="disable_background_tasks",
                description=(
                    "Disable Resolve background tasks for the current session "
                    "(transcoding, proxy generation, etc.)"
                ),
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        # --- layout presets ---
        if tool_name == "get_layout_presets":
            return client.get_layout_presets()
        elif tool_name == "load_layout_preset":
            preset_name = arguments.get("preset_name", "")
            result = client.load_layout_preset(preset_name)
            return f"Loaded layout '{preset_name}'" if result else "Failed to load"
        elif tool_name == "save_layout_preset":
            preset_name = arguments.get("preset_name", "")
            result = client.save_layout_preset(preset_name)
            return f"Saved layout '{preset_name}'" if result else "Failed to save"
        elif tool_name == "delete_layout_preset":
            preset_name = arguments.get("preset_name", "")
            if err := _confirm_gate(
                arguments, f"Permanently deletes layout preset '{preset_name}'."
            ):
                return err
            result = client.delete_layout_preset(preset_name)
            return f"Deleted layout '{preset_name}'" if result else "Delete failed"
        elif tool_name == "export_layout_preset":
            preset_name = arguments.get("preset_name", "")
            file_path = arguments.get("file_path", "")
            result = client.export_layout_preset(preset_name, file_path)
            return f"Exported layout '{preset_name}'" if result else "Export failed"
        elif tool_name == "import_layout_preset":
            file_path = arguments.get("file_path", "")
            preset_name = arguments.get("preset_name", "")
            result = client.import_layout_preset(file_path, preset_name)
            return f"Imported layout as '{preset_name}'" if result else "Import failed"

        # --- Fairlight presets ---
        elif tool_name == "get_fairlight_presets":
            return client.get_fairlight_presets()
        elif tool_name == "apply_fairlight_preset":
            preset_name = arguments.get("preset_name", "")
            result = client.apply_fairlight_preset(preset_name)
            return f"Applied Fairlight preset '{preset_name}'" if result else "Failed"

        # --- keyframe mode ---
        elif tool_name == "get_keyframe_mode":
            return client.get_keyframe_mode()
        elif tool_name == "set_keyframe_mode":
            result = client.set_keyframe_mode(int(arguments.get("keyframe_mode", 0)))
            return "Keyframe mode set" if result else "Failed to set keyframe mode"

        # --- Fairlight audio insert ---
        elif tool_name == "insert_audio_at_playhead":
            result = client.insert_audio_at_playhead(
                arguments.get("media_path", ""),
                int(arguments.get("start_offset", 0)),
                int(arguments.get("duration", 0)),
            )
            return "Audio inserted" if result else "Failed to insert audio"

        # --- media storage ---
        elif tool_name == "get_mounted_volumes":
            return client.get_mounted_volumes()
        elif tool_name == "get_storage_subfolders":
            return client.get_storage_subfolders(arguments.get("folder_path", ""))
        elif tool_name == "get_storage_files":
            return client.get_storage_files(arguments.get("folder_path", ""))
        elif tool_name == "add_storage_items_to_pool":
            result = client.add_storage_items_to_pool(arguments.get("items", []))
            return "Items added to media pool" if result else "Failed to add items"

        # --- background tasks ---
        elif tool_name == "disable_background_tasks":
            result = client.disable_background_tasks()
            return "Background tasks disabled" if result else "Failed to disable"

        return f"Unknown tool in system_fairlight_storage domain: {tool_name}"
