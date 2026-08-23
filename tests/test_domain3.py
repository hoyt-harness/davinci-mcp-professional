# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 3: Media Pool Operations.

Written before implementation (Article VIII).
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from davinci_mcp.server import DaVinciMCPServer


def _make_mock_client() -> MagicMock:
    client = MagicMock()
    client.is_connected.return_value = True
    return client


@contextmanager
def _mock_request_ctx():
    from mcp.server.lowlevel.server import request_ctx
    mock_session = AsyncMock()
    token = request_ctx.set(MagicMock(session=mock_session))
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


# ---------------------------------------------------------------------------
# Domain 3 dispatch table
# ---------------------------------------------------------------------------

_MP_DISPATCH: list[tuple] = [
    # --- original migrated tools ---
    ("list_media_clips",  "list_media_clips",  {},                        ()),
    ("import_media",      "import_media",       {"file_path": "/f.mov"},  ("/f.mov",)),
    # --- folder inspection ---
    ("get_media_pool_root_folder",    "get_media_pool_root_folder",    {}, ()),
    ("get_current_media_pool_folder", "get_current_media_pool_folder", {}, ()),
    ("get_folder_clips",      "get_folder_clips",    {"folder_path": "Master/B-Roll"}, ("Master/B-Roll",)),
    ("get_folder_subfolders", "get_folder_subfolders",{"folder_path": "Master"},        ("Master",)),
    ("get_selected_pool_clips","get_selected_pool_clips", {},                           ()),
    ("set_selected_pool_clip", "set_selected_pool_clip", {"clip_id": "abc-123"},        ("abc-123",)),
    ("refresh_media_pool_folders","refresh_media_pool_folders",{},                      ()),
    # --- folder management ---
    ("create_media_pool_folder","create_media_pool_folder",
     {"folder_path": "Master", "name": "VFX"},    ("Master", "VFX")),
    ("set_current_media_pool_folder","set_current_media_pool_folder",
     {"folder_path": "Master/VFX"},               ("Master/VFX",)),
    ("move_folders","move_folders",
     {"folder_paths": ["Master/A"], "target_folder_path": "Master/B"},
     (["Master/A"], "Master/B")),
    # --- clip operations ---
    ("append_clips_to_timeline","append_clips_to_timeline",
     {"clip_ids": ["id1", "id2"]},               (["id1", "id2"],)),
    ("create_timeline_from_clips","create_timeline_from_clips",
     {"name": "Cut", "clip_ids": ["id1"]},        ("Cut", ["id1"])),
    ("import_timeline_from_file","import_timeline_from_file",
     {"file_path": "/edl.xml", "import_options": {}}, ("/edl.xml", {})),
    ("export_clip_metadata","export_clip_metadata",
     {"file_name": "/meta.csv", "clip_ids": []}, ("/meta.csv", [])),
    ("relink_clips","relink_clips",
     {"clip_ids": ["id1"], "folder_path": "/media"}, (["id1"], "/media")),
    ("auto_sync_audio","auto_sync_audio",
     {"clip_ids": ["id1"], "audio_sync_settings": {"syncMode": "AUDIO_SYNC_WAVEFORM"}},
     (["id1"], {"syncMode": "AUDIO_SYNC_WAVEFORM"})),
    ("get_clip_matte_list","get_clip_matte_list",{"clip_id": "id1"}, ("id1",)),
    ("add_timeline_mattes","add_timeline_mattes",{"file_paths": ["/m.exr"]}, (["/m.exr"],)),
    ("import_folder_from_file","import_folder_from_file",
     {"file_path": "/bin.drb", "source_clips_path": "/media"},
     ("/bin.drb", "/media")),
    ("create_stereo_clip","create_stereo_clip",
     {"left_clip_id": "l1", "right_clip_id": "r1"}, ("l1", "r1")),
]

_MP_DESTRUCTIVE: list[tuple] = [
    ("move_clips_to_folder","move_clips_to_folder",
     {"clip_ids": ["id1"], "target_folder_path": "Master/VFX", "confirm": True},
     (["id1"], "Master/VFX")),
    ("delete_media_pool_clips","delete_media_pool_clips",
     {"clip_ids": ["id1"], "confirm": True}, (["id1"],)),
    ("delete_media_pool_folders","delete_media_pool_folders",
     {"folder_paths": ["Master/Old"], "confirm": True}, (["Master/Old"],)),
    ("unlink_clips","unlink_clips",
     {"clip_ids": ["id1"], "confirm": True}, (["id1"],)),
    ("add_clip_mattes","add_clip_mattes",
     {"clip_id": "id1", "file_paths": ["/m.exr"], "stereo_eye": "left", "confirm": True},
     ("id1", ["/m.exr"], "left")),
    ("delete_clip_mattes","delete_clip_mattes",
     {"clip_id": "id1", "file_paths": ["/m.exr"], "confirm": True},
     ("id1", ["/m.exr"])),
]


class TestDomain3Dispatch:
    @pytest.mark.parametrize("tool,method,args,call_args",
                             _MP_DISPATCH + _MP_DESTRUCTIVE)
    def test_dispatches_to_client(self, tool, method, args, call_args):
        server, client = _make_server_with_domain_active("media_pool")
        getattr(client, method).return_value = True

        result = _run(server._dispatch_tool(tool, args))

        assert "Unknown tool" not in str(result)
        assert "activate_domain" not in str(result)
        if call_args is not None:
            getattr(client, method).assert_called_once_with(*call_args)


class TestDomain3DestructiveGate:
    @pytest.mark.parametrize("tool,args_without_confirm", [
        ("move_clips_to_folder",    {"clip_ids": ["id1"], "target_folder_path": "X"}),
        ("delete_media_pool_clips", {"clip_ids": ["id1"]}),
        ("delete_media_pool_clips", {"clip_ids": ["id1"], "confirm": False}),
        ("delete_media_pool_folders",{"folder_paths": ["X"]}),
        ("unlink_clips",            {"clip_ids": ["id1"]}),
        ("add_clip_mattes",         {"clip_id": "id1", "file_paths": ["/m.exr"], "stereo_eye": "left"}),
        ("delete_clip_mattes",      {"clip_id": "id1", "file_paths": ["/m.exr"]}),
    ])
    def test_destructive_rejected_without_confirm(self, tool, args_without_confirm):
        server, _ = _make_server_with_domain_active("media_pool")
        result = _run(server._dispatch_tool(tool, args_without_confirm))
        assert "DESTRUCTIVE" in str(result) or "confirm" in str(result).lower()
