# Implementation Plan: MCP Python SDK v1 → v2 Migration

**Branch**: `002-mcp-v2-migration` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

## Summary

Mechanical migration from mcp 1.29.0 to mcp 2.x. Two areas of change:
(1) `server.py` — handler registration rewrite and ctx threading; (2) field
rename sweep across `tools/__init__.py` and all 9 domain modules. No behavior
change to the external protocol surface.

## Technical Context

**Current state**: `mcp>=1.10.0,<2.0.0`, locked at 1.29.0. Decorator-based
handler API. `request_ctx` contextvar for session access inside handlers.
`AnyUrl` for resource URI parameter. `inputSchema=` in all Tool definitions.

**Target state**: `mcp>=2.0.0,<3.0.0`, locked at 2.1.1. Constructor `on_*`
handler params. `ctx: ServerRequestContext` threaded through handlers for
session access. `params: ReadResourceRequestParams` with `params.uri` (str).
`input_schema=` in all Tool definitions.

**Unchanged**: `stdio_server()`, `server.run()`, `InitializationOptions`,
`NotificationOptions`, `send_tool_list_changed()` on session,
`DaVinciResolveClient`, all 9 domain `dispatch()` methods.

**Testing**: pytest; CI gate is `hooks/ci-check.sh`. Integration/live tests
require running Resolve — skip with `-m "not integration and not live"` for
the development loop.

## Phases

### Phase 1 — Dependency bump and lock

**Goal**: mcp 2.x resolves and installs cleanly before touching any source.

**Tasks**:

1. **T1.1** — Edit `pyproject.toml`: change `mcp>=1.10.0,<2.0.0` to
   `mcp>=2.0.0,<3.0.0`.
2. **T1.2** — Run `uv lock` to regenerate `uv.lock` against mcp 2.x.
   Resolve any transitive conflicts (pydantic floor ≥2.12, anyio floor ≥4.9,
   typing-extensions ≥4.13 are the known floor raises in mcp v2).
3. **T1.3** — Run `uv sync` to install the new environment.
4. **T1.4** — Smoke-test import: `uv run python -c "import mcp; print(mcp)"`.
   Expect success. Any `ModuleNotFoundError` here is a lock/sync issue, not a
   code issue.

**Gate**: `uv sync` succeeds, smoke import passes.

---

### Phase 2 — `server.py` rewrite

**Goal**: All five handler registrations converted to `on_*` constructor params;
`ctx` threaded to the two methods that call `send_tool_list_changed()`.

**Tasks**:

5. **T2.1** — Update imports in `server.py`:
   - Remove: `from mcp.server.lowlevel.server import request_ctx`
   - Remove: `from pydantic import AnyUrl`
   - Add: `from mcp.server import NotificationOptions, Server, ServerRequestContext`
   - Add from `mcp.types`: `CallToolRequestParams`, `CallToolResult`,
     `ListResourcesResult`, `ListResourceTemplatesResult`, `ListToolsResult`,
     `PaginatedRequestParams`, `ReadResourceRequestParams`, `ReadResourceResult`,
     `TextResourceContents`

6. **T2.2** — Add `ctx: ServerRequestContext` parameter to `_activate_domain`
   and `_deactivate_domain`. Replace:
   ```python
   await request_ctx.get().session.send_tool_list_changed()
   ```
   with:
   ```python
   await ctx.session.send_tool_list_changed()
   ```

7. **T2.3** — Add `ctx: ServerRequestContext` parameter to `_call_kernel_tool`
   and thread it into `_activate_domain` / `_deactivate_domain` calls.

8. **T2.4** — Add `ctx: ServerRequestContext` parameter to `_dispatch_tool`
   and thread it into `_call_kernel_tool` call.

9. **T2.5** — Rewrite `_register_handlers` into five standalone async handler
   functions and pass them to the `Server()` constructor:

   **`handle_list_tools`**:
   ```python
   async def handle_list_tools(
       ctx: ServerRequestContext,
       params: PaginatedRequestParams | None,
   ) -> ListToolsResult:
       return ListToolsResult(tools=await self._handle_list_tools())
   ```

   **`handle_call_tool`**:
   ```python
   async def handle_call_tool(
       ctx: ServerRequestContext,
       params: CallToolRequestParams,
   ) -> CallToolResult:
       arguments = params.arguments or {}
       try:
           ...connect logic...
           result = await self._dispatch_tool(ctx, params.name, arguments)
           return CallToolResult(content=[types.TextContent(type="text", text=str(result))])
       except DaVinciResolveError as e:
           ...
           return CallToolResult(content=[...], is_error=True)
       except Exception as e:
           ...
           return CallToolResult(content=[...], is_error=True)
   ```

   **`handle_list_resources`**:
   ```python
   async def handle_list_resources(
       ctx: ServerRequestContext,
       params: PaginatedRequestParams | None,
   ) -> ListResourcesResult:
       return ListResourcesResult(resources=get_all_resources())
   ```

   **`handle_list_resource_templates`**:
   ```python
   async def handle_list_resource_templates(
       ctx: ServerRequestContext,
       params: PaginatedRequestParams | None,
   ) -> ListResourceTemplatesResult:
       return ListResourceTemplatesResult(resource_templates=[])
   ```

   **`handle_read_resource`**:
   ```python
   async def handle_read_resource(
       ctx: ServerRequestContext,
       params: ReadResourceRequestParams,
   ) -> ReadResourceResult:
       uri = str(params.uri)
       try:
           ...connect...
           result = await self._read_resource(uri)
           return ReadResourceResult(
               contents=[TextResourceContents(uri=uri, text=str(result))]
           )
       except ...:
           return ReadResourceResult(
               contents=[TextResourceContents(uri=uri, text=error_msg)]
           )
   ```

