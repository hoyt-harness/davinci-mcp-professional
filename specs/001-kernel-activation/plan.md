# Implementation Plan: Kernel Activation

**Branch**: `001-kernel-activation` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

## Summary

Restructure the server from a flat 13-tool list into a kernel + domain
architecture. Six kernel tools are always present; domain tools register
dynamically via `activate_domain`, which fires `notifications/tools/list_changed`
so Claude Code auto-refetches. The three domains that cover the existing 13 tools
(project management, timeline operations, media pool) are implemented in this
branch. Domains 4–9 follow in separate domain specs.

## Technical Context

**Language/version**: Python 3.14.7 (venv) — but venv artifacts show 3.13 ABI;
verify before the first `uv run` if anything behaves unexpectedly.

**MCP SDK**: mcp 1.29.0 (`<2.0.0` ceiling in `pyproject.toml`). Decorator-based
handler API. Session accessed via `request_ctx` contextvar
(`from mcp.server.lowlevel.server import request_ctx`).

**Notification path**: `await request_ctx.get().session.send_tool_list_changed()`
inside a `@self.server.call_tool()` handler.

**Testing**: pytest; existing tests in `tests/test_security.py`. New unit tests
go in `tests/test_kernel.py`. Mock boundary: `DaVinciResolveClient` (already
established) + `request_ctx` (new — set via `contextvars` in test setup).
`@pytest.mark.live` excludes tests requiring a running Resolve instance from CI.

**CI gate**: `hooks/ci-check.sh` (ruff, pyright, pytest). Must pass green before
any commit leaves this branch.

## Constitution Check

| Article | Principle | Gate | Status |
|---------|-----------|------|--------|
| I | Typed-activation model | Kernel is fixed; domain tools only after `activate_domain` | ✓ |
| II | Domain modules | Each domain independent; no cross-domain deps | ✓ |
| III | Python-native API | `DaVinciResolveClient` unchanged; domain modules call it | ✓ |
| IV | Stateless request handling | `_active_domains` / routing tables are server state, not Resolve object refs | ✓ |
| V | Object reference scheme | Domain modules inherit existing resolve_client conventions | ✓ |
| VI | Error taxonomy | All four exception types caught; domains propagate to server | ✓ |
| VII | One tool, one concern | Each kernel tool has one job; domain tools unchanged | ✓ |
| VIII | Test-first | Tests written and failing before implementation (enforced in tasks) | gate |
| IX | Simplicity | Registry is a plain dict; no config files, no plugin loading | ✓ |

**Simplicity gate**: Adding a `domains/` package is the minimum structural change
that satisfies the spec. No abstraction layers beyond the Protocol. ✓

## Phase 0 — Scaffolding (imports compile; no logic yet)

Create the `domains/` package with the Protocol and an empty registry. This
makes the test imports work before any implementation exists.

**Files created:**
- `src/davinci_mcp/domains/__init__.py` — package init, exports Protocol
- `src/davinci_mcp/domains/registry.py` — `DomainModule` Protocol +
  `DOMAIN_REGISTRY: dict[str, DomainModule] = {}` (empty until Phase 2)

**Acceptance**: `python -c "from davinci_mcp.domains.registry import DOMAIN_REGISTRY"` exits 0.

## Phase 1 — Tests (written before implementation; all fail)

Write `tests/test_kernel.py`. All test cases import from modules that either
don't exist yet or have stub behavior — they must fail at the end of this phase.

**Test groups:**

### 1a — Domain registry
- `test_registry_empty_at_import` — DOMAIN_REGISTRY is a dict
- `test_registry_entries_implement_protocol` — each entry has `name`,
  `description`, `get_tools()`, `dispatch()` (fails until Phase 2 populates it)

### 1b — Tool list composition
- `test_initial_tool_list_is_kernel_only` — 6 tools returned before any activation
- `test_tool_list_after_activation_adds_domain_tools` — kernel + domain tools
- `test_tool_list_after_deactivation_contracts` — domain tools absent after deactivate
- `test_tool_list_two_domains_active` — kernel + A tools + B tools, no duplicates

### 1c — Activation flow
- `test_activate_known_domain_returns_status` — status dict with `tools_added`
- `test_activate_already_active_returns_already_active` — no notification fired
- `test_activate_unknown_domain_returns_error` — error message, no exception raised
- `test_deactivate_active_domain` — domain removed, notification fired
- `test_deactivate_inactive_domain_returns_error`

### 1d — Notification firing
Uses `request_ctx` contextvar with a mock session:
```python
mock_session = AsyncMock()
mock_ctx = MagicMock(session=mock_session)
token = request_ctx.set(mock_ctx)
# ... call activate_domain ...
mock_session.send_tool_list_changed.assert_called_once()
request_ctx.reset(token)
```
- `test_activate_fires_notification`
- `test_activate_already_active_does_not_fire_notification`
- `test_deactivate_fires_notification`

### 1e — Dispatch routing (FR-008 four cases)
- `test_dispatch_kernel_tool` — `get_version` handled inline
- `test_dispatch_active_domain_tool` — routed to domain dispatch
- `test_dispatch_inactive_domain_tool_returns_helpful_error` — names the domain
- `test_dispatch_unknown_tool_returns_error`

### 1f — Capability flag (static check)
- `test_notification_options_tools_changed` — `NotificationOptions(tools_changed=True)`
  is set in the server's capabilities call (inspect the `InitializationOptions`
  constructed in `server.run`)

**Acceptance**: All tests collected; all fail (ImportError or assertion failure).
No test passes at the end of Phase 1.

## Phase 2 — Domain modules

Implement the three domain modules and populate `DOMAIN_REGISTRY`. The logic
is cut from existing `resolve_client.py` methods with no behavior change.

