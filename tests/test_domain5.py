# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 5: Timeline Item Editing.

Written before implementation (Article VIII).
TimelineItems are addressed as {track_type, track_index, item_index} within
the current timeline (Article V).
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


# Standard item reference
_TL = "Timeline 1"
_REF = {"track_type": "video", "track_index": 1, "item_index": 1}
_CID = "uuid-1234"

_TI_DISPATCH: list[tuple] = [
    # --- name ---
    ("get_item_name",     "get_item_name",     {"timeline_name": _TL, "item_ref": _REF},                           (_TL, _REF)),
    ("set_item_name",     "set_item_name",     {"timeline_name": _TL, "item_ref": _REF, "name": "Shot A"},        (_TL, _REF, "Shot A")),
    # --- timing ---
    ("get_item_duration", "get_item_duration", {"timeline_name": _TL, "item_ref": _REF, "subframe_precision": False}, (_TL, _REF, False)),  # noqa: E501
    ("get_item_start",    "get_item_start",    {"timeline_name": _TL, "item_ref": _REF, "subframe_precision": False}, (_TL, _REF, False)),  # noqa: E501
    ("get_item_end",      "get_item_end",      {"timeline_name": _TL, "item_ref": _REF, "subframe_precision": False}, (_TL, _REF, False)),  # noqa: E501
    ("get_item_source_start", "get_item_source_start", {"timeline_name": _TL, "item_ref": _REF},                   (_TL, _REF)),
    ("get_item_source_end",   "get_item_source_end",   {"timeline_name": _TL, "item_ref": _REF},                   (_TL, _REF)),
    ("get_item_left_offset",  "get_item_left_offset",  {"timeline_name": _TL, "item_ref": _REF, "subframe_precision": False}, (_TL, _REF, False)),  # noqa: E501
    ("get_item_right_offset", "get_item_right_offset", {"timeline_name": _TL, "item_ref": _REF, "subframe_precision": False}, (_TL, _REF, False)),  # noqa: E501
    # --- properties ---
    ("get_item_properties", "get_item_properties", {"timeline_name": _TL, "item_ref": _REF},                       (_TL, _REF)),
    ("set_item_property",   "set_item_property",   {"timeline_name": _TL, "item_ref": _REF, "property_key": "Pan", "property_value": 0.5}, (_TL, _REF, "Pan", 0.5)),  # noqa: E501
    # --- enabled / color ---
    ("get_item_enabled",  "get_item_enabled",  {"timeline_name": _TL, "item_ref": _REF},                           (_TL, _REF)),
    ("set_item_enabled",  "set_item_enabled",  {"timeline_name": _TL, "item_ref": _REF, "enabled": True},          (_TL, _REF, True)),
    ("get_item_color",    "get_item_color",    {"timeline_name": _TL, "item_ref": _REF},                           (_TL, _REF)),
    ("set_item_color",    "set_item_color",    {"timeline_name": _TL, "item_ref": _REF, "color_name": "Red"},       (_TL, _REF, "Red")),
    ("clear_item_color",  "clear_item_color",  {"timeline_name": _TL, "item_ref": _REF},                           (_TL, _REF)),
    # --- flags ---
    ("add_item_flag",     "add_item_flag",     {"timeline_name": _TL, "item_ref": _REF, "color": "Blue"},          (_TL, _REF, "Blue")),
    ("get_item_flags",    "get_item_flags",    {"timeline_name": _TL, "item_ref": _REF},                           (_TL, _REF)),
    ("clear_item_flags",  "clear_item_flags",  {"timeline_name": _TL, "item_ref": _REF, "color": "All"},           (_TL, _REF, "All")),
    # --- markers ---
    ("add_item_marker",   "add_item_marker",   {"timeline_name": _TL, "item_ref": _REF, "frame_id": 5, "color": "Green", "marker_name": "M", "note": "", "duration": 1, "custom_data": ""}, (_TL, _REF, 5, "Green", "M", "", 1, "")),  # noqa: E501
    ("get_item_markers",  "get_item_markers",  {"timeline_name": _TL, "item_ref": _REF},                           (_TL, _REF)),
    # --- takes ---
    ("add_take",           "add_take",           {"timeline_name": _TL, "item_ref": _REF, "clip_id": _CID, "start_frame": 0, "end_frame": 100}, (_TL, _REF, _CID, 0, 100)),  # noqa: E501
    ("get_take_count",     "get_take_count",     {"timeline_name": _TL, "item_ref": _REF},                         (_TL, _REF)),
    ("get_take_by_index",  "get_take_by_index",  {"timeline_name": _TL, "item_ref": _REF, "take_index": 1},        (_TL, _REF, 1)),
    ("select_take",        "select_take",        {"timeline_name": _TL, "item_ref": _REF, "take_index": 1},        (_TL, _REF, 1)),
    ("finalize_take",      "finalize_take",      {"timeline_name": _TL, "item_ref": _REF},                         (_TL, _REF)),
    # --- color versions ---
    ("get_current_color_version", "get_current_color_version", {"timeline_name": _TL, "item_ref": _REF},           (_TL, _REF)),
    ("get_color_version_list",    "get_color_version_list",    {"timeline_name": _TL, "item_ref": _REF, "version_type": 0}, (_TL, _REF, 0)),  # noqa: E501
    ("add_color_version",         "add_color_version",         {"timeline_name": _TL, "item_ref": _REF, "version_name": "v2", "version_type": 0}, (_TL, _REF, "v2", 0)),  # noqa: E501
    ("load_color_version",        "load_color_version",        {"timeline_name": _TL, "item_ref": _REF, "version_name": "v2", "version_type": 0}, (_TL, _REF, "v2", 0)),  # noqa: E501
    ("rename_color_version",      "rename_color_version",      {"timeline_name": _TL, "item_ref": _REF, "old_name": "v1", "new_name": "v2", "version_type": 0}, (_TL, _REF, "v1", "v2", 0)),  # noqa: E501
    # --- Fusion comps ---
    ("list_fusion_comps",   "list_fusion_comps",   {"timeline_name": _TL, "item_ref": _REF},                       (_TL, _REF)),
    ("add_fusion_comp",     "add_fusion_comp",     {"timeline_name": _TL, "item_ref": _REF},                       (_TL, _REF)),
    ("load_fusion_comp",    "load_fusion_comp",    {"timeline_name": _TL, "item_ref": _REF, "comp_name": "Comp1"}, (_TL, _REF, "Comp1")),
    ("import_fusion_comp",  "import_fusion_comp",  {"timeline_name": _TL, "item_ref": _REF, "file_path": "/p/c.setting"}, (_TL, _REF, "/p/c.setting")),  # noqa: E501
    ("export_fusion_comp",  "export_fusion_comp",  {"timeline_name": _TL, "item_ref": _REF, "file_path": "/p/c.setting", "comp_index": 0}, (_TL, _REF, "/p/c.setting", 0)),  # noqa: E501
    # --- node graph / grade ---
    ("get_item_node_graph", "get_item_node_graph", {"timeline_name": _TL, "item_ref": _REF, "layer_index": 1},     (_TL, _REF, 1)),
    ("copy_grades",         "copy_grades",         {"timeline_name": _TL, "item_ref": _REF, "target_item_refs": [_REF]}, (_TL, _REF, [_REF])),  # noqa: E501
    ("set_cdl",             "set_cdl",             {"timeline_name": _TL, "item_ref": _REF, "cdl_map": {"NodeIndex": 1}}, (_TL, _REF, {"NodeIndex": 1})),  # noqa: E501
    ("export_item_lut",     "export_item_lut",     {"timeline_name": _TL, "item_ref": _REF, "export_type": 0, "file_path": "/p/l.cube"}, (_TL, _REF, 0, "/p/l.cube")),  # noqa: E501
    ("update_sidecar",      "update_sidecar",      {"timeline_name": _TL, "item_ref": _REF},                       (_TL, _REF)),
    # --- linked items / track info ---
    ("get_linked_items",    "get_linked_items",    {"timeline_name": _TL, "item_ref": _REF},                       (_TL, _REF)),
    ("get_item_track",      "get_item_track",      {"timeline_name": _TL, "item_ref": _REF},                       (_TL, _REF)),
    ("get_item_audio_channel_mapping", "get_item_audio_channel_mapping", {"timeline_name": _TL, "item_ref": _REF}, (_TL, _REF)),  # noqa: E501
    # --- color group ---
    ("get_item_color_group",    "get_item_color_group",    {"timeline_name": _TL, "item_ref": _REF},                (_TL, _REF)),
    ("assign_to_color_group",   "assign_to_color_group",   {"timeline_name": _TL, "item_ref": _REF, "group_name": "A"}, (_TL, _REF, "A")),  # noqa: E501
    ("remove_from_color_group", "remove_from_color_group", {"timeline_name": _TL, "item_ref": _REF},                (_TL, _REF)),
    # --- cache ---
    ("get_item_color_cache_enabled",  "get_item_color_cache_enabled",  {"timeline_name": _TL, "item_ref": _REF},   (_TL, _REF)),
    ("set_item_color_cache",          "set_item_color_cache",          {"timeline_name": _TL, "item_ref": _REF, "cache_value": 1}, (_TL, _REF, 1)),  # noqa: E501
    ("get_item_fusion_cache_enabled", "get_item_fusion_cache_enabled", {"timeline_name": _TL, "item_ref": _REF},   (_TL, _REF)),
    ("set_item_fusion_cache",         "set_item_fusion_cache",         {"timeline_name": _TL, "item_ref": _REF, "cache_value": 1}, (_TL, _REF, 1)),  # noqa: E501
    # --- media pool item / node colors ---
    ("get_item_media_pool_item",  "get_item_media_pool_item",  {"timeline_name": _TL, "item_ref": _REF},            (_TL, _REF)),
    ("reset_item_node_colors",    "reset_item_node_colors",    {"timeline_name": _TL, "item_ref": _REF},            (_TL, _REF)),
]

