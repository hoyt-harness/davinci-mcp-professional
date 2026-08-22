# SPDX-License-Identifier: GPL-3.0-or-later
"""
Domain modules for the DaVinci Resolve MCP server.

Each domain encapsulates a subset of the Resolve API. Domains register
dynamically via the kernel's activate_domain tool.
"""

from .registry import DOMAIN_REGISTRY, DomainModule

__all__ = ["DOMAIN_REGISTRY", "DomainModule"]
