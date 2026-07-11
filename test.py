#!/usr/bin/env python3
"""
Test script for the new DaVinci Resolve MCP implementation.
"""

import os
import subprocess
import sys
from pathlib import Path

# Get the current directory and virtual environment
current_dir = Path(__file__).parent
venv_dir = current_dir / ".venv"

# Check if we're in the virtual environment
if not hasattr(sys, "real_prefix") and not (
    hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
):
    # Not in virtual environment, run with the venv python
    if os.name == "nt":  # Windows
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:  # macOS/Linux
        venv_python = venv_dir / "bin" / "python"

    if venv_python.exists():
        print(f"Running tests with virtual environment: {venv_python}")
        # Re-run this script with the virtual environment Python
        result = subprocess.run(
            [str(venv_python), __file__] + sys.argv[1:], check=False
        )
        sys.exit(result.returncode)
    else:
        print(f"Virtual environment not found at {venv_dir}")
        print("Please run 'python setup.py' first")
        sys.exit(1)

# Add the src directory to Python path
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from davinci_mcp.resolve_client import DaVinciResolveClient, DaVinciResolveError
from davinci_mcp.utils import (
    check_resolve_installation,
    check_resolve_running,
    get_platform,
    setup_resolve_environment,
)


def test_platform_detection():
    """Test platform detection."""
    print("Testing platform detection...")
    platform = get_platform()
    print(f"  Detected platform: {platform}")
    return True


def test_resolve_installation():
    """Test DaVinci Resolve installation check."""
    print("Testing DaVinci Resolve installation...")

    installation = check_resolve_installation()

    print(f"  API path exists: {installation['api_path_exists']}")
    print(f"  Library exists: {installation['lib_path_exists']}")
    print(f"  Modules path exists: {installation['modules_path_exists']}")

    return all(installation.values())


def test_resolve_running():
    """Test DaVinci Resolve running check."""
    print("Testing DaVinci Resolve running check...")

    running = check_resolve_running()
    print(f"  DaVinci Resolve running: {running}")

    return running


def test_environment_setup():
    """Test environment setup."""
    print("Testing environment setup...")

    result = setup_resolve_environment()
    print(f"  Environment setup successful: {result}")

    return result


def test_resolve_client():
    """Test DaVinci Resolve client."""
    print("Testing DaVinci Resolve client...")

    client = DaVinciResolveClient()

    try:
        # Test connection
        print("  Attempting to connect...")
        client.connect()
        print(f"  Connected: {client.is_connected()}")

        # Test basic operations
        print("  Testing basic operations...")
        version = client.get_version()
        print(f"    Version: {version}")

        page = client.get_current_page()
        print(f"    Current page: {page}")

        projects = client.list_projects()
        print(f"    Available projects: {len(projects)}")
        for i, project in enumerate(projects[:3]):  # Show first 3
            print(f"      {i + 1}. {project}")

        current_project = client.get_current_project_name()
        print(f"    Current project: {current_project}")

        if current_project:
            timelines = client.list_timelines()
            print(f"    Available timelines: {len(timelines)}")
            for i, timeline in enumerate(timelines[:3]):  # Show first 3
                print(f"      {i + 1}. {timeline}")

            current_timeline = client.get_current_timeline_name()
            print(f"    Current timeline: {current_timeline}")

            media_clips = client.list_media_clips()
            print(f"    Media clips: {len(media_clips)}")
            for i, clip in enumerate(media_clips[:3]):  # Show first 3
                print(f"      {i + 1}. {clip['name']} ({clip['duration']} frames)")

        # Disconnect
        client.disconnect()
        print(f"  Disconnected: {not client.is_connected()}")

        return True

    except DaVinciResolveError as e:
        print(f"  DaVinci Resolve error: {e}")
        return False
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("  DaVinci MCP Professional v2.1.0 Test Suite")
    print("=" * 60)

    tests = [
        ("Platform Detection", test_platform_detection),
        ("DaVinci Resolve Installation", test_resolve_installation),
        ("DaVinci Resolve Running", test_resolve_running),
        ("Environment Setup", test_environment_setup),
        ("Resolve Client", test_resolve_client),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  Result: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"  Result: ✗ ERROR - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1

    print(f"\nPassed: {passed}/{len(results)}")

    if passed == len(results):
        print("\n🎉 All tests passed! The new implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
