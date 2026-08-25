# CLAUDE.md

> Vault documentation: `C:\Users\hoyth\Obsidian\Positronikal\03-OPERATIONS\Engineering\davinci-mcp-professional\`

This file provides guidance to Claude Code when working with this repository.

## Project Overview

DaVinci MCP Professional is an enterprise-grade Model Context Protocol (MCP)
server that exposes DaVinci Resolve's full Python scripting API to AI assistants
(Claude Desktop, Cursor) via the MCP. It targets both Windows and macOS and
requires Python >= 3.10.

This is a hard/project fork from https://github.com/samuelgursky/davinci-resolve-mcp,
now independent due to major architectural overhaul. Licensed under GPL-3.0
(see COPYING.md).

## Development Environment

### Package Management

Use **uv** exclusively for dependency and virtual environment management.
Never use raw pip for project dependencies.

```bash
# First-time setup
uv venv
uv sync

# Run the server
uv run python main.py

# Run the MCP server entry point (for Claude Desktop / Cursor)
uv run python mcp_server.py

# Add a dependency
uv add <package>

# Upgrade a dependency
uv lock --upgrade-package <package>
```

### Python Version

Python >= 3.10 is required (the MCP Python SDK uses `match` statements and
other 3.10+ features).  All tool configurations (pyright, mypy, ruff)
must target 3.10 as the minimum version.

On **Windows**, the virtual environment MUST be created from the
system-installed Python — the same installation that appears in the
Windows registry under `HKLM\SOFTWARE\Python\PythonCore`.  DaVinci
Resolve's `fusionscript.dll` discovers Python via this registry key and
loads `python3.dll` by full path.  If the running Python is a different
installation (e.g. a uv-managed download), two Python runtimes end up
in the same process and the server crashes.  Use:

```bash
uv venv --python "C:\Program Files\PythonXYZ\python.exe"
uv sync
```

where `PythonXYZ` matches the system-installed version.

### Upstream Reference

The MCP Python SDK is the upstream dependency for protocol implementation
(installed via uv from PyPI). The MCP specification repository is at:

    D:\Engineering\_MCP-Tools-Dev\modelcontextprotocol

Audit this project's MCP usage and dependency versions against this reference
when making protocol-level changes.

## Common Commands

```bash
# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking (pyright scoped to src/ per pyproject.toml)
uv run pyright
uv run mypy src/

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_security.py -v

# Run tests with coverage
uv run pytest --cov=src/davinci_mcp --cov-report=html

# Security scanning
uv run bandit -r src/
uv run safety check

# Regenerate Doxygen documentation
doxygen Doxyfile
```

## Architecture

Data flow: **CLI → MCP Server (kernel dispatch) → Domain → Resolve Client → DaVinci Resolve scripting API**

```
src/davinci_mcp/
├── cli.py                    # Entry point: prerequisite checks, colored output, click commands
├── server.py                 # MCP protocol: kernel dispatch, domain routing, tool list management
├── resolve_client.py         # Wraps DaVinci Resolve Python API; owns connection lifecycle
├── types.py                  # Runtime-checkable Protocol types (DaVinciProject, DaVinciTimeline, etc.)
├── tools/
│   └── __init__.py           # Kernel tool definitions only (6 tools always available)
├── domains/
│   ├── registry.py           # DomainModule protocol + DOMAIN_REGISTRY dict
│   ├── project_management.py # Domain 1 — 23 tools
│   ├── timeline_operations.py# Domain 2 — 51 tools
│   ├── media_pool.py         # Domain 3 — 28 tools
│   ├── clip_properties.py    # Domain 4 — 29 tools
│   ├── timeline_item_editing.py # Domain 5 — 59 tools
│   ├── color_grading.py      # Domain 6 — 33 tools
│   ├── render_delivery.py    # Domain 7 — 26 tools
│   ├── ai_studio.py          # Domain 8 — 18 tools (Studio only)
│   └── system_fairlight_storage.py # Domain 9 — 16 tools
├── resources/
│   └── __init__.py           # All 7 MCP resource definitions (resolve://... URIs)
└── utils/
    ├── __init__.py
    └── platform.py           # Platform detection, PYTHONPATH setup, process checking
