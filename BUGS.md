# Support

**Issues**: Report bugs and feature requests via
[GitHub Issues](https://github.com/Positronikal/davinci-mcp-professional/issues).

---

## Troubleshooting

### DaVinci Resolve Not Found

If you get errors about DaVinci Resolve not being found:

1. Confirm DaVinci Resolve is installed in the default location for your OS.
2. On Windows, Resolve must be in `Program Files`, not `Program Files (x86)`.
3. Run `uv run python main.py` to see the prerequisite check output.

### DaVinci Resolve Not Running

The server requires DaVinci Resolve to be running before it can connect:

1. Start DaVinci Resolve.
2. Wait for it to fully load (project manager visible).
3. Then start or restart the MCP server.

### Import Errors

If you get Python import errors:

1. Confirm the virtual environment exists: `.venv/` should be present in the
   project root. If not, run `uv venv && uv sync`.
2. Run all commands through `uv run` or activate `.venv` first.
3. If the lockfile is out of sync, run `uv sync --reinstall`.

### Debug Mode

```bash
uv run python main.py --debug
```

This enables detailed logging for all MCP and Resolve API activity.

### Dependency Conflicts

```bash
uv sync --reinstall
```

### Checking the Installation

```bash
uv run python -c "from davinci_mcp import __version__; print(__version__)"
```

This should print the version string derived from the latest git tag.
