# Developer Guide — DaVinci MCP Professional

This document covers everything needed to work on the project from source:
setup, architecture, running, building, testing, and contributing.

For end-user installation and client configuration, see [README.md](README.md).

---

## Prerequisites

- Python 3.10 or later, **installed system-wide** (the installer from
  [python.org](https://www.python.org/downloads/) with "Add to PATH" and
  "Install for all users" selected)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- DaVinci Resolve Studio, installed and running when using the server
- Git, configured with GPG signing (required for commits — see CONTRIBUTING.md)

---

## Development Setup

```bash
git clone https://github.com/hoyt-harness/davinci-mcp-professional.git
cd davinci-mcp-professional
```

**Windows — important:** DaVinci Resolve's `fusionscript.dll` discovers Python
through the Windows registry (`HKLM\SOFTWARE\Python\PythonCore`) and loads
`python3.dll` by full path from that installation. If the virtual environment
uses a *different* Python (e.g. one downloaded by `uv` automatically), two
Python runtimes end up in the same process and the server crashes at connection
time. Always create the venv from the **system Python**:

```powershell
py -0p   # Windows Python Launcher — lists installed versions and paths
```

```bash
uv venv --python "C:\Program Files\Python314\python.exe"   # adjust to your path
uv sync
```

**macOS / Linux:**

```bash
uv venv
uv sync
```

`uv sync` installs all runtime and dev dependencies from `uv.lock` into `.venv`.

---

## Architecture

### Kernel + domain model

The server uses a two-layer architecture to keep context cost proportional to
the task at hand.

**Kernel** (`src/davinci_mcp/tools/__init__.py`, `server.py`):
Six tools that are always available at session start:

| Tool | Purpose |
|---|---|
| `activate_domain` | Register a domain's tools; fires `notifications/tools/list_changed` |
| `deactivate_domain` | Unregister a domain's tools; fires `notifications/tools/list_changed` |
| `list_domains` | Return all registered domains with activation status and tool counts |
| `get_version` | DaVinci Resolve version (always useful, no domain context needed) |
| `get_current_page` | Current Resolve page |
| `switch_page` | Navigate to a Resolve page |

**Domains** (`src/davinci_mcp/domains/`):
Each domain is an independent module implementing the `DomainModule` protocol
(`registry.py`). It registers its tools on demand when activated. Active domain
tools appear in `tools/list` after the client receives `notifications/tools/list_changed`
and refetches — no session restart required.

Current domains:

| Domain name | Tools | Coverage |
|---|---|---|
| `project_management` | 23 | Open/save/close/rename/delete projects, export/import/archive/restore, folder navigation, database switching |
| `timeline_operations` | 51 | Settings, timecode, tracks, markers, items, export/import, generators, Fusion clips, Dolby Vision |
| `media_pool` | 28 | Folder inspection and management, clip operations, relink, mattes, stereo clips |

### Object reference scheme (constitution Article V)

Callers identify Resolve objects using these stable reference types:

| Object | Reference | Resolution |
|---|---|---|
| Timeline | `name: string` | Walk `GetTimelineByIndex()` until name matches |
| Folder | `folder_path: string` | Slash-separated from root, e.g. `"Master/Interviews"` |
| MediaPoolItem | `clip_id: UUID string` | From `GetUniqueId()`; server walks folder tree to resolve |
| TimelineItem | `{track_type, track_index, item_index}` | `GetItemListInTrack()[item_index-1]`; 1-based, within current timeline |

List operations always return both IDs and human-readable identifiers.
Item coordinates are invalidated by any timeline modification — re-call
`get_items_in_track` after mutations.

### Destructive operation gate

Tools that permanently modify or delete data require `confirm: true` in the
arguments. The server rejects the call with a descriptive message if the flag
is absent or false. This is enforced at two levels: the MCP inputSchema marks
`confirm` as required (schema validation), and the domain dispatch checks it
before calling any Resolve API method.

---

## Running from Source

**`mcp_server.py` — MCP server (for AI clients)**

```bash
uv run python mcp_server.py
```

Speaks the MCP stdio protocol with no console output. Point your AI client
configuration at this file.

**`main.py` — Interactive CLI (for humans)**

```bash
uv run python main.py
uv run python main.py --debug
```

Wraps the same MCP server with a human-friendly terminal interface: colored
startup banner, prerequisite checks (is Resolve running? is Python compatible?),
and `--debug` / `--skip-checks` flags. Use this to verify connectivity before
configuring a client.

---

## MCP Client Configuration for Development

Point your MCP client at the venv interpreter and `mcp_server.py`. A ready-to-edit
template is at `claude_desktop_config_template.json`.

**Windows:**
```json
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci MCP Professional",
      "command": "C:\\path\\to\\davinci-mcp-professional\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\davinci-mcp-professional\\mcp_server.py"]
    }
  }
}
```

**macOS:**
```json
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci MCP Professional",
      "command": "/path/to/davinci-mcp-professional/.venv/bin/python",
      "args": ["/path/to/davinci-mcp-professional/mcp_server.py"]
    }
  }
}
```

---

## Project Structure

```
davinci-mcp-professional/
├── mcp_server.py                   # Pure MCP stdio server entry point
├── main.py                         # Interactive CLI entry point
├── build.py                        # PyInstaller build script
├── src/davinci_mcp/
│   ├── __init__.py                 # Package init; version from hatch-vcs
│   ├── cli.py                      # click CLI, prerequisite checks, banner
│   ├── server.py                   # Kernel dispatch, routing tables, activation handlers
│   ├── resolve_client.py           # DaVinci Resolve API wrapper (all domain methods)
│   ├── types.py                    # Protocol types for Resolve objects
│   ├── tools/__init__.py           # Kernel tool definitions (6 tools)
│   ├── domains/
│   │   ├── __init__.py
│   │   ├── registry.py             # DomainModule protocol + DOMAIN_REGISTRY
│   │   ├── project_management.py   # Domain 1: 23 tools
│   │   ├── timeline_operations.py  # Domain 2: 51 tools
│   │   └── media_pool.py           # Domain 3: 28 tools
│   ├── resources/__init__.py       # 7 MCP resource definitions
│   └── utils/
│       ├── __init__.py
│       └── platform.py             # Platform detection, Python compatibility check
├── tests/
│   ├── conftest.py
│   ├── test_security.py            # Security and input-validation tests
│   ├── test_kernel.py              # Kernel architecture: dispatch, routing, notification
│   ├── test_domain1.py             # Domain 1 (project management) parametrized dispatch
│   ├── test_domain2.py             # Domain 2 (timeline operations) parametrized dispatch
│   └── test_domain3.py             # Domain 3 (media pool) parametrized dispatch
├── specs/
│   └── 001-kernel-activation/      # Spec and plan for the kernel architecture
├── doxygen/                        # Doxygen-generated HTML (not tracked in git)
├── pyproject.toml
├── uv.lock
└── Doxyfile
```

---

## Kernel and Domain Tool Reference

### Kernel tools (always available)

| Tool | Parameters | Description |
|---|---|---|
| `activate_domain` | `domain: string (enum)` | Register a domain; fires tools/list_changed |
| `deactivate_domain` | `domain: string` | Unregister a domain; fires tools/list_changed |
| `list_domains` | — | List all domains with status and tool counts |
| `get_version` | — | DaVinci Resolve version string |
| `get_current_page` | — | Currently active page |
| `switch_page` | `page: string (enum)` | Navigate to a page |

### Domain tools (activated on demand)

Use `list_domains` to see available domains and their tool counts, then
`activate_domain` to load the tools you need. Refer to each domain module's
`get_tools()` for full parameter documentation.

---

## Extending the Server

### Adding a new domain

1. Create `src/davinci_mcp/domains/your_domain.py`. Implement a class that
   satisfies `DomainModule` (`registry.py`): set `name` and `description`
   class attributes, implement `get_tools() -> list[types.Tool]` and
   `async def dispatch(tool_name, arguments, client) -> Any`.

2. Add the corresponding methods to `resolve_client.py`. Every method
   re-queries the Resolve API fresh on every call — never cache Resolve object
   references between calls (constitution Article IV).

3. Register the domain in `src/davinci_mcp/domains/registry.py`:
   ```python
   from .your_domain import YourDomain
   DOMAIN_REGISTRY: dict[str, DomainModule] = {
       ...existing entries...,
       "your_domain": YourDomain(),
   }
   ```
   That is the only other file that needs to change. The kernel's
   `activate_domain` enum, `list_domains` output, and routing tables all
   derive from `DOMAIN_REGISTRY` at runtime.

4. Write parametrized dispatch tests in `tests/test_your_domain.py` using the
   same pattern as `test_domain1.py`. Tests are written before implementation
   (constitution Article VIII).

### Adding a new resource

1. Add its definition to `src/davinci_mcp/resources/__init__.py`.
2. Add a dispatch branch in `server.py` → `_read_resource()`.
3. Add the method to `resolve_client.py`.

---

## Testing, Linting, and Type Checking

```bash
# Run all tests
uv run pytest

# Run a specific domain test
uv run pytest tests/test_domain1.py -v

# Skip live tests (requires Resolve running)
uv run pytest -m "not live"

# Coverage
uv run pytest --cov=src/davinci_mcp --cov-report=html

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run pyright

# Full CI gate (same as pre-push hook)
bash hooks/ci-check.sh
```

The pre-push hook runs `hooks/ci-check.sh` automatically on `git push`. It
must pass before any push reaches GitHub. If a push fails locally but passes
on GitHub, the local and remote environments differ — investigate before
proceeding.

---

## PyInstaller Builds

```bash
uv sync --extra build      # install PyInstaller into the venv
uv run python build.py     # build both targets
```

Output:

```
dist/davinci-mcp-server/davinci-mcp-server.exe   # MCP server (for AI clients)
dist/davinci-mcp/davinci-mcp.exe                 # Interactive CLI (for humans)
```

---

## API Documentation

Doxygen-generated API documentation is written to `doxygen/html/` (not tracked
in git):

```bash
doxygen Doxyfile                          # regenerate
start doxygen/html/index.html             # Windows
open doxygen/html/index.html              # macOS
```

---

## Troubleshooting

**"Python runtime conflict" error**

The venv was created from a uv-managed Python, not the system Python. On
Windows, DaVinci Resolve requires the venv and the system Python DLL to match.
Rebuild the venv:

```bash
py -0p   # find your system Python path
uv venv --clear --python "C:\Program Files\Python314\python.exe"
uv sync
```

**DaVinci Resolve not found / not running**

The server requires Resolve to be fully loaded before connecting. Start Resolve
first, wait for the UI to appear, then connect the MCP client.

**Import errors after setup**

```bash
uv sync
```

**Debug mode**

```bash
uv run python main.py --debug
```

**Dependency conflicts**

```bash
uv sync --reinstall
```