_TI_DESTRUCTIVE: list[tuple] = [
    ("delete_item_markers_by_color", "delete_item_markers_by_color", {"timeline_name": _TL, "item_ref": _REF, "color": "All", "confirm": True}, (_TL, _REF, "All")),  # noqa: E501
    ("delete_item_marker_at_frame",  "delete_item_marker_at_frame",  {"timeline_name": _TL, "item_ref": _REF, "frame_num": 5, "confirm": True}, (_TL, _REF, 5)),  # noqa: E501
    ("delete_take",                  "delete_take",                  {"timeline_name": _TL, "item_ref": _REF, "take_index": 1, "confirm": True}, (_TL, _REF, 1)),  # noqa: E501
    ("delete_color_version",         "delete_color_version",         {"timeline_name": _TL, "item_ref": _REF, "version_name": "v1", "version_type": 0, "confirm": True}, (_TL, _REF, "v1", 0)),  # noqa: E501
    ("delete_fusion_comp",           "delete_fusion_comp",           {"timeline_name": _TL, "item_ref": _REF, "comp_name": "Comp1", "confirm": True}, (_TL, _REF, "Comp1")),  # noqa: E501
    ("rename_fusion_comp",           "rename_fusion_comp",           {"timeline_name": _TL, "item_ref": _REF, "old_name": "Comp1", "new_name": "Comp2"}, (_TL, _REF, "Comp1", "Comp2")),  # noqa: E501
]