```

### Key Architectural Facts

**Kernel + domain model.** At session start, only 6 kernel tools are visible to
the MCP client. Calling `activate_domain("project_management")` fires a
`notifications/tools/list_changed` event; the client refetches the tool list and
that domain's tools become available — no restart needed. `deactivate_domain`
removes them again.

- **`server.py`** owns the `DaVinciMCPServer` class: routing tables
  (`_tool_to_domain`, `_inactive_tool_to_domain`), `_rebuild_routing_tables()`
  (called on every activation/deactivation), and the four-case dispatch (FR-008):
  kernel tool → domain active → domain inactive (hint to activate) → unknown.
- **`domains/registry.py`** defines the `DomainModule` protocol and the
  `DOMAIN_REGISTRY` dict. Adding a new domain: implement the protocol, add one
  entry to `DOMAIN_REGISTRY` — no other server file changes required.
- Each domain module exposes `get_tools() → list[Tool]` and
  `async dispatch(tool_name, arguments, client) → Any`.
- **`resolve_client.py`** uses lazy loading: current project fetched on demand
  and cached per-request. Raises from a custom exception hierarchy
  (`DaVinciResolveError` → `DaVinciResolveNotRunningError`,
  `DaVinciResolveConnectionError`).
- **`tools/__init__.py`** contains kernel tool definitions only. Domain tool
  definitions live in their respective domain modules.
- **`types.py`** uses `typing.Protocol` with `runtime_checkable` so Resolve
  objects can be type-checked without importing the Resolve module.
- **`utils/platform.py`** handles OS differences: Windows uses `tasklist` for
  process detection and `ProgramData` paths; macOS/Linux use `pgrep` and
  standard POSIX paths.

### FusionScript ABI Behavior

DaVinci Resolve's Python bindings (FusionScript) silently return `None` for
method attribute lookups on objects that don't support those methods — no
`AttributeError` is raised. Calling the result crashes: `'NoneType' object is
not callable`. Always guard before calling any method that may be unsupported
on a given object type:

```python
get_uid = item.GetUniqueId   # None if unsupported, not AttributeError
if get_uid is not None:
    uid = get_uid()
```

This is especially relevant when iterating `GetClipList()` on a media pool
folder: the list may contain both `MediaPoolItem` objects (regular clips, which
support `GetUniqueId`) and timeline objects (which do not).

### MCP Tool/Resource Inventory

**Kernel tools (6 — always visible):** `activate_domain`, `deactivate_domain`,
`list_domains`, `get_version`, `get_current_page`, `switch_page`.

**Domain tools (283 — loaded on demand):**

| Domain | Key | Tool count |
|--------|-----|-----------|
| Project Management | `project_management` | 23 |
| Timeline Operations | `timeline_operations` | 51 |
| Media Pool | `media_pool` | 28 |
| Clip Properties | `clip_properties` | 29 |
| Timeline Item Editing | `timeline_item_editing` | 59 |
| Color Grading | `color_grading` | 33 |
| Render & Delivery | `render_delivery` | 26 |
| AI & Studio *(Studio edition only)* | `ai_studio` | 18 |
| System / Fairlight / Storage | `system_fairlight_storage` | 16 |

**Resources (7 — always available):** `resolve://version`, `resolve://current-page`,
`resolve://projects`, `resolve://current-project`, `resolve://timelines`,
`resolve://current-timeline`, `resolve://media-clips`.

## Code Style and Standards

### Paradigm and Standards

Follow the **imperative paradigm** with close attention to procedural and
structured sub-paradigms. Project structure and formatting follow **GNU
Coding Standards** (https://www.gnu.org/prep/standards/).

### Tooling

- **ruff** for linting and formatting (replaces black, isort, flake8).
- **mypy** with `disallow_untyped_defs = true`.
- **pyright** in basic mode, scoped to `src/`.
- Line length: 88 characters for Python.
- All MCP handler methods in `server.py` must be `async`.
- Custom exceptions always preferred over bare `Exception`.
- `colorama` for cross-platform terminal color; `click` for CLI structure.

### Exception Handling

- Catch specific exceptions where possible.
- Use `logger.exception()` instead of `logger.error()` when catching exceptions.
- Avoid bare `except Exception:` outside of top-level handlers.

## Documentation

### Doxygen

The project uses Doxygen for API documentation. Configuration is in `Doxyfile`
at the repo root. Generated HTML output goes to `docs/html/` and is tracked
in git.

When the project version changes or source code is modified, update
`PROJECT_NUMBER` in `Doxyfile` and regenerate with `doxygen Doxyfile`.

### Project Documentation

Root-level Markdown files follow GNU conventions:
- `README.md` — project overview, installation, usage summary
- `USING.md` — detailed setup and usage instructions
- `BUGS.md` — troubleshooting and bug reporting
- `CONTRIBUTING.md` — contribution guidelines, legal requirements
- `COPYING.md` — GPL-3.0 license text
- `AUTHORS.md` — project authors
- `ATTRIBUTION.md` — third-party attribution
- `VERSION.md` — versioning information

## Distribution

### PyInstaller

The project supports PyInstaller for building standalone executables.
Windows binaries are provided in GitHub releases.

### Claude Desktop / Cursor Integration

Users running from source configure Claude Desktop via
`claude_desktop_config.json` pointing to the `uv`-managed virtual
environment and `mcp_server.py` entry point. See `USING.md` for details.

## Test Organization

- `tests/test_security.py` — hardcoded-secret detection, dependency
  vulnerability scanning, file permission checks, input validation.
  Marked with `@pytest.mark.security`.
- `tests/conftest.py` — fixtures: `project_root`, `src_dir`,
  `temp_config_file`. Markers: `security`, `integration`, `slow`.
- Integration tests require DaVinci Resolve to be running; skip with
  `-m "not integration"` when Resolve is unavailable.

## Contributing

- GPG-signed commits required (see `CONTRIBUTING.md`).
- GNU Coding Standards apply to formatting and project structure.
- A signed legal disclaimer form is required before PRs are accepted
  from new contributors.
