#!/usr/bin/env python3
"""
Main entry point for DaVinci Resolve MCP Server.
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the current directory and virtual environment
current_dir = Path(__file__).parent
venv_dir = current_dir / ".venv"

# Check if we're in the virtual environment (skip when running as a frozen executable)
if not getattr(sys, 'frozen', False) and not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    # Not in virtual environment, run with the venv python
    if os.name == "nt":  # Windows
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:  # macOS/Linux
        venv_python = venv_dir / "bin" / "python"
    
    if venv_python.exists():
        print(f"Starting with virtual environment: {venv_python}")
        # Re-run this script with the virtual environment Python
        result = subprocess.run([str(venv_python), __file__] + sys.argv[1:], check=False)
        sys.exit(result.returncode)
    else:
        print(f"Virtual environment not found at {venv_dir}")
        print("Please run 'python setup.py' first")
        sys.exit(1)

# Add the src directory to Python path
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from davinci_mcp.cli import main

if __name__ == "__main__":
    main()