class TestDomain5Dispatch:
    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _TI_DISPATCH,
        ids=[r[0] for r in _TI_DISPATCH],
    )
    def test_dispatches_to_client(self, tool_name, client_method, mcp_args, call_args):
        server, mock_client = _make_server_with_domain_active("timeline_item_editing")
        domain = DOMAIN_REGISTRY["timeline_item_editing"]
        with _mock_request_ctx():
            _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _TI_DESTRUCTIVE,
        ids=[r[0] for r in _TI_DESTRUCTIVE],
    )
    def test_destructive_dispatches_with_confirm(
        self, tool_name, client_method, mcp_args, call_args
    ):
        server, mock_client = _make_server_with_domain_active("timeline_item_editing")
        domain = DOMAIN_REGISTRY["timeline_item_editing"]
        with _mock_request_ctx():
            _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,mcp_args",
        [(r[0], {k: v for k, v in r[2].items() if k != "confirm"}) for r in _TI_DESTRUCTIVE
         if r[0] not in {"rename_fusion_comp"}],
        ids=[r[0] for r in _TI_DESTRUCTIVE if r[0] not in {"rename_fusion_comp"}],
    )
    def test_destructive_blocked_without_confirm(self, tool_name, mcp_args):
        server, mock_client = _make_server_with_domain_active("timeline_item_editing")
        domain = DOMAIN_REGISTRY["timeline_item_editing"]
        with _mock_request_ctx():
            result = _run(domain.dispatch(tool_name, mcp_args, mock_client))
        assert "DESTRUCTIVE" in str(result)
