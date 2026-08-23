# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parametrized dispatch tests for Domain 1: Project Management.

One row per tool. Tests verify that the domain correctly dispatches
each tool call to the expected DaVinciResolveClient method with the
expected arguments. DaVinciResolveClient is the mock boundary.

Written before implementation (Article VIII). All tests should fail
at the end of this file's creation and pass after implementation.
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from davinci_mcp.domains.registry import DOMAIN_REGISTRY
from davinci_mcp.server import DaVinciMCPServer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
    """Return (server, mock_client) with the named domain activated."""
    mock_client = _make_mock_client()
    with patch("davinci_mcp.server.DaVinciResolveClient", return_value=mock_client):
        server = DaVinciMCPServer()
    with _mock_request_ctx():
        _run(server._activate_domain(domain_name))
    return server, mock_client


# ---------------------------------------------------------------------------
# Domain 1 dispatch table
# Each row: (tool_name, client_method, mcp_args, expected_call_args)
# expected_call_args is what the client method should be called with.
# Use None to skip call-args assertion (return-value tools).
# ---------------------------------------------------------------------------

_PM_DISPATCH: list[tuple] = [
    # --- original migrated tools ---
    ("list_projects",       "list_projects",            {},                         ()),
    ("get_current_project", "get_current_project_name", {},                         ()),
    ("open_project",        "open_project",             {"name": "MyProj"},         ("MyProj",)),
    ("create_project",      "create_project",           {"name": "NewProj"},        ("NewProj",)),
    # --- new project tools ---
    ("save_project",        "save_project",             {},                         ()),
    ("rename_project",      "rename_project",           {"new_name": "Renamed"},    ("Renamed",)),
    ("get_project_attributes", "get_project_attributes", {},                        ()),
    # --- folder navigation ---
    ("list_project_folders",    "list_project_folders",    {},                      ()),
    ("get_current_project_folder", "get_current_project_folder", {},               ()),
    ("create_project_folder",   "create_project_folder",   {"folder_name": "Bin"}, ("Bin",)),
    ("open_project_folder",     "open_project_folder",     {"folder_name": "Bin"}, ("Bin",)),
    ("goto_root_folder",        "goto_root_folder",        {},                      ()),
    ("goto_parent_folder",      "goto_parent_folder",      {},                      ()),
    # --- archive / export / import ---
    ("export_project",  "export_project",
     {"name": "P", "file_path": "/out/p.drp", "with_stills_and_luts": False},
     ("P", "/out/p.drp", False)),
    ("import_project",  "import_project",
     {"file_path": "/in/p.drp", "project_name": "Imported"},
     ("/in/p.drp", "Imported")),
    ("restore_project", "restore_project",
     {"file_path": "/in/p.dra", "project_name": "Restored", "confirm": True},
     ("/in/p.dra", "Restored")),
    # --- databases ---
    ("list_databases",      "list_databases",      {},                                        ()),
    ("get_current_database","get_current_database",{},                                        ()),
    ("set_current_database","set_current_database",
     {"db_info": {"DbType": "Disk", "DbName": "Local"}, "confirm": True},
     ({"DbType": "Disk", "DbName": "Local"},)),
]

# Destructive tools require confirm=True; table rows use it directly.
# The negative case (missing confirm) is tested in TestDestructiveGate.
_PM_DESTRUCTIVE: list[tuple] = [
    ("close_project",         "close_project",         {"confirm": True},                    ()),
    ("delete_project",        "delete_project",        {"name": "OldProj", "confirm": True}, ("OldProj",)),
    ("delete_project_folder", "delete_project_folder", {"folder_name": "Bin", "confirm": True}, ("Bin",)),
    ("archive_project",       "archive_project",
     {"name": "P", "file_path": "/arc/p.dra",
      "src_media": True, "render_cache": False, "proxy_media": False, "confirm": True},
     ("P", "/arc/p.dra", True, False, False)),
]


# ---------------------------------------------------------------------------
# Dispatch tests
# ---------------------------------------------------------------------------


class TestDomain1Dispatch:
    @pytest.mark.parametrize("tool,method,args,call_args",
                             _PM_DISPATCH + _PM_DESTRUCTIVE)
    def test_dispatches_to_client(self, tool, method, args, call_args):
        server, client = _make_server_with_domain_active("project_management")
        getattr(client, method).return_value = True

        result = _run(server._dispatch_tool(tool, args))

        # Should not be an "Unknown tool" or "activate_domain" error
        assert "Unknown tool" not in str(result)
        assert "activate_domain" not in str(result)

        if call_args is not None:
            getattr(client, method).assert_called_once_with(*call_args)


# ---------------------------------------------------------------------------
# Destructive gate tests (confirm missing / false → rejection message)
# ---------------------------------------------------------------------------


class TestDestructiveGate:
    @pytest.mark.parametrize("tool,args_without_confirm", [
        ("close_project",         {}),
        ("close_project",         {"confirm": False}),
        ("delete_project",        {"name": "P"}),
        ("delete_project",        {"name": "P", "confirm": False}),
        ("delete_project_folder", {"folder_name": "Bin"}),
        ("archive_project",       {"name": "P", "file_path": "/f",
                                   "src_media": True, "render_cache": False, "proxy_media": False}),
        ("restore_project",       {"file_path": "/f", "project_name": "R"}),
        ("set_current_database",  {"db_info": {"DbType": "Disk", "DbName": "L"}}),
    ])
    def test_destructive_rejected_without_confirm(self, tool, args_without_confirm):
        server, _ = _make_server_with_domain_active("project_management")
        result = _run(server._dispatch_tool(tool, args_without_confirm))
        result_str = str(result)
        assert "DESTRUCTIVE" in result_str or "confirm" in result_str.lower()
