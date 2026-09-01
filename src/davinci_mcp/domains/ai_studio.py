# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 8: AI & Studio Features tools.

All tools require DaVinci Resolve Studio. Several require additional
Extras downloads (transcription, audio classification, IntelliSearch, Slate ID).
"""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "
_STUDIO = "Requires DaVinci Resolve Studio. "
_EXTRAS = "Requires Studio + Extras download. "

_ITEM_REF = {
    "timeline_name": {"type": "string", "description": "Timeline name"},
    "item_ref": {
        "type": "object",
        "description": "Item: {track_type, track_index, item_index}",
        "properties": {
            "track_type": {"type": "string"},
            "track_index": {"type": "integer"},
            "item_index": {"type": "integer"},
        },
        "required": ["track_type", "track_index", "item_index"],
    },
}


def _confirm_gate(arguments: dict[str, Any], description: str) -> str | None:
    if not arguments.get("confirm", False):
        return f"{_DESTRUCTIVE}{description} Set confirm=true to proceed."
    return None


class AIStudioDomain:
    name = "ai_studio"
    description = (
        "AI and Studio-only features: magic masks, stabilization, smart reframe, "
        "subtitles from audio, scene cut detection, clip/folder transcription, "
        "audio classification, IntelliSearch/Slate analysis, motion blur removal, "
        "voice isolation, speech generation, and IntelliSearch reset"
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        return [
            # ----------------------------------------------------------------
            # Timeline item AI tools
            # ----------------------------------------------------------------
            types.Tool(
                name="create_magic_mask",
                description=f"{_STUDIO}Create a magic mask on a timeline item. mode: F/B/BI.",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        **_ITEM_REF,
                        "mode": {
                            "type": "string",
                            "description": "F=foreground, B=background, BI=both",
                        },
                    },
                    "required": ["timeline_name", "item_ref", "mode"],
                },
            ),
            types.Tool(
                name="regenerate_magic_mask",
                description=f"{_STUDIO}Regenerate the magic mask on a timeline item.",
                input_schema={
                    "type": "object",
                    "properties": _ITEM_REF,
                    "required": ["timeline_name", "item_ref"],
                },
            ),
            types.Tool(
                name="stabilize_clip",
                description=f"{_STUDIO}Stabilize a timeline item.",
                input_schema={
                    "type": "object",
                    "properties": _ITEM_REF,
                    "required": ["timeline_name", "item_ref"],
                },
            ),
            types.Tool(
                name="smart_reframe_clip",
                description=f"{_STUDIO}Apply Smart Reframe to a timeline item.",
                input_schema={
                    "type": "object",
                    "properties": _ITEM_REF,
                    "required": ["timeline_name", "item_ref"],
                },
            ),
            # ----------------------------------------------------------------
            # Timeline AI tools
            # ----------------------------------------------------------------
            types.Tool(
                name="create_subtitles_from_audio",
                description=(
                    f"{_STUDIO}Generate subtitles from audio for a timeline. "
                    "settings keys: presetName, audioTrackRange, exportHearingImpaired, "  # noqa: E501
                    "maxLines, maxCharsPerLine, autoClipBoundaries, targetLanguage."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "timeline_name": {
                            "type": "string",
                            "description": "Timeline name",
                        },
                        "settings": {
                            "type": "object",
                            "description": "AutoCaption settings dict",
                        },
                    },
                    "required": ["timeline_name", "settings"],
                },
            ),
            types.Tool(
                name="detect_scene_cuts",
                description=f"{_STUDIO}Detect scene cuts in a timeline.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "timeline_name": {
                            "type": "string",
                            "description": "Timeline name",
                        },
                    },
                    "required": ["timeline_name"],
                },
            ),
            # ----------------------------------------------------------------
            # Clip transcription / audio classification
            # ----------------------------------------------------------------
            types.Tool(
                name="transcribe_clip_audio",
                description=f"{_EXTRAS}Transcribe audio for a media pool clip.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "use_speaker_detection": {
                            "type": "boolean",
                            "description": "Enable speaker detection",
                        },
                    },
                    "required": ["clip_id", "use_speaker_detection"],
                },
            ),
            types.Tool(
                name="clear_transcription",
                description=(
                    f"{_DESTRUCTIVE}{_STUDIO}Clear the transcription for a clip. "
                    "Requires confirm=true."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "confirm"],
                },
            ),
            types.Tool(
                name="classify_clip_audio",
                description=f"{_EXTRAS}Classify audio content for a media pool clip.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                    },
                    "required": ["clip_id"],
                },
            ),
            types.Tool(
                name="clear_audio_classification",
                description=(
                    f"{_DESTRUCTIVE}{_STUDIO}Clear audio classification for a clip. "
                    "Requires confirm=true."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["clip_id", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Folder AI tools
            # ----------------------------------------------------------------
            types.Tool(
                name="transcribe_folder_audio",
                description=f"{_EXTRAS}Transcribe audio for all clips in a media pool folder.",  # noqa: E501
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path"},
                        "use_speaker_detection": {
                            "type": "boolean",
                            "description": "Enable speaker detection",
                        },
                    },
                    "required": ["folder_path", "use_speaker_detection"],
                },
            ),
            types.Tool(
                name="analyze_for_intellisearch",
                description=(
                    f"{_EXTRAS}Analyze clips in a folder for IntelliSearch. "
                    "Requires AI Extras download."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path"},
                        "identify_faces": {
                            "type": "boolean",
                            "description": "Enable face identification",
                        },
                        "is_better_mode": {
                            "type": "boolean",
                            "description": "Use higher-quality analysis mode",
                        },
                    },
                    "required": ["folder_path", "identify_faces", "is_better_mode"],
                },
            ),
            types.Tool(
                name="analyze_for_slate",
                description=(
                    f"{_EXTRAS}Analyze clips in a folder for Slate ID. "
                    "Requires AI Slate ID Extras download."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path"},
                        "marker_color": {
                            "type": "string",
                            "description": "Marker color for identified slates",
                        },
                    },
                    "required": ["folder_path", "marker_color"],
                },
            ),
            # ----------------------------------------------------------------
            # Remove motion blur
            # ----------------------------------------------------------------
            types.Tool(
                name="remove_motion_blur",
                description=(
                    f"{_STUDIO}Remove motion blur from a clip. "
                    "Returns new MediaPoolItem info."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "clip_id": {"type": "string", "description": "Clip UUID"},
                        "deblur_options": {
                            "type": "object",
                            "description": "Deblur option dict",
                        },
                    },
                    "required": ["clip_id", "deblur_options"],
                },
            ),
            # ----------------------------------------------------------------
            # Voice isolation
            # ----------------------------------------------------------------
            types.Tool(
                name="set_voice_isolation",
                description=(
                    f"{_STUDIO}Set voice isolation state for an audio track. "
                    "state keys: VoiceIsolationState, amount (0-100)."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "timeline_name": {
                            "type": "string",
                            "description": "Timeline name",
                        },
                        "track_index": {
                            "type": "integer",
                            "description": "Audio track index (1-based)",
                        },
                        "state": {
                            "type": "object",
                            "description": "VoiceIsolationState dict",
                        },
                    },
                    "required": ["timeline_name", "track_index", "state"],
                },
            ),
            types.Tool(
                name="set_item_voice_isolation",
                description=(
                    f"{_STUDIO}Set voice isolation state for a timeline item. "
                    "state keys: VoiceIsolationState, amount (0-100)."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        **_ITEM_REF,
                        "state": {
                            "type": "object",
                            "description": "VoiceIsolationState dict",
                        },
                    },
                    "required": ["timeline_name", "item_ref", "state"],
                },
            ),
            # ----------------------------------------------------------------
            # Generate speech
            # ----------------------------------------------------------------
            types.Tool(
                name="generate_speech",
                description=(
                    f"{_EXTRAS}Generate speech and add it to the timeline. "
                    "settings keys: text, voiceType, language, pitch, speed, etc. "
                    "Requires AI Speech Generator Extras."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "settings": {
                            "type": "object",
                            "description": "Speech generation settings",
                        },
                        "timecode": {
                            "type": "string",
                            "description": "Insertion timecode (HH:MM:SS:FF)",
                        },
                    },
                    "required": ["settings", "timecode"],
                },
            ),
            # ----------------------------------------------------------------
            # Reset IntelliSearch
            # ----------------------------------------------------------------
            types.Tool(
                name="reset_intellisearch",
                description=(
                    f"{_DESTRUCTIVE}{_STUDIO}Reset IntelliSearch analysis for the current "  # noqa: E501
                    "project. Requires confirm=true."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "confirm": {"type": "boolean", "description": "Must be true."},
                    },
                    "required": ["confirm"],
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
        item_ref = arguments.get("item_ref", {})

        # --- timeline item AI tools ---
        if tool_name == "create_magic_mask":
            result = client.create_magic_mask(tl, item_ref, arguments.get("mode", "F"))
            return "Magic mask created" if result else "Failed to create magic mask"
        elif tool_name == "regenerate_magic_mask":
            result = client.regenerate_magic_mask(tl, item_ref)
            return "Magic mask regenerated" if result else "Failed"
        elif tool_name == "stabilize_clip":
            result = client.stabilize_clip(tl, item_ref)
            return "Clip stabilized" if result else "Failed to stabilize"
        elif tool_name == "smart_reframe_clip":
            result = client.smart_reframe_clip(tl, item_ref)
            return "Smart Reframe applied" if result else "Failed"

        # --- timeline AI tools ---
        elif tool_name == "create_subtitles_from_audio":
            result = client.create_subtitles_from_audio(
                tl, arguments.get("settings", {})
            )  # noqa: E501
            return (
                "Subtitles created"
                if result
                else (
                    "Failed to create subtitles. Requires DaVinci Resolve Studio with "
                    "AI Speech Recognition installed "
                    "(Help → Download DaVinci Resolve AI Models)."
                )
            )
        elif tool_name == "detect_scene_cuts":
            return client.detect_scene_cuts(tl)

        # --- clip transcription / audio classification ---
        elif tool_name == "transcribe_clip_audio":
            clip_id = arguments.get("clip_id", "")
            result = client.transcribe_clip_audio(
                clip_id, bool(arguments.get("use_speaker_detection", False))
            )
            return (
                "Transcription started" if result else "Failed to start transcription"
            )  # noqa: E501
        elif tool_name == "clear_transcription":
            clip_id = arguments.get("clip_id", "")
            if err := _confirm_gate(
                arguments, f"Clears transcription data for clip '{clip_id}'."
            ):
                return err
            result = client.clear_transcription(clip_id)
            return "Transcription cleared" if result else "Failed"
        elif tool_name == "classify_clip_audio":
            result = client.classify_clip_audio(arguments.get("clip_id", ""))
            return "Audio classification started" if result else "Failed"
        elif tool_name == "clear_audio_classification":
            clip_id = arguments.get("clip_id", "")
            if err := _confirm_gate(
                arguments, f"Clears audio classification for clip '{clip_id}'."
            ):
                return err
            result = client.clear_audio_classification(clip_id)
            return "Audio classification cleared" if result else "Failed"

        # --- folder AI tools ---
        elif tool_name == "transcribe_folder_audio":
            result = client.transcribe_folder_audio(
                arguments.get("folder_path", ""),
                bool(arguments.get("use_speaker_detection", False)),
            )
            return "Folder transcription started" if result else "Failed"
        elif tool_name == "analyze_for_intellisearch":
            result = client.analyze_for_intellisearch(
                arguments.get("folder_path", ""),
                bool(arguments.get("identify_faces", False)),
                bool(arguments.get("is_better_mode", False)),
            )
            return "IntelliSearch analysis started" if result else "Failed"
        elif tool_name == "analyze_for_slate":
            result = client.analyze_for_slate(
                arguments.get("folder_path", ""),
                arguments.get("marker_color", "Blue"),
            )
            return "Slate analysis started" if result else "Failed"

        # --- remove motion blur ---
        elif tool_name == "remove_motion_blur":
            return client.remove_motion_blur(
                arguments.get("clip_id", ""),
                arguments.get("deblur_options", {}),
            )

        # --- voice isolation ---
        elif tool_name == "set_voice_isolation":
            result = client.set_voice_isolation(
                tl,
                int(arguments.get("track_index", 1)),
                arguments.get("state", {}),
            )
            return "Voice isolation set" if result else "Failed"
        elif tool_name == "set_item_voice_isolation":
            result = client.set_item_voice_isolation(
                tl, item_ref, arguments.get("state", {})
            )  # noqa: E501
            return "Voice isolation set" if result else "Failed"

        # --- generate speech ---
        elif tool_name == "generate_speech":
            result = client.generate_speech(
                arguments.get("settings", {}),
                arguments.get("timecode", ""),
            )
            return "Speech generated" if result else "Failed"

        # --- reset intellisearch ---
        elif tool_name == "reset_intellisearch":
            if err := _confirm_gate(
                arguments, "Resets IntelliSearch analysis for the current project."
            ):
                return err
            result = client.reset_intellisearch()
            return "IntelliSearch reset" if result else "Failed"

        return f"Unknown tool in ai_studio domain: {tool_name}"
