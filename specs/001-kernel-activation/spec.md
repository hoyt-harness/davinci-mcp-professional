# Specification: Kernel Activation

**Feature branch**: `001-kernel-activation`

**Created**: 2026-08-19

**Status**: Draft

---

## Overview

Restructure the MCP server from a flat 13-tool list into a kernel + domain
architecture. The kernel exposes a small, fixed tool surface at session start.
Domain tools are registered dynamically when a client calls `activate_domain`,
which fires `notifications/tools/list_changed` so the client auto-refetches the
expanded tool list. Context cost at session start is bounded by the kernel alone.

This spec covers the kernel implementation and the server refactor required to
support it. Domain specs (the nine domain tool sets) follow this one.

---

## User Scenarios

### S1 — Context-controlled session start (P1)

A user opens a Claude Code session with the MCP server configured. Only the
kernel tools are visible in Claude's tool palette. The user calls `list_domains`
to see what's available, then calls `activate_domain("project_management")`.
Claude Code immediately refetches the tool list and the full project management
tool set is available — no session restart required.

**Acceptance criteria:**

1. **Given** a fresh session, **when** the client fetches tools, **then** only
   the 6 kernel tools are returned (no domain tools).
2. **Given** `activate_domain("project_management")` is called, **when** the
   handler returns, **then** `notifications/tools/list_changed` has been fired
   and the client's next `tools/list` call returns the kernel tools plus all
   project management domain tools.
3. **Given** a domain is active, **when** any of its tools is called, **then**
   the call dispatches correctly to that domain's handler.

---

### S2 — Multi-domain workflow (P2)

A user activates multiple domains across a session to work on a complex task
(e.g., project management + timeline operations + render delivery). Each
activation fires an independent notification. Active domains accumulate and
do not conflict.

**Acceptance criteria:**

1. **Given** two domains are active, **when** the client fetches tools, **then**
   the tool list is: kernel tools + domain-A tools + domain-B tools, with no
   duplicates or omissions.
2. **Given** domain A is active, **when** `activate_domain("A")` is called
   again, **then** the response indicates "already active" and no notification
   is fired.

---

### S3 — Domain deactivation (P3)

A user deactivates a domain to clean up context when switching tasks. The tool
list contracts. A subsequent call to a deactivated domain's tool fails cleanly
with a helpful error rather than an unknown-tool error.

**Acceptance criteria:**

1. **Given** a domain is active and then deactivated, **when** the client
   fetches tools, **then** the deactivated domain's tools are absent.
2. **Given** a domain is deactivated, **when** one of its tools is called,
   **then** the error response names the domain and instructs the caller to
   activate it first.

---

## Requirements

### FR-001 — Kernel tool surface

The kernel MUST expose exactly these tools at all times, unconditionally:

| Tool | Purpose |
|------|---------|
| `activate_domain` | Register a domain's tools and fire `tools/list_changed` |
| `deactivate_domain` | Unregister a domain's tools and fire `tools/list_changed` |
| `list_domains` | Return all registered domains with their activation status |
| `get_version` | DaVinci Resolve version (always useful, no domain context needed) |
| `get_current_page` | Current Resolve page (needed before `switch_page`) |
| `switch_page` | Navigate to a Resolve page |

No other tool belongs in the kernel unless its need is constant regardless of
the active domain set.

### FR-002 — Domain module interface

Each domain module MUST implement this interface (enforced at runtime by the
registry):

```python
class DomainModule(Protocol):
    name: str            # registry key, snake_case, e.g. "project_management"
    description: str     # one line shown by list_domains
    def get_tools(self) -> list[types.Tool]: ...
    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any: ...
```

`get_tools()` returns the fully-typed MCP tool definitions for this domain.
`dispatch()` handles all tool calls whose names belong to this domain.

### FR-003 — Domain registry

The registry MUST be a static code-level mapping, not a configuration file.
It lives in `src/davinci_mcp/domains/registry.py` as a plain dict:
`DOMAIN_REGISTRY: dict[str, DomainModule]`. Each domain module is instantiated
once at import time. Adding a domain means adding one entry to this dict — no
other file changes in the server.

### FR-004 — Activation mechanism

`activate_domain(domain)` MUST:

1. Validate the domain name against `DOMAIN_REGISTRY`. Unknown name → error
   response (not exception).
2. If already active, return `{"status": "already_active", "domain": domain}`.
   Do not fire a notification.
3. Add the domain to the server's `_active_domains: dict[str, DomainModule]`.
4. Rebuild the routing tables (`_tool_to_domain`, `_inactive_tool_to_domain`).
5. Fire `notifications/tools/list_changed` via
   `await request_ctx.get().session.send_tool_list_changed()`.
6. Return `{"status": "activated", "domain": domain, "tools_added": [list of
   tool names now available]}`.

`deactivate_domain(domain)` MUST mirror this: validate → check active → remove
from dict → rebuild routing tables → fire notification → return status.

### FR-005 — Notification mechanism

The 1.x MCP SDK (mcp 1.29.0, pinned at `<2.0.0`) exposes a module-level
contextvar that is set for the duration of every tool call handler:

```python
from mcp.server.lowlevel.server import request_ctx
```

Inside `handle_call_tool`, `activate_domain` fires the notification via:

```python
await request_ctx.get().session.send_tool_list_changed()
```

