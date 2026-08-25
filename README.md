# DaVinci MCP Professional

An enterprise-grade Model Context Protocol (MCP) server that exposes the full
DaVinci Resolve scripting API to AI assistants. This project is a hard fork of
[davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp) by
@samuelgursky, rewritten and maintained independently.

Supported MCP clients: **Claude Desktop**, **Claude Code**, Gemini CLI, ChatGPT.

---

## How It Works

Most MCP servers dump every available tool into the AI's context window at
session start. With a large API surface, that means hundreds of tool definitions
loaded whether or not the current task needs them — wasting tokens and slowing
response time.

This server uses a **kernel + domain** architecture instead:

- **Kernel tools** (always available, 6 total): `activate_domain`,
  `deactivate_domain`, `list_domains`, `get_version`, `get_current_page`,
  `switch_page`. These are useful regardless of what you're doing in Resolve.
- **Domain tools** (loaded on demand): the full Resolve API is organized into
  domains — Project Management, Timeline Operations, Media Pool, and more. Call
  `activate_domain("project_management")` and the server fires a
  `notifications/tools/list_changed` event; your MCP client refetches the tool
  list and the domain's tools are immediately available, no session restart
  needed.

Context cost at session start is bounded by the kernel alone. You expand it
deliberately, only for the domains your current workflow actually needs.

---

## Who This Is For

This server is built for **independent creators and boutique studios** where AI
API costs are real and context overhead matters.

**Compared to [davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp):**

`davinci-resolve-mcp` is a well-maintained alternative with 353 tool definitions
loaded into the AI's context at every session start. For a well-resourced
production environment — a studio running Claude on dedicated infrastructure
with token budgets absorbed into overhead — that approach is solid and the
dense tool coverage is immediately useful.

This server makes a different architectural choice: 6 kernel tools at session
start, domains activated on demand, context cost proportional to the work at
hand. The full API surface (289 tools across 9 domains) is available, but none
of it loads until you ask for it.

| | `davinci-resolve-mcp` | `davinci-mcp-professional` |
|---|---|---|
| Tools at session start | 353 | **6** |
| Total tools available | 353 | 289 |
| Domain activation | — | On demand |

If you're an independent creator or a small shop where every Claude API call
has a cost, this architecture was designed for you. Professional-grade Resolve
integration without professional-budget infrastructure requirements.

---

## Prerequisites

- [DaVinci Resolve Studio](https://www.blackmagicdesign.com/products/davinciresolve)
  installed and licensed (the free edition does not support external scripting)
- Python 3.10 or later, **installed system-wide** via the
  [official installer](https://www.python.org/downloads/) with "Add to PATH"
  and "Install for all users" selected

  > **Windows — critical:** DaVinci Resolve locates Python through the Windows
  > registry and loads `python3.dll` by full path from that installation.
  > A uv-managed or user-only Python install uses a *different* DLL and will
  > cause a two-runtime crash at connection time. Always create the virtual
  > environment from the **system Python** (see Installation below).

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python
  package and virtual environment manager

---

## Installation

### From source

```bash
git clone https://github.com/hoyt-harness/davinci-mcp-professional.git
cd davinci-mcp-professional
```

**Windows** — find your system Python path, then create the venv from it:

```powershell
py -0p   # lists installed Python versions and their paths
```

```bash
uv venv --python "C:\Program Files\Python314\python.exe"   # adjust to your path
uv sync
```

**macOS / Linux** — `uv venv` with no `--python` flag works if the default
`python3` is a system-wide installation:

```bash
uv venv
uv sync
```

### Standalone Windows executable

Download the pre-built Windows binaries from
[Releases](https://github.com/hoyt-harness/davinci-mcp-professional/releases).
No Python installation required.

| Executable | Purpose |
|---|---|
| `davinci-mcp-server.exe` | MCP server launched by your AI client. Use this in `claude_desktop_config.json`. |
| `davinci-mcp.exe` | Interactive CLI with a startup banner and prerequisite checks. Use this to verify connectivity before configuring a client. |

---

## Configuring Claude Desktop

Locate or create `claude_desktop_config.json`:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**From source (Windows):**
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

**From source (macOS):**
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

**Standalone Windows executable:**
```json
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci MCP Professional",
      "command": "C:\\path\\to\\davinci-mcp-server\\davinci-mcp-server.exe",
      "args": []
    }
  }
}
```

Restart Claude Desktop after saving the config.

---

## Configuring Claude Code

```bash
claude mcp add -s user davinci-resolve \
  -- /path/to/davinci-mcp-professional/.venv/Scripts/python.exe \
  /path/to/davinci-mcp-professional/mcp_server.py
```

This writes to `~/.claude.json` and makes the server available in all Claude
Code sessions without per-project configuration.

---

## Basic Usage

1. Start DaVinci Resolve and wait for it to fully load.
2. Start the MCP server (Claude Desktop / Claude Code does this automatically).
3. The server starts with **6 kernel tools** available. Use `list_domains` to
   see what domains are registered, then activate what you need:

```
What version of DaVinci Resolve is running?          # get_version — no activation needed
List the available domains.                           # list_domains
Activate the project management domain.              # activate_domain("project_management")
List all projects in the database.                    # list_projects — now available
Create a new timeline called "Act 1".                 # needs timeline_operations domain
Switch to the Color page.                             # switch_page — always in kernel
```

### Domain overview

| Domain | Activates | Tools |
|---|---|---|
| `project_management` | `activate_domain("project_management")` | Open/save/close/rename/delete projects, folder navigation, database switching |
| `timeline_operations` | `activate_domain("timeline_operations")` | Tracks, markers, timecode, export/import, generators, Fusion clips |
| `media_pool` | `activate_domain("media_pool")` | Folder management, clip operations, relink, mattes, stereo |

### Destructive operations require explicit confirmation

Any tool that permanently modifies or deletes data requires `confirm: true` in
its arguments. If you call a destructive tool without it, the server returns a
detailed error message describing exactly what would be destroyed and what you
need to set to proceed. This applies to operations like `delete_project`,
`delete_timeline`, `delete_track`, `delete_media_pool_clips`, and others.

---

## Further Reading

| Document | Purpose |
|---|---|
| [USING.md](USING.md) | Developer setup, architecture, build instructions, contributing |
| [BUGS.md](BUGS.md) | Troubleshooting and bug reporting |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [COPYING](COPYING) | GPL-3.0 license |
