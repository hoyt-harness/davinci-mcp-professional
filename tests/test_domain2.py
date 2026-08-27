# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 2: Timeline Operations.

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


def _make_server_with_domain_active(
    domain_name: str,
) -> tuple[DaVinciMCPServer, MagicMock]:
    mock_client = _make_mock_client()
    with patch("davinci_mcp.server.DaVinciResolveClient", return_value=mock_client):
        server = DaVinciMCPServer()
    with _mock_request_ctx():
        _run(server._activate_domain(domain_name))
    return server, mock_client


# ---------------------------------------------------------------------------
# Domain 2 dispatch table
# One row: (tool_name, client_method, mcp_args, expected_call_args)
# ---------------------------------------------------------------------------

_TL_DISPATCH: list[tuple] = [
    # --- original migrated tools ---
    ("list_timelines", "list_timelines", {}, ()),
    ("get_current_timeline", "get_current_timeline_name", {}, ()),
    ("create_timeline", "create_timeline", {"name": "Edit"}, ("Edit",)),
    ("switch_timeline", "switch_timeline", {"name": "Edit"}, ("Edit",)),
    # --- management ---
    (
        "rename_timeline",
        "rename_timeline",
        {"name": "Old", "new_name": "New"},
        ("Old", "New"),
    ),
    (
        "duplicate_timeline",
        "duplicate_timeline",
        {"name": "Edit", "new_name": "Edit Copy"},
        ("Edit", "Edit Copy"),
    ),
    # --- settings / timecode ---
    (
        "get_timeline_settings",
        "get_timeline_settings",
        {"name": "Edit", "setting_name": None},
        ("Edit", None),
    ),
    (
        "set_timeline_setting",
        "set_timeline_setting",
        {
            "name": "Edit",
            "setting_name": "timelineResolutionWidth",
            "setting_value": 3840,
        },
        ("Edit", "timelineResolutionWidth", 3840),
    ),
    ("get_start_timecode", "get_start_timecode", {"name": "Edit"}, ("Edit",)),
    (
        "set_start_timecode",
        "set_start_timecode",
        {"name": "Edit", "timecode": "01:00:00:00"},
        ("Edit", "01:00:00:00"),
    ),
    ("get_current_timecode", "get_current_timecode", {"name": "Edit"}, ("Edit",)),
    (
        "set_current_timecode",
        "set_current_timecode",
        {"name": "Edit", "timecode": "01:00:10:00"},
        ("Edit", "01:00:10:00"),
    ),
    (
        "get_timeline_start_frame",
        "get_timeline_start_frame",
        {"name": "Edit"},
        ("Edit",),
    ),
    ("get_timeline_end_frame", "get_timeline_end_frame", {"name": "Edit"}, ("Edit",)),
    # --- marks ---
    ("get_timeline_marks", "get_timeline_marks", {"name": "Edit"}, ("Edit",)),
    (
        "set_timeline_marks",
        "set_timeline_marks",
        {"name": "Edit", "mark_in": 0, "mark_out": 100, "mark_type": "video"},
        ("Edit", 0, 100, "video"),
    ),
    (
        "clear_timeline_marks",
        "clear_timeline_marks",
        {"name": "Edit", "mark_type": "video"},
        ("Edit", "video"),
    ),
    # --- tracks ---
    (
        "get_track_count",
        "get_track_count",
        {"name": "Edit", "track_type": "video"},
        ("Edit", "video"),
    ),
    (
        "add_track",
        "add_track",
        {"name": "Edit", "track_type": "video", "sub_track_type": ""},
        ("Edit", "video", ""),
    ),
    (
        "get_track_name",
        "get_track_name",
        {"name": "Edit", "track_type": "video", "track_index": 1},
        ("Edit", "video", 1),
    ),
    (
        "set_track_name",
        "set_track_name",
        {"name": "Edit", "track_type": "video", "track_index": 1, "new_name": "V1"},
        ("Edit", "video", 1, "V1"),
    ),
    (
        "get_track_subtype",
        "get_track_subtype",
        {"name": "Edit", "track_type": "audio", "track_index": 1},
        ("Edit", "audio", 1),
    ),
    (
        "enable_track",
        "enable_track",
        {"name": "Edit", "track_type": "video", "track_index": 1, "enabled": True},
        ("Edit", "video", 1, True),
    ),
    (
        "get_track_enabled",
        "get_track_enabled",
        {"name": "Edit", "track_type": "video", "track_index": 1},
        ("Edit", "video", 1),
    ),
    (
        "lock_track",
        "lock_track",
        {"name": "Edit", "track_type": "video", "track_index": 1, "locked": True},
        ("Edit", "video", 1, True),
    ),
    (
        "get_track_locked",
        "get_track_locked",
        {"name": "Edit", "track_type": "video", "track_index": 1},
        ("Edit", "video", 1),
    ),
    # --- items ---
    (
        "get_items_in_track",
        "get_items_in_track",
        {"name": "Edit", "track_type": "video", "track_index": 1},
        ("Edit", "video", 1),
    ),
    (
        "get_selected_timeline_clips",
        "get_selected_timeline_clips",
        {"name": "Edit"},
        ("Edit",),
    ),
    ("get_current_video_item", "get_current_video_item", {"name": "Edit"}, ("Edit",)),
    (
        "get_current_clip_thumbnail",
        "get_current_clip_thumbnail",
        {"name": "Edit"},
        ("Edit",),
    ),
    (
        "get_timeline_media_pool_item",
        "get_timeline_media_pool_item",
        {"name": "Edit"},
        ("Edit",),
    ),
    # --- markers ---
    (
        "add_timeline_marker",
        "add_timeline_marker",
        {
            "name": "Edit",
            "frame_id": 0,
            "color": "Red",
            "marker_name": "M",
            "note": "",
            "duration": 1,
            "custom_data": "",
        },
        ("Edit", 0, "Red", "M", "", 1, ""),
    ),
    ("get_timeline_markers", "get_timeline_markers", {"name": "Edit"}, ("Edit",)),
    # --- export / insert ---
    (
        "export_timeline",
        "export_timeline",
        {
            "name": "Edit",
            "file_name": "/out.xml",
            "export_type": "EXPORT_AAF",
            "export_subtype": "EXPORT_AAF_NEW",
        },
        ("Edit", "/out.xml", "EXPORT_AAF", "EXPORT_AAF_NEW"),
    ),
    (
        "import_into_timeline",
        "import_into_timeline",
        {"name": "Edit", "file_path": "/in.aaf", "import_options": {}},
        ("Edit", "/in.aaf", {}),
    ),
    (
        "insert_generator",
        "insert_generator",
        {"name": "Edit", "generator_name": "Solid Color"},
        ("Edit", "Solid Color"),
    ),
    (
        "insert_fusion_generator",
        "insert_fusion_generator",
        {"name": "Edit", "generator_name": "Background"},
        ("Edit", "Background"),
    ),
    (
        "insert_ofx_generator",
        "insert_ofx_generator",
        {"name": "Edit", "generator_name": "Noise"},
        ("Edit", "Noise"),
    ),
    (
        "insert_title",
        "insert_title",
        {"name": "Edit", "title_name": "Lower Third"},
        ("Edit", "Lower Third"),
    ),
    (
        "insert_fusion_title",
        "insert_fusion_title",
        {"name": "Edit", "title_name": "Text+"},
        ("Edit", "Text+"),
    ),
    (
        "insert_fusion_composition",
        "insert_fusion_composition",
        {"name": "Edit"},
        ("Edit",),
    ),
    ("get_timeline_node_graph", "get_timeline_node_graph", {"name": "Edit"}, ("Edit",)),
    (
        "link_clips",
        "link_clips",
        {
            "name": "Edit",
            "item_refs": [{"track_type": "video", "track_index": 1, "item_index": 1}],
            "linked": True,
        },
        ("Edit", [{"track_type": "video", "track_index": 1, "item_index": 1}], True),
    ),
    (
        "analyze_dolby_vision",
        "analyze_dolby_vision",
        {
            "name": "Edit",
            "item_refs": [{"track_type": "video", "track_index": 1, "item_index": 1}],
            "analysis_type": 0,
        },
        ("Edit", [{"track_type": "video", "track_index": 1, "item_index": 1}], 0),
    ),
]

