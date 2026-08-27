# SPDX-License-Identifier: GPL-3.0-or-later
"""
Unit tests for the kernel activation architecture.

Tests are written before implementation (Phase 1 of the spec). They must all
fail (ImportError or assertion failure) at the end of Phase 1 and pass green
by the end of Phase 4.

Mock boundary: DaVinciResolveClient + request_ctx contextvar.
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import mcp.types as types

from davinci_mcp.domains.registry import DOMAIN_REGISTRY, DomainModule
from davinci_mcp.server import DaVinciMCPServer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_client() -> MagicMock:
    """Return a mock DaVinciResolveClient that is always connected."""
    client = MagicMock()
    client.is_connected.return_value = True
    return client


def _make_mock_domain(name: str, tool_names: list[str]) -> MagicMock:
    """Return a mock DomainModule with the given tool names."""
    domain = MagicMock(spec=DomainModule)
    domain.name = name
    domain.description = f"Mock domain: {name}"
    domain.get_tools.return_value = [
        types.Tool(
            name=t,
            description=f"Tool {t}",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )
        for t in tool_names
    ]
    domain.dispatch = AsyncMock(return_value=f"dispatched:{name}")
    return domain


@contextmanager
def _mock_request_ctx(mock_session: AsyncMock):
    """Inject a mock request context into the MCP contextvar."""
    from mcp.server.lowlevel.server import request_ctx

    mock_ctx = MagicMock()
    mock_ctx.session = mock_session
    token = request_ctx.set(mock_ctx)
    try:
        yield
    finally:
        request_ctx.reset(token)


def _run(coro: Any) -> Any:
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# 1a — Domain registry
# ---------------------------------------------------------------------------


class TestDomainRegistry:
    def test_registry_is_a_dict(self) -> None:
        assert isinstance(DOMAIN_REGISTRY, dict)

    def test_registry_entries_implement_protocol(self) -> None:
        """Every entry in DOMAIN_REGISTRY must satisfy DomainModule."""
        assert len(DOMAIN_REGISTRY) > 0, "DOMAIN_REGISTRY is empty — Phase 2 not done"
        for name, domain in DOMAIN_REGISTRY.items():
            assert isinstance(domain, DomainModule), (
                f"Domain '{name}' does not satisfy DomainModule protocol"
            )
            assert hasattr(domain, "name")
            assert hasattr(domain, "description")
            assert callable(domain.get_tools)
            assert callable(domain.dispatch)


# ---------------------------------------------------------------------------
# 1b — Tool list composition
# ---------------------------------------------------------------------------


class TestToolListComposition:
    def _server_with_mock_client(self) -> DaVinciMCPServer:
        with patch(
            "davinci_mcp.server.DaVinciResolveClient", return_value=_make_mock_client()
        ):
            return DaVinciMCPServer()

    def test_initial_tool_list_is_kernel_only(self) -> None:
        server = self._server_with_mock_client()
        tools = _run(server._handle_list_tools())
        names = {t.name for t in tools}
        kernel = {
            "activate_domain",
            "deactivate_domain",
            "list_domains",
            "get_version",
            "get_current_page",
            "switch_page",
        }
        assert names == kernel, f"Expected kernel only, got: {names}"

    def test_tool_list_after_activation_adds_domain_tools(self) -> None:
        server = self._server_with_mock_client()
        domain = _make_mock_domain("test_domain", ["tool_a", "tool_b"])

        with patch.dict(DOMAIN_REGISTRY, {"test_domain": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("test_domain"))

            tools = _run(server._handle_list_tools())
            names = {t.name for t in tools}
            assert "tool_a" in names
            assert "tool_b" in names
            assert "activate_domain" in names

    def test_tool_list_after_deactivation_contracts(self) -> None:
        server = self._server_with_mock_client()
        domain = _make_mock_domain("test_domain", ["tool_a", "tool_b"])

        with patch.dict(DOMAIN_REGISTRY, {"test_domain": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("test_domain"))
                _run(server._deactivate_domain("test_domain"))

            tools = _run(server._handle_list_tools())
            names = {t.name for t in tools}
            assert "tool_a" not in names
            assert "tool_b" not in names

    def test_tool_list_two_domains_active(self) -> None:
        server = self._server_with_mock_client()
        domain_a = _make_mock_domain("domain_a", ["tool_a"])
        domain_b = _make_mock_domain("domain_b", ["tool_b"])

        with patch.dict(DOMAIN_REGISTRY, {"domain_a": domain_a, "domain_b": domain_b}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("domain_a"))
                _run(server._activate_domain("domain_b"))

            tools = _run(server._handle_list_tools())
            names = [t.name for t in tools]
            assert "tool_a" in names
            assert "tool_b" in names
            # No duplicates
            assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# 1c — Activation flow
# ---------------------------------------------------------------------------


class TestActivationFlow:
    def _server(self) -> DaVinciMCPServer:
        with patch(
            "davinci_mcp.server.DaVinciResolveClient", return_value=_make_mock_client()
        ):
            return DaVinciMCPServer()

    def test_activate_known_domain_returns_status(self) -> None:
        server = self._server()
        domain = _make_mock_domain("pm", ["list_projects"])

        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                result = _run(server._activate_domain("pm"))

        assert result["status"] == "activated"
        assert result["domain"] == "pm"
        assert "list_projects" in result["tools_added"]

    def test_activate_already_active_returns_already_active(self) -> None:
        server = self._server()
        domain = _make_mock_domain("pm", ["list_projects"])

        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("pm"))
                result = _run(server._activate_domain("pm"))

        assert result["status"] == "already_active"

    def test_activate_unknown_domain_returns_error(self) -> None:
        server = self._server()
        result = _run(server._activate_domain("no_such_domain"))
        assert "error" in result
        assert "no_such_domain" in result["error"]

    def test_deactivate_active_domain(self) -> None:
        server = self._server()
        domain = _make_mock_domain("pm", ["list_projects"])

        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("pm"))
                result = _run(server._deactivate_domain("pm"))

        assert result["status"] == "deactivated"
        assert "pm" not in server._active_domains

    def test_deactivate_inactive_domain_returns_error(self) -> None:
        server = self._server()
        result = _run(server._deactivate_domain("pm"))
        assert "error" in result


# ---------------------------------------------------------------------------
# 1d — Notification firing
# ---------------------------------------------------------------------------


class TestNotificationFiring:
    def _server(self) -> DaVinciMCPServer:
        with patch(
            "davinci_mcp.server.DaVinciResolveClient", return_value=_make_mock_client()
        ):
            return DaVinciMCPServer()

    def test_activate_fires_notification(self) -> None:
        server = self._server()
        domain = _make_mock_domain("pm", ["list_projects"])

        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("pm"))

        mock_session.send_tool_list_changed.assert_called_once()

    def test_activate_already_active_does_not_fire_notification(self) -> None:
        server = self._server()
        domain = _make_mock_domain("pm", ["list_projects"])

        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("pm"))
                mock_session.reset_mock()
                _run(server._activate_domain("pm"))

        mock_session.send_tool_list_changed.assert_not_called()

    def test_deactivate_fires_notification(self) -> None:
        server = self._server()
        domain = _make_mock_domain("pm", ["list_projects"])

        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("pm"))
                mock_session.reset_mock()
                _run(server._deactivate_domain("pm"))

        mock_session.send_tool_list_changed.assert_called_once()


# ---------------------------------------------------------------------------
# 1e — Dispatch routing (FR-008 four cases)
# ---------------------------------------------------------------------------


class TestDispatchRouting:
    def _server(self) -> DaVinciMCPServer:
        with patch(
            "davinci_mcp.server.DaVinciResolveClient", return_value=_make_mock_client()
        ):
            return DaVinciMCPServer()

    def test_dispatch_kernel_tool(self) -> None:
        server = self._server()
        server.resolve_client.get_version.return_value = "18.0.0"
        result = _run(server._dispatch_tool("get_version", {}))
        assert result is not None

    def test_dispatch_active_domain_tool(self) -> None:
        server = self._server()
        domain = _make_mock_domain("pm", ["list_projects"])

        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}):
            mock_session = AsyncMock()
            with _mock_request_ctx(mock_session):
                _run(server._activate_domain("pm"))

            result = _run(server._dispatch_tool("list_projects", {}))

        domain.dispatch.assert_called_once_with(
            "list_projects", {}, server.resolve_client
        )
        assert result == "dispatched:pm"

    def test_dispatch_inactive_domain_tool_returns_helpful_error(self) -> None:
        domain = _make_mock_domain("pm", ["pm_only_tool"])
        with patch.dict(DOMAIN_REGISTRY, {"pm": domain}, clear=False):
            with patch(
                "davinci_mcp.server.DaVinciResolveClient",
                return_value=_make_mock_client(),
            ):
                server = DaVinciMCPServer()
            result = _run(server._dispatch_tool("pm_only_tool", {}))

        assert "pm" in result
        assert "activate_domain" in result

    def test_dispatch_unknown_tool_returns_error(self) -> None:
        server = self._server()
        result = _run(server._dispatch_tool("totally_unknown_tool", {}))
        assert "Unknown tool" in result or "unknown" in result.lower()


# ---------------------------------------------------------------------------
# 1f — Capability flag (static check)
# ---------------------------------------------------------------------------


class TestCapabilityFlag:
    def test_notification_options_tools_changed(self) -> None:
        """server.py must pass tools_changed=True to NotificationOptions."""
        import ast
        import pathlib

        src = pathlib.Path("src/davinci_mcp/server.py").read_text(encoding="utf-8")
        tree = ast.parse(src)

        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                func_name = (
                    func.attr
                    if isinstance(func, ast.Attribute)
                    else func.id
                    if isinstance(func, ast.Name)
                    else ""
                )
                if func_name == "NotificationOptions":
                    for kw in node.keywords:
                        if kw.arg == "tools_changed" and isinstance(
                            kw.value, ast.Constant
                        ):
                            if kw.value.value is True:
                                found = True
        assert found, (
            "NotificationOptions(tools_changed=True) not found in server.py. "
            "FR-006 requires this for the initialize response to advertise "
            "capabilities.tools.listChanged: true."
        )
