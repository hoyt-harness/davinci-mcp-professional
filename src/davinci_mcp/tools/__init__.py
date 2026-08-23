# SPDX-License-Identifier: GPL-3.0-or-later
"""
Kernel tool definitions for the DaVinci Resolve MCP server.

Only tools that are always useful regardless of active domain belong here.
Domain-specific tool definitions live in their respective domain modules.
"""

import mcp.types as types

from ..domains.registry import DOMAIN_REGISTRY


def get_all_tools() -> list[types.Tool]:
    """Return the fixed kernel tool set."""
    domain_names = sorted(DOMAIN_REGISTRY)
    return [
        types.Tool(
            name="activate_domain",
            description=(
                "Activate a domain to make its tools available. "
                f"Available domains: {', '.join(domain_names)}. "
                "Call list_domains to see current activation status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to activate",
                        "enum": domain_names,
                    }
                },
                "required": ["domain"],
            },
        ),
        types.Tool(
            name="deactivate_domain",
            description=(
                "Deactivate a domain to remove its tools from the active tool list."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to deactivate",
                    }
                },
                "required": ["domain"],
            },
        ),
        types.Tool(
            name="list_domains",
            description=(
                "List all registered domains and their activation status. "
                "Use this to discover available domains before calling activate_domain."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_version",
            description="Get DaVinci Resolve version information",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_current_page",
            description=(
                "Get the current page open in DaVinci Resolve"
                " (Edit, Color, Fusion, etc.)"
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="switch_page",
            description="Switch to a specific page in DaVinci Resolve",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "string",
                        "description": "The page to switch to",
                        "enum": [
                            "media",
                            "cut",
                            "edit",
                            "fusion",
                            "color",
                            "fairlight",
                            "deliver",
                        ],
                    }
                },
                "required": ["page"],
            },
        ),
    ]
