"""Offline host/composition seam for a future separately authorized activation.

Does not activate the Cap 7.2 host graph. Construction, import, and default
runtime leave HOST_GRAPH_ACTIVATION=false and do not reach a productive wire.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.recording_transport_v1 import (
    OfflineRecordingTransportV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    HOST_COMPOSITION_SEAM_IMPLEMENTED,
    HOST_GRAPH_ACTIVATION,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_v1 import (
    RouteCSubmitCompositionInputV1,
    RouteCSubmitCompositionResultV1,
    run_route_c_submit_composition_v1,
)


class RouteCHostCompositionSeamError(RuntimeError):
    """Fail-closed host composition seam violation."""


@dataclass(frozen=True)
class RouteCHostCompositionSeamV1:
    """Opt-in offline port. Future host activation requires a separate Owner-GO."""

    host_graph_activation: bool = False
    seam_implemented: bool = HOST_COMPOSITION_SEAM_IMPLEMENTED

    def __post_init__(self) -> None:
        if self.host_graph_activation or HOST_GRAPH_ACTIVATION:
            raise RouteCHostCompositionSeamError("HOST_GRAPH_ACTIVATION_FORBIDDEN")
        if self.seam_implemented is not True:
            raise RouteCHostCompositionSeamError("HOST_COMPOSITION_SEAM_NOT_IMPLEMENTED")

    def compose(
        self,
        payload: RouteCSubmitCompositionInputV1,
        *,
        transport: OfflineRecordingTransportV1 | None = None,
    ) -> RouteCSubmitCompositionResultV1:
        if payload.host_activation_requested:
            raise RouteCHostCompositionSeamError("HOST_GRAPH_ACTIVATION_FORBIDDEN")
        return run_route_c_submit_composition_v1(payload, transport=transport)

    def to_dict(self) -> dict[str, Any]:
        return {
            "host_graph_activation": self.host_graph_activation,
            "seam_implemented": self.seam_implemented,
            "HOST_GRAPH_ACTIVATION": HOST_GRAPH_ACTIVATION,
        }


def bind_route_c_host_composition_seam_v1() -> RouteCHostCompositionSeamV1:
    """Return the inactive offline host seam. Does not activate runtime."""
    return RouteCHostCompositionSeamV1()
