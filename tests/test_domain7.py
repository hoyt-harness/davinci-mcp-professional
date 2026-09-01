# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 7: Render & Delivery.

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


# ---------------------------------------------------------------------------
# Domain 7 dispatch table
# Each row: (tool_name, client_method, mcp_args, expected_call_args)
# ---------------------------------------------------------------------------

_RD_DISPATCH: list[tuple] = [
    # --- render format / codec queries ---
    ("get_render_formats", "get_render_formats", {}, ()),
    ("get_render_codecs", "get_render_codecs", {"render_format": "MP4"}, ("MP4",)),
    (
        "get_render_resolutions",
        "get_render_resolutions",
        {"render_format": "MP4", "codec": "H.264"},
        ("MP4", "H.264"),
    ),
    ("get_current_render_format", "get_current_render_format", {}, ()),
    (
        "set_render_format_and_codec",
        "set_render_format_and_codec",
        {"render_format": "MP4", "codec": "H.264"},
        ("MP4", "H.264"),
    ),
    ("get_render_mode", "get_render_mode", {}, ()),
    ("set_render_mode", "set_render_mode", {"render_mode": 1}, (1,)),
    # --- render settings / presets ---
    (
        "set_render_settings",
        "set_render_settings",
        {"settings": {"width": 1920}},
        ({"width": 1920},),
    ),
    ("get_render_preset_list", "get_render_preset_list", {}, ()),
    (
        "load_render_preset",
        "load_render_preset",
        {"preset_name": "YouTube"},
        ("YouTube",),
    ),
    (
        "save_render_preset",
        "save_render_preset",
        {"preset_name": "MyPreset"},
        ("MyPreset",),
    ),
    ("get_quick_export_presets", "get_quick_export_presets", {}, ()),
    (
        "render_with_quick_export",
        "render_with_quick_export",
        {"preset_name": "YouTube", "params": {}},
        ("YouTube", {}),
    ),
    # --- render job management ---
    ("add_render_job", "add_render_job", {}, ()),
    ("get_render_job_list", "get_render_job_list", {}, ()),
    (
        "get_render_job_status",
        "get_render_job_status",
        {"job_id": "abc123"},
        ("abc123",),
    ),
    (
        "start_rendering",
        "start_rendering",
        {"job_ids": ["abc123"], "interactive": False},
        (["abc123"], False),
    ),
    ("stop_rendering", "stop_rendering", {}, ()),
    ("is_rendering_in_progress", "is_rendering_in_progress", {}, ()),
    # --- project settings ---
    (
        "get_project_setting",
        "get_project_setting",
        {"setting_name": "timelineFrameRate"},
        ("timelineFrameRate",),
    ),
    (
        "set_project_setting",
        "set_project_setting",
        {"setting_name": "timelineFrameRate", "setting_value": "24"},
        ("timelineFrameRate", "24"),
    ),
    # --- burn-in ---
    ("get_burn_in_preset_list", "get_burn_in_preset_list", {}, ()),
    (
        "load_project_burn_in_preset",
        "load_project_burn_in_preset",
        {"preset_name": "Default"},
        ("Default",),
    ),
]

# Destructive tools (require confirm=true)
_RD_DESTRUCTIVE: list[tuple] = [
    (
        "delete_render_preset",
        "delete_render_preset",
        {"preset_name": "MyPreset", "confirm": True},
        ("MyPreset",),
    ),
    (
        "delete_render_job",
        "delete_render_job",
        {"job_id": "abc123", "confirm": True},
        ("abc123",),
    ),
    ("delete_all_render_jobs", "delete_all_render_jobs", {"confirm": True}, ()),
]


class TestDomain7Dispatch:
    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _RD_DISPATCH,
        ids=[r[0] for r in _RD_DISPATCH],
    )
    def test_dispatches_to_client(self, tool_name, client_method, mcp_args, call_args):
        server, mock_client = _make_server_with_domain_active("render_delivery")
        domain = DOMAIN_REGISTRY["render_delivery"]
        _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,client_method,mcp_args,call_args",
        _RD_DESTRUCTIVE,
        ids=[r[0] for r in _RD_DESTRUCTIVE],
    )
    def test_destructive_dispatches_with_confirm(
        self, tool_name, client_method, mcp_args, call_args
    ):
        server, mock_client = _make_server_with_domain_active("render_delivery")
        domain = DOMAIN_REGISTRY["render_delivery"]
        _run(domain.dispatch(tool_name, mcp_args, mock_client))
        method = getattr(mock_client, client_method)
        method.assert_called_once()
        if call_args:
            method.assert_called_once_with(*call_args)

    @pytest.mark.parametrize(
        "tool_name,mcp_args",
        [
            (r[0], {k: v for k, v in r[2].items() if k != "confirm"})
            for r in _RD_DESTRUCTIVE
        ],
        ids=[r[0] for r in _RD_DESTRUCTIVE],
    )
    def test_destructive_blocked_without_confirm(self, tool_name, mcp_args):
        server, mock_client = _make_server_with_domain_active("render_delivery")
        domain = DOMAIN_REGISTRY["render_delivery"]
        result = _run(domain.dispatch(tool_name, mcp_args, mock_client))
        assert "DESTRUCTIVE" in str(result)
