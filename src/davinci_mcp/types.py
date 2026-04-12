"""
Type definitions for DaVinci Resolve API.

This module provides Protocol definitions for the DaVinci Resolve API
to improve type safety while working with the external scripting interface.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DaVinciProject(Protocol):
    """Protocol for DaVinci Resolve Project objects."""

    def GetName(self) -> str:
        """Get the project name."""
        ...

    def GetTimelines(self) -> list[Any]:
        """Get all timelines in the project."""
        ...

    def GetCurrentTimeline(self) -> Any | None:
        """Get the currently active timeline."""
        ...

    def AddTimeline(self, name: str) -> Any | None:
        """Add a new timeline with the given name."""
        ...

    def GetMediaPool(self) -> Any:
        """Get the media pool for this project."""
        ...


@runtime_checkable
class DaVinciTimeline(Protocol):
    """Protocol for DaVinci Resolve Timeline objects."""

    def GetName(self) -> str:
        """Get the timeline name."""
        ...

    def GetTrackCount(self, track_type: str) -> int:
        """Get the number of tracks of the specified type."""
        ...


@runtime_checkable
class DaVinciMediaPool(Protocol):
    """Protocol for DaVinci Resolve MediaPool objects."""

    def GetClips(self) -> list[Any]:
        """Get all clips in the media pool."""
        ...

    def ImportMedia(self, file_path: str) -> bool:
        """Import media from the specified file path."""
        ...


@runtime_checkable
class DaVinciProjectManager(Protocol):
    """Protocol for DaVinci Resolve ProjectManager objects."""

    def GetCurrentProject(self) -> DaVinciProject | None:
        """Get the currently open project."""
        ...

    def GetProjectsInDatabase(self) -> list[dict[str, Any]]:
        """Get all projects in the current database."""
        ...

    def GetProjectListInCurrentFolder(self) -> list[str]:
        """Get project list in current folder."""
        ...

    def CreateProject(self, name: str) -> DaVinciProject | None:
        """Create a new project with the given name."""
        ...

    def LoadProject(self, name: str) -> DaVinciProject | None:
        """Load an existing project by name."""
        ...


@runtime_checkable
class DaVinciResolveApp(Protocol):
    """Protocol for the main DaVinci Resolve application object."""

    def GetVersion(self) -> list[str]:
        """Get the DaVinci Resolve version information."""
        ...

    def GetProductName(self) -> str:
        """Get the product name."""
        ...

    def GetVersionString(self) -> str:
        """Get the version as a string."""
        ...

    def GetProjectManager(self) -> DaVinciProjectManager:
        """Get the project manager."""
        ...

    def GetCurrentPage(self) -> str:
        """Get the currently active page."""
        ...

    def OpenPage(self, page: str) -> bool:
        """Open a specific page."""
        ...

    def GetCurrentProject(self) -> DaVinciProject | None:
        """Get the currently active project."""
        ...


# Type aliases for common return types
ResolveVersion = list[str]
ProjectName = str
TimelineName = str
PageName = str
MediaClipInfo = dict[str, Any]
