"""Double Play GHOSV observation adapter. AUTHORITY=NONE."""

from scripts.ops.double_play_ghosv_observation_adapter_v1.observe_v1 import (
    ObservationRequestV1,
    observe_double_play_catalog_v1,
)

__all__ = [
    "ObservationRequestV1",
    "observe_double_play_catalog_v1",
]
