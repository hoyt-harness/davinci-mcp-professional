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

from .utils.platform import check_resolve_running, setup_resolve_environment

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

        # Set up environment
        if not setup_resolve_environment():
            raise DaVinciResolveConnectionError(
                "Failed to set up DaVinci Resolve environment variables."
            )

        try:
            # Import and connect to Resolve
            import DaVinciResolveScript as dvr_script  # type: ignore[reportMissingImports]

            self._resolve = dvr_script.scriptapp("Resolve")  # type: ignore[reportUnknownMemberType]

            if self._resolve is None:
                raise DaVinciResolveConnectionError(
                    "Failed to get Resolve object. "
                    "Check that DaVinci Resolve is running."
                )  # type: ignore[reportUnknownMemberType]

            # Get project manager
            self._project_manager = self._resolve.GetProjectManager()  # type: ignore[reportUnknownMemberType]
            if self._project_manager is None:
                raise DaVinciResolveConnectionError("Failed to get Project Manager.")

            # Get current project if one is open
            self._current_project = self._project_manager.GetCurrentProject()  # type: ignore[reportUnknownMemberType]

            self._is_connected = True
            logger.info(f"Connected to {self.get_version()}")

        except ImportError as e:
            raise DaVinciResolveConnectionError(
                f"Failed to import DaVinciResolveScript: {e}. "
                "Check environment variables and DaVinci Resolve installation."
            )
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

        # Import the media file
        imported_clips = media_pool.ImportMedia([file_path])

        if imported_clips:
            logger.info(f"Imported media: {file_path}")
            return True

        return False
