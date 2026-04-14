"""
Platform detection and environment setup utilities.
"""

import os
import platform
import sys
from pathlib import Path


def get_platform() -> str:
    """Get the current platform name."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        return system


def get_resolve_paths() -> dict[str, Path]:
    """Get platform-specific paths for DaVinci Resolve scripting API."""
    current_platform = get_platform()

    if current_platform == "macos":
        api_path = Path(
            "/Library/Application Support/Blackmagic Design"
            "/DaVinci Resolve/Developer/Scripting"
        )
        lib_path = Path(
            "/Applications/DaVinci Resolve/DaVinci Resolve.app"
            "/Contents/Libraries/Fusion/fusionscript.so"
        )

    elif current_platform == "windows":
        program_data = Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
        program_files = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files"))

        api_path = (
            program_data
            / "Blackmagic Design"
            / "DaVinci Resolve"
            / "Support"
            / "Developer"
            / "Scripting"
        )
        lib_path = (
            program_files / "Blackmagic Design" / "DaVinci Resolve" / "fusionscript.dll"
        )

    elif current_platform == "linux":
        # Default Linux paths - may need adjustment based on installation
        api_path = Path("/opt/resolve/Developer/Scripting")
        lib_path = Path("/opt/resolve/libs/fusionscript.so")

    else:
        raise RuntimeError(f"Unsupported platform: {current_platform}")

    return {
        "api_path": api_path,
        "lib_path": lib_path,
        "modules_path": api_path / "Modules",
    }


def setup_resolve_environment() -> bool:
    """Set up environment variables for DaVinci Resolve scripting."""
    try:
        paths = get_resolve_paths()

        # Set environment variables
        os.environ["RESOLVE_SCRIPT_API"] = str(paths["api_path"])
        os.environ["RESOLVE_SCRIPT_LIB"] = str(paths["lib_path"])

        # Add modules path to Python path if not already there
        modules_path_str = str(paths["modules_path"])
        if modules_path_str not in sys.path:
            sys.path.insert(0, modules_path_str)

        # On Windows (Python 3.8+), the default DLL search path excludes
        # directories formerly found via PATH.  fusionscript.dll depends
        # on sibling DLLs in the Resolve install directory (lua5.1.dll,
        # tbbmalloc.dll, etc.) so we must add that directory explicitly.
        if platform.system().lower() == "windows":
            lib_dir = paths["lib_path"].parent
            if lib_dir.exists():
                os.add_dll_directory(str(lib_dir))

        return True
    except Exception:
        return False


def check_resolve_installation() -> dict[str, bool]:
    """Check if DaVinci Resolve is properly installed."""
    paths = get_resolve_paths()

    return {
        "api_path_exists": paths["api_path"].exists(),
        "lib_path_exists": paths["lib_path"].exists(),
        "modules_path_exists": paths["modules_path"].exists(),
    }


def check_resolve_running() -> bool:
    """Check if DaVinci Resolve is currently running."""
    current_platform = get_platform()

    try:
        if current_platform == "windows":
            import subprocess

            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Resolve.exe"],
                capture_output=True,
                text=True,
                check=False,
            )
            return "Resolve.exe" in result.stdout

        elif current_platform in ["macos", "linux"]:
            import subprocess

            result = subprocess.run(
                ["pgrep", "-f", "DaVinci Resolve"], capture_output=True, check=False
            )
            return result.returncode == 0

        return False
    except Exception:
        return False


_probe_cache: tuple[bool, str] | None = None


def probe_resolve_scripting(*, use_cache: bool = True) -> tuple[bool, str]:
    """
    Test that fusionscript loads without crashing the Python process.

    Imports DaVinciResolveScript in a child process so that an ABI-level
    crash (segfault) kills only the child, not the MCP server.  The probe
    does NOT call ``scriptapp("Resolve")`` — that would open an IPC
    connection to Resolve whose teardown-on-exit can block subsequent
    connections.  Only the DLL import is tested, which is where the ABI
    crash occurs.

    A successful result is cached for the lifetime of the process (the
    DLL's ABI compatibility will not change while the server is running).
    Failures are never cached so the user can fix the issue and retry.

    Skipped inside PyInstaller bundles where sys.executable is the
    frozen EXE.

    Returns
    -------
    (success, message)
        *success* is True when the DLL loaded without crashing.
        *message* is a short status on success, or a diagnostic on
        failure.
    """
    import subprocess as _sp

    global _probe_cache  # noqa: PLW0603

    if use_cache and _probe_cache is not None:
        return _probe_cache

    # In a PyInstaller bundle sys.executable is the EXE, not python,
    # so a "-c" probe cannot work.  The frozen bundle was built with a
    # specific Python version, so skip the probe.
    if getattr(sys, "frozen", False):
        _probe_cache = (True, "probe skipped (frozen executable)")
        return _probe_cache

    paths = get_resolve_paths()
    lib_path = str(paths["lib_path"])
    modules_path = str(paths["modules_path"])

    # Build a small script that only imports the DLL — no IPC.
    lines: list[str] = ["import sys, os"]

    if platform.system().lower() == "windows":
        resolve_dir = str(paths["lib_path"].parent)
        lines.append(f"os.add_dll_directory({resolve_dir!r})")

    lines += [
        f"os.environ['RESOLVE_SCRIPT_LIB'] = {lib_path!r}",
        f"sys.path.insert(0, {modules_path!r})",
        "try:",
        "    import DaVinciResolveScript",
        "    print('OK')",
        "except SystemError:",
        "    print('FAIL:INIT_ERROR')",
        "except ImportError as e:",
        "    print('FAIL:IMPORT_ERROR:' + str(e))",
        "except Exception as e:",
        "    print('FAIL:ERROR:' + str(e))",
    ]

    probe_code = "\n".join(lines)

    try:
        # stdin must be DEVNULL — the parent's stdin is the MCP
        # transport pipe and inheriting it lets the child steal
        # JSON-RPC bytes or hang reading from it.  close_fds
        # prevents other inherited handles on Windows.
        result = _sp.run(
            [sys.executable, "-c", probe_code],
            stdin=_sp.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            close_fds=True,
        )
    except _sp.TimeoutExpired:
        return (False, "Timed out probing DaVinci Resolve scripting API")
    except Exception as e:
        return (False, f"Failed to run scripting probe: {e}")

    stdout = result.stdout.strip()

    # Non-zero exit with no Python-level output means the child process
    # crashed (segfault).  This is the ABI-mismatch scenario.
    # Cache this — the DLL's ABI won't change while the server runs.
    if result.returncode != 0 and not stdout:
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        _probe_cache = (
            False,
            f"fusionscript.dll crashed during initialization "
            f"(Python {py_ver} may be incompatible). "
            f"DaVinci Resolve typically requires Python 3.10 or 3.11. "
            f"Recreate the virtual environment with: "
            f"uv venv --python 3.10",
        )
        return _probe_cache

    if stdout == "OK":
        _probe_cache = (True, "fusionscript loaded successfully")
        return _probe_cache

    # DLL init failures are deterministic for this process; cache them.
    if "INIT_ERROR" in stdout:
        _probe_cache = (
            False,
            "fusionscript.dll failed to initialize. "
            "External scripting may require DaVinci Resolve Studio, "
            "or scripting access may need to be enabled in "
            "Resolve Preferences > System > General.",
        )
        return _probe_cache

    if "IMPORT_ERROR" in stdout:
        detail = stdout.split(":", 2)[-1] if stdout.count(":") >= 2 else ""
        _probe_cache = (
            False,
            f"Failed to import DaVinciResolveScript: {detail}",
        )
        return _probe_cache

    # Anything else (unexpected output) is not cached — may be transient.
    return (
        False,
        f"Scripting probe failed: {stdout or result.stderr.strip()}",
    )
