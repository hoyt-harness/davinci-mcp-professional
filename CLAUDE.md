# CLAUDE.md

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

Python >= 3.10 is required. The MCP Python SDK uses `match` statements and
other 3.10+ features. All tool configurations (pyright, mypy, ruff, black)
must target 3.10 as the minimum version. Never declare compatibility with
Python 3.9.

### Upstream Reference

The MCP Python SDK is the upstream dependency for protocol implementation.
A local reference copy is available at:

    D:\dev\ARTIFICIAL_INTELLIGENCE\MCP\_MCP-Tools-Dev\python-sdk

The upstream MCP specification repository is at:

    D:\dev\ARTIFICIAL_INTELLIGENCE\MCP\_MCP-Tools-Dev\modelcontextprotocol

Audit this project's MCP usage and dependency versions against these
references when making protocol-level changes.

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

Data flow: **CLI -> MCP Server -> Resolve Client -> DaVinci Resolve scripting API**

```
src/davinci_mcp/
├── cli.py              # Entry point: prerequisite checks, colored output, click commands
├── server.py           # MCP protocol: routes tool calls and resource reads
├── resolve_client.py   # Wraps DaVinci Resolve Python API; owns connection lifecycle
├── types.py            # Runtime-checkable Protocol types (DaVinciProject, DaVinciTimeline, etc.)
├── tools/
│   └── __init__.py     # All 13 MCP tool definitions (name, description, inputSchema)
├── resources/
│   └── __init__.py     # All 7 MCP resource definitions (resolve://... URIs)
└── utils/
    ├── __init__.py
    └── platform.py     # Platform detection, PYTHONPATH setup, process checking
```

### Key Architectural Facts

- `server.py` implements `list_tools`, `call_tool`, `list_resources`,
  `read_resource` — all async. Tool dispatch and resource reads delegate
  to `resolve_client.py`.
- `resolve_client.py` uses lazy loading: current project fetched on demand
  and cached per-request. Raises from a custom exception hierarchy
  (`DaVinciResolveError` -> `DaVinciResolveNotRunningError`,
  `DaVinciResolveConnectionError`).
- `tools/__init__.py` and `resources/__init__.py` are pure data (lists of
  MCP tool/resource definitions). Adding a new tool: add definition in
  `tools/__init__.py`, add dispatch in `server.py`, implement in
  `resolve_client.py`.
- `types.py` uses `typing.Protocol` with `runtime_checkable` so Resolve
  objects can be type-checked without importing the Resolve module (which
  may not be present at type-check time).
- `utils/platform.py` handles OS differences: Windows uses `tasklist` for
  process detection and `ProgramData` paths; macOS/Linux use `pgrep` and
  standard POSIX paths.

### MCP Tool/Resource Inventory

**Tools (13):** `get_version`, `get_current_page`, `switch_page`,
`list_projects`, `get_current_project`, `open_project`, `create_project`,
`list_timelines`, `get_current_timeline`, `create_timeline`,
`switch_timeline`, `list_media_clips`, `import_media`.

**Resources (7):** `resolve://version`, `resolve://current-page`,
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
