# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 8: AI & Studio Features.

Written before implementation (Article VIII).
All tools require DaVinci Resolve Studio. Some require additional Extras downloads.
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from davinci_mcp.domains.registry import DOMAIN_REGISTRY
from davinci_mcp.server import DaVinciMCPServer


def _make_mock_client() -> MagicMock:
    client = MagicMock()
    client.is_connected.return_value = True
    return client


@contextmanager
def _mock_request_ctx():
    from mcp.server.lowlevel.server import request_ctx

    mock_session = AsyncMock()
    mock_ctx = MagicMock(session=mock_session)
    token = request_ctx.set(mock_ctx)
    try:
        yield mock_session
    finally:
        request_ctx.reset(token)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_server_with_domain_active(domain_name: str) -> tuple[DaVinciMCPServer, MagicMock]:
    mock_client = _make_mock_client()
    with patch("davinci_mcp.server.DaVinciResolveClient", return_value=mock_client):
        server = DaVinciMCPServer()
    with _mock_request_ctx():
        _run(server._activate_domain(domain_name))
    return server, mock_client


_TL = "Timeline 1"
_REF = {"track_type": "video", "track_index": 1, "item_index": 1}
_CID = "uuid-1234"
_FP = "/Volumes/M/clips"
_DOMAIN = "ai_studio"

_AI_DISPATCH: list[tuple] = [
    # --- timeline item AI tools ---
    ("create_magic_mask",     "create_magic_mask",     {"timeline_name": _TL, "item_ref": _REF, "mode": "F"}, (_TL, _REF, "F")),  # noqa: E501
    ("regenerate_magic_mask", "regenerate_magic_mask", {"timeline_name": _TL, "item_ref": _REF},              (_TL, _REF)),
    ("stabilize_clip",        "stabilize_clip",        {"timeline_name": _TL, "item_ref": _REF},              (_TL, _REF)),
    ("smart_reframe_clip",    "smart_reframe_clip",    {"timeline_name": _TL, "item_ref": _REF},              (_TL, _REF)),
    # --- timeline AI tools ---
    ("create_subtitles_from_audio", "create_subtitles_from_audio", {"timeline_name": _TL, "settings": {}},   (_TL, {})),
    ("detect_scene_cuts",     "detect_scene_cuts",     {"timeline_name": _TL},                                (_TL,)),
    # --- clip transcription ---
    ("transcribe_clip_audio",       "transcribe_clip_audio",       {"clip_id": _CID, "use_speaker_detection": False}, (_CID, False)),  # noqa: E501
    ("clear_transcription",         "clear_transcription",         {"clip_id": _CID, "confirm": True},        (_CID,)),
    ("classify_clip_audio",         "classify_clip_audio",         {"clip_id": _CID},                         (_CID,)),
    ("clear_audio_classification",  "clear_audio_classification",  {"clip_id": _CID, "confirm": True},        (_CID,)),
    # --- folder AI tools ---
    ("transcribe_folder_audio",     "transcribe_folder_audio",     {"folder_path": _FP, "use_speaker_detection": False}, (_FP, False)),  # noqa: E501
    ("analyze_for_intellisearch",   "analyze_for_intellisearch",   {"folder_path": _FP, "identify_faces": True, "is_better_mode": False}, (_FP, True, False)),  # noqa: E501
    ("analyze_for_slate",           "analyze_for_slate",           {"folder_path": _FP, "marker_color": "Blue"}, (_FP, "Blue")),  # noqa: E501
    # --- remove motion blur ---
    ("remove_motion_blur",          "remove_motion_blur",          {"clip_id": _CID, "deblur_options": {}},    (_CID, {})),
    # --- voice isolation ---
    ("set_voice_isolation",       "set_voice_isolation",       {"timeline_name": _TL, "track_index": 1, "state": {}}, (_TL, 1, {})),  # noqa: E501
    ("set_item_voice_isolation",  "set_item_voice_isolation",  {"timeline_name": _TL, "item_ref": _REF, "state": {}}, (_TL, _REF, {})),  # noqa: E501
    # --- generate speech ---
    ("generate_speech",           "generate_speech",           {"settings": {}, "timecode": "01:00:00:00"},    ({}, "01:00:00:00")),
    # --- reset intellisearch ---
    ("reset_intellisearch",       "reset_intellisearch",       {"confirm": True},                              ()),
]

_AI_DESTRUCTIVE: list[tuple] = [
    ("reset_intellisearch", "reset_intellisearch", {"confirm": True}, ()),
]


class TestDomain8Dispatch:
    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        [r for r in _AI_DISPATCH if r[0] != "reset_intellisearch"],
        ids=[r[0] for r in _AI_DISPATCH if r[0] != "reset_intellisearch"],
    )
    def test_dispatches_to_client(self, tool_name, client_method, mcp_args, call_args):
        server, mock_client = _make_server_with_domain_active(_DOMAIN)
        domain = DOMAIN_REGISTRY[_DOMAIN]
        with _mock_request_ctx():
            _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    def test_reset_intellisearch_with_confirm(self):
        server, mock_client = _make_server_with_domain_active(_DOMAIN)
        domain = DOMAIN_REGISTRY[_DOMAIN]
        with _mock_request_ctx():
            _run(domain.dispatch("reset_intellisearch", {"confirm": True}, mock_client))
        mock_client.reset_intellisearch.assert_called_once_with()

    def test_reset_intellisearch_blocked_without_confirm(self):
        server, mock_client = _make_server_with_domain_active(_DOMAIN)
        domain = DOMAIN_REGISTRY[_DOMAIN]
        with _mock_request_ctx():
            result = _run(domain.dispatch("reset_intellisearch", {}, mock_client))
        assert "DESTRUCTIVE" in str(result)
