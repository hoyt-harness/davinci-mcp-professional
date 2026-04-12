#!/usr/bin/env python3
"""
PyInstaller build script for DaVinci MCP Professional.

Produces standalone single-directory bundles in dist/:
  - davinci-mcp-server/  (pure MCP stdio server, no console noise)
  - davinci-mcp/         (interactive CLI with prerequisite checks)

Usage:
  uv run --extra build python build.py

The build extra installs PyInstaller. Alternatively install it manually:
  uv add --optional build pyinstaller
"""

import sys
import os
from pathlib import Path

try:
    import PyInstaller.__main__
except ImportError:
    print("[ERROR] PyInstaller not found.")
    print("        Install with: uv run --extra build python build.py")
    print("        Or manually:  uv add --optional build pyinstaller")
    sys.exit(1)

ROOT = Path(__file__).parent
SRC = ROOT / "src"

# ---------------------------------------------------------------------------
# Hidden imports
#
# PyInstaller's static analysis misses modules that are imported at runtime
# via importlib, __import__(), or behind try/except blocks.
# ---------------------------------------------------------------------------
HIDDEN_IMPORTS: list[str] = [
    # anyio: backends are selected at runtime by the event-loop policy
    "anyio._backends._asyncio",
    "anyio._backends._trio",
    # MCP internals used at connection time
    "mcp.server.stdio",
    "mcp.server.models",
    "mcp.server.lowlevel",
    "mcp.server.lowlevel.server",
    "mcp.types",
    # pydantic v2: validators and core are loaded dynamically
    "pydantic.deprecated.class_validators",
    "pydantic_core",
    # click / colorama: usually auto-detected, listed for safety
    "click",
    "colorama",
    "colorama.initialise",
    # importlib.metadata: used by __init__.py version fallback
    "importlib.metadata",
]

# On Windows, mcp pulls in pywin32 for named-pipe transport
if sys.platform == "win32":
    HIDDEN_IMPORTS += ["win32api", "win32con", "win32process", "pywintypes"]

# ---------------------------------------------------------------------------
# Packages to collect in full (Python files + data files + submodules).
# Needed for packages that rely heavily on runtime discovery.
# ---------------------------------------------------------------------------
COLLECT_ALL: list[str] = [
    "mcp",
    "pydantic",
    "pydantic_core",
    "anyio",
    "httpx",
    "httpx_sse",
    "starlette",
    "sse_starlette",
]


def _args(name: str, script: Path) -> list[str]:
    """Assemble the PyInstaller argument list for one target."""
    args = [
        str(script),
        "--name", name,
        "--onedir",               # directory bundle — avoids AV false positives
        "--noconfirm",            # overwrite previous dist without prompting
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        "--paths", str(SRC),      # ensure src/ is on the analysis path
    ]

    for imp in HIDDEN_IMPORTS:
        args += ["--hidden-import", imp]

    for pkg in COLLECT_ALL:
        args += ["--collect-all", pkg]

    return args


def build_target(name: str, script_name: str) -> bool:
    """
    Build one executable bundle. Returns True on success.

    The MCP server communicates over stdio (JSON-RPC), so we deliberately
    do NOT pass --noconsole / --windowed. Hiding the console on Windows
    would break the stdio transport that Claude Desktop uses.
    """
    script = ROOT / script_name
    if not script.exists():
        print(f"[ERROR] Entry point not found: {script}")
        return False

    print(f"\n{'=' * 60}")
    print(f"  Building: {name}  ({script_name})")
    print(f"{'=' * 60}\n")

    args = _args(name, script)

    try:
        PyInstaller.__main__.run(args)
    except SystemExit as exc:
        if exc.code != 0:
            print(f"\n[ERROR] PyInstaller exited with code {exc.code}")
            return False
    except Exception as exc:  # noqa: BLE001
        print(f"\n[ERROR] Build failed: {exc}")
        return False

    output_dir = ROOT / "dist" / name
    if output_dir.exists():
        print(f"\n[OK] Output directory: {output_dir}")
        return True

    print(f"\n[ERROR] Expected output not found: {output_dir}")
    return False


def main() -> int:
    targets = [
        ("davinci-mcp-server", "mcp_server.py"),
        ("davinci-mcp",        "main.py"),
    ]

    results: list[tuple[str, bool]] = []
    for name, script in targets:
        results.append((name, build_target(name, script)))

    print(f"\n{'=' * 60}")
    print("  Build Summary")
    print(f"{'=' * 60}")
    for name, ok in results:
        tag = "[OK]    " if ok else "[FAILED]"
        print(f"  {tag}  dist/{name}/")

    if all(ok for _, ok in results):
        print(f"\nExecutables are inside their respective dist/ subdirectories.")
        if sys.platform == "win32":
            print("  dist/davinci-mcp-server/davinci-mcp-server.exe")
            print("  dist/davinci-mcp/davinci-mcp.exe")
        else:
            print("  dist/davinci-mcp-server/davinci-mcp-server")
            print("  dist/davinci-mcp/davinci-mcp")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
