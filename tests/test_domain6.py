# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 6: Color Grading.

Written before implementation (Article VIII).
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
_ALB = "Stills"
_GRP = "Group A"

_CG_DISPATCH: list[tuple] = [
    # --- graph / node operations (current timeline's graph) ---
    ("get_graph_node_count",    "get_graph_node_count",    {"timeline_name": _TL},                    (_TL,)),
    ("get_graph_node_label",    "get_graph_node_label",    {"timeline_name": _TL, "node_index": 1},   (_TL, 1)),
    ("get_graph_node_tools",    "get_graph_node_tools",    {"timeline_name": _TL, "node_index": 1},   (_TL, 1)),
    ("get_graph_node_lut",      "get_graph_node_lut",      {"timeline_name": _TL, "node_index": 1},   (_TL, 1)),
    ("set_graph_node_lut",      "set_graph_node_lut",      {"timeline_name": _TL, "node_index": 1, "lut_path": "/p/l.cube"}, (_TL, 1, "/p/l.cube")),  # noqa: E501
    ("get_graph_node_cache_mode","get_graph_node_cache_mode",{"timeline_name": _TL, "node_index": 1}, (_TL, 1)),
    ("set_graph_node_enabled",  "set_graph_node_enabled",  {"timeline_name": _TL, "node_index": 1, "enabled": True}, (_TL, 1, True)),  # noqa: E501
    ("set_graph_node_cache_mode","set_graph_node_cache_mode",{"timeline_name": _TL, "node_index": 1, "cache_mode": 1}, (_TL, 1, 1)),  # noqa: E501
    ("apply_grade_from_drx",    "apply_grade_from_drx",    {"timeline_name": _TL, "drx_path": "/p/g.drx", "grade_mode": 0}, (_TL, "/p/g.drx", 0)),  # noqa: E501
    ("apply_arri_cdl_lut",      "apply_arri_cdl_lut",      {"timeline_name": _TL},                    (_TL,)),
    # --- gallery stills ---
    ("get_gallery_albums",      "get_gallery_albums",      {},                                         ()),
    ("get_gallery_powergrade_albums", "get_gallery_powergrade_albums", {},                             ()),
    ("get_current_still_album", "get_current_still_album", {},                                         ()),
    ("create_still_album",      "create_still_album",      {},                                         ()),
    ("create_powergrade_album", "create_powergrade_album", {},                                         ()),
    ("grab_still",              "grab_still",              {"timeline_name": _TL},                    (_TL,)),
    ("grab_all_stills",         "grab_all_stills",         {"timeline_name": _TL, "still_frame_source": 1}, (_TL, 1)),  # noqa: E501
    ("get_stills",              "get_stills",              {"album_name": _ALB},                       (_ALB,)),
    ("get_still_label",         "get_still_label",         {"album_name": _ALB, "still_index": 1},    (_ALB, 1)),
    ("set_still_label",         "set_still_label",         {"album_name": _ALB, "still_index": 1, "label": "Hero"}, (_ALB, 1, "Hero")),  # noqa: E501
    ("export_stills",           "export_stills",           {"album_name": _ALB, "still_indices": [1], "folder_path": "/p/s", "file_prefix": "s", "format": "dpx"}, (_ALB, [1], "/p/s", "s", "dpx")),  # noqa: E501
    ("import_stills",           "import_stills",           {"album_name": _ALB, "file_paths": ["/p/s.dpx"]}, (_ALB, ["/p/s.dpx"])),  # noqa: E501
    # --- color groups ---
    ("get_color_groups",        "get_color_groups",        {},                                         ()),
    ("create_color_group",      "create_color_group",      {"group_name": _GRP},                      (_GRP,)),
    ("rename_color_group",      "rename_color_group",      {"group_name": _GRP, "new_name": "B"},     (_GRP, "B")),
    ("get_clips_in_color_group","get_clips_in_color_group",{"group_name": _GRP, "timeline_name": _TL}, (_GRP, _TL)),  # noqa: E501
    ("get_color_group_pre_graph","get_color_group_pre_graph",{"group_name": _GRP},                    (_GRP,)),
    ("get_color_group_post_graph","get_color_group_post_graph",{"group_name": _GRP},                  (_GRP,)),
    # --- project-level color ---
    ("refresh_lut_list",        "refresh_lut_list",        {},                                         ()),
    ("export_current_frame_as_still", "export_current_frame_as_still", {"file_path": "/p/f.dpx"},     ("/p/f.dpx",)),
]

_CG_DESTRUCTIVE: list[tuple] = [
    ("reset_all_grades",   "reset_all_grades",   {"timeline_name": _TL, "confirm": True},             (_TL,)),
    ("delete_stills",      "delete_stills",      {"album_name": _ALB, "still_indices": [1], "confirm": True}, (_ALB, [1])),  # noqa: E501
    ("delete_color_group", "delete_color_group", {"group_name": _GRP, "confirm": True},               (_GRP,)),
]


class TestDomain6Dispatch:
    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _CG_DISPATCH,
        ids=[r[0] for r in _CG_DISPATCH],
    )
    def test_dispatches_to_client(self, tool_name, client_method, mcp_args, call_args):
        server, mock_client = _make_server_with_domain_active("color_grading")
        domain = DOMAIN_REGISTRY["color_grading"]
        with _mock_request_ctx():
            _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _CG_DESTRUCTIVE,
        ids=[r[0] for r in _CG_DESTRUCTIVE],
    )
    def test_destructive_dispatches_with_confirm(
        self, tool_name, client_method, mcp_args, call_args
    ):
        server, mock_client = _make_server_with_domain_active("color_grading")
        domain = DOMAIN_REGISTRY["color_grading"]
        with _mock_request_ctx():
            _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,mcp_args",
        [(r[0], {k: v for k, v in r[2].items() if k != "confirm"}) for r in _CG_DESTRUCTIVE],
        ids=[r[0] for r in _CG_DESTRUCTIVE],
    )
    def test_destructive_blocked_without_confirm(self, tool_name, mcp_args):
        server, mock_client = _make_server_with_domain_active("color_grading")
        domain = DOMAIN_REGISTRY["color_grading"]
        with _mock_request_ctx():
            result = _run(domain.dispatch(tool_name, mcp_args, mock_client))
        assert "DESTRUCTIVE" in str(result)
