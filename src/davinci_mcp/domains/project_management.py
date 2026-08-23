# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain 1: Project Management tools."""

from typing import Any

import mcp.types as types

from ..resolve_client import DaVinciResolveClient

_DESTRUCTIVE = "DESTRUCTIVE — permanent, no API undo. "


def _confirm_gate(tool_name: str, arguments: dict[str, Any], description: str) -> str | None:
    """Return an error string if confirm=True is missing, else None."""
    if not arguments.get("confirm", False):
        return (
            f"{_DESTRUCTIVE}{description} "
            f"Set confirm=true to proceed."
        )
    return None


class ProjectManagementDomain:
    name = "project_management"
    description = (
        "Full project lifecycle: open, save, close, rename, delete, export/import/archive, "
        "project folder navigation, and database management"
    )

    def get_tools(self) -> list[types.Tool]:  # noqa: PLR0915
        return [
            # ----------------------------------------------------------------
            # Original migrated tools
            # ----------------------------------------------------------------
            types.Tool(
                name="list_projects",
                description="List all available projects in the current database folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_project",
                description="Get the name of the currently open project",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="open_project",
                description="Open a project by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Project name to open"},
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="create_project",
                description="Create a new project with the given name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name for the new project"},
                    },
                    "required": ["name"],
                },
            ),
            # ----------------------------------------------------------------
            # Save / rename
            # ----------------------------------------------------------------
            types.Tool(
                name="save_project",
                description="Save the current project",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="rename_project",
                description="Rename the currently open project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "new_name": {"type": "string", "description": "New project name"},
                    },
                    "required": ["new_name"],
                },
            ),
            types.Tool(
                name="get_project_attributes",
                description=(
                    "Get attributes of all projects in the current folder "
                    "(lastModifiedDate, creationDate, notes, liveCollaborationMode)"
                ),
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            # ----------------------------------------------------------------
            # Destructive project operations
            # ----------------------------------------------------------------
            types.Tool(
                name="close_project",
                description=(
                    f"{_DESTRUCTIVE}Close the current project. "
                    "Unsaved changes are lost. Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. Unsaved changes will be lost.",
                        },
                    },
                    "required": ["confirm"],
                },
            ),
            types.Tool(
                name="delete_project",
                description=(
                    f"{_DESTRUCTIVE}Permanently delete a project by name. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Project name to delete"},
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. Deletion cannot be undone.",
                        },
                    },
                    "required": ["name", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Export / import / archive / restore
            # ----------------------------------------------------------------
            types.Tool(
                name="export_project",
                description="Export a project to a .drp file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Project name to export"},
                        "file_path": {"type": "string", "description": "Destination .drp file path"},
                        "with_stills_and_luts": {
                            "type": "boolean",
                            "description": "Include gallery stills and LUTs in the export",
                        },
                    },
                    "required": ["name", "file_path", "with_stills_and_luts"],
                },
            ),
            types.Tool(
                name="import_project",
                description="Import a project from a .drp file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Source .drp file path"},
                        "project_name": {"type": "string", "description": "Name for the imported project"},
                    },
                    "required": ["file_path", "project_name"],
                },
            ),
            types.Tool(
                name="archive_project",
                description=(
                    f"{_DESTRUCTIVE}Archive a project to a .dra file with optional media. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Project name to archive"},
                        "file_path": {"type": "string", "description": "Destination .dra file path"},
                        "src_media": {"type": "boolean", "description": "Include source media"},
                        "render_cache": {"type": "boolean", "description": "Include render cache"},
                        "proxy_media": {"type": "boolean", "description": "Include proxy media"},
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. This operation cannot be undone.",
                        },
                    },
                    "required": ["name", "file_path", "src_media", "render_cache", "proxy_media", "confirm"],
                },
            ),
            types.Tool(
                name="restore_project",
                description=(
                    f"{_DESTRUCTIVE}Restore a project from a .dra archive. "
                    "Will overwrite if a project with the same name exists. Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Source .dra archive path"},
                        "project_name": {"type": "string", "description": "Name for the restored project"},
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. Will overwrite an existing project of the same name.",
                        },
                    },
                    "required": ["file_path", "project_name", "confirm"],
                },
            ),
            # ----------------------------------------------------------------
            # Project folder navigation
            # ----------------------------------------------------------------
            types.Tool(
                name="list_project_folders",
                description="List project subfolders in the current folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_project_folder",
                description="Get the name of the current project folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="create_project_folder",
                description="Create a project subfolder in the current folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_name": {"type": "string", "description": "Folder name to create"},
                    },
                    "required": ["folder_name"],
                },
            ),
            types.Tool(
                name="delete_project_folder",
                description=(
                    f"{_DESTRUCTIVE}Delete a project folder and all projects it contains. "
                    "Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_name": {"type": "string", "description": "Folder name to delete"},
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. Deletes the folder and all contained projects.",
                        },
                    },
                    "required": ["folder_name", "confirm"],
                },
            ),
            types.Tool(
                name="open_project_folder",
                description="Navigate into a project subfolder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_name": {"type": "string", "description": "Folder name to open"},
                    },
                    "required": ["folder_name"],
                },
            ),
            types.Tool(
                name="goto_root_folder",
                description="Navigate to the root project folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="goto_parent_folder",
                description="Navigate to the parent project folder",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            # ----------------------------------------------------------------
            # Database management
            # ----------------------------------------------------------------
            types.Tool(
                name="list_databases",
                description="List all available project databases",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="get_current_database",
                description="Get info about the current project database",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="set_current_database",
                description=(
                    f"{_DESTRUCTIVE}Switch to a different project database. "
                    "Closes the current project. Requires confirm=true."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "db_info": {
                            "type": "object",
                            "description": (
                                "Database descriptor: "
                                '{"DbType": "Disk"|"PostgreSQL", "DbName": "...", '
                                '"IpAddress": "..."}'
                            ),
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true. Closes the current project.",
                        },
                    },
                    "required": ["db_info", "confirm"],
                },
            ),
        ]

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any:
        # --- original migrated tools ---
        if tool_name == "list_projects":
            return client.list_projects()
        elif tool_name == "get_current_project":
            return client.get_current_project_name()
        elif tool_name == "open_project":
            name = arguments.get("name", "")
            result = client.open_project(name)
            return f"Opened project '{name}'" if result else f"Failed to open '{name}'"
        elif tool_name == "create_project":
            name = arguments.get("name", "")
            result = client.create_project(name)
            return f"Created project '{name}'" if result else f"Failed to create '{name}'"

        # --- save / rename ---
        elif tool_name == "save_project":
            result = client.save_project()
            return "Project saved" if result else "Save failed"
        elif tool_name == "rename_project":
            new_name = arguments.get("new_name", "")
            result = client.rename_project(new_name)
            return f"Project renamed to '{new_name}'" if result else "Rename failed"
        elif tool_name == "get_project_attributes":
            return client.get_project_attributes()

        # --- destructive project operations ---
        elif tool_name == "close_project":
            if err := _confirm_gate("close_project", arguments, "Closes the current project; unsaved changes are lost."):
                return err
            result = client.close_project()
            return "Project closed" if result else "Close failed"
        elif tool_name == "delete_project":
            name = arguments.get("name", "")
            if err := _confirm_gate("delete_project", arguments, f"Permanently deletes project '{name}'."):
                return err
            result = client.delete_project(name)
            return f"Deleted project '{name}'" if result else f"Delete failed for '{name}'"

        # --- export / import / archive / restore ---
        elif tool_name == "export_project":
            name = arguments.get("name", "")
            file_path = arguments.get("file_path", "")
            with_stills = bool(arguments.get("with_stills_and_luts", False))
            result = client.export_project(name, file_path, with_stills)
            return f"Exported '{name}' to {file_path}" if result else "Export failed"
        elif tool_name == "import_project":
            file_path = arguments.get("file_path", "")
            project_name = arguments.get("project_name", "")
            result = client.import_project(file_path, project_name)
            return f"Imported project as '{project_name}'" if result else "Import failed"
        elif tool_name == "archive_project":
            name = arguments.get("name", "")
            file_path = arguments.get("file_path", "")
            if err := _confirm_gate("archive_project", arguments, f"Archives project '{name}' to {file_path}."):
                return err
            result = client.archive_project(
                name,
                file_path,
                bool(arguments.get("src_media", False)),
                bool(arguments.get("render_cache", False)),
                bool(arguments.get("proxy_media", False)),
            )
            return f"Archived '{name}' to {file_path}" if result else "Archive failed"
        elif tool_name == "restore_project":
            file_path = arguments.get("file_path", "")
            project_name = arguments.get("project_name", "")
            if err := _confirm_gate("restore_project", arguments, f"Restores project from {file_path} as '{project_name}'."):
                return err
            result = client.restore_project(file_path, project_name)
            return f"Restored project as '{project_name}'" if result else "Restore failed"

        # --- folder navigation ---
        elif tool_name == "list_project_folders":
            return client.list_project_folders()
        elif tool_name == "get_current_project_folder":
            return client.get_current_project_folder()
        elif tool_name == "create_project_folder":
            folder_name = arguments.get("folder_name", "")
            result = client.create_project_folder(folder_name)
            return f"Created folder '{folder_name}'" if result else "Folder creation failed"
        elif tool_name == "delete_project_folder":
            folder_name = arguments.get("folder_name", "")
            if err := _confirm_gate("delete_project_folder", arguments, f"Permanently deletes folder '{folder_name}' and all projects it contains."):
                return err
            result = client.delete_project_folder(folder_name)
            return f"Deleted folder '{folder_name}'" if result else "Delete failed"
        elif tool_name == "open_project_folder":
            folder_name = arguments.get("folder_name", "")
            result = client.open_project_folder(folder_name)
            return f"Opened folder '{folder_name}'" if result else "Open failed"
        elif tool_name == "goto_root_folder":
            result = client.goto_root_folder()
            return "Navigated to root folder" if result else "Navigation failed"
        elif tool_name == "goto_parent_folder":
            result = client.goto_parent_folder()
            return "Navigated to parent folder" if result else "Navigation failed"

        # --- database management ---
        elif tool_name == "list_databases":
            return client.list_databases()
        elif tool_name == "get_current_database":
            return client.get_current_database()
        elif tool_name == "set_current_database":
            db_info = arguments.get("db_info", {})
            if err := _confirm_gate("set_current_database", arguments, f"Switches database to {db_info}; closes the current project."):
                return err
            result = client.set_current_database(db_info)
            return f"Switched to database {db_info}" if result else "Database switch failed"

        return f"Unknown tool in project_management domain: {tool_name}"