**Files created:**
- `src/davinci_mcp/domains/project_management.py`
  - `ProjectManagementDomain` implements `DomainModule`
  - `get_tools()` returns the 4 project tool definitions (from current `tools/__init__.py`)
  - `dispatch()` handles: `list_projects`, `get_current_project`, `open_project`,
    `create_project` — delegates to `client.list_projects()`, etc.
- `src/davinci_mcp/domains/timeline_operations.py`
  - `TimelineOperationsDomain` implements `DomainModule`
  - 4 timeline tools: `list_timelines`, `get_current_timeline`, `create_timeline`,
    `switch_timeline`
- `src/davinci_mcp/domains/media_pool.py`
  - `MediaPoolDomain` implements `DomainModule`
  - 2 media tools: `list_media_clips`, `import_media`

**Update `registry.py`**:
```python
DOMAIN_REGISTRY: dict[str, DomainModule] = {
    "project_management": ProjectManagementDomain(),
    "timeline_operations": TimelineOperationsDomain(),
    "media_pool": MediaPoolDomain(),
}
```

**Acceptance**: `test_registry_entries_implement_protocol` passes.

## Phase 3 — Kernel tool definitions

Rewrite `src/davinci_mcp/tools/__init__.py` to contain only the 6 kernel tools.
The 10 migrated tool definitions are now in the domain modules.

**Kernel tools defined here:**
- `activate_domain` — `domain: str` (required); description lists valid domain names
- `deactivate_domain` — `domain: str` (required)
- `list_domains` — no parameters
- `get_version` — no parameters (retained from current)
- `get_current_page` — no parameters (retained)
- `switch_page` — `page: str`, enum (retained)

**Acceptance**: `test_initial_tool_list_is_kernel_only` passes (6 tools).

## Phase 4 — Server refactor

Modify `src/davinci_mcp/server.py`. This is the only file that changes in the
server package.

**Changes in `DaVinciMCPServer.__init__`:**
- Add `self._active_domains: dict[str, DomainModule] = {}`
- Add `self._tool_to_domain: dict[str, str] = {}`
- Add `self._inactive_tool_to_domain: dict[str, str] = {}`
- Call `self._rebuild_routing_tables()` at end of `__init__`

**New method `_rebuild_routing_tables()`:**
```python
def _rebuild_routing_tables(self) -> None:
    self._tool_to_domain = {
        tool.name: domain_name
        for domain_name, domain in self._active_domains.items()
        for tool in domain.get_tools()
    }
    self._inactive_tool_to_domain = {
        tool.name: domain_name
        for domain_name, domain in DOMAIN_REGISTRY.items()
        if domain_name not in self._active_domains
        for tool in domain.get_tools()
    }
```

**Update `handle_list_tools`:**
```python
return get_all_tools() + [
    tool
    for domain in self._active_domains.values()
    for tool in domain.get_tools()
]
```

**Update `handle_call_tool` — 4-case dispatch (FR-008):**
```python
KERNEL_TOOLS = {"activate_domain", "deactivate_domain", "list_domains",
                "get_version", "get_current_page", "switch_page"}

if name in KERNEL_TOOLS:
    result = await self._call_kernel_tool(name, arguments)
elif name in self._tool_to_domain:
    domain = self._active_domains[self._tool_to_domain[name]]
    result = await domain.dispatch(name, arguments, self.resolve_client)
elif name in self._inactive_tool_to_domain:
    domain_name = self._inactive_tool_to_domain[name]
    result = (f"Tool '{name}' is in domain '{domain_name}'. "
              f"Call activate_domain('{domain_name}') first.")
else:
    result = f"Unknown tool: {name}"
```

**New method `_call_kernel_tool`:**
Moves the existing `get_version`, `get_current_page`, `switch_page` dispatch here.
Adds `activate_domain`, `deactivate_domain`, `list_domains` handling.

`activate_domain` handler (inside `_call_kernel_tool`):
```python
if domain_name not in DOMAIN_REGISTRY:
    return {"error": f"Unknown domain: '{domain_name}'. "
                     f"Available: {list(DOMAIN_REGISTRY)}"}
if domain_name in self._active_domains:
    return {"status": "already_active", "domain": domain_name}
self._active_domains[domain_name] = DOMAIN_REGISTRY[domain_name]
self._rebuild_routing_tables()
await request_ctx.get().session.send_tool_list_changed()
return {
    "status": "activated",
    "domain": domain_name,
    "tools_added": [t.name for t in DOMAIN_REGISTRY[domain_name].get_tools()],
}
```

**Fix capability flag:**
```python
# server.py:182 (in run())
capabilities=self.server.get_capabilities(
    notification_options=NotificationOptions(tools_changed=True),
    experimental_capabilities={},
),
```

**Imports to add:**
```python
from mcp.server.lowlevel.server import request_ctx
from .domains.registry import DOMAIN_REGISTRY, DomainModule
```

**Acceptance**: All Phase 1 test groups pass.

## Phase 5 — CI

```bash
hooks/ci-check.sh
```

Resolve any ruff or pyright findings. Common expected findings:
- pyright may flag `request_ctx.get()` return type — annotate with `cast` if needed
- ruff may flag the `DomainModule` Protocol import if not used as a type annotation

**Acceptance**: `hooks/ci-check.sh` exits 0, all 46+ tests pass.

## Sequence Summary

```
Phase 0  →  Phase 1  →  Phase 2  →  Phase 3  →  Phase 4  →  Phase 5
scaffold    tests        domains      kernel       server       CI
(imports)   (all fail)   (some pass)  (more pass)  (all pass)   (clean)
```

Each phase ends with a checkpoint: run `pytest` to confirm the expected test
state before moving on.
