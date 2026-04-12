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
