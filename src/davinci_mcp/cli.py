"""
Command line interface for DaVinci Resolve MCP Server.
"""

import asyncio
import logging
import os
import sys

import click
from colorama import Fore, Style
from colorama import init as init_colorama

# Set UTF-8 encoding for Windows console only for direct output, not for stdio
if os.name == "nt":  # Windows
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Only set console encoding if we're running in interactive mode
    # Don't modify stdout/stderr if they might be used by MCP stdio
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        try:
            # Store original stdout/stderr in case we need them
            _original_stdout = sys.stdout
            _original_stderr = sys.stderr
        except (AttributeError, OSError):
            pass  # Fallback to default behavior

from . import __version__
from .server import DaVinciMCPServer
from .utils import check_resolve_installation, check_resolve_running

# Initialize colorama for cross-platform colored output
init_colorama()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - "
    f"{Fore.YELLOW}%(name)s{Style.RESET_ALL} - "
    f"%(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def print_status(message: str, status: str = "INFO") -> None:
    """Print a colored status message."""
    if status == "OK":
        click.echo(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {message}")
    elif status == "ERROR":
        click.echo(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
    elif status == "WARNING":
        click.echo(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")
    else:
        click.echo(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")


def check_prerequisites() -> bool:
    """Check if prerequisites are met."""
    print_status("Checking DaVinci Resolve installation...")

    installation = check_resolve_installation()

    if not installation["api_path_exists"]:
        print_status("DaVinci Resolve API path not found", "ERROR")
        return False

    if not installation["lib_path_exists"]:
        print_status("DaVinci Resolve library not found", "ERROR")
        return False

    if not installation["modules_path_exists"]:
        print_status("DaVinci Resolve modules path not found", "ERROR")
        return False

    print_status("DaVinci Resolve installation verified", "OK")

    print_status("Checking if DaVinci Resolve is running...")
    if not check_resolve_running():
        print_status("DaVinci Resolve is not running", "ERROR")
        print_status(
            "Please start DaVinci Resolve before running the MCP server", "WARNING"
        )
        return False

    print_status("DaVinci Resolve is running", "OK")
    return True


@click.command()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--skip-checks", is_flag=True, help="Skip prerequisite checks")
def main(debug: bool = False, skip_checks: bool = False) -> None:
    """Start the DaVinci Resolve MCP Server."""

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("davinci_mcp").setLevel(logging.DEBUG)
        print_status("Debug logging enabled")

    # Print banner
    vi = sys.version_info
    py_ver = f"{vi.major}.{vi.minor}.{vi.micro}"
    click.echo(f"\n{Fore.MAGENTA}{'=' * 60}{Style.RESET_ALL}")
    click.echo(
        f"{Fore.MAGENTA}  DaVinci MCP Professional v{__version__}{Style.RESET_ALL}"
    )
    click.echo(f"{Fore.MAGENTA}  Python {py_ver}{Style.RESET_ALL}")
    click.echo(f"{Fore.MAGENTA}{'=' * 60}{Style.RESET_ALL}\n")

    # Check prerequisites unless skipped
    if not skip_checks:
        if not check_prerequisites():
            print_status("Prerequisites not met. Exiting.", "ERROR")
            sys.exit(1)

        click.echo()  # Empty line for spacing

    # Start the server
    try:
        print_status("Starting MCP server...")
        server = DaVinciMCPServer()

        asyncio.run(server.run())

    except KeyboardInterrupt:
        print_status("\nShutting down server...", "WARNING")
        sys.exit(0)
    except Exception as e:
        print_status(f"Server error: {e}", "ERROR")
        if debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