_TL_DESTRUCTIVE: list[tuple] = [
    (
        "delete_timeline",
        "delete_timeline",
        {"name": "Edit", "confirm": True},
        ("Edit",),
    ),
    (
        "delete_track",
        "delete_track",
        {"name": "Edit", "track_type": "video", "track_index": 1, "confirm": True},
        ("Edit", "video", 1),
    ),
    (
        "delete_timeline_markers_by_color",
        "delete_timeline_markers_by_color",
        {"name": "Edit", "color": "Red", "confirm": True},
        ("Edit", "Red"),
    ),
    (
        "delete_timeline_marker_at_frame",
        "delete_timeline_marker_at_frame",
        {"name": "Edit", "frame_num": 42, "confirm": True},
        ("Edit", 42),
    ),
    (
        "delete_timeline_clips",
        "delete_timeline_clips",
        {
            "name": "Edit",
            "item_refs": [{"track_type": "video", "track_index": 1, "item_index": 1}],
            "ripple": False,
            "confirm": True,
        },
        ("Edit", [{"track_type": "video", "track_index": 1, "item_index": 1}], False),
    ),
    (
        "create_compound_clip",
        "create_compound_clip",
        {
            "name": "Edit",
            "item_refs": [{"track_type": "video", "track_index": 1, "item_index": 1}],
            "clip_info": {},
            "confirm": True,
        },
        ("Edit", [{"track_type": "video", "track_index": 1, "item_index": 1}], {}),
    ),
    (
        "create_fusion_clip",
        "create_fusion_clip",
        {
            "name": "Edit",
            "item_refs": [{"track_type": "video", "track_index": 1, "item_index": 1}],
            "confirm": True,
        },
        ("Edit", [{"track_type": "video", "track_index": 1, "item_index": 1}]),
    ),
]


