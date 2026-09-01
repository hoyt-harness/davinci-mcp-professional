# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 4: Clip Properties & Metadata.

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


_CID = "uuid-1234"

_CP_DISPATCH: list[tuple] = [
    # --- name ---
    ("get_clip_name", "get_clip_name", {"clip_id": _CID}, (_CID,)),
    (
        "set_clip_name",
        "set_clip_name",
        {"clip_id": _CID, "name": "MyClip"},
        (_CID, "MyClip"),
    ),
    # --- properties ---
    ("get_clip_properties", "get_clip_properties", {"clip_id": _CID}, (_CID,)),
    (
        "set_clip_property",
        "set_clip_property",
        {"clip_id": _CID, "property_key": "Reel Name", "property_value": "A001"},
        (_CID, "Reel Name", "A001"),
    ),  # noqa: E501
    # --- metadata ---
    ("get_clip_metadata", "get_clip_metadata", {"clip_id": _CID}, (_CID,)),
    (
        "set_clip_metadata",
        "set_clip_metadata",
        {"clip_id": _CID, "metadata_type": "Scene", "metadata_value": "1"},
        (_CID, "Scene", "1"),
    ),  # noqa: E501
    (
        "get_clip_third_party_metadata",
        "get_clip_third_party_metadata",
        {"clip_id": _CID},
        (_CID,),
    ),  # noqa: E501
    (
        "set_clip_third_party_metadata",
        "set_clip_third_party_metadata",
        {"clip_id": _CID, "metadata_type": "mykey", "metadata_value": "val"},
        (_CID, "mykey", "val"),
    ),  # noqa: E501
    # --- color / flags ---
    ("get_clip_color", "get_clip_color", {"clip_id": _CID}, (_CID,)),
    (
        "set_clip_color",
        "set_clip_color",
        {"clip_id": _CID, "color_name": "Red"},
        (_CID, "Red"),
    ),
    ("clear_clip_color", "clear_clip_color", {"clip_id": _CID}, (_CID,)),
    (
        "add_clip_flag",
        "add_clip_flag",
        {"clip_id": _CID, "color": "Blue"},
        (_CID, "Blue"),
    ),
    ("get_clip_flags", "get_clip_flags", {"clip_id": _CID}, (_CID,)),
    (
        "clear_clip_flags",
        "clear_clip_flags",
        {"clip_id": _CID, "color": "All"},
        (_CID, "All"),
    ),
    # --- markers ---
    (
        "add_clip_marker",
        "add_clip_marker",
        {
            "clip_id": _CID,
            "frame_id": 10,
            "color": "Red",
            "marker_name": "M1",
            "note": "",
            "duration": 1,
            "custom_data": "",
        },
        (_CID, 10, "Red", "M1", "", 1, ""),
    ),  # noqa: E501
    ("get_clip_markers", "get_clip_markers", {"clip_id": _CID}, (_CID,)),
    # --- audio / mark in-out ---
    ("get_clip_audio_mapping", "get_clip_audio_mapping", {"clip_id": _CID}, (_CID,)),
    ("get_clip_mark_in_out", "get_clip_mark_in_out", {"clip_id": _CID}, (_CID,)),
    (
        "set_clip_mark_in_out",
        "set_clip_mark_in_out",
        {"clip_id": _CID, "mark_in": 0, "mark_out": 100, "mark_type": "video"},
        (_CID, 0, 100, "video"),
    ),  # noqa: E501
    (
        "clear_clip_mark_in_out",
        "clear_clip_mark_in_out",
        {"clip_id": _CID, "mark_type": "video"},
        (_CID, "video"),
    ),  # noqa: E501
    # --- proxy / resolution links ---
    (
        "link_proxy_media",
        "link_proxy_media",
        {"clip_id": _CID, "file_path": "/p/proxy.mov"},
        (_CID, "/p/proxy.mov"),
    ),  # noqa: E501
    ("unlink_proxy_media", "unlink_proxy_media", {"clip_id": _CID}, (_CID,)),
    (
        "link_full_resolution_media",
        "link_full_resolution_media",
        {"clip_id": _CID, "file_path": "/p/full.mov"},
        (_CID, "/p/full.mov"),
    ),  # noqa: E501
    # --- unique id / timeline ---
    ("get_clip_unique_id", "get_clip_unique_id", {"clip_id": _CID}, (_CID,)),
    ("get_clip_timeline", "get_clip_timeline", {"clip_id": _CID}, (_CID,)),
]

_CP_DESTRUCTIVE: list[tuple] = [
    (
        "delete_clip_markers_by_color",
        "delete_clip_markers_by_color",
        {"clip_id": _CID, "color": "All", "confirm": True},
        (_CID, "All"),
    ),  # noqa: E501
    (
        "delete_clip_marker_at_frame",
        "delete_clip_marker_at_frame",
        {"clip_id": _CID, "frame_num": 10, "confirm": True},
        (_CID, 10),
    ),  # noqa: E501
    (
        "replace_clip",
        "replace_clip",
        {"clip_id": _CID, "file_path": "/p/new.mov", "confirm": True},
        (_CID, "/p/new.mov"),
    ),  # noqa: E501
    (
        "replace_clip_preserve_subclip",
        "replace_clip_preserve_subclip",
        {"clip_id": _CID, "file_path": "/p/new.mov", "confirm": True},
        (_CID, "/p/new.mov"),
    ),  # noqa: E501
]


class TestDomain4Dispatch:
    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _CP_DISPATCH,
        ids=[r[0] for r in _CP_DISPATCH],
    )
    def test_dispatches_to_client(self, tool_name, client_method, mcp_args, call_args):
        server, mock_client = _make_server_with_domain_active("clip_properties")
        domain = DOMAIN_REGISTRY["clip_properties"]
        _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _CP_DESTRUCTIVE,
        ids=[r[0] for r in _CP_DESTRUCTIVE],
    )
    def test_destructive_dispatches_with_confirm(
        self, tool_name, client_method, mcp_args, call_args
    ):
        server, mock_client = _make_server_with_domain_active("clip_properties")
        domain = DOMAIN_REGISTRY["clip_properties"]
        _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,mcp_args",
        [
            (r[0], {k: v for k, v in r[2].items() if k != "confirm"})
            for r in _CP_DESTRUCTIVE
        ],
        ids=[r[0] for r in _CP_DESTRUCTIVE],
    )
    def test_destructive_blocked_without_confirm(self, tool_name, mcp_args):
        server, mock_client = _make_server_with_domain_active("clip_properties")
        domain = DOMAIN_REGISTRY["clip_properties"]
        result = _run(domain.dispatch(tool_name, mcp_args, mock_client))
        assert "DESTRUCTIVE" in str(result)
