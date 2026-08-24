# SPDX-License-Identifier: GPL-3.0-or-later
"""
Domain registry and DomainModule protocol.

DOMAIN_REGISTRY maps domain names to their module instances. Adding a new
domain means adding one entry here — no other server file changes.
"""

from typing import Any, Protocol, runtime_checkable

import mcp.types as types

from ..resolve_client import DaVinciResolveClient


@runtime_checkable
class DomainModule(Protocol):
    """Interface every domain module must satisfy."""

    name: str
    description: str

    def get_tools(self) -> list[types.Tool]: ...

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        client: DaVinciResolveClient,
    ) -> Any: ...


from .clip_properties import ClipPropertiesDomain  # noqa: E402
from .color_grading import ColorGradingDomain  # noqa: E402
from .media_pool import MediaPoolDomain  # noqa: E402
from .project_management import ProjectManagementDomain  # noqa: E402
from .render_delivery import RenderDeliveryDomain  # noqa: E402
from .system_fairlight_storage import SystemFairlightStorageDomain  # noqa: E402
from .timeline_item_editing import TimelineItemEditingDomain  # noqa: E402
from .timeline_operations import TimelineOperationsDomain  # noqa: E402

DOMAIN_REGISTRY: dict[str, DomainModule] = {
    "project_management": ProjectManagementDomain(),
    "timeline_operations": TimelineOperationsDomain(),
    "media_pool": MediaPoolDomain(),
    "render_delivery": RenderDeliveryDomain(),
    "clip_properties": ClipPropertiesDomain(),
    "system_fairlight_storage": SystemFairlightStorageDomain(),
    "color_grading": ColorGradingDomain(),
    "timeline_item_editing": TimelineItemEditingDomain(),
}