class TestDomain2Dispatch:
    @pytest.mark.parametrize(
        "tool,method,args,call_args", _TL_DISPATCH + _TL_DESTRUCTIVE
    )
    def test_dispatches_to_client(self, tool, method, args, call_args):
        server, client = _make_server_with_domain_active("timeline_operations")
        getattr(client, method).return_value = True

        result = _run(server._dispatch_tool(tool, args))

        assert "Unknown tool" not in str(result)
        assert "activate_domain" not in str(result)
        if call_args is not None:
            getattr(client, method).assert_called_once_with(*call_args)


class TestDomain2DestructiveGate:
    @pytest.mark.parametrize(
        "tool,args_without_confirm",
        [
            ("delete_timeline", {"name": "Edit"}),
            ("delete_timeline", {"name": "Edit", "confirm": False}),
            ("delete_track", {"name": "Edit", "track_type": "video", "track_index": 1}),
            ("delete_timeline_markers_by_color", {"name": "Edit", "color": "Red"}),
            ("delete_timeline_marker_at_frame", {"name": "Edit", "frame_num": 42}),
            (
                "delete_timeline_clips",
                {
                    "name": "Edit",
                    "item_refs": [
                        {"track_type": "video", "track_index": 1, "item_index": 1}
                    ],
                    "ripple": False,
                },
            ),
            (
                "create_compound_clip",
                {
                    "name": "Edit",
                    "item_refs": [
                        {"track_type": "video", "track_index": 1, "item_index": 1}
                    ],
                    "clip_info": {},
                },
            ),
            (
                "create_fusion_clip",
                {
                    "name": "Edit",
                    "item_refs": [
                        {"track_type": "video", "track_index": 1, "item_index": 1}
                    ],
                },
            ),
        ],
    )
    def test_destructive_rejected_without_confirm(self, tool, args_without_confirm):
        server, _ = _make_server_with_domain_active("timeline_operations")
        result = _run(server._dispatch_tool(tool, args_without_confirm))
        assert "DESTRUCTIVE" in str(result) or "confirm" in str(result).lower()
