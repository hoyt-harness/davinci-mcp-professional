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


def check_python_runtime_compatibility() -> tuple[bool, str]:
    """
    Detect whether fusionscript.dll will load a conflicting Python runtime.

    On Windows, DaVinci Resolve's fusionscript.dll discovers the system
    Python installation via the Windows registry and calls LoadLibrary
    with a full path to that installation's python3.dll.  If the MCP
    server is running under a *different* Python installation (e.g. a
    uv-managed Python), two incompatible Python runtimes end up in the
    same process and the server crashes with an access violation.

    This function compares the running Python's python3.dll path to the
    registry-registered Python's install directory.  If they differ, it
    returns an actionable diagnostic.

    On non-Windows platforms or inside PyInstaller bundles the check is
    skipped (always returns success).
    """
    if platform.system().lower() != "windows":
        return (True, "")

    if getattr(sys, "frozen", False):
        return (True, "")

    try:
        import ctypes
        import winreg

        # --- Find the registry-registered Python install path ---
        base_key = r"SOFTWARE\Python\PythonCore"
        registered_path: str | None = None
        registered_ver: str | None = None

        try:
            core_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key)
        except FileNotFoundError:
            # No system Python registered — fusionscript.dll may fail to
            # find Python at all, but that is a different error path.
            return (True, "")

        # Pick the highest registered Python 3.x version.
        i = 0
        while True:
            try:
                ver = winreg.EnumKey(core_key, i)
                i += 1
            except OSError:
                break
            if not ver.startswith("3"):
                continue
            try:
                ip_key = winreg.OpenKey(core_key, ver + r"\InstallPath")
                val, _ = winreg.QueryValueEx(ip_key, "")
                winreg.CloseKey(ip_key)
                if registered_ver is None or ver > registered_ver:
                    registered_ver = ver
                    registered_path = val
            except (FileNotFoundError, OSError):
                continue
        winreg.CloseKey(core_key)

        if not registered_path:
            return (True, "")

        # --- Find the running Python's python3.dll location ---
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        GetModuleHandleW = kernel32.GetModuleHandleW
        GetModuleHandleW.restype = ctypes.c_void_p
        GetModuleFileNameW = kernel32.GetModuleFileNameW

        handle = GetModuleHandleW("python3.dll")
        if not handle:
            return (True, "")

        buf = ctypes.create_unicode_buffer(512)
        GetModuleFileNameW(ctypes.c_void_p(handle), buf, 512)
        loaded_python3_path = buf.value

        if not loaded_python3_path:
            return (True, "")

        # --- Compare directories ---
        loaded_dir = os.path.normcase(os.path.dirname(loaded_python3_path))
        registry_dir = os.path.normcase(registered_path.rstrip("\\/"))

        if loaded_dir == registry_dir:
            return (True, "")

        return (
            False,
            f"Python runtime conflict: this process loaded python3.dll "
            f"from {os.path.dirname(loaded_python3_path)}, but DaVinci "
            f"Resolve will load Python from the system installation at "
            f"{registered_path.rstrip(chr(92) + '/')}. Two Python "
            f"runtimes in one process will crash. Create the virtual "
            f"environment from the system Python instead:\n"
            f'  uv venv --python "{registered_path}python.exe"\n'
            f"  uv sync",
        )

    except Exception:
        # If anything goes wrong in detection, don't block startup.
        return (True, "")
