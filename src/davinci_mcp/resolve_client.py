# SPDX-License-Identifier: GPL-3.0-or-later
"""
DaVinci Resolve client wrapper.

Provides a clean interface to the DaVinci Resolve API with proper error handling
and logging.
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Import for type checking only to avoid runtime import issues
    from .types import DaVinciProject, DaVinciProjectManager, DaVinciResolveApp

from .utils.platform import (
    check_python_runtime_compatibility,
    check_resolve_running,
    setup_resolve_environment,
)

logger = logging.getLogger(__name__)


class DaVinciResolveError(Exception):
    """Base exception for DaVinci Resolve related errors."""

    pass


class DaVinciResolveNotRunningError(DaVinciResolveError):
    """Raised when DaVinci Resolve is not running."""

    pass


class DaVinciResolveConnectionError(DaVinciResolveError):
    """Raised when connection to DaVinci Resolve fails."""

    pass


class DaVinciResolveClient:
    """
    A clean interface to the DaVinci Resolve API.

    This class handles the connection to DaVinci Resolve and provides
    organized methods for interacting with projects, timelines, media, etc.
    """

    def __init__(self) -> None:
        self._resolve: DaVinciResolveApp | None = None
        self._project_manager: DaVinciProjectManager | None = None
        self._current_project: DaVinciProject | None = None
        self._is_connected = False

    def connect(self) -> None:
        """Connect to DaVinci Resolve."""
        # Check if Resolve is running
        if not check_resolve_running():
            raise DaVinciResolveNotRunningError(
                "DaVinci Resolve is not running. Please start DaVinci Resolve first."
            )

        # Set up environment (env vars, sys.path, DLL search dirs)
        if not setup_resolve_environment():
            raise DaVinciResolveConnectionError(
                "Failed to set up DaVinci Resolve environment variables."
            )

        # On Windows, fusionscript.dll discovers Python via the Windows
        # registry and loads python3.dll by full path.  If the running
        # Python is a different installation (e.g. uv-managed), two
        # runtimes end up in the same process and it crashes.
        compat_ok, compat_msg = check_python_runtime_compatibility()
        if not compat_ok:
            raise DaVinciResolveConnectionError(compat_msg)

        try:
            # Import and connect to Resolve
            import DaVinciResolveScript as dvr_script  # type: ignore

            self._resolve = dvr_script.scriptapp("Resolve")  # type: ignore

            if self._resolve is None:
                raise DaVinciResolveConnectionError(
                    "Failed to get Resolve object. "
                    "Check that DaVinci Resolve is running."
                )  # type: ignore

            # Get project manager
            self._project_manager = self._resolve.GetProjectManager()  # type: ignore
            if self._project_manager is None:
                raise DaVinciResolveConnectionError("Failed to get Project Manager.")

            # Get current project if one is open
            self._current_project = (  # type: ignore
                self._project_manager.GetCurrentProject()
            )

            self._is_connected = True
            logger.info(f"Connected to {self.get_version()}")

        except SystemError as e:
            raise DaVinciResolveConnectionError(
                f"fusionscript.dll initialization failed: {e}. "
                "Check that DaVinci Resolve Studio is running with "
                "external scripting enabled in Preferences."
            )
        except ImportError as e:
            raise DaVinciResolveConnectionError(
                f"Failed to import DaVinciResolveScript: {e}. "
                "Check environment variables and DaVinci Resolve installation."
            )
        except DaVinciResolveConnectionError:
            raise
        except Exception as e:
            raise DaVinciResolveConnectionError(f"Unexpected error connecting: {e}")

    def disconnect(self) -> None:
        """Disconnect from DaVinci Resolve."""
        self._resolve = None
        self._project_manager = None
        self._current_project = None
        self._is_connected = False
        logger.info("Disconnected from DaVinci Resolve")

    def is_connected(self) -> bool:
        """Check if connected to DaVinci Resolve."""
        return self._is_connected

    def _ensure_connected(self) -> None:
        """Ensure we're connected to Resolve."""
        if not self._is_connected:
            raise DaVinciResolveConnectionError("Not connected to DaVinci Resolve")

    def _ensure_project(self) -> Any:
        """Ensure we have a current project."""
        self._ensure_connected()

        # Refresh current project
        if self._project_manager:
            self._current_project = self._project_manager.GetCurrentProject()

        if self._current_project is None:
            raise DaVinciResolveError("No project is currently open")

        return self._current_project

    # System Information
    def get_version(self) -> str:
        """Get DaVinci Resolve version."""
        self._ensure_connected()
        if self._resolve:
            return (
                f"{self._resolve.GetProductName()} {self._resolve.GetVersionString()}"
            )
        return "Unknown"

    def get_current_page(self) -> str:
        """Get the current page (Edit, Color, Fusion, etc.)."""
        self._ensure_connected()
        if self._resolve:
            return self._resolve.GetCurrentPage()
        return "Unknown"

    def switch_page(self, page: str) -> bool:
        """Switch to a specific page."""
        self._ensure_connected()

        valid_pages = [
            "media",
            "cut",
            "edit",
            "fusion",
            "color",
            "fairlight",
            "deliver",
        ]
        if page.lower() not in valid_pages:
            raise ValueError(f"Invalid page. Must be one of: {', '.join(valid_pages)}")

        if self._resolve:
            return bool(self._resolve.OpenPage(page.lower()))
        return False

    # Project Management
    def list_projects(self) -> list[str]:
        """List all projects in the current database."""
        self._ensure_connected()

        if self._project_manager:
            projects = self._project_manager.GetProjectListInCurrentFolder()
            return [p for p in projects if p]  # Filter out empty strings
        return []

    def get_current_project_name(self) -> str | None:
        """Get the name of the currently open project."""
        try:
            project = self._ensure_project()
            return project.GetName()
        except DaVinciResolveError:
            return None

    def open_project(self, name: str) -> bool:
        """Open a project by name."""
        self._ensure_connected()

        if not self._project_manager:
            return False

        # Check if project exists
        projects = self.list_projects()
        if name not in projects:
            raise ValueError(
                f"Project '{name}' not found. Available: {', '.join(projects)}"
            )

        result = self._project_manager.LoadProject(name)
        if result:
            self._current_project = self._project_manager.GetCurrentProject()
            logger.info(f"Opened project: {name}")

        return bool(result)

    def create_project(self, name: str) -> bool:
        """Create a new project."""
        self._ensure_connected()

        if not self._project_manager:
            return False

        # Check if project already exists
        projects = self.list_projects()
        if name in projects:
            raise ValueError(f"Project '{name}' already exists")

        result = self._project_manager.CreateProject(name)
        if result:
            self._current_project = self._project_manager.GetCurrentProject()
            logger.info(f"Created project: {name}")

        return bool(result)

    def save_project(self) -> bool:
        """Save the current project."""
        project = self._ensure_project()
        return bool(project.SaveProject())

    def close_project(self) -> bool:
        """Close the current project (unsaved changes are lost)."""
        self._ensure_connected()
        if not self._project_manager or not self._current_project:
            return False
        result = self._project_manager.CloseProject(self._current_project)
        if result:
            self._current_project = None
        return bool(result)

    def delete_project(self, name: str) -> bool:
        """Permanently delete a project by name."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.DeleteProject(name))

    def rename_project(self, new_name: str) -> bool:
        """Rename the current project."""
        project = self._ensure_project()
        return bool(project.SetName(new_name))

    def export_project(self, name: str, file_path: str, with_stills_and_luts: bool) -> bool:
        """Export a project to a .drp file."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.ExportProject(name, file_path, with_stills_and_luts))

    def import_project(self, file_path: str, project_name: str) -> bool:
        """Import a project from a .drp file."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.ImportProject(file_path, project_name))

    def archive_project(
        self,
        name: str,
        file_path: str,
        src_media: bool,
        render_cache: bool,
        proxy_media: bool,
    ) -> bool:
        """Archive a project with optional media to a .dra file."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(
            self._project_manager.ArchiveProject(
                name, file_path, src_media, render_cache, proxy_media
            )
        )

    def restore_project(self, file_path: str, project_name: str) -> bool:
        """Restore a project from a .dra archive."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.RestoreProject(file_path, project_name))

    def get_project_attributes(self) -> dict[str, Any]:
        """Get attributes of all projects in the current folder."""
        self._ensure_connected()
        if not self._project_manager:
            return {}
        attrs = self._project_manager.GetProjectAttributesInCurrentFolder()
        return dict(attrs) if attrs else {}

    def create_project_folder(self, folder_name: str) -> bool:
        """Create a project folder in the current location."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.CreateFolder(folder_name))

    def delete_project_folder(self, folder_name: str) -> bool:
        """Permanently delete a project folder."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.DeleteFolder(folder_name))

    def list_project_folders(self) -> list[str]:
        """List project folders in the current location."""
        self._ensure_connected()
        if not self._project_manager:
            return []
        folders = self._project_manager.GetFolderListInCurrentFolder()
        return list(folders) if folders else []

    def get_current_project_folder(self) -> str:
        """Get the name of the current project folder."""
        self._ensure_connected()
        if not self._project_manager:
            return ""
        name = self._project_manager.GetCurrentFolder()
        return str(name) if name else ""

    def open_project_folder(self, folder_name: str) -> bool:
        """Open a project folder."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.OpenFolder(folder_name))

    def goto_root_folder(self) -> bool:
        """Navigate to the root project folder."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.GotoRootFolder())

    def goto_parent_folder(self) -> bool:
        """Navigate to the parent project folder."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(self._project_manager.GotoParentFolder())

    def list_databases(self) -> list[dict[str, Any]]:
        """List available project databases."""
        self._ensure_connected()
        if not self._project_manager:
            return []
        dbs = self._project_manager.GetDatabaseList()
        return [dict(db) for db in dbs] if dbs else []

    def get_current_database(self) -> dict[str, Any]:
        """Get the current project database info."""
        self._ensure_connected()
        if not self._project_manager:
            return {}
        db = self._project_manager.GetCurrentDatabase()
        return dict(db) if db else {}

    def set_current_database(self, db_info: dict[str, Any]) -> bool:
        """Switch to a different project database (closes current project)."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        result = self._project_manager.SetCurrentDatabase(db_info)
        if result:
            self._current_project = None
        return bool(result)

    # Timeline Management
    def list_timelines(self) -> list[str]:
        """List all timelines in the current project."""
        project = self._ensure_project()

        timeline_count = project.GetTimelineCount()
        timelines: list[str] = []

        for i in range(1, timeline_count + 1):
            timeline = project.GetTimelineByIndex(i)
            if timeline:
                name = timeline.GetName()
                if isinstance(name, str):
                    timelines.append(name)

        return timelines

    def get_current_timeline_name(self) -> str | None:
        """Get the name of the current timeline."""
        try:
            project = self._ensure_project()
            current_timeline = project.GetCurrentTimeline()
            return current_timeline.GetName() if current_timeline else None
        except DaVinciResolveError:
            return None

    def create_timeline(self, name: str) -> bool:
        """Create a new timeline."""
        project = self._ensure_project()

        media_pool = project.GetMediaPool()
        if not media_pool:
            raise DaVinciResolveError("Failed to get Media Pool")

        timeline = media_pool.CreateEmptyTimeline(name)
        if timeline:
            logger.info(f"Created timeline: {name}")
            return True

        return False

    def switch_timeline(self, name: str) -> bool:
        """Switch to a timeline by name."""
        project = self._ensure_project()

        # Find timeline by name
        timeline_count = project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            timeline = project.GetTimelineByIndex(i)
            if timeline and timeline.GetName() == name:
                result = project.SetCurrentTimeline(timeline)
                if result:
                    logger.info(f"Switched to timeline: {name}")
                return bool(result)

        raise ValueError(f"Timeline '{name}' not found")

    # Media Pool Management
    def list_media_clips(self) -> list[dict[str, Any]]:
        """List all clips in the media pool root folder."""
        project = self._ensure_project()

        media_pool = project.GetMediaPool()
        if not media_pool:
            raise DaVinciResolveError("Failed to get Media Pool")

        root_folder = media_pool.GetRootFolder()
        if not root_folder:
            raise DaVinciResolveError("Failed to get root folder")

        clips = root_folder.GetClipList()
        if not clips:
            return []

        result: list[dict[str, Any]] = []
        for clip in clips:
            clip_info = {
                "name": clip.GetName(),
                "duration": clip.GetDuration(),
                "fps": clip.GetClipProperty("FPS") or "Unknown",
            }
            result.append(clip_info)

        return result

    def import_media(self, file_path: str) -> bool:
        """Import a media file into the media pool."""
        project = self._ensure_project()

        media_pool = project.GetMediaPool()
        if not media_pool:
            raise DaVinciResolveError("Failed to get Media Pool")

        imported_clips = media_pool.ImportMedia([file_path])

        if imported_clips:
            logger.info(f"Imported media: {file_path}")
            return True

        return False

    # ------------------------------------------------------------------
    # Media Pool helpers
    # ------------------------------------------------------------------

    def _get_media_pool(self) -> Any:
        project = self._ensure_project()
        media_pool = project.GetMediaPool()
        if not media_pool:
            raise DaVinciResolveError("Failed to get Media Pool")
        return media_pool

    def _get_folder_by_path(self, folder_path: str) -> Any:
        """Walk the folder tree by slash-separated path from root."""
        media_pool = self._get_media_pool()
        folder = media_pool.GetRootFolder()
        if not folder:
            raise DaVinciResolveError("Failed to get root folder")
        if not folder_path or folder_path in ("", "/", "Master"):
            return folder
        parts = [p for p in folder_path.strip("/").split("/") if p]
        for part in parts:
            subfolders = folder.GetSubFolderList() or []
            match = next((f for f in subfolders if f.GetName() == part), None)
            if match is None:
                raise ValueError(f"Folder not found: '{part}' in path '{folder_path}'")
            folder = match
        return folder

    def _get_clip_by_id(self, clip_id: str) -> Any:
        """Walk the folder tree to find a MediaPoolItem by UUID."""
        media_pool = self._get_media_pool()
        root = media_pool.GetRootFolder()

        def _walk(folder: Any) -> Any:
            for clip in folder.GetClipList() or []:
                if clip.GetUniqueId() == clip_id:
                    return clip
            for sub in folder.GetSubFolderList() or []:
                found = _walk(sub)
                if found:
                    return found
            return None

        clip = _walk(root)
        if clip is None:
            raise ValueError(f"Clip not found with id '{clip_id}'")
        return clip

    def _resolve_clip_ids(self, clip_ids: list[str]) -> list[Any]:
        return [self._get_clip_by_id(cid) for cid in clip_ids]

    def _resolve_folder_paths(self, folder_paths: list[str]) -> list[Any]:
        return [self._get_folder_by_path(p) for p in folder_paths]

    # ------------------------------------------------------------------
    # Media Pool expanded methods
    # ------------------------------------------------------------------

    def get_media_pool_root_folder(self) -> dict[str, Any]:
        """Get info about the media pool root folder."""
        media_pool = self._get_media_pool()
        root = media_pool.GetRootFolder()
        if not root:
            raise DaVinciResolveError("Failed to get root folder")
        return {"name": root.GetName(), "folder_path": "/"}

    def get_current_media_pool_folder(self) -> dict[str, Any]:
        """Get info about the currently selected media pool folder."""
        media_pool = self._get_media_pool()
        folder = media_pool.GetCurrentFolder()
        if not folder:
            raise DaVinciResolveError("Failed to get current folder")
        return {"name": folder.GetName()}

    def set_current_media_pool_folder(self, folder_path: str) -> bool:
        """Set the currently selected media pool folder by path."""
        media_pool = self._get_media_pool()
        folder = self._get_folder_by_path(folder_path)
        return bool(media_pool.SetCurrentFolder(folder))

    def get_folder_clips(self, folder_path: str) -> list[dict[str, Any]]:
        """List clips in a specific folder."""
        folder = self._get_folder_by_path(folder_path)
        clips = folder.GetClipList() or []
        return [
            {
                "clip_id": c.GetUniqueId(),
                "name": c.GetName(),
                "duration": c.GetDuration(),
                "fps": c.GetClipProperty("FPS") or "Unknown",
            }
            for c in clips
        ]

    def get_folder_subfolders(self, folder_path: str) -> list[dict[str, Any]]:
        """List subfolders of a folder."""
        folder = self._get_folder_by_path(folder_path)
        subs = folder.GetSubFolderList() or []
        return [{"name": s.GetName()} for s in subs]

    def create_media_pool_folder(self, folder_path: str, name: str) -> bool:
        """Create a subfolder inside the given folder."""
        media_pool = self._get_media_pool()
        parent = self._get_folder_by_path(folder_path)
        result = media_pool.AddSubFolder(parent, name)
        return bool(result)

    def delete_media_pool_folders(self, folder_paths: list[str]) -> bool:
        """Permanently delete media pool folders."""
        media_pool = self._get_media_pool()
        folders = self._resolve_folder_paths(folder_paths)
        return bool(media_pool.DeleteFolders(folders))

    def move_clips_to_folder(self, clip_ids: list[str], target_folder_path: str) -> bool:
        """Move clips to a target folder."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids)
        target = self._get_folder_by_path(target_folder_path)
        return bool(media_pool.MoveClips(clips, target))

    def move_folders(self, folder_paths: list[str], target_folder_path: str) -> bool:
        """Move folders to a target folder."""
        media_pool = self._get_media_pool()
        folders = self._resolve_folder_paths(folder_paths)
        target = self._get_folder_by_path(target_folder_path)
        return bool(media_pool.MoveFolders(folders, target))

    def delete_media_pool_clips(self, clip_ids: list[str]) -> bool:
        """Permanently delete clips from the media pool."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids)
        return bool(media_pool.DeleteClips(clips))

    def append_clips_to_timeline(self, clip_ids: list[str]) -> bool:
        """Append clips to the current timeline."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids)
        result = media_pool.AppendToTimeline(clips)
        return bool(result)

    def create_timeline_from_clips(self, name: str, clip_ids: list[str]) -> bool:
        """Create a new timeline from a list of clips."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids)
        result = media_pool.CreateTimelineFromClips(name, clips)
        return bool(result)

    def import_timeline_from_file(self, file_path: str, import_options: dict[str, Any]) -> bool:
        """Import a timeline from EDL/AAF/XML/FCPXML/DRT/ADL/OTIO."""
        media_pool = self._get_media_pool()
        result = media_pool.ImportTimelineFromFile(file_path, import_options)
        return bool(result)

    def export_clip_metadata(self, file_name: str, clip_ids: list[str]) -> bool:
        """Export clip metadata to a CSV file."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids) if clip_ids else []
        return bool(media_pool.ExportMetadata(file_name, clips))

    def refresh_media_pool_folders(self) -> bool:
        """Refresh media pool folders (useful in collaboration mode)."""
        media_pool = self._get_media_pool()
        return bool(media_pool.RefreshFolders())

    def import_folder_from_file(self, file_path: str, source_clips_path: str) -> bool:
        """Import a folder from a .drb bin file."""
        media_pool = self._get_media_pool()
        return bool(media_pool.ImportFolderFromFile(file_path, source_clips_path))

    def relink_clips(self, clip_ids: list[str], folder_path: str) -> bool:
        """Relink offline clips to a new folder path."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids)
        return bool(media_pool.RelinkClips(clips, folder_path))

    def unlink_clips(self, clip_ids: list[str]) -> bool:
        """Unlink clips from their source media."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids)
        return bool(media_pool.UnlinkClips(clips))

    def auto_sync_audio(
        self, clip_ids: list[str], audio_sync_settings: dict[str, Any]
    ) -> bool:
        """Auto-sync audio to clips by waveform or timecode."""
        media_pool = self._get_media_pool()
        clips = self._resolve_clip_ids(clip_ids)
        return bool(media_pool.AutoSyncAudio(clips, audio_sync_settings))

    def get_clip_matte_list(self, clip_id: str) -> list[str]:
        """Get the list of matte file paths for a clip."""
        media_pool = self._get_media_pool()
        clip = self._get_clip_by_id(clip_id)
        mattes = media_pool.GetClipMatteList(clip)
        return list(mattes) if mattes else []

    def add_clip_mattes(
        self, clip_id: str, file_paths: list[str], stereo_eye: str
    ) -> bool:
        """Add matte files to a clip."""
        project = self._ensure_project()
        media_storage = self._resolve.GetMediaStorage() if self._resolve else None  # type: ignore[union-attr]
        if not media_storage:
            raise DaVinciResolveError("Failed to get MediaStorage")
        clip = self._get_clip_by_id(clip_id)
        return bool(media_storage.AddClipMattesToMediaPool(clip, file_paths, stereo_eye))

    def delete_clip_mattes(self, clip_id: str, file_paths: list[str]) -> bool:
        """Permanently delete matte files from a clip."""
        media_pool = self._get_media_pool()
        clip = self._get_clip_by_id(clip_id)
        return bool(media_pool.DeleteClipMattes(clip, file_paths))

    def add_timeline_mattes(self, file_paths: list[str]) -> bool:
        """Add timeline matte files to the media pool."""
        media_storage = self._resolve.GetMediaStorage() if self._resolve else None  # type: ignore[union-attr]
        if not media_storage:
            raise DaVinciResolveError("Failed to get MediaStorage")
        return bool(media_storage.AddTimelineMattesToMediaPool(file_paths))

    def create_stereo_clip(self, left_clip_id: str, right_clip_id: str) -> bool:
        """Create a stereo clip from two existing clips (Studio only)."""
        media_pool = self._get_media_pool()
        left = self._get_clip_by_id(left_clip_id)
        right = self._get_clip_by_id(right_clip_id)
        result = media_pool.CreateStereoClip(left, right)
        return bool(result)

    def get_selected_pool_clips(self) -> list[dict[str, Any]]:
        """Get clips currently selected in the media pool."""
        media_pool = self._get_media_pool()
        clips = media_pool.GetSelectedClips() or []
        return [
            {"clip_id": c.GetUniqueId(), "name": c.GetName()}
            for c in clips
        ]

    def set_selected_pool_clip(self, clip_id: str) -> bool:
        """Set a clip as the selected clip in the media pool."""
        media_pool = self._get_media_pool()
        clip = self._get_clip_by_id(clip_id)
        return bool(media_pool.SetSelectedClip(clip))