The decorator-based handler signatures in `server.py` are CORRECT for this SDK
version and MUST NOT be changed. No API migration is required.

### FR-006 — Capability declaration

The server MUST declare `tools_changed=True` in `NotificationOptions` so that
the `initialize` response advertises `capabilities.tools.listChanged: true`.
Without this, a compliant client has no reason to honor the notification.

The current call in `server.py:182` is `NotificationOptions()` (bare). It MUST
become `NotificationOptions(tools_changed=True)`.

### FR-007 — Tool list composition

`handle_list_tools` MUST return the kernel tool list plus the union of
`domain.get_tools()` for every domain in the active-domains dict. Order:
kernel tools first, then domain tools in activation order (insertion order of
the active-domains dict).

### FR-008 — Dispatch routing

The server maintains a `_tool_to_domain: dict[str, str]` routing table that
maps each active domain tool name to its domain name. This table is rebuilt
once on each activation or deactivation call. It is NOT rebuilt on every tool
call — Article IV forbids caching stale Resolve object references, not static
code-derived maps.

`handle_call_tool` routes as follows:

1. If `name` is a kernel tool → handle inline.
2. If `name` is in `_tool_to_domain` → delegate to the owning domain's
   `dispatch()`.
3. If `name` belongs to a registered but inactive domain → return error:
   `"Tool '{name}' is in domain '{domain}'. Call activate_domain('{domain}') first."`.
4. If `name` is unrecognized → return error: `"Unknown tool: {name}"`.

For case 3, the server builds a secondary `_inactive_tool_to_domain` map
from all registered domains minus the active set, also rebuilt on each
activation change.

### FR-009 — Existing tool migration

The 10 non-kernel tools currently exposed MUST migrate to their domain modules.
The kernel's initial state exposes no project, timeline, or media tools:

| Current tool | Destination domain |
|-------------|-------------------|
| `list_projects` | Domain 1: Project Management |
| `get_current_project` | Domain 1: Project Management |
| `open_project` | Domain 1: Project Management |
| `create_project` | Domain 1: Project Management |
| `list_timelines` | Domain 2: Timeline Operations |
| `get_current_timeline` | Domain 2: Timeline Operations |
| `create_timeline` | Domain 2: Timeline Operations |
| `switch_timeline` | Domain 2: Timeline Operations |
| `list_media_clips` | Domain 3: Media Pool Operations |
| `import_media` | Domain 3: Media Pool Operations |

The domain implementations for the migrated tools copy the existing
`resolve_client.py` logic. No behavior change — relocation only.

### FR-010 — Error handling

All four exception types from constitution Article VI MUST be caught in
`handle_call_tool` and returned as `types.TextContent` error messages.
No raw exception reaches the MCP protocol layer. This behavior is unchanged
from the current server.

### FR-011 — Test coverage

Every kernel tool MUST have unit tests against a mocked `DaVinciResolveClient`.
The activation/deactivation flow MUST have tests that verify:
- The active-domains set before and after activation
- The tool list composition before and after activation
- The notification is fired (via a mock session)
- The dispatch routing for all four cases in FR-008

---

## File Structure

```
src/davinci_mcp/
  server.py                    # Refactored: kernel dispatch, routing tables
  resolve_client.py            # Unchanged
  domains/
    __init__.py
    registry.py                # DOMAIN_REGISTRY dict + DomainModule Protocol
    project_management.py      # Domain 1 (migrated tools only)
    timeline_operations.py     # Domain 2 (migrated tools only)
    media_pool.py              # Domain 3 (migrated tools only)
  tools/
    __init__.py                # Replaced: kernel tool definitions only
```

The `domains/` package is new. Only the three domains with migrated tools
exist in this spec. `DOMAIN_REGISTRY` holds only implemented domains —
domains 4–9 appear only when their specs land.

---

## Success Criteria

- **SC-001**: `tools/list` at session start returns exactly 6 tools.
- **SC-002**: After `activate_domain("project_management")`,
  `tools/list` returns 6 + (count of project management tools).
- **SC-003**: Calling a domain tool when the domain is inactive returns a
  human-readable error naming the domain and the activation step required.
- **SC-004**: All existing tests pass after the refactor (behavior unchanged
  for the 10 migrated tools when their domain is active).
- **SC-005**: The `initialize` response contains
  `capabilities.tools.listChanged: true`.
- **SC-006**: `hooks/ci-check.sh` passes (ruff, pyright, pytest).

---

## Assumptions

- `DaVinciResolveClient` does not change in this spec. Domain modules receive
  it as a parameter to `dispatch()` — they do not own or manage the connection.
- The MCP `<2.0.0` ceiling in `pyproject.toml` remains in place. This spec
  targets mcp 1.29.0, which uses the decorator-based handler API and exposes
  `request_ctx` as a contextvar for notification firing.
- `deactivate_domain` is implemented in this spec for symmetry with activation.
  It does not reclaim context already injected into an ongoing conversation;
  it only contracts future tool lists.
- The resource handlers (`list_resources`, `read_resource`) are left unchanged
  and are not migrated to the domain model in this spec.
- Domains 4–9 do not appear in `DOMAIN_REGISTRY` in this spec. `list_domains`
  will show only the three implemented domains until later domain specs land.
  A future kernel patch can add a separate `list_unimplemented_domains` call
  if discoverability of the full nine-domain plan is needed.
