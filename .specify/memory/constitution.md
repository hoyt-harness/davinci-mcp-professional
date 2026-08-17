# davinci-mcp-professional Constitution

## I. Typed-Activation Model

The kernel MCP server exposes a fixed set of always-available tools at session start. Domain tools
are not registered until explicitly activated. When `activate_domain(domain)` is called, the domain's
fully-typed MCP tools are registered and `notifications/tools/list_changed` is fired. Clients that
honor the MCP specification re-fetch the tool list automatically and can call domain tools immediately.

This means:
- Context cost at session start is bounded by the kernel alone (~5-8 tool definitions)
- Domain tools carry full MCP parameter schemas — no type erasure, no generic dispatch
- Domain tools are visible in client UIs after activation
- Adding a domain never changes the kernel interface

**The kernel is fixed and small.** It contains: `activate_domain`, `deactivate_domain` (if
implemented), and a handful of always-useful system tools (`get_version`, `get_current_page`,
`switch_page`). Nothing else belongs in the kernel unless its need is constant regardless of task.

## II. Domain Modules

Each domain is an independent module that registers its own typed tools. The nine initial domains are:

1. Project Management
2. Timeline Operations
3. Media Pool Operations
4. Clip Properties & Metadata
5. Timeline Item Editing
6. Color Grading
7. Render & Delivery
8. AI & Studio Features
9. System, Fairlight & Storage

Adding a domain means: writing a domain module, adding it to the registry, and adding a description
to the kernel's `list_domains` output. No other file changes. No cross-domain dependencies.

Fusion scripting and Workflow Integrations are future domains — the architecture accommodates them
without structural changes.

## III. Python-Native API Binding

DaVinci Resolve's scripting API is accessed via `fusionscript.dll`, a Python C extension that
exports `PyInit_fusionscript`. It is not callable from any other language without Python as an
intermediary. All Resolve API calls run in-process with the MCP server.

The Python version must match the version fusionscript.dll expects. As of Resolve v21.0.4 Studio,
Python 3.14.7 works. The project venv Python is always the correct runtime — never invoke the
server with a different Python (ABI mismatch crashes at import time). The existing
`check_python_runtime_compatibility()` probe in `resolve_client.py` guards against this at startup.

## IV. Stateless Request Handling

The server holds no cached Resolve object references between tool calls. Every tool invocation
re-queries the Resolve API from scratch to obtain the objects it needs. `resolve_client.py` may
cache the connection itself (`_resolve`, `_project_manager`) but never caches `Timeline`,
`TimelineItem`, `MediaPoolItem`, or `Folder` object references.

Why: the Resolve IPC connection documented teardown-on-child-exit behavior; cached object
references silently go stale if Resolve changes state between calls.

## V. Object Reference Scheme

Callers identify Resolve objects using these stable reference types:

| Object type | Reference | Resolution |
|---|---|---|
| Timeline | `name: string` | Walk `Project.GetTimelineByIndex()` until name matches |
| Folder | `folder_path: string` | Slash-separated from root, e.g. `"Master/Interviews"`. Walk `GetSubFolderList()` |
| MediaPoolItem | `clip_id: UUID string` | From `GetUniqueId()`. Returned by list operations. Server walks folder tree to resolve. |
| TimelineItem | `{track_type, track_index, item_index}` | `GetItemListInTrack(track_type, track_index)[item_index-1]`. 1-based. Within current timeline. |
| ColorGroup | `name: string` | Walk `Project.GetColorGroupsList()` until name matches |

List operations always return both IDs and human-readable identifiers. Callers store the ID from
a list response and pass it back to subsequent single-item operations.

No reverse lookup exists in the Resolve API. The server walks the graph fresh on every call —
there is no FindByUniqueId() or equivalent.

## VI. Error Taxonomy

Four exception types cover all failure modes. No raw exceptions reach the MCP protocol layer.

| Exception | Meaning | Typical cause |
|---|---|---|
| `DaVinciResolveNotRunningError` | Resolve process not detected | Server called before Resolve is open |
| `DaVinciResolveConnectionError` | DLL/IPC initialization failed | ABI mismatch, scripting disabled in prefs |
| `DaVinciResolveError` | API call returned failure or None | No project open, invalid operation |
| `ValueError` | Invalid caller-supplied arguments | Wrong domain, bad params, object not found |

All exceptions are caught at the server dispatch layer and returned as MCP `TextContent` with the
error class and message clearly indicated. A tool call never raises through the MCP protocol.

## VII. One Tool, One Concern

Each MCP tool maps to exactly one Resolve API concern. No compound operations in a single tool.
A workflow that creates a timeline and then appends clips is two tool calls, not one.

Tool names use `snake_case`. They describe the operation, not the object class
(`add_timeline_marker`, not `timeline_marker_add`).

## VIII. Test-First

Tests are written before implementation for every domain tool. The `DaVinciResolveClient`
interface is the mock boundary — tests operate against a mocked client, not a live Resolve
connection. Integration tests requiring a live Resolve instance are marked `@pytest.mark.live`
and excluded from CI (`hooks/ci-check.sh`).

The live Resolve integration test suite is run manually on the Studio workstation before any
release. A test project with known media (`mcp_test`) is the reference environment.

## IX. Simplicity

No configuration files, feature flags, plugin systems, or backwards-compatibility shims. The
domain registry is code. Convention over configuration throughout. When a simpler approach
correctly solves the problem, it wins over a more flexible one.

The external surface of this server (the kernel interface) is stable and small. Internal domain
modules are not part of the public contract and may be restructured freely.

---

**Version**: 1.0.0 | **Ratified**: 2026-08-16 | **Last Amended**: 2026-08-16
