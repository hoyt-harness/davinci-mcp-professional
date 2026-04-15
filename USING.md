# Developer Guide — DaVinci MCP Professional

This document covers everything needed to work on the project from source,
including setup, running, building, testing, and contributing.

For end-user installation, see [README.md](README.md).
For full API documentation, see `docs/html/index.html` or regenerate with
`doxygen Doxyfile`.

---

## Prerequisites

- Python 3.10 or later, **installed system-wide** (the installer from
  [python.org](https://www.python.org/downloads/) with "Add to PATH" and
  "Install for all users" selected)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- DaVinci Resolve Studio, installed and running when using the server
  (the free edition does not support external scripting)
- Git, configured with GPG signing (required for commits — see CONTRIBUTING.md)

---

## Development Setup

```bash
git clone https://github.com/Positronikal/davinci-mcp-professional.git
cd davinci-mcp-professional
uv venv --python <system-python>
uv sync
```

**Windows — important:** The `--python` flag must point to the
system-installed Python executable.  DaVinci Resolve's `fusionscript.dll`
discovers Python through the Windows registry
(`HKLM\SOFTWARE\Python\PythonCore`) and loads `python3.dll` by full path
from that installation.  If the virtual environment uses a *different*
Python (e.g. one downloaded by `uv` automatically), two Python runtimes
end up in the same process and the server crashes.

To find your system Python, run:

```powershell
py -0p          # Windows Python Launcher — lists installed versions and paths
```

Then create the venv:

```bash
uv venv --python "C:\Program Files\Python314\python.exe"   # adjust to your version
uv sync
```

On **macOS / Linux**, `uv venv` with no `--python` flag works if the
default `python3` is a system-wide installation.

`uv sync` installs all runtime and dev dependencies from `uv.lock` into `.venv`.

---

## Running from Source

The project has two entry points that serve different purposes:

**`mcp_server.py` — MCP server (for AI clients)**

```bash
uv run python mcp_server.py
```

This is the entry point that MCP clients (Claude Desktop, Gemini CLI, etc.)
launch as a subprocess. It speaks the MCP stdio protocol with no console
output. Point your `claude_desktop_config.json` at this file.

**`main.py` — Interactive CLI (for humans)**

```bash
uv run python main.py
uv run python main.py --debug
```

This wraps the same MCP server with a human-friendly terminal interface:
a colored startup banner, prerequisite checks (is Resolve running? is
PYTHONPATH set?), and `--debug` / `--skip-checks` flags. Use this when
running the server manually to verify connectivity or troubleshoot issues.

---

## MCP Client Configuration for Development

Point your MCP client at the venv interpreter and `mcp_server.py`. Example
for Claude Desktop (`claude_desktop_config.json`):

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

A ready-to-edit template is at `claude_desktop_config_template.json`.

---

## PyInstaller Builds

Build standalone executables (single-directory bundles):

```bash
uv sync --extra build      # install PyInstaller into the venv
uv run python build.py     # build both targets
```

Output:

```
dist/davinci-mcp-server/davinci-mcp-server.exe   # MCP server (for AI clients)
dist/davinci-mcp/davinci-mcp.exe                 # Interactive CLI (for humans)
```

These mirror the two entry points described in **Running from Source** above:

- **`davinci-mcp-server.exe`** — the MCP stdio server. Use this in MCP client
  configurations when distributing to end users who do not have Python
  installed.
- **`davinci-mcp.exe`** — the interactive CLI with prerequisite checks and
  colored output. Useful for manual testing and troubleshooting.

---

## Project Structure

```
davinci-mcp-professional/
├── mcp_server.py              # Pure MCP stdio server entry point
├── main.py                    # Interactive CLI entry point
├── build.py                   # PyInstaller build script
├── src/davinci_mcp/
│   ├── __init__.py            # Package init; imports __version__ from hatch-vcs
│   ├── cli.py                 # click CLI, prerequisite checks, banner
│   ├── server.py              # MCP server: registers tool/resource handlers
│   ├── resolve_client.py      # DaVinci Resolve API wrapper
│   ├── types.py               # runtime_checkable Protocol types for Resolve objects
│   ├── tools/__init__.py      # All 13 MCP tool definitions (name, schema)
│   ├── resources/__init__.py  # All 7 MCP resource definitions (URI, schema)
│   └── utils/
│       ├── __init__.py
│       └── platform.py        # Platform detection, PYTHONPATH setup, process check
├── tests/
│   ├── conftest.py
│   └── test_security.py
├── docs/                      # Doxygen-generated HTML (tracked in git)
├── pyproject.toml
├── uv.lock
└── Doxyfile
```

---

## Available Tools

| Tool | Description |
|---|---|
| `get_version` | DaVinci Resolve version string |
| `get_current_page` | Currently active page (Edit, Color, etc.) |
| `switch_page` | Navigate to a page (media/cut/edit/fusion/color/fairlight/deliver) |
| `list_projects` | All projects in the current database |
| `get_current_project` | Name of the open project |
| `open_project` | Open a project by name |
| `create_project` | Create a new project |
| `list_timelines` | All timelines in the current project |
| `get_current_timeline` | Name of the active timeline |
| `create_timeline` | Create a new empty timeline |
| `switch_timeline` | Switch to a timeline by name |
| `list_media_clips` | All clips in the media pool root folder |
| `import_media` | Import a media file into the media pool |

## Available Resources

| URI | MIME type | Content |
|---|---|---|
| `resolve://version` | text/plain | Resolve version string |
| `resolve://current-page` | text/plain | Active page name |
| `resolve://projects` | application/json | Project list |
| `resolve://current-project` | text/plain | Open project name |
| `resolve://timelines` | application/json | Timeline list |
| `resolve://current-timeline` | text/plain | Active timeline name |
| `resolve://media-clips` | application/json | Media pool clip list |

---

## Extending the Server

### Adding a new tool

1. Add its definition to `src/davinci_mcp/tools/__init__.py` (name, description,
   inputSchema).
2. Add a dispatch branch in `server.py` → `_call_tool()`.
3. Implement the method in `resolve_client.py`.

### Adding a new resource

1. Add its definition to `src/davinci_mcp/resources/__init__.py` (URI, mimeType).
2. Add a dispatch branch in `server.py` → `_read_resource()`.
3. Implement the method in `resolve_client.py`.

---

## Testing, Linting, and Type Checking

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_security.py -v

# Skip integration tests (requires Resolve running)
uv run pytest -m "not integration"

# Coverage
uv run pytest --cov=src/davinci_mcp --cov-report=html

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run pyright
uv run mypy src/

# Security
uv run bandit -r src/
uv run safety check
```

---

## API Documentation

Full Doxygen-generated API documentation is in `docs/html/`:

```bash
# View locally
open docs/html/index.html          # macOS
start docs/html/index.html         # Windows

# Serve with search support
cd docs/html
uv run python -m http.server 8000
# then open http://localhost:8000

# Regenerate after code changes
doxygen Doxyfile
```

---

## Troubleshooting

**DaVinci Resolve not found**
- Confirm Resolve is installed in the default location for your OS.
- On Windows: `C:\Program Files\Blackmagic Design\DaVinci Resolve\`
- On macOS: `/Applications/DaVinci Resolve/`

**DaVinci Resolve not running**
- The server requires Resolve to be fully loaded before connecting.
- Start Resolve first, wait for the UI to appear, then start the server.

**Import errors after setup**
- Run `uv sync` to ensure all dependencies are installed.
- Confirm you are running via `uv run python ...` or have activated `.venv`.

**Debug mode**
```bash
uv run python main.py --debug
```

**Dependency conflicts**
```bash
uv sync --reinstall
```