10. **T2.6** — Replace `Server("davinci-resolve-mcp")` instantiation with:
    ```python
    self.server = Server(
        "davinci-resolve-mcp",
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
        on_list_resources=handle_list_resources,
        on_list_resource_templates=handle_list_resource_templates,
        on_read_resource=handle_read_resource,
    )
    ```
    Remove the `_register_handlers()` call from `__init__` and the method itself.

11. **T2.7** — Verify `run()` method. The `server.run(read_stream, write_stream,
    InitializationOptions(...))` call is unchanged per the migration guide —
    confirm it still compiles.

**Gate**: `uv run python -c "from davinci_mcp.server import DaVinciMCPServer"` exits 0.

---

### Phase 3 — Field rename sweep

**Goal**: Every `inputSchema=` in Tool definitions renamed to `input_schema=`.

**Tasks**:

12. **T3.1** — `src/davinci_mcp/tools/__init__.py`: rename all `inputSchema=`
    occurrences to `input_schema=`.

13. **T3.2** — `src/davinci_mcp/domains/project_management.py`: same.
14. **T3.3** — `src/davinci_mcp/domains/timeline_operations.py`: same.
15. **T3.4** — `src/davinci_mcp/domains/media_pool.py`: same.
16. **T3.5** — `src/davinci_mcp/domains/clip_properties.py`: same.
17. **T3.6** — `src/davinci_mcp/domains/timeline_item_editing.py`: same.
18. **T3.7** — `src/davinci_mcp/domains/color_grading.py`: same.
19. **T3.8** — `src/davinci_mcp/domains/render_delivery.py`: same.
20. **T3.9** — `src/davinci_mcp/domains/ai_studio.py`: same.
21. **T3.10** — `src/davinci_mcp/domains/system_fairlight_storage.py`: same.

**Note**: These are pure text replacements. Use ruff after the sweep to confirm
no stray `inputSchema` references remain (`ruff check` will not catch this, but
`grep -r "inputSchema" src/` will).

**Gate**: `grep -r "inputSchema" src/` returns empty.

---

### Phase 4 — Test suite update and CI

**Goal**: All non-integration tests green; type checkers and linter clean.

**Tasks**:

22. **T4.1** — Search tests for any mock of `request_ctx` or old handler
    signatures. Update to new shape. (Expected: minimal changes — existing tests
    mock `DaVinciResolveClient`, not the MCP layer.)

23. **T4.2** — Run `uv run pytest -m "not integration and not live" -v`.
    Fix any failures.

24. **T4.3** — Run `uv run pyright && uv run mypy src/`. Fix any new type
    errors (expected: mostly new import names, possibly `ctx` threading).

25. **T4.4** — Run `uv run ruff check src/ tests/`. Fix any lint issues.

26. **T4.5** — Run `hooks/ci-check.sh` end-to-end. Must pass green.

**Gate**: `hooks/ci-check.sh` exits 0.

---

### Phase 5 — Live verification

**Goal**: Confirm protocol behavior is identical to pre-migration with a live
Resolve + MCP Inspector session.

**Tasks**:

27. **T5.1** — Start DaVinci Resolve. Start the MCP server.
28. **T5.2** — Connect MCP Inspector. Verify 6 kernel tools visible.
29. **T5.3** — Call `activate_domain("project_management")`. Verify
    `notifications/tools/list_changed` fires and tool list expands.
30. **T5.4** — Call `deactivate_domain("project_management")`. Verify contraction.
31. **T5.5** — Read one resource (e.g. `resolve://version`). Verify correct value.

**Gate**: All 5 verification steps pass. No regression from pre-migration behavior.

---

## Commit Strategy

Single signed commit per phase that passes its gate:

| Phase | Commit message |
|-------|---------------|
| 1 | `chore: bump mcp dependency to >=2.0.0,<3.0.0` |
| 2 | `feat: migrate server.py to mcp v2 on_* handler API` |
| 3 | `fix: rename inputSchema → input_schema across all Tool definitions` |
| 4 | `test: update tests and fix type/lint issues for mcp v2` |
| Post-live | `chore: release v4.1.0 — mcp v2 migration` |

Version bump: **MINOR** (v4.0.2 → v4.1.0). No breaking change to the external
protocol surface; mcp v2 is an internal dependency upgrade. Callers (Claude
Desktop, Cursor, MCP Inspector) see identical tool lists and behavior.
