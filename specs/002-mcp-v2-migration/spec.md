# Specification: MCP Python SDK v1 → v2 Migration

**Feature branch**: `002-mcp-v2-migration`

**Created**: 2026-08-31

**Status**: Draft

**Reference**: [MCP Python SDK v1→v2 Migration Guide](https://py.sdk.modelcontextprotocol.io/migration/)
Local copy: `D:\Engineering\_MCP-Tools-Dev\python-sdk\docs\migration.md`

---

## Overview

Migrate `davinci-mcp-professional` from `mcp>=1.10.0,<2.0.0` (locked at
1.29.0) to `mcp>=2.0.0,<3.0.0` (latest: 2.1.1). The mcp v2 SDK introduces
breaking changes to the lowlevel `Server` API — specifically decorator-based
handler registration, handler signatures, return types, and the removal of the
`request_ctx` contextvar. No user-facing behavior changes. The server's
external protocol surface (tools, resources, notifications) remains identical.

This is a mechanical migration. All changes follow directly from the migration
guide. No architectural decisions remain open.

---

## Scope

### In scope

- `pyproject.toml` — bump `mcp` dependency ceiling
- `src/davinci_mcp/server.py` — rewrite handler registration and signatures
- `src/davinci_mcp/tools/__init__.py` — rename `inputSchema` → `input_schema`
- `src/davinci_mcp/domains/*.py` (all 9) — rename `inputSchema` → `input_schema`
- `uv.lock` — regenerated automatically
- Tests — update any mocks that reference `request_ctx` or old handler shapes

### Out of scope

- Protocol behavior changes (tool list, resources, notifications unchanged)
- New tools or domains
- PyInstaller build (follows this migration as a separate release step)
- `doxygen-mcp` migration (separate session)

---

## Breaking Changes Being Addressed

### BC-1: Decorator handlers → constructor `on_*` params

**Before (v1):**
```python
server = Server("davinci-resolve-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [...]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    return [...]
```

**After (v2):**
```python
async def handle_list_tools(ctx: ServerRequestContext, params: PaginatedRequestParams | None) -> ListToolsResult:
    return ListToolsResult(tools=[...])

async def handle_call_tool(ctx: ServerRequestContext, params: CallToolRequestParams) -> CallToolResult:
    return CallToolResult(content=[...])

server = Server(
    "davinci-resolve-mcp",
    on_list_tools=handle_list_tools,
    on_call_tool=handle_call_tool,
    ...
)
```

Affected handlers: `on_list_tools`, `on_call_tool`, `on_list_resources`,
`on_list_resource_templates`, `on_read_resource`.

### BC-2: `request_ctx` removed; context threaded via handler `ctx`

**Before (v1):**
```python
from mcp.server.lowlevel.server import request_ctx
# inside a handler:
await request_ctx.get().session.send_tool_list_changed()
```

**After (v2):**
`request_ctx` is removed entirely. The `ctx: ServerRequestContext` parameter
passed to every `on_*` handler carries `ctx.session`. Methods that need to send
notifications (`_activate_domain`, `_deactivate_domain`) must receive `ctx` as
a parameter threaded down from the handler.

```python
async def _activate_domain(self, ctx: ServerRequestContext, domain_name: str) -> dict:
    ...
    await ctx.session.send_tool_list_changed()
```

`send_tool_list_changed()` itself is unchanged on the session object.

### BC-3: Return value wrapping removed

Handlers must now return fully-constructed result types:

| Handler | v1 return | v2 return |
|---------|-----------|-----------|
| `on_list_tools` | `list[Tool]` | `ListToolsResult(tools=[...])` |
| `on_call_tool` | `list[TextContent]` | `CallToolResult(content=[...], is_error=False)` |
| `on_list_resources` | `list[Resource]` | `ListResourcesResult(resources=[...])` |
| `on_list_resource_templates` | `list[ResourceTemplate]` | `ListResourceTemplatesResult(resource_templates=[...])` |
| `on_read_resource` | `str` | `ReadResourceResult(contents=[TextResourceContents(...)])` |

### BC-4: `inputSchema` → `input_schema` (camelCase → snake_case)

All `types.Tool(...)` calls across `tools/__init__.py` and all 9 domain modules
must rename the `inputSchema=` kwarg to `input_schema=`. This is a wire-format
change handled by Pydantic aliases; the Python field is now snake_case.

### BC-5: `AnyUrl` → `str` for resource URIs

The `on_read_resource` handler signature changes: `uri: AnyUrl` → `params:
ReadResourceRequestParams`; the URI is accessed as `str(params.uri)`.

---

## Acceptance Criteria

### AC-1: Dependency

- `pyproject.toml` specifies `mcp>=2.0.0,<3.0.0`
- `uv lock` resolves cleanly to mcp 2.1.1 (or latest 2.x)
- `uv sync` installs without conflict

### AC-2: Import health

```bash
uv run python -c "from davinci_mcp.server import DaVinciMCPServer; print('OK')"
```
Exits 0 with no deprecation warnings related to mcp.

### AC-3: Test suite

```bash
uv run pytest -m "not integration and not live"
```
All non-integration tests pass. No new skips introduced.

### AC-4: Type checking

```bash
uv run pyright
uv run mypy src/
```
No new type errors introduced by the migration.

### AC-5: Lint

```bash
uv run ruff check src/ tests/
```
Clean (0 errors).

### AC-6: Live protocol verification (manual)

Start the server and connect MCP Inspector:
- `list_domains` returns 9 domains (kernel tool visible)
- `activate_domain("project_management")` fires `notifications/tools/list_changed`
- Tool list expands correctly after activation
- `deactivate_domain("project_management")` fires `notifications/tools/list_changed`
- Tool list contracts correctly

### AC-7: CI gate

`hooks/ci-check.sh` passes green (runs ruff, pyright, pytest).

---

## What Does Not Change

- All tool names, descriptions, and schemas (user-visible)
- Resource URIs and their return values
- `notifications/tools/list_changed` behavior
- `DaVinciResolveClient` — no changes
- All domain dispatch logic (`dispatch()` methods)
- `cli.py` entry point
- `resolve_client.py`, `types.py`, `utils/`
- `InitializationOptions`, `NotificationOptions`, `stdio_server()` — all
  import paths survive in mcp v2 unchanged
