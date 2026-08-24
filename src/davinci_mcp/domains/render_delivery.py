# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 7: Render & Delivery tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


class RenderDeliveryDomain:
    name = "render_delivery"
    description = (
        "Render format/codec/resolution queries, render settings, preset management, "
        "render job lifecycle, project settings, and burn-in presets"  # noqa: E501
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        return [
            # ----------------------------------------------------------------
            # Format / codec / resolution queries
            # ----------------------------------------------------------------
            types.Tool(
                name="get_render_formats",
                description="Get available render formats as {format: file_extension}",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_render_codecs",
                description="Get codecs for a render format as {description: codec}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "render_format": {"type": "string", "description": "Format"},
                    },
                    "required": ["render_format"],
                },
            ),
            types.Tool(
                name="get_render_resolutions",
                description="Get available resolutions for a format and codec",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "render_format": {"type": "string", "description": "Format"},
                        "codec": {"type": "string", "description": "Codec name"},
                    },
                    "required": ["render_format", "codec"],
                },
            ),
            types.Tool(
                name="get_current_render_format",
                description="Get the currently selected render format and codec",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="set_render_format_and_codec",
                description="Set the current render format and codec",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "render_format": {"type": "string", "description": "Format"},
                        "codec": {"type": "string", "description": "Codec name"},
                    },
                    "required": ["render_format", "codec"],
                },
            ),
            types.Tool(
                name="get_render_mode",
                description="Get render mode (0=individual clips, 1=single clip)",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="set_render_mode",
                description="Set render mode (0=individual clips, 1=single clip)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "render_mode": {
                            "type": "integer",
                            "description": "0=individual clips, 1=single clip",
                        },
                    },
                    "required": ["render_mode"],
                },
            ),
            # ----------------------------------------------------------------
            # Render settings
            # ----------------------------------------------------------------
            types.Tool(
                name="set_render_settings",
                description=(
                    "Apply render settings dict. Common keys: SelectAllFrames, MarkIn, "
                    "MarkOut, TargetDir, CustomName, ExportVideo, ExportAudio, "
                    "FormatWidth, FormatHeight, FrameRate, VideoQuality, AudioCodec, "
                    "AudioBitDepth, AudioSampleRate, ExportAlpha, BurnInPreset."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "settings": {
                            "type": "object",
                            "description": "Dict of render setting key/value pairs",
                        },
                    },
                    "required": ["settings"],
                },
            ),
            # ----------------------------------------------------------------
            # Render presets
            # ----------------------------------------------------------------
            types.Tool(
                name="get_render_preset_list",
                description="Get the list of available render preset names",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="load_render_preset",
                description="Load a render preset by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name"},
                    },
                    "required": ["preset_name"],
                },
            ),
            types.Tool(
                name="save_render_preset",
                description="Save current render settings as a new named preset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "New name"},
                    },
                    "required": ["preset_name"],
                },
            ),
            types.Tool(
                name="delete_render_preset",
                description=(
                    f"{_DESTRUCTIVE}Permanently delete a render preset. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["preset_name", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Quick export
            # ----------------------------------------------------------------
            types.Tool(
                name="get_quick_export_presets",
                description="Get available Quick Export preset names",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="render_with_quick_export",
                description=(
                    "Render via a Quick Export preset (supports direct upload to "
                    "YouTube/Vimeo/etc.). params keys vary by preset."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name"},
                        "params": {
                            "type": "object",
                            "description": "Preset-specific parameters (may be empty)",
                        },
                    },
                    "required": ["preset_name", "params"],
                },
            ),
            # ----------------------------------------------------------------
            # Render job management
            # ----------------------------------------------------------------
            types.Tool(
                name="add_render_job",
                description=(
                    "Add the current timeline/settings as a render job. "
                    "Returns the job ID."
                ),
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="delete_render_job",
                description=(
                    f"{_DESTRUCTIVE}Delete a render job by ID. Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "Job ID to delete"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["job_id", "confirm"],
                },
            ),
            types.Tool(
                name="delete_all_render_jobs",
                description=(
                    f"{_DESTRUCTIVE}Delete all render jobs. Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["confirm"],
                },
            ),
            types.Tool(
                name="get_render_job_list",
                description="Get the list of all render jobs and their settings",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_render_job_status",
                description="Get the status and completion percentage of a render job",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "Job ID to query"},
                    },
                    "required": ["job_id"],
                },
            ),
            types.Tool(
                name="start_rendering",
                description=(
                    "Start rendering one or more jobs. Pass [] for job_ids to render all."  # noqa: E501
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Job IDs to render, or [] for all",
                        },
                        "interactive": {
                            "type": "boolean",
                            "description": "Show Resolve render dialog",
                        },
                    },
                    "required": ["job_ids", "interactive"],
                },
            ),
            types.Tool(
                name="stop_rendering",
                description="Stop the current render operation",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="is_rendering_in_progress",
                description="Check whether a render is currently in progress",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            # ----------------------------------------------------------------
            # Project settings
            # ----------------------------------------------------------------
            types.Tool(
                name="get_project_setting",
                description=(
                    "Get a project setting. Pass empty string to get all settings. "
                    "Common keys: timelineFrameRate, timelineResolutionWidth, "
                    "timelineResolutionHeight, colorScienceMode, videoMonitorFormat."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "setting_name": {
                            "type": "string",
                            "description": "Setting key, or empty string for all",
                        },
                    },
                    "required": ["setting_name"],
                },
            ),
            types.Tool(
                name="set_project_setting",
                description="Set a project setting value",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "setting_name": {"type": "string", "description": "Key"},
                        "setting_value": {"type": "string", "description": "New value"},
                    },
                    "required": ["setting_name", "setting_value"],
                },
            ),
            # ----------------------------------------------------------------
            # Burn-in presets
            # ----------------------------------------------------------------
            types.Tool(
                name="get_burn_in_preset_list",
                description="Get the list of available burn-in preset names",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="load_project_burn_in_preset",
                description="Load a burn-in preset for the current project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name"},
                    },
                    "required": ["preset_name"],
                },
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        # --- format / codec queries ---
        if tool_name == "get_render_formats":
            return client.get_render_formats()
        elif tool_name == "get_render_codecs":
            return client.get_render_codecs(arguments.get("render_format", ""))
        elif tool_name == "get_render_resolutions":
            return client.get_render_resolutions(
                arguments.get("render_format", ""),
                arguments.get("codec", ""),
            )
        elif tool_name == "get_current_render_format":
            return client.get_current_render_format()
        elif tool_name == "set_render_format_and_codec":
            result = client.set_render_format_and_codec(
                arguments.get("render_format", ""),
                arguments.get("codec", ""),
            )
            return "Render format and codec set" if result else "Failed to set"
        elif tool_name == "get_render_mode":
            return client.get_render_mode()
        elif tool_name == "set_render_mode":
            result = client.set_render_mode(int(arguments.get("render_mode", 0)))
            return "Render mode set" if result else "Failed to set render mode"

        # --- render settings ---
        elif tool_name == "set_render_settings":
            result = client.set_render_settings(arguments.get("settings", {}))
            return "Render settings applied" if result else "Failed to apply settings"

        # --- render presets ---
        elif tool_name == "get_render_preset_list":
            return client.get_render_preset_list()
        elif tool_name == "load_render_preset":
            preset_name = arguments.get("preset_name", "")
            result = client.load_render_preset(preset_name)
            return f"Loaded preset '{preset_name}'" if result else "Failed to load"
        elif tool_name == "save_render_preset":
            preset_name = arguments.get("preset_name", "")
            result = client.save_render_preset(preset_name)
            return f"Saved preset '{preset_name}'" if result else "Failed to save"
        elif tool_name == "delete_render_preset":
            preset_name = arguments.get("preset_name", "")
            if err := _confirm_gate(
                arguments, f"Permanently deletes render preset '{preset_name}'."
            ):
                return err
            result = client.delete_render_preset(preset_name)
            return f"Deleted preset '{preset_name}'" if result else "Delete failed"

        # --- quick export ---
        elif tool_name == "get_quick_export_presets":
            return client.get_quick_export_presets()
        elif tool_name == "render_with_quick_export":
            preset_name = arguments.get("preset_name", "")
            params = arguments.get("params", {})
            result = client.render_with_quick_export(preset_name, params)
            return f"Quick export with '{preset_name}'" if result else "Export failed"

        # --- render job management ---
        elif tool_name == "add_render_job":
            job_id = client.add_render_job()
            return f"Render job added: {job_id}" if job_id else "Failed to add job"
        elif tool_name == "delete_render_job":
            job_id = arguments.get("job_id", "")
            if err := _confirm_gate(
                arguments, f"Permanently deletes render job '{job_id}'."
            ):
                return err
            result = client.delete_render_job(job_id)
            return f"Deleted render job '{job_id}'" if result else "Delete failed"
        elif tool_name == "delete_all_render_jobs":
            if err := _confirm_gate(
                arguments, "Permanently deletes all render jobs in the queue."
            ):
                return err
            result = client.delete_all_render_jobs()
            return "All render jobs deleted" if result else "Delete failed"
        elif tool_name == "get_render_job_list":
            return client.get_render_job_list()
        elif tool_name == "get_render_job_status":
            return client.get_render_job_status(arguments.get("job_id", ""))
        elif tool_name == "start_rendering":
            job_ids = arguments.get("job_ids", [])
            interactive = bool(arguments.get("interactive", False))
            result = client.start_rendering(job_ids, interactive)
            return "Rendering started" if result else "Failed to start rendering"
        elif tool_name == "stop_rendering":
            client.stop_rendering()
            return "Rendering stopped"
        elif tool_name == "is_rendering_in_progress":
            return client.is_rendering_in_progress()

        # --- project settings ---
        elif tool_name == "get_project_setting":
            return client.get_project_setting(arguments.get("setting_name", ""))
        elif tool_name == "set_project_setting":
            result = client.set_project_setting(
                arguments.get("setting_name", ""),
                arguments.get("setting_value", ""),
            )
            return "Project setting updated" if result else "Failed to update"

        # --- burn-in ---
        elif tool_name == "get_burn_in_preset_list":
            return client.get_burn_in_preset_list()
        elif tool_name == "load_project_burn_in_preset":
            preset_name = arguments.get("preset_name", "")
            result = client.load_project_burn_in_preset(preset_name)
            return f"Loaded burn-in preset '{preset_name}'" if result else "Failed"

        return f"Unknown tool in render_delivery domain: {tool_name}"
