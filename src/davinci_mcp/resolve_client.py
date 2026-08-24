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

    def export_project(
        self, name: str, file_path: str, with_stills_and_luts: bool
    ) -> bool:
        """Export a project to a .drp file."""
        self._ensure_connected()
        if not self._project_manager:
            return False
        return bool(
            self._project_manager.ExportProject(name, file_path, with_stills_and_luts)
        )

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

        timeline_count = project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            timeline = project.GetTimelineByIndex(i)
            if timeline and timeline.GetName() == name:
                result = project.SetCurrentTimeline(timeline)
                if result:
                    logger.info(f"Switched to timeline: {name}")
                return bool(result)

        raise ValueError(f"Timeline '{name}' not found")

    # ------------------------------------------------------------------
    # Timeline helpers
    # ------------------------------------------------------------------

    def _get_timeline_by_name(self, name: str) -> Any:
        """Look up a Timeline object by name. Re-walks on every call (Article IV)."""
        project = self._ensure_project()
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == name:
                return tl
        raise ValueError(f"Timeline '{name}' not found")

    def _get_current_timeline_obj(self) -> Any:
        project = self._ensure_project()
        tl = project.GetCurrentTimeline()
        if not tl:
            raise DaVinciResolveError("No current timeline")
        return tl

    def _resolve_timeline_items(
        self, timeline: Any, item_refs: list[dict[str, Any]]
    ) -> list[Any]:
        """Resolve [{track_type, track_index, item_index}] to TimelineItem objects."""
        items = []
        for ref in item_refs:
            track_type = ref.get("track_type", "video")
            track_index = int(ref.get("track_index", 1))
            item_index = int(ref.get("item_index", 1))
            track_items = timeline.GetItemListInTrack(track_type, track_index) or []
            if item_index < 1 or item_index > len(track_items):
                raise ValueError(
                    f"item_index {item_index} out of range for {track_type} track {track_index}"  # noqa: E501
                )
            items.append(track_items[item_index - 1])
        return items

    # ------------------------------------------------------------------
    # Timeline expanded methods
    # ------------------------------------------------------------------

    def rename_timeline(self, name: str, new_name: str) -> bool:
        """Rename a timeline."""
        tl = self._get_timeline_by_name(name)
        return bool(tl.SetName(new_name))

    def delete_timeline(self, name: str) -> bool:
        """Permanently delete a timeline."""
        project = self._ensure_project()
        tl = self._get_timeline_by_name(name)
        media_pool = project.GetMediaPool()
        if not media_pool:
            raise DaVinciResolveError("Failed to get Media Pool")
        return bool(media_pool.DeleteTimelines([tl]))

    def duplicate_timeline(self, name: str, new_name: str) -> bool:
        """Duplicate a timeline with a new name."""
        tl = self._get_timeline_by_name(name)
        result = tl.DuplicateTimeline(new_name)
        return bool(result)

    def get_timeline_settings(self, name: str, setting_name: str | None) -> Any:
        """Get timeline setting(s). Pass None to get all settings."""
        tl = self._get_timeline_by_name(name)
        if setting_name:
            return tl.GetSetting(setting_name)
        return tl.GetSetting()

    def set_timeline_setting(
        self, name: str, setting_name: str, setting_value: Any
    ) -> bool:
        """Set a timeline setting."""
        tl = self._get_timeline_by_name(name)
        return bool(tl.SetSetting(setting_name, setting_value))

    def get_start_timecode(self, name: str) -> str:
        """Get the start timecode of a timeline."""
        return str(self._get_timeline_by_name(name).GetStartTimecode())

    def set_start_timecode(self, name: str, timecode: str) -> bool:
        """Set the start timecode of a timeline."""
        return bool(self._get_timeline_by_name(name).SetStartTimecode(timecode))

    def get_current_timecode(self, name: str) -> str:
        """Get the current playhead timecode of a timeline."""
        return str(self._get_timeline_by_name(name).GetCurrentTimecode())

    def set_current_timecode(self, name: str, timecode: str) -> bool:
        """Move the playhead to a timecode."""
        return bool(self._get_timeline_by_name(name).SetCurrentTimecode(timecode))

    def get_timeline_start_frame(self, name: str) -> int:
        """Get the start frame number of a timeline."""
        return int(self._get_timeline_by_name(name).GetStartFrame())

    def get_timeline_end_frame(self, name: str) -> int:
        """Get the end frame number of a timeline."""
        return int(self._get_timeline_by_name(name).GetEndFrame())

    def get_timeline_marks(self, name: str) -> dict[str, Any]:
        """Get the in/out marks of a timeline."""
        result = self._get_timeline_by_name(name).GetMarkInOut()
        return dict(result) if result else {}

    def set_timeline_marks(
        self, name: str, mark_in: int, mark_out: int, mark_type: str
    ) -> bool:
        """Set the in/out marks on a timeline."""
        return bool(
            self._get_timeline_by_name(name).SetMarkInOut(mark_in, mark_out, mark_type)
        )

    def clear_timeline_marks(self, name: str, mark_type: str) -> bool:
        """Clear in/out marks from a timeline."""
        return bool(self._get_timeline_by_name(name).ClearMarkInOut(mark_type))

    def get_track_count(self, name: str, track_type: str) -> int:
        """Get the number of tracks of a given type."""
        return int(self._get_timeline_by_name(name).GetTrackCount(track_type))

    def add_track(self, name: str, track_type: str, sub_track_type: str) -> bool:
        """Add a track to a timeline."""
        tl = self._get_timeline_by_name(name)
        if sub_track_type:
            return bool(tl.AddTrack(track_type, sub_track_type))
        return bool(tl.AddTrack(track_type))

    def delete_track(self, name: str, track_type: str, track_index: int) -> bool:
        """Permanently delete a track from a timeline."""
        return bool(
            self._get_timeline_by_name(name).DeleteTrack(track_type, track_index)
        )

    def get_track_name(self, name: str, track_type: str, track_index: int) -> str:
        """Get the name of a timeline track."""
        return str(
            self._get_timeline_by_name(name).GetTrackName(track_type, track_index)
        )

    def set_track_name(
        self, name: str, track_type: str, track_index: int, new_name: str
    ) -> bool:
        """Set the name of a timeline track."""
        return bool(
            self._get_timeline_by_name(name).SetTrackName(
                track_type, track_index, new_name
            )
        )

    def get_track_subtype(self, name: str, track_type: str, track_index: int) -> str:
        """Get the subtype (audio format) of a timeline track."""
        return str(
            self._get_timeline_by_name(name).GetTrackSubType(track_type, track_index)
        )

    def enable_track(
        self, name: str, track_type: str, track_index: int, enabled: bool
    ) -> bool:
        """Enable or disable a timeline track."""
        return bool(
            self._get_timeline_by_name(name).SetTrackEnable(
                track_type, track_index, enabled
            )
        )

    def get_track_enabled(self, name: str, track_type: str, track_index: int) -> bool:
        """Get whether a timeline track is enabled."""
        return bool(
            self._get_timeline_by_name(name).GetIsTrackEnabled(track_type, track_index)
        )

    def lock_track(
        self, name: str, track_type: str, track_index: int, locked: bool
    ) -> bool:
        """Lock or unlock a timeline track."""
        return bool(
            self._get_timeline_by_name(name).SetTrackLock(
                track_type, track_index, locked
            )
        )

    def get_track_locked(self, name: str, track_type: str, track_index: int) -> bool:
        """Get whether a timeline track is locked."""
        return bool(
            self._get_timeline_by_name(name).GetIsTrackLocked(track_type, track_index)
        )

    def get_items_in_track(
        self, name: str, track_type: str, track_index: int
    ) -> list[dict[str, Any]]:
        """List items in a timeline track with their coordinates.

        Coordinates are valid until any timeline modification — re-list after mutations.
        """
        tl = self._get_timeline_by_name(name)
        items = tl.GetItemListInTrack(track_type, track_index) or []
        return [
            {
                "item_index": i + 1,
                "track_type": track_type,
                "track_index": track_index,
                "name": item.GetName(),
                "start": item.GetStart(),
                "end": item.GetEnd(),
                "duration": item.GetDuration(),
            }
            for i, item in enumerate(items)
        ]

    def get_selected_timeline_clips(self, name: str) -> list[dict[str, Any]]:
        """Get clips currently selected in a timeline (name/position info)."""
        tl = self._get_timeline_by_name(name)
        clips = tl.GetSelectedClips() or []
        return [
            {"name": c.GetName(), "start": c.GetStart(), "end": c.GetEnd()}
            for c in clips
        ]

    def get_current_video_item(self, name: str) -> dict[str, Any] | None:
        """Get the current video item in a timeline."""
        tl = self._get_timeline_by_name(name)
        item = tl.GetCurrentVideoItem()
        if not item:
            return None
        return {"name": item.GetName(), "start": item.GetStart(), "end": item.GetEnd()}

    def get_current_clip_thumbnail(self, name: str) -> dict[str, Any] | None:
        """Get the current clip thumbnail image data from the Color page."""
        tl = self._get_timeline_by_name(name)
        data = tl.GetCurrentClipThumbnailImage()
        if not data:
            return None
        return dict(data)

    def get_timeline_media_pool_item(self, name: str) -> dict[str, Any] | None:
        """Get the media pool item associated with a timeline."""
        tl = self._get_timeline_by_name(name)
        item = tl.GetMediaPoolItem()
        if not item:
            return None
        return {"clip_id": item.GetUniqueId(), "name": item.GetName()}

    def add_timeline_marker(
        self,
        name: str,
        frame_id: int,
        color: str,
        marker_name: str,
        note: str,
        duration: int,
        custom_data: str,
    ) -> bool:
        """Add a marker to a timeline."""
        tl = self._get_timeline_by_name(name)
        return bool(
            tl.AddMarker(frame_id, color, marker_name, note, duration, custom_data)
        )

    def get_timeline_markers(self, name: str) -> dict[str, Any]:
        """Get all markers on a timeline."""
        result = self._get_timeline_by_name(name).GetMarkers()
        return dict(result) if result else {}

    def delete_timeline_markers_by_color(self, name: str, color: str) -> bool:
        """Delete timeline markers by color. Use 'All' to clear all markers."""
        return bool(self._get_timeline_by_name(name).DeleteMarkersByColor(color))

    def delete_timeline_marker_at_frame(self, name: str, frame_num: int) -> bool:
        """Delete the timeline marker at a specific frame."""
        return bool(self._get_timeline_by_name(name).DeleteMarkerAtFrame(frame_num))

    def export_timeline(
        self, name: str, file_name: str, export_type: str, export_subtype: str
    ) -> bool:
        """Export a timeline to AAF/EDL/XML/FCPXML/OTIO/DRT/ALE/HDR/DolbyVision."""
        tl = self._get_timeline_by_name(name)
        return bool(tl.Export(file_name, export_type, export_subtype))

    def import_into_timeline(
        self, name: str, file_path: str, import_options: dict[str, Any]
    ) -> bool:
        """Import content into a timeline from AAF with remapping options."""
        tl = self._get_timeline_by_name(name)
        return bool(tl.ImportIntoTimeline(file_path, import_options))

    def create_compound_clip(
        self,
        name: str,
        item_refs: list[dict[str, Any]],
        clip_info: dict[str, Any],
    ) -> bool:
        """Create a compound clip from selected timeline items."""
        tl = self._get_timeline_by_name(name)
        items = self._resolve_timeline_items(tl, item_refs)
        result = tl.CreateCompoundClip(items, clip_info)
        return bool(result)

    def create_fusion_clip(self, name: str, item_refs: list[dict[str, Any]]) -> bool:
        """Create a Fusion clip from selected timeline items."""
        tl = self._get_timeline_by_name(name)
        items = self._resolve_timeline_items(tl, item_refs)
        result = tl.CreateFusionClip(items)
        return bool(result)

    def insert_generator(self, name: str, generator_name: str) -> bool:
        """Insert a generator into the current position of a timeline."""
        return bool(
            self._get_timeline_by_name(name).InsertGeneratorIntoTimeline(generator_name)
        )

    def insert_fusion_generator(self, name: str, generator_name: str) -> bool:
        """Insert a Fusion generator into a timeline."""
        return bool(
            self._get_timeline_by_name(name).InsertFusionGeneratorIntoTimeline(
                generator_name
            )
        )

    def insert_ofx_generator(self, name: str, generator_name: str) -> bool:
        """Insert an OFX generator into a timeline."""
        return bool(
            self._get_timeline_by_name(name).InsertOFXGeneratorIntoTimeline(
                generator_name
            )
        )

    def insert_title(self, name: str, title_name: str) -> bool:
        """Insert a title into a timeline."""
        return bool(
            self._get_timeline_by_name(name).InsertTitleIntoTimeline(title_name)
        )

    def insert_fusion_title(self, name: str, title_name: str) -> bool:
        """Insert a Fusion title into a timeline."""
        return bool(
            self._get_timeline_by_name(name).InsertFusionTitleIntoTimeline(title_name)
        )

    def insert_fusion_composition(self, name: str) -> bool:
        """Insert a Fusion composition into a timeline."""
        return bool(
            self._get_timeline_by_name(name).InsertFusionCompositionIntoTimeline()
        )

    def get_timeline_node_graph(self, name: str) -> dict[str, Any]:
        """Get the node graph for a timeline (Color page)."""
        tl = self._get_timeline_by_name(name)
        graph = tl.GetNodeGraph()
        if not graph:
            return {}
        return {"node_count": graph.GetNumNodes()}

    def delete_timeline_clips(
        self, name: str, item_refs: list[dict[str, Any]], ripple: bool
    ) -> bool:
        """Permanently delete clips from a timeline."""
        tl = self._get_timeline_by_name(name)
        items = self._resolve_timeline_items(tl, item_refs)
        return bool(tl.DeleteClips(items, ripple))

    def link_clips(
        self, name: str, item_refs: list[dict[str, Any]], linked: bool
    ) -> bool:
        """Link or unlink timeline clips."""
        tl = self._get_timeline_by_name(name)
        items = self._resolve_timeline_items(tl, item_refs)
        return bool(tl.SetClipsLinked(items, linked))

    def analyze_dolby_vision(
        self, name: str, item_refs: list[dict[str, Any]], analysis_type: int
    ) -> bool:
        """Run Dolby Vision analysis on timeline items."""
        tl = self._get_timeline_by_name(name)
        items = self._resolve_timeline_items(tl, item_refs)
        return bool(tl.AnalyzeDolbyVision(items, analysis_type))

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
                "duration": clip.GetClipProperty("Duration") or "Unknown",
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

    def move_clips_to_folder(
        self, clip_ids: list[str], target_folder_path: str
    ) -> bool:
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

    def import_timeline_from_file(
        self, file_path: str, import_options: dict[str, Any]
    ) -> bool:
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
        self._ensure_project()
        media_storage = self._resolve.GetMediaStorage() if self._resolve else None  # type: ignore[union-attr]
        if not media_storage:
            raise DaVinciResolveError("Failed to get MediaStorage")
        clip = self._get_clip_by_id(clip_id)
        return bool(
            media_storage.AddClipMattesToMediaPool(clip, file_paths, stereo_eye)
        )

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
        return [{"clip_id": c.GetUniqueId(), "name": c.GetName()} for c in clips]

    def set_selected_pool_clip(self, clip_id: str) -> bool:
        """Set a clip as the selected clip in the media pool."""
        media_pool = self._get_media_pool()
        clip = self._get_clip_by_id(clip_id)
        return bool(media_pool.SetSelectedClip(clip))

    # ------------------------------------------------------------------
    # Domain 7: Render & Delivery
    # ------------------------------------------------------------------

    def get_render_formats(self) -> dict[str, Any]:
        """Get available render formats as {format: file_extension}."""
        project = self._ensure_project()
        result = project.GetRenderFormats()
        return dict(result) if result else {}

    def get_render_codecs(self, render_format: str) -> dict[str, Any]:
        """Get available codecs for a render format."""
        project = self._ensure_project()
        result = project.GetRenderCodecs(render_format)
        return dict(result) if result else {}

    def get_render_resolutions(
        self, render_format: str, codec: str
    ) -> list[dict[str, Any]]:  # noqa: E501
        """Get available render resolutions for a format and codec."""
        project = self._ensure_project()
        result = project.GetRenderResolutions(render_format, codec)
        return [dict(r) for r in result] if result else []

    def get_current_render_format(self) -> dict[str, Any]:
        """Get the currently selected render format and codec."""
        project = self._ensure_project()
        result = project.GetCurrentRenderFormatAndCodec()
        return dict(result) if result else {}

    def set_render_format_and_codec(self, render_format: str, codec: str) -> bool:
        """Set the current render format and codec."""
        project = self._ensure_project()
        return bool(project.SetCurrentRenderFormatAndCodec(render_format, codec))

    def get_render_mode(self) -> int:
        """Get the current render mode (0=individual clips, 1=single clip)."""
        project = self._ensure_project()
        return int(project.GetCurrentRenderMode())

    def set_render_mode(self, render_mode: int) -> bool:
        """Set the render mode."""
        project = self._ensure_project()
        return bool(project.SetCurrentRenderMode(render_mode))

    def set_render_settings(self, settings: dict[str, Any]) -> bool:
        """Apply render settings from a dict."""
        project = self._ensure_project()
        return bool(project.SetRenderSettings(settings))

    def get_render_preset_list(self) -> list[str]:
        """Get the list of available render preset names."""
        project = self._ensure_project()
        result = project.GetRenderPresetList()
        return list(result) if result else []

    def load_render_preset(self, preset_name: str) -> bool:
        """Load a render preset by name."""
        project = self._ensure_project()
        return bool(project.LoadRenderPreset(preset_name))

    def save_render_preset(self, preset_name: str) -> bool:
        """Save the current render settings as a named preset."""
        project = self._ensure_project()
        return bool(project.SaveAsNewRenderPreset(preset_name))

    def delete_render_preset(self, preset_name: str) -> bool:
        """Permanently delete a render preset."""
        project = self._ensure_project()
        return bool(project.DeleteRenderPreset(preset_name))

    def get_quick_export_presets(self) -> list[str]:
        """Get available Quick Export render preset names."""
        project = self._ensure_project()
        result = project.GetQuickExportRenderPresets()
        return list(result) if result else []

    def render_with_quick_export(
        self, preset_name: str, params: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Render using a Quick Export preset."""
        project = self._ensure_project()
        return bool(project.RenderWithQuickExport(preset_name, params))

    def add_render_job(self) -> str | None:
        """Add the current timeline/settings as a render job. Returns job ID."""
        project = self._ensure_project()
        job_id = project.AddRenderJob()
        return str(job_id) if job_id else None

    def delete_render_job(self, job_id: str) -> bool:
        """Permanently delete a render job by ID."""
        project = self._ensure_project()
        return bool(project.DeleteRenderJob(job_id))

    def delete_all_render_jobs(self) -> bool:
        """Delete all render jobs in the queue."""
        project = self._ensure_project()
        return bool(project.DeleteAllRenderJobs())

    def get_render_job_list(self) -> list[dict[str, Any]]:
        """Get the list of all render jobs."""
        project = self._ensure_project()
        result = project.GetRenderJobList()
        return [dict(j) for j in result] if result else []

    def get_render_job_status(self, job_id: str) -> dict[str, Any]:
        """Get status and completion percentage of a render job."""
        project = self._ensure_project()
        result = project.GetRenderJobStatus(job_id)
        return dict(result) if result else {}

    def start_rendering(self, job_ids: list[str], interactive: bool) -> bool:
        """Start rendering one or more jobs."""
        project = self._ensure_project()
        if job_ids:
            return bool(project.StartRendering(job_ids, interactive))
        return bool(project.StartRendering(isInteractiveMode=interactive))

    def stop_rendering(self) -> None:
        """Stop the current render operation."""
        project = self._ensure_project()
        project.StopRendering()

    def is_rendering_in_progress(self) -> bool:
        """Check whether a render is currently in progress."""
        project = self._ensure_project()
        return bool(project.IsRenderingInProgress())

    def get_project_setting(self, setting_name: str) -> Any:
        """Get a project setting. Pass empty string for all settings."""
        project = self._ensure_project()
        if setting_name:
            return project.GetSetting(setting_name)
        return project.GetSetting()

    def set_project_setting(self, setting_name: str, setting_value: str) -> bool:
        """Set a project setting value."""
        project = self._ensure_project()
        return bool(project.SetSetting(setting_name, setting_value))

    def get_burn_in_preset_list(self) -> list[str]:
        """Get the list of available burn-in preset names."""
        if not self._resolve:
            return []
        result = self._resolve.GetBurnInPresetList()
        return list(result) if result else []

    def load_project_burn_in_preset(self, preset_name: str) -> bool:
        """Load a burn-in preset for the current project."""
        project = self._ensure_project()
        return bool(project.LoadBurnInPreset(preset_name))

    # ------------------------------------------------------------------
    # Domain 4: Clip Properties & Metadata
    # ------------------------------------------------------------------

    def get_clip_name(self, clip_id: str) -> str:
        """Get the name of a media pool clip."""
        return str(self._get_clip_by_id(clip_id).GetName())

    def set_clip_name(self, clip_id: str, name: str) -> bool:
        """Set the name of a media pool clip."""
        return bool(self._get_clip_by_id(clip_id).SetName(name))

    def get_clip_properties(self, clip_id: str) -> Any:
        """Get clip properties (all if no key given)."""
        clip = self._get_clip_by_id(clip_id)
        return clip.GetClipProperty()

    def set_clip_property(
        self, clip_id: str, property_key: str, property_value: str
    ) -> bool:  # noqa: E501
        """Set a single clip property."""
        return bool(
            self._get_clip_by_id(clip_id).SetClipProperty(property_key, property_value)
        )  # noqa: E501

    def get_clip_metadata(self, clip_id: str) -> Any:
        """Get clip metadata (all if no key given)."""
        return self._get_clip_by_id(clip_id).GetMetadata()

    def set_clip_metadata(
        self, clip_id: str, metadata_type: str, metadata_value: str
    ) -> bool:  # noqa: E501
        """Set a clip metadata field."""
        return bool(
            self._get_clip_by_id(clip_id).SetMetadata(metadata_type, metadata_value)
        )  # noqa: E501

    def get_clip_third_party_metadata(self, clip_id: str) -> Any:
        """Get third-party metadata from a clip."""
        return self._get_clip_by_id(clip_id).GetThirdPartyMetadata()

    def set_clip_third_party_metadata(  # noqa: E501
        self, clip_id: str, metadata_type: str, metadata_value: str
    ) -> bool:
        """Set a third-party metadata field on a clip."""
        return bool(
            self._get_clip_by_id(clip_id).SetThirdPartyMetadata(
                metadata_type, metadata_value
            )  # noqa: E501
        )

    def get_clip_color(self, clip_id: str) -> str:
        """Get the color label of a clip."""
        return str(self._get_clip_by_id(clip_id).GetClipColor())

    def set_clip_color(self, clip_id: str, color_name: str) -> bool:
        """Set the color label of a clip."""
        return bool(self._get_clip_by_id(clip_id).SetClipColor(color_name))

    def clear_clip_color(self, clip_id: str) -> bool:
        """Clear the color label of a clip."""
        return bool(self._get_clip_by_id(clip_id).ClearClipColor())

    def add_clip_flag(self, clip_id: str, color: str) -> bool:
        """Add a color flag to a clip."""
        return bool(self._get_clip_by_id(clip_id).AddFlag(color))

    def get_clip_flags(self, clip_id: str) -> list[str]:
        """Get the list of color flags on a clip."""
        result = self._get_clip_by_id(clip_id).GetFlagList()
        return list(result) if result else []

    def clear_clip_flags(self, clip_id: str, color: str) -> bool:
        """Clear clip flags by color ('All' clears all)."""
        return bool(self._get_clip_by_id(clip_id).ClearFlags(color))

    def add_clip_marker(
        self,
        clip_id: str,
        frame_id: int,
        color: str,
        marker_name: str,
        note: str,
        duration: int,
        custom_data: str,
    ) -> bool:
        """Add a marker to a clip at a specific source frame."""
        return bool(
            self._get_clip_by_id(clip_id).AddMarker(
                frame_id, color, marker_name, note, duration, custom_data
            )
        )

    def get_clip_markers(self, clip_id: str) -> dict[str, Any]:
        """Get all markers on a clip."""
        result = self._get_clip_by_id(clip_id).GetMarkers()
        return dict(result) if result else {}

    def delete_clip_markers_by_color(self, clip_id: str, color: str) -> bool:
        """Delete clip markers by color ('All' clears all)."""
        return bool(self._get_clip_by_id(clip_id).DeleteMarkersByColor(color))

    def delete_clip_marker_at_frame(self, clip_id: str, frame_num: int) -> bool:
        """Delete the clip marker at a specific frame."""
        return bool(self._get_clip_by_id(clip_id).DeleteMarkerAtFrame(frame_num))

    def get_clip_audio_mapping(self, clip_id: str) -> str:
        """Get the audio channel mapping for a clip as a JSON string."""
        result = self._get_clip_by_id(clip_id).GetAudioMapping()
        return str(result) if result else ""

    def get_clip_mark_in_out(self, clip_id: str) -> dict[str, Any]:
        """Get the in/out marks set on a clip."""
        result = self._get_clip_by_id(clip_id).GetMarkInOut()
        return dict(result) if result else {}

    def set_clip_mark_in_out(
        self, clip_id: str, mark_in: int, mark_out: int, mark_type: str
    ) -> bool:
        """Set in/out marks on a clip."""
        return bool(
            self._get_clip_by_id(clip_id).SetMarkInOut(mark_in, mark_out, mark_type)
        )

    def clear_clip_mark_in_out(self, clip_id: str, mark_type: str) -> bool:
        """Clear in/out marks from a clip."""
        return bool(self._get_clip_by_id(clip_id).ClearMarkInOut(mark_type))

    def link_proxy_media(self, clip_id: str, file_path: str) -> bool:
        """Link a proxy media file to a clip."""
        return bool(self._get_clip_by_id(clip_id).LinkProxyMedia(file_path))

    def unlink_proxy_media(self, clip_id: str) -> bool:
        """Unlink the proxy media from a clip."""
        return bool(self._get_clip_by_id(clip_id).UnlinkProxyMedia())

    def link_full_resolution_media(self, clip_id: str, file_path: str) -> bool:
        """Link a full-resolution media file to a clip."""
        return bool(self._get_clip_by_id(clip_id).LinkFullResolutionMedia(file_path))

    def replace_clip(self, clip_id: str, file_path: str) -> bool:
        """Replace the underlying asset of a clip."""
        return bool(self._get_clip_by_id(clip_id).ReplaceClip(file_path))

    def replace_clip_preserve_subclip(self, clip_id: str, file_path: str) -> bool:
        """Replace a clip's asset, preserving subclip marks."""
        return bool(self._get_clip_by_id(clip_id).ReplaceClipPreserveSubClip(file_path))

    def get_clip_unique_id(self, clip_id: str) -> str:
        """Get the UUID of a clip."""
        return str(self._get_clip_by_id(clip_id).GetUniqueId())

    def get_clip_timeline(self, clip_id: str) -> dict[str, Any] | None:
        """Get the timeline associated with a clip (if it is a timeline clip)."""
        clip = self._get_clip_by_id(clip_id)
        tl = clip.GetTimeline()
        if not tl:
            return None
        return {"name": tl.GetName()}

    # ------------------------------------------------------------------
    # Domain 9: System, Fairlight & Storage
    # ------------------------------------------------------------------

    def _get_media_storage(self) -> Any:
        self._ensure_connected()
        if not self._resolve:
            raise DaVinciResolveError("Not connected")
        storage = self._resolve.GetMediaStorage()
        if not storage:
            raise DaVinciResolveError("Failed to get MediaStorage")
        return storage

    def get_layout_presets(self) -> list[str]:
        """Get the list of available UI layout preset names."""
        self._ensure_connected()
        if not self._resolve:
            return []
        result = self._resolve.GetLayoutPresetList()
        return list(result) if result else []

    def load_layout_preset(self, preset_name: str) -> bool:
        """Load a UI layout preset by name."""
        self._ensure_connected()
        if not self._resolve:
            return False
        return bool(self._resolve.LoadLayoutPreset(preset_name))

    def save_layout_preset(self, preset_name: str) -> bool:
        """Save the current UI layout as a named preset."""
        self._ensure_connected()
        if not self._resolve:
            return False
        return bool(self._resolve.SaveLayoutPreset(preset_name))

    def delete_layout_preset(self, preset_name: str) -> bool:
        """Permanently delete a layout preset."""
        self._ensure_connected()
        if not self._resolve:
            return False
        return bool(self._resolve.DeleteLayoutPreset(preset_name))

    def export_layout_preset(self, preset_name: str, file_path: str) -> bool:
        """Export a layout preset to a file."""
        self._ensure_connected()
        if not self._resolve:
            return False
        return bool(self._resolve.ExportLayoutPreset(preset_name, file_path))

    def import_layout_preset(self, file_path: str, preset_name: str) -> bool:
        """Import a layout preset from a file."""
        self._ensure_connected()
        if not self._resolve:
            return False
        return bool(self._resolve.ImportLayoutPreset(file_path, preset_name))

    def get_fairlight_presets(self) -> list[str]:
        """Get the list of available Fairlight audio preset names."""
        self._ensure_connected()
        if not self._resolve:
            return []
        result = self._resolve.GetFairlightPresets()
        return list(result) if result else []

    def apply_fairlight_preset(self, preset_name: str) -> bool:
        """Apply a Fairlight preset to the current timeline."""
        project = self._ensure_project()
        return bool(project.ApplyFairlightPresetToCurrentTimeline(preset_name))

    def get_keyframe_mode(self) -> int:
        """Get the current keyframe mode (0=all, 1=color, 2=sizing)."""
        self._ensure_connected()
        if not self._resolve:
            return 0
        return int(self._resolve.GetKeyframeMode())

    def set_keyframe_mode(self, keyframe_mode: int) -> bool:
        """Set keyframe mode."""
        self._ensure_connected()
        if not self._resolve:
            return False
        return bool(self._resolve.SetKeyframeMode(keyframe_mode))

    def insert_audio_at_playhead(
        self, media_path: str, start_offset: int, duration: int
    ) -> bool:
        """Insert audio from a file at the current playhead on the Fairlight page."""
        project = self._ensure_project()
        return bool(
            project.InsertAudioToCurrentTrackAtPlayhead(
                media_path, start_offset, duration
            )  # noqa: E501
        )

    def get_mounted_volumes(self) -> list[str]:
        """Get the list of mounted volumes visible to Resolve."""
        storage = self._get_media_storage()
        result = storage.GetMountedVolumeList()
        return list(result) if result else []

    def get_storage_subfolders(self, folder_path: str) -> list[str]:
        """List subfolders in a media storage path."""
        storage = self._get_media_storage()
        result = storage.GetSubFolderList(folder_path)
        return list(result) if result else []

    def get_storage_files(self, folder_path: str) -> list[str]:
        """List files in a media storage path."""
        storage = self._get_media_storage()
        result = storage.GetFileList(folder_path)
        return list(result) if result else []

    def add_storage_items_to_pool(self, items: list[str]) -> bool:
        """Add files or folders from media storage to the media pool."""
        storage = self._get_media_storage()
        return bool(storage.AddItemListToMediaPool(items))

    def disable_background_tasks(self) -> bool:
        """Disable Resolve background tasks for the current session."""
        self._ensure_connected()
        if not self._resolve:
            return False
        return bool(self._resolve.DisableBackgroundTasksForCurrentResolveSession())

    # ------------------------------------------------------------------
    # Domain 6: Color Grading
    # ------------------------------------------------------------------

    def _get_timeline_graph(self, timeline_name: str) -> Any:
        """Get the node graph for the named timeline."""
        tl = self._get_timeline_by_name(timeline_name)
        graph = tl.GetNodeGraph()
        if not graph:
            raise DaVinciResolveError(f"No node graph on timeline '{timeline_name}'")
        return graph

    def _get_gallery(self) -> Any:
        project = self._ensure_project()
        gallery = project.GetGallery()
        if not gallery:
            raise DaVinciResolveError("Failed to get Gallery")
        return gallery

    def _get_album_by_name(self, album_name: str) -> Any:
        """Walk gallery still albums and return the one matching album_name."""
        gallery = self._get_gallery()
        albums = gallery.GetGalleryStillAlbums() or []
        for album in albums:
            if album.GetLabel() == album_name:
                return album
        raise ValueError(f"Gallery still album '{album_name}' not found")

    def _get_still_by_index(self, album_name: str, still_index: int) -> Any:
        """Return the GalleryStill at still_index (1-based) within the named album."""
        album = self._get_album_by_name(album_name)
        stills = album.GetStills() or []
        if still_index < 1 or still_index > len(stills):
            raise ValueError(
                f"still_index {still_index} out of range (album has {len(stills)} stills)"  # noqa: E501
            )
        return stills[still_index - 1]

    def _get_color_group_by_name(self, group_name: str) -> Any:
        project = self._ensure_project()
        groups = project.GetColorGroupsList() or []
        for g in groups:
            if g.GetName() == group_name:
                return g
        raise ValueError(f"Color group '{group_name}' not found")

    # --- Graph / node operations ---

    def get_graph_node_count(self, timeline_name: str) -> int:
        """Get the number of nodes in a timeline's node graph."""
        return int(self._get_timeline_graph(timeline_name).GetNumNodes())

    def get_graph_node_label(self, timeline_name: str, node_index: int) -> str:
        """Get the label of a graph node."""
        return str(self._get_timeline_graph(timeline_name).GetNodeLabel(node_index))

    def get_graph_node_tools(self, timeline_name: str, node_index: int) -> list[str]:
        """Get the list of tool names active in a graph node."""
        result = self._get_timeline_graph(timeline_name).GetToolsInNode(node_index)
        return list(result) if result else []

    def get_graph_node_lut(self, timeline_name: str, node_index: int) -> str:
        """Get the LUT path assigned to a graph node."""
        return str(self._get_timeline_graph(timeline_name).GetLUT(node_index))

    def set_graph_node_lut(
        self, timeline_name: str, node_index: int, lut_path: str
    ) -> bool:  # noqa: E501
        """Assign a LUT file to a graph node."""
        return bool(
            self._get_timeline_graph(timeline_name).SetLUT(node_index, lut_path)
        )  # noqa: E501

    def get_graph_node_cache_mode(self, timeline_name: str, node_index: int) -> int:
        """Get the cache mode of a graph node."""
        return int(self._get_timeline_graph(timeline_name).GetNodeCacheMode(node_index))

    def set_graph_node_enabled(
        self, timeline_name: str, node_index: int, enabled: bool
    ) -> bool:  # noqa: E501
        """Enable or disable a graph node."""
        return bool(
            self._get_timeline_graph(timeline_name).SetNodeEnabled(node_index, enabled)
        )  # noqa: E501

    def set_graph_node_cache_mode(
        self, timeline_name: str, node_index: int, cache_mode: int
    ) -> bool:  # noqa: E501
        """Set the cache mode of a graph node."""
        return bool(
            self._get_timeline_graph(timeline_name).SetNodeCacheMode(
                node_index, cache_mode
            )  # noqa: E501
        )

    def apply_grade_from_drx(
        self, timeline_name: str, drx_path: str, grade_mode: int
    ) -> bool:  # noqa: E501
        """Apply a grade from a .drx file."""
        return bool(
            self._get_timeline_graph(timeline_name).ApplyGradeFromDRX(
                drx_path, grade_mode
            )
        )  # noqa: E501

    def apply_arri_cdl_lut(self, timeline_name: str) -> bool:
        """Apply ARRI CDL LUT to a timeline's graph."""
        return bool(self._get_timeline_graph(timeline_name).ApplyArriCdlLut())

    def reset_all_grades(self, timeline_name: str) -> bool:
        """Reset all grades in a timeline's node graph."""
        return bool(self._get_timeline_graph(timeline_name).ResetAllGrades())

    # --- Gallery stills — albums ---

    def get_gallery_albums(self) -> list[str]:
        """Get the list of gallery still album names."""
        gallery = self._get_gallery()
        albums = gallery.GetGalleryStillAlbums() or []
        return [a.GetLabel() for a in albums]

    def get_gallery_powergrade_albums(self) -> list[str]:
        """Get the list of gallery PowerGrade album names."""
        gallery = self._get_gallery()
        albums = gallery.GetGalleryPowerGradeAlbums() or []
        return [a.GetLabel() for a in albums]

    def get_current_still_album(self) -> str | None:
        """Get the name of the currently active still album."""
        gallery = self._get_gallery()
        album = gallery.GetCurrentStillAlbum()
        return album.GetLabel() if album else None

    def create_still_album(self) -> bool:
        """Create a new gallery still album."""
        gallery = self._get_gallery()
        result = gallery.CreateGalleryStillAlbum()
        return bool(result)

    def create_powergrade_album(self) -> bool:
        """Create a new gallery PowerGrade album."""
        gallery = self._get_gallery()
        result = gallery.CreateGalleryPowerGradeAlbum()
        return bool(result)

    # --- Gallery stills — grab / list ---

    def grab_still(self, timeline_name: str) -> bool:
        """Grab a still from the current clip on the Color page."""
        tl = self._get_timeline_by_name(timeline_name)
        result = tl.GrabStill()
        return bool(result)

    def grab_all_stills(self, timeline_name: str, still_frame_source: int) -> bool:
        """Grab stills from all clips in a timeline."""
        tl = self._get_timeline_by_name(timeline_name)
        result = tl.GrabAllStills(still_frame_source)
        return bool(result)

    def get_stills(self, album_name: str) -> list[dict[str, Any]]:
        """Get stills in an album as [{still_index, label}]."""
        album = self._get_album_by_name(album_name)
        stills = album.GetStills() or []
        return [
            {"still_index": i + 1, "label": album.GetLabel(still)}
            for i, still in enumerate(stills)
        ]

    def export_stills(
        self,
        album_name: str,
        still_indices: list[int],
        folder_path: str,
        file_prefix: str,
        format: str,
    ) -> bool:
        """Export stills from an album."""
        album = self._get_album_by_name(album_name)
        all_stills = album.GetStills() or []
        stills = [all_stills[i - 1] for i in still_indices if 1 <= i <= len(all_stills)]
        return bool(album.ExportStills(stills, folder_path, file_prefix, format))

    def import_stills(self, album_name: str, file_paths: list[str]) -> bool:
        """Import still files into a gallery album."""
        album = self._get_album_by_name(album_name)
        return bool(album.ImportStills(file_paths))

    def delete_stills(self, album_name: str, still_indices: list[int]) -> bool:
        """Permanently delete stills from an album by index."""
        album = self._get_album_by_name(album_name)
        all_stills = album.GetStills() or []
        stills = [all_stills[i - 1] for i in still_indices if 1 <= i <= len(all_stills)]
        return bool(album.DeleteStills(stills))

    def get_still_label(self, album_name: str, still_index: int) -> str:
        """Get the label of a still by index."""
        still = self._get_still_by_index(album_name, still_index)
        album = self._get_album_by_name(album_name)
        return str(album.GetLabel(still))

    def set_still_label(self, album_name: str, still_index: int, label: str) -> bool:
        """Set the label of a still by index."""
        still = self._get_still_by_index(album_name, still_index)
        album = self._get_album_by_name(album_name)
        return bool(album.SetLabel(still, label))

    # --- Color groups ---

    def get_color_groups(self) -> list[str]:
        """Get the list of color group names."""
        project = self._ensure_project()
        groups = project.GetColorGroupsList() or []
        return [g.GetName() for g in groups]

    def create_color_group(self, group_name: str) -> bool:
        """Create a new color group."""
        project = self._ensure_project()
        result = project.AddColorGroup(group_name)
        return bool(result)

    def delete_color_group(self, group_name: str) -> bool:
        """Delete a color group (clips become ungrouped)."""
        project = self._ensure_project()
        group = self._get_color_group_by_name(group_name)
        return bool(project.DeleteColorGroup(group))

    def rename_color_group(self, group_name: str, new_name: str) -> bool:
        """Rename a color group."""
        group = self._get_color_group_by_name(group_name)
        return bool(group.SetName(new_name))

    def get_clips_in_color_group(
        self, group_name: str, timeline_name: str
    ) -> list[dict[str, Any]]:  # noqa: E501
        """Get timeline items assigned to a color group."""
        group = self._get_color_group_by_name(group_name)
        tl = self._get_timeline_by_name(timeline_name)
        items = group.GetClipsInTimeline(tl) or []
        return [{"name": item.GetName()} for item in items]

    def get_color_group_pre_graph(self, group_name: str) -> dict[str, Any]:
        """Get the pre-clip node graph for a color group."""
        group = self._get_color_group_by_name(group_name)
        graph = group.GetPreClipNodeGraph()
        if not graph:
            return {}
        return {"node_count": graph.GetNumNodes()}

    def get_color_group_post_graph(self, group_name: str) -> dict[str, Any]:
        """Get the post-clip node graph for a color group."""
        group = self._get_color_group_by_name(group_name)
        graph = group.GetPostClipNodeGraph()
        if not graph:
            return {}
        return {"node_count": graph.GetNumNodes()}

    # --- Project-level color utilities ---

    def refresh_lut_list(self) -> bool:
        """Refresh the LUT list from disk."""
        project = self._ensure_project()
        return bool(project.RefreshLUTList())

    def export_current_frame_as_still(self, file_path: str) -> bool:
        """Export the current frame as a still image file."""
        project = self._ensure_project()
        return bool(project.ExportCurrentFrameAsStill(file_path))

    # ------------------------------------------------------------------
    # Domain 5: Timeline Item Editing
    # ------------------------------------------------------------------

    def _get_timeline_item(self, timeline_name: str, item_ref: dict[str, Any]) -> Any:
        """Resolve an item_ref to a TimelineItem object. Re-walks on every call."""
        tl = self._get_timeline_by_name(timeline_name)
        items = self._resolve_timeline_items(tl, [item_ref])
        return items[0]

    def _get_color_group_for_item(self, group_name: str) -> Any:
        """Walk project color groups to find one by name."""
        project = self._ensure_project()
        groups = project.GetColorGroupsList() or []
        for g in groups:
            if g.GetName() == group_name:
                return g
        raise ValueError(f"Color group '{group_name}' not found")

    # --- Name ---

    def get_item_name(self, timeline_name: str, item_ref: dict[str, Any]) -> str:
        """Get the name of a timeline item."""
        return str(self._get_timeline_item(timeline_name, item_ref).GetName())

    def set_item_name(
        self, timeline_name: str, item_ref: dict[str, Any], name: str
    ) -> bool:  # noqa: E501
        """Set the name of a timeline item."""  # noqa: E501
        return bool(self._get_timeline_item(timeline_name, item_ref).SetName(name))

    # --- Timing ---

    def get_item_duration(
        self, timeline_name: str, item_ref: dict[str, Any], subframe_precision: bool
    ) -> Any:  # noqa: E501
        """Get the duration of a timeline item."""
        return self._get_timeline_item(timeline_name, item_ref).GetDuration(
            subframe_precision
        )  # noqa: E501

    def get_item_start(
        self, timeline_name: str, item_ref: dict[str, Any], subframe_precision: bool
    ) -> Any:  # noqa: E501
        """Get the timeline start of a timeline item."""
        return self._get_timeline_item(timeline_name, item_ref).GetStart(
            subframe_precision
        )  # noqa: E501

    def get_item_end(
        self, timeline_name: str, item_ref: dict[str, Any], subframe_precision: bool
    ) -> Any:  # noqa: E501
        """Get the timeline end of a timeline item."""
        return self._get_timeline_item(timeline_name, item_ref).GetEnd(
            subframe_precision
        )  # noqa: E501

    def get_item_source_start(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> Any:  # noqa: E501
        """Get the source media start frame."""  # noqa: E501
        return self._get_timeline_item(timeline_name, item_ref).GetSourceStartFrame()

    def get_item_source_end(self, timeline_name: str, item_ref: dict[str, Any]) -> Any:
        """Get the source media end frame."""  # noqa: E501
        return self._get_timeline_item(timeline_name, item_ref).GetSourceEndFrame()

    def get_item_left_offset(
        self, timeline_name: str, item_ref: dict[str, Any], subframe_precision: bool
    ) -> Any:  # noqa: E501
        """Get the left trim headroom."""
        return self._get_timeline_item(timeline_name, item_ref).GetLeftOffset(
            subframe_precision
        )  # noqa: E501

    def get_item_right_offset(
        self, timeline_name: str, item_ref: dict[str, Any], subframe_precision: bool
    ) -> Any:  # noqa: E501
        """Get the right trim headroom."""
        return self._get_timeline_item(timeline_name, item_ref).GetRightOffset(
            subframe_precision
        )  # noqa: E501

    # --- Properties ---

    def get_item_properties(self, timeline_name: str, item_ref: dict[str, Any]) -> Any:
        """Get all transform/composite properties of a timeline item."""
        return self._get_timeline_item(timeline_name, item_ref).GetProperty()

    def set_item_property(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        property_key: str,
        property_value: Any,
    ) -> bool:  # noqa: E501
        """Set a single property on a timeline item."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).SetProperty(
                property_key, property_value
            )  # noqa: E501
        )

    # --- Enabled / color ---

    def get_item_enabled(self, timeline_name: str, item_ref: dict[str, Any]) -> bool:
        """Check whether a timeline item is enabled."""  # noqa: E501
        return bool(self._get_timeline_item(timeline_name, item_ref).GetClipEnabled())

    def set_item_enabled(
        self, timeline_name: str, item_ref: dict[str, Any], enabled: bool
    ) -> bool:  # noqa: E501
        """Enable or disable a timeline item."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).SetClipEnabled(enabled)
        )  # noqa: E501

    def get_item_color(self, timeline_name: str, item_ref: dict[str, Any]) -> str:
        """Get the color label of a timeline item."""  # noqa: E501
        return str(self._get_timeline_item(timeline_name, item_ref).GetClipColor())

    def set_item_color(
        self, timeline_name: str, item_ref: dict[str, Any], color_name: str
    ) -> bool:  # noqa: E501
        """Set the color label of a timeline item."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).SetClipColor(color_name)
        )  # noqa: E501

    def clear_item_color(self, timeline_name: str, item_ref: dict[str, Any]) -> bool:
        """Clear the color label of a timeline item."""  # noqa: E501
        return bool(self._get_timeline_item(timeline_name, item_ref).ClearClipColor())

    # --- Flags ---

    def add_item_flag(
        self, timeline_name: str, item_ref: dict[str, Any], color: str
    ) -> bool:  # noqa: E501
        """Add a color flag to a timeline item."""  # noqa: E501
        return bool(self._get_timeline_item(timeline_name, item_ref).AddFlag(color))

    def get_item_flags(self, timeline_name: str, item_ref: dict[str, Any]) -> list[str]:
        """Get the list of color flags on a timeline item."""  # noqa: E501
        result = self._get_timeline_item(timeline_name, item_ref).GetFlagList()
        return list(result) if result else []

    def clear_item_flags(
        self, timeline_name: str, item_ref: dict[str, Any], color: str
    ) -> bool:  # noqa: E501
        """Clear flags from a timeline item."""
        return bool(self._get_timeline_item(timeline_name, item_ref).ClearFlags(color))

    # --- Markers ---

    def add_item_marker(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        frame_id: int,
        color: str,
        marker_name: str,
        note: str,
        duration: int,
        custom_data: str,
    ) -> bool:
        """Add a marker to a timeline item at a source frame."""
        item = self._get_timeline_item(timeline_name, item_ref)
        return bool(
            item.AddMarker(frame_id, color, marker_name, note, duration, custom_data)
        )

    def get_item_markers(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> dict[str, Any]:  # noqa: E501
        """Get all markers on a timeline item."""  # noqa: E501
        result = self._get_timeline_item(timeline_name, item_ref).GetMarkers()
        return dict(result) if result else {}

    def delete_item_markers_by_color(
        self, timeline_name: str, item_ref: dict[str, Any], color: str
    ) -> bool:  # noqa: E501
        """Delete item markers by color."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).DeleteMarkersByColor(color)
        )  # noqa: E501

    def delete_item_marker_at_frame(
        self, timeline_name: str, item_ref: dict[str, Any], frame_num: int
    ) -> bool:  # noqa: E501
        """Delete the item marker at a specific frame."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).DeleteMarkerAtFrame(
                frame_num
            )
        )  # noqa: E501

    # --- Takes ---

    def add_take(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        clip_id: str,
        start_frame: int,
        end_frame: int,
    ) -> bool:
        """Add a media pool clip as a take to a timeline item."""
        item = self._get_timeline_item(timeline_name, item_ref)
        clip = self._get_clip_by_id(clip_id)
        return bool(item.AddTake(clip, start_frame, end_frame))

    def get_take_count(self, timeline_name: str, item_ref: dict[str, Any]) -> int:
        """Get the number of takes on a timeline item."""  # noqa: E501
        return int(self._get_timeline_item(timeline_name, item_ref).GetTakesCount())

    def get_take_by_index(
        self, timeline_name: str, item_ref: dict[str, Any], idx: int
    ) -> Any:  # noqa: E501
        """Get take info (startFrame, endFrame, mediaPoolItem) by 1-based index."""  # noqa: E501
        result = self._get_timeline_item(timeline_name, item_ref).GetTakeByIndex(idx)
        if not result:
            return {}
        mpi = result.get("mediaPoolItem")
        return {
            "startFrame": result.get("startFrame"),
            "endFrame": result.get("endFrame"),
            "clip_name": mpi.GetName() if mpi else None,
        }

    def select_take(
        self, timeline_name: str, item_ref: dict[str, Any], idx: int
    ) -> bool:  # noqa: E501
        """Select the active take by 1-based index."""  # noqa: E501
        return bool(
            self._get_timeline_item(timeline_name, item_ref).SelectTakeByIndex(idx)
        )  # noqa: E501

    def delete_take(
        self, timeline_name: str, item_ref: dict[str, Any], idx: int
    ) -> bool:  # noqa: E501
        """Permanently delete a take by 1-based index."""  # noqa: E501
        return bool(
            self._get_timeline_item(timeline_name, item_ref).DeleteTakeByIndex(idx)
        )  # noqa: E501

    def finalize_take(self, timeline_name: str, item_ref: dict[str, Any]) -> bool:
        """Finalize the current take on a timeline item."""  # noqa: E501
        return bool(self._get_timeline_item(timeline_name, item_ref).FinalizeTake())

    # --- Color versions ---

    def get_current_color_version(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> Any:  # noqa: E501
        """Get the current color version (name and type)."""  # noqa: E501
        result = self._get_timeline_item(timeline_name, item_ref).GetCurrentVersion()
        return dict(result) if result else {}

    def get_color_version_list(
        self, timeline_name: str, item_ref: dict[str, Any], version_type: int
    ) -> list[str]:  # noqa: E501
        """Get color version names for an item."""
        result = self._get_timeline_item(timeline_name, item_ref).GetVersionNameList(
            version_type
        )  # noqa: E501
        return list(result) if result else []

    def add_color_version(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        version_name: str,
        version_type: int,
    ) -> bool:  # noqa: E501
        """Add a new color version to a timeline item."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).AddVersion(
                version_name, version_type
            )  # noqa: E501
        )

    def load_color_version(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        version_name: str,
        version_type: int,
    ) -> bool:  # noqa: E501
        """Load a color version by name."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).LoadVersionByName(
                version_name, version_type
            )  # noqa: E501
        )

    def delete_color_version(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        version_name: str,
        version_type: int,
    ) -> bool:  # noqa: E501
        """Permanently delete a color version by name."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).DeleteVersionByName(
                version_name, version_type
            )  # noqa: E501
        )

    def rename_color_version(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        old_name: str,
        new_name: str,
        version_type: int,
    ) -> bool:  # noqa: E501
        """Rename a color version."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).RenameVersionByName(
                old_name, new_name, version_type
            )  # noqa: E501
        )

    # --- Fusion comps ---

    def list_fusion_comps(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> list[str]:  # noqa: E501
        """List Fusion composition names on a timeline item."""  # noqa: E501
        result = self._get_timeline_item(
            timeline_name, item_ref
        ).GetFusionCompNameList()  # noqa: E501
        return list(result) if result else []

    def add_fusion_comp(self, timeline_name: str, item_ref: dict[str, Any]) -> bool:
        """Add a new Fusion composition to a timeline item."""  # noqa: E501
        result = self._get_timeline_item(timeline_name, item_ref).AddFusionComp()
        return bool(result)

    def load_fusion_comp(
        self, timeline_name: str, item_ref: dict[str, Any], comp_name: str
    ) -> bool:  # noqa: E501
        """Load a Fusion composition by name."""
        result = self._get_timeline_item(timeline_name, item_ref).LoadFusionCompByName(
            comp_name
        )  # noqa: E501
        return bool(result)

    def import_fusion_comp(
        self, timeline_name: str, item_ref: dict[str, Any], file_path: str
    ) -> bool:  # noqa: E501
        """Import a Fusion composition from a file."""
        result = self._get_timeline_item(timeline_name, item_ref).ImportFusionComp(
            file_path
        )  # noqa: E501
        return bool(result)

    def export_fusion_comp(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        file_path: str,
        comp_index: int,
    ) -> bool:  # noqa: E501
        """Export a Fusion composition to a file."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).ExportFusionComp(
                file_path, comp_index
            )  # noqa: E501
        )

    def delete_fusion_comp(
        self, timeline_name: str, item_ref: dict[str, Any], comp_name: str
    ) -> bool:  # noqa: E501
        """Permanently delete a Fusion comp by name."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).DeleteFusionCompByName(
                comp_name
            )  # noqa: E501
        )

    def rename_fusion_comp(
        self, timeline_name: str, item_ref: dict[str, Any], old_name: str, new_name: str
    ) -> bool:  # noqa: E501
        """Rename a Fusion composition."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).RenameFusionCompByName(
                old_name, new_name
            )  # noqa: E501
        )

    # --- Node graph / grade ---

    def get_item_node_graph(
        self, timeline_name: str, item_ref: dict[str, Any], layer_index: int
    ) -> dict[str, Any]:  # noqa: E501
        """Get node-count info for a timeline item's color node graph."""
        item = self._get_timeline_item(timeline_name, item_ref)
        graph = item.GetNodeGraph(layer_index)
        if not graph:
            return {}
        return {"node_count": graph.GetNumNodes()}

    def copy_grades(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        target_item_refs: list[dict[str, Any]],
    ) -> bool:  # noqa: E501
        """Copy grades from one timeline item to others."""
        tl = self._get_timeline_by_name(timeline_name)
        source_item = self._get_timeline_item(timeline_name, item_ref)
        targets = self._resolve_timeline_items(tl, target_item_refs)
        return bool(source_item.CopyGrades(targets))

    def set_cdl(
        self, timeline_name: str, item_ref: dict[str, Any], cdl_map: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Set CDL values on a timeline item."""
        return bool(self._get_timeline_item(timeline_name, item_ref).SetCDL(cdl_map))

    def export_item_lut(
        self,
        timeline_name: str,
        item_ref: dict[str, Any],
        export_type: int,
        file_path: str,
    ) -> bool:  # noqa: E501
        """Export the LUT for a timeline item."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).ExportLUT(
                export_type, file_path
            )  # noqa: E501
        )

    def update_sidecar(self, timeline_name: str, item_ref: dict[str, Any]) -> bool:
        """Sync BRAW/R3D sidecar file for a timeline item."""  # noqa: E501
        return bool(self._get_timeline_item(timeline_name, item_ref).UpdateSidecar())

    # --- Linked items / track info ---

    def get_linked_items(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> list[dict[str, Any]]:  # noqa: E501
        """Get items linked to a timeline item."""
        item = self._get_timeline_item(timeline_name, item_ref)
        linked = item.GetLinkedItems() or []
        return [{"name": li.GetName()} for li in linked]

    def get_item_track(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> dict[str, Any]:  # noqa: E501
        """Get the track type and index of a timeline item."""  # noqa: E501
        item = self._get_timeline_item(timeline_name, item_ref)
        result = item.GetTrackTypeAndIndex()
        if not result or len(result) < 2:
            return {}
        return {"track_type": result[0], "track_index": result[1]}

    def get_item_audio_channel_mapping(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> str:  # noqa: E501
        """Get audio channel mapping for a timeline item as a JSON string."""
        result = self._get_timeline_item(
            timeline_name, item_ref
        ).GetSourceAudioChannelMapping()  # noqa: E501
        return str(result) if result else ""

    # --- Color group ---

    def get_item_color_group(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> str | None:  # noqa: E501
        """Get the color group assigned to a timeline item."""  # noqa: E501
        item = self._get_timeline_item(timeline_name, item_ref)
        group = item.GetColorGroup()
        return group.GetName() if group else None

    def assign_to_color_group(
        self, timeline_name: str, item_ref: dict[str, Any], group_name: str
    ) -> bool:  # noqa: E501
        """Assign a timeline item to a color group."""
        item = self._get_timeline_item(timeline_name, item_ref)
        group = self._get_color_group_for_item(group_name)
        return bool(item.AssignToColorGroup(group))

    def remove_from_color_group(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Remove a timeline item from its color group."""  # noqa: E501
        return bool(
            self._get_timeline_item(timeline_name, item_ref).RemoveFromColorGroup()
        )  # noqa: E501

    # --- Cache ---

    def get_item_color_cache_enabled(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Check whether color output cache is enabled."""
        return bool(
            self._get_timeline_item(
                timeline_name, item_ref
            ).GetIsColorOutputCacheEnabled()
        )  # noqa: E501

    def set_item_color_cache(
        self, timeline_name: str, item_ref: dict[str, Any], cache_value: int
    ) -> bool:  # noqa: E501
        """Set color output cache mode."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).SetColorOutputCache(
                cache_value
            )
        )  # noqa: E501

    def get_item_fusion_cache_enabled(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Check whether Fusion output cache is enabled."""
        return bool(
            self._get_timeline_item(
                timeline_name, item_ref
            ).GetIsFusionOutputCacheEnabled()
        )  # noqa: E501

    def set_item_fusion_cache(
        self, timeline_name: str, item_ref: dict[str, Any], cache_value: int
    ) -> bool:  # noqa: E501
        """Set Fusion output cache mode."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).SetFusionOutputCache(
                cache_value
            )
        )  # noqa: E501

    # --- Media pool item / node colors ---

    def get_item_media_pool_item(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> dict[str, Any] | None:  # noqa: E501
        """Get the media pool item associated with a timeline item."""
        item = self._get_timeline_item(timeline_name, item_ref)
        mpi = item.GetMediaPoolItem()
        if not mpi:
            return None
        return {"clip_id": mpi.GetUniqueId(), "name": mpi.GetName()}

    def reset_item_node_colors(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Reset all node colors on a timeline item."""  # noqa: E501
        return bool(
            self._get_timeline_item(timeline_name, item_ref).ResetAllNodeColors()
        )  # noqa: E501

    # ------------------------------------------------------------------
    # Domain 8: AI & Studio Features
    # ------------------------------------------------------------------

    def create_magic_mask(
        self, timeline_name: str, item_ref: dict[str, Any], mode: str
    ) -> bool:
        """Create a magic mask on a timeline item (Studio only)."""
        item = self._get_timeline_item(timeline_name, item_ref)
        return bool(item.CreateMagicMask(mode))

    def regenerate_magic_mask(
        self, timeline_name: str, item_ref: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Regenerate the magic mask on a timeline item (Studio only)."""
        return bool(
            self._get_timeline_item(timeline_name, item_ref).RegenerateMagicMask()
        )  # noqa: E501

    def stabilize_clip(self, timeline_name: str, item_ref: dict[str, Any]) -> bool:
        """Stabilize a timeline item (Studio only)."""
        return bool(self._get_timeline_item(timeline_name, item_ref).Stabilize())

    def smart_reframe_clip(self, timeline_name: str, item_ref: dict[str, Any]) -> bool:
        """Apply Smart Reframe to a timeline item (Studio only)."""
        return bool(self._get_timeline_item(timeline_name, item_ref).SmartReframe())

    def create_subtitles_from_audio(
        self, timeline_name: str, settings: dict[str, Any]
    ) -> bool:  # noqa: E501
        """Generate subtitles from audio for a timeline (Studio only)."""
        tl = self._get_timeline_by_name(timeline_name)
        return bool(tl.CreateSubtitlesFromAudio(settings))

    def detect_scene_cuts(self, timeline_name: str) -> bool:
        """Detect scene cuts in a timeline (Studio only)."""
        tl = self._get_timeline_by_name(timeline_name)
        return bool(tl.DetectSceneCuts())

    def transcribe_clip_audio(self, clip_id: str, use_speaker_detection: bool) -> bool:
        """Transcribe audio for a media pool clip (Studio + Extras)."""
        clip = self._get_clip_by_id(clip_id)
        return bool(clip.TranscribeAudio(use_speaker_detection))

    def clear_transcription(self, clip_id: str) -> bool:
        """Clear transcription data for a clip (Studio only)."""
        return bool(self._get_clip_by_id(clip_id).ClearTranscription())

    def classify_clip_audio(self, clip_id: str) -> bool:
        """Classify audio content for a clip (Studio + Extras)."""
        return bool(self._get_clip_by_id(clip_id).PerformAudioClassification())

    def clear_audio_classification(self, clip_id: str) -> bool:
        """Clear audio classification for a clip (Studio only)."""
        return bool(self._get_clip_by_id(clip_id).ClearAudioClassification())

    def transcribe_folder_audio(
        self, folder_path: str, use_speaker_detection: bool
    ) -> bool:  # noqa: E501
        """Transcribe audio for all clips in a folder (Studio + Extras)."""
        folder = self._get_folder_by_path(folder_path)
        return bool(folder.TranscribeAudio(use_speaker_detection))

    def analyze_for_intellisearch(
        self, folder_path: str, identify_faces: bool, is_better_mode: bool
    ) -> bool:
        """Analyze folder clips for IntelliSearch (Studio + AI Extras)."""
        folder = self._get_folder_by_path(folder_path)
        return bool(folder.AnalyzeForIntellisearch(identify_faces, is_better_mode))

    def analyze_for_slate(self, folder_path: str, marker_color: str) -> bool:
        """Analyze folder clips for Slate ID (Studio + AI Slate ID Extras)."""
        folder = self._get_folder_by_path(folder_path)
        return bool(folder.AnalyzeForSlate(marker_color))

    def remove_motion_blur(
        self, clip_id: str, deblur_options: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Remove motion blur from a clip (Studio only). Returns new item info."""
        clip = self._get_clip_by_id(clip_id)
        result = clip.RemoveMotionBlur(deblur_options)
        if not result:
            return None
        return {"clip_id": result.GetUniqueId(), "name": result.GetName()}

    def set_voice_isolation(
        self, timeline_name: str, track_index: int, state: dict[str, Any]
    ) -> bool:
        """Set voice isolation state for an audio track (Studio only)."""
        tl = self._get_timeline_by_name(timeline_name)
        return bool(tl.SetVoiceIsolationState(track_index, state))

    def set_item_voice_isolation(
        self, timeline_name: str, item_ref: dict[str, Any], state: dict[str, Any]
    ) -> bool:
        """Set voice isolation state for a timeline item (Studio only)."""
        item = self._get_timeline_item(timeline_name, item_ref)
        return bool(item.SetVoiceIsolationState(state))

    def generate_speech(self, settings: dict[str, Any], timecode: str) -> bool:
        """Generate speech and add it to the timeline (Studio + AI Speech Generator)."""
        project = self._ensure_project()
        return bool(project.GenerateSpeech(settings, timecode))

    def reset_intellisearch(self) -> bool:
        """Reset IntelliSearch analysis for the current project (Studio only)."""
        project = self._ensure_project()
        return bool(project.ResetIntellisearchAnalysis())
