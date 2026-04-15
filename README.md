# DaVinci MCP Professional

An enterprise-grade Model Context Protocol (MCP) server that exposes the full
DaVinci Resolve scripting API to AI assistants. This project is a hard fork of
[davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp) by
@samuelgursky, rewritten and maintained independently.

Supported MCP clients: **Claude Desktop** (primary), Gemini CLI, ChatGPT.

---

## Prerequisites

- [DaVinci Resolve Studio](https://www.blackmagicdesign.com/products/davinciresolve)
  installed and licensed (the free edition does not support external scripting)
- Python 3.10 or later, **installed system-wide** (the installer from
  [python.org](https://www.python.org/downloads/) with "Add to PATH" and
  "Install for all users" selected). On Windows, DaVinci Resolve locates
  Python through the Windows registry; a uv-managed or user-only Python
  install will not be found and will cause a crash.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python
  package and virtual environment manager

---

## Installation

### From source (recommended)

```bash
git clone https://github.com/Positronikal/davinci-mcp-professional.git
cd davinci-mcp-professional
uv venv
uv sync
```

### Standalone Windows executable

Download the pre-built Windows binaries from
[Releases](https://github.com/Positronikal/davinci-mcp-professional/releases).
No Python installation required.

The release includes two executables:

| Executable | Purpose |
|---|---|
| `davinci-mcp-server.exe` | **MCP server** — launched automatically by Claude Desktop (or another MCP client). Communicates over stdio with no console output. Use this in your `claude_desktop_config.json`. |
| `davinci-mcp.exe` | **Interactive CLI** — for running the server manually in a terminal. Displays a startup banner, checks that DaVinci Resolve is running, and supports `--debug` and `--skip-checks` flags. |

Most users only need `davinci-mcp-server.exe` configured in their MCP client.
`davinci-mcp.exe` is useful for troubleshooting or verifying that the server
can connect to Resolve before configuring a client.

---

## Configuring Claude Desktop

Locate or create your `claude_desktop_config.json` file:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the server entry:

**Running from source (Windows):**
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

**Running from source (macOS):**
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

**Using the standalone Windows executable:**
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

## Other Supported Clients

**Gemini CLI** and **ChatGPT** support the MCP standard and can connect to this
server using the same `mcp_server.py` entry point. Their MCP integration is
still maturing — consult each client's documentation for the current
configuration method.

---

## Basic Usage

1. Start DaVinci Resolve and wait for it to fully load.
2. Start the MCP server (Claude Desktop does this automatically when configured).
3. Ask your AI assistant to interact with Resolve:

```
What version of DaVinci Resolve is running?
List all projects in the database.
Create a new timeline called "Act 1".
Switch to the Color page.
Import /path/to/clip.mp4 into the media pool.
```

---

## Further Reading

| Document | Purpose |
|---|---|
| [USING.md](USING.md) | Developer setup, build instructions, contributing |
| [BUGS.md](BUGS.md) | Troubleshooting and bug reporting |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [COPYING.md](COPYING.md) | GPL-3.0 license |

For developer setup, build instructions, and contribution guidelines,
see **USING.md**.
