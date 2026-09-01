# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 9: System, Fairlight & Storage.

Written before implementation (Article VIII).
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from davinci_mcp.domains.registry import DOMAIN_REGISTRY
from davinci_mcp.server import DaVinciMCPServer


def _make_mock_client() -> MagicMock:
    client = MagicMock()
    client.is_connected.return_value = True
    return client




def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_server_with_domain_active(
    domain_name: str,
) -> tuple[DaVinciMCPServer, MagicMock]:
    mock_client = _make_mock_client()
    with patch("davinci_mcp.server.DaVinciResolveClient", return_value=mock_client):
        server = DaVinciMCPServer()
    mock_ctx = MagicMock(session=AsyncMock())
    _run(server._activate_domain(mock_ctx, domain_name))
    return server, mock_client


_SFS_DISPATCH: list[tuple] = [
    # --- layout presets ---
    ("get_layout_presets", "get_layout_presets", {}, ()),
    ("load_layout_preset", "load_layout_preset", {"preset_name": "Color"}, ("Color",)),
    (
        "save_layout_preset",
        "save_layout_preset",
        {"preset_name": "MyLayout"},
        ("MyLayout",),
    ),
    (
        "export_layout_preset",
        "export_layout_preset",
        {"preset_name": "MyLayout", "file_path": "/p/l.epresetx"},
        ("MyLayout", "/p/l.epresetx"),
    ),  # noqa: E501
    (
        "import_layout_preset",
        "import_layout_preset",
        {"file_path": "/p/l.epresetx", "preset_name": "MyLayout"},
        ("/p/l.epresetx", "MyLayout"),
    ),  # noqa: E501
    # --- Fairlight presets ---
    ("get_fairlight_presets", "get_fairlight_presets", {}, ()),
    (
        "apply_fairlight_preset",
        "apply_fairlight_preset",
        {"preset_name": "Dialogue"},
        ("Dialogue",),
    ),
    # --- keyframe mode ---
    ("get_keyframe_mode", "get_keyframe_mode", {}, ()),
    ("set_keyframe_mode", "set_keyframe_mode", {"keyframe_mode": 1}, (1,)),
    # --- Fairlight audio insert ---
    (
        "insert_audio_at_playhead",
        "insert_audio_at_playhead",
        {"media_path": "/p/a.wav", "start_offset": 0, "duration": 1000},
        ("/p/a.wav", 0, 1000),
    ),  # noqa: E501
    # --- media storage ---
    ("get_mounted_volumes", "get_mounted_volumes", {}, ()),
    (
        "get_storage_subfolders",
        "get_storage_subfolders",
        {"folder_path": "/Volumes/SSD"},
        ("/Volumes/SSD",),
    ),
    (
        "get_storage_files",
        "get_storage_files",
        {"folder_path": "/Volumes/SSD"},
        ("/Volumes/SSD",),
    ),
    (
        "add_storage_items_to_pool",
        "add_storage_items_to_pool",
        {"items": ["/p/a.mov"]},
        (["/p/a.mov"],),
    ),
    # --- background tasks ---
    ("disable_background_tasks", "disable_background_tasks", {}, ()),
]

_SFS_DESTRUCTIVE: list[tuple] = [
    (
        "delete_layout_preset",
        "delete_layout_preset",
        {"preset_name": "MyLayout", "confirm": True},
        ("MyLayout",),
    ),
]


class TestDomain9Dispatch:
    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _SFS_DISPATCH,
        ids=[r[0] for r in _SFS_DISPATCH],
    )
    def test_dispatches_to_client(self, tool_name, client_method, mcp_args, call_args):
        server, mock_client = _make_server_with_domain_active(
            "system_fairlight_storage"
        )
        domain = DOMAIN_REGISTRY["system_fairlight_storage"]
        _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _SFS_DESTRUCTIVE,
        ids=[r[0] for r in _SFS_DESTRUCTIVE],
    )
    def test_destructive_dispatches_with_confirm(
        self, tool_name, client_method, mcp_args, call_args
    ):
        server, mock_client = _make_server_with_domain_active(
            "system_fairlight_storage"
        )
        domain = DOMAIN_REGISTRY["system_fairlight_storage"]
        _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,mcp_args",
        [
            (r[0], {k: v for k, v in r[2].items() if k != "confirm"})
            for r in _SFS_DESTRUCTIVE
        ],
        ids=[r[0] for r in _SFS_DESTRUCTIVE],
    )
    def test_destructive_blocked_without_confirm(self, tool_name, mcp_args):
        server, mock_client = _make_server_with_domain_active(
            "system_fairlight_storage"
        )
        domain = DOMAIN_REGISTRY["system_fairlight_storage"]
        result = _run(domain.dispatch(tool_name, mcp_args, mock_client))
        assert "DESTRUCTIVE" in str(result)
