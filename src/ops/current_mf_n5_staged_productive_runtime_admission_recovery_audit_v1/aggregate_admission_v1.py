"""Conservative multi-lane aggregate admission (no upgrade of lane dispositions)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.orchestrator_v1 import (
    ProductiveFullAutonomyN5LaneRollupV1,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.constants_v1 import (
    ADMISSION_DENIED_N_GT_1,
    AGGREGATE_ADMISSION_DENIED,
    AGGREGATE_ALL_LANES_SUCCESS,
    AGGREGATE_FAIL_CLOSED,
    AGGREGATE_PARTIAL,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.staged_cardinality_v1 import (
    StagedTargetCardinalityDecisionV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_COMPLETED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)

_LANE_SUCCESS = frozenset(
    {
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        DISPOSITION_HOLD,
        DISPOSITION_COMPLETED,
    }
)


@dataclass(frozen=True)
class AggregateMultiLaneAdmissionV1:
    aggregate_class: str
    aggregate_disposition: str
    lane_count: int
    success_lane_count: int
    fail_closed_lane_count: int
    per_lane_dispositions: tuple[tuple[str, str], ...]
    admission_denied_before_orchestration: bool


def compose_aggregate_multi_lane_admission_v1(
    *,
    cardinality: StagedTargetCardinalityDecisionV1,
    lane_rollups: Sequence[ProductiveFullAutonomyN5LaneRollupV1],
) -> AggregateMultiLaneAdmissionV1:
    if cardinality.admission_class == ADMISSION_DENIED_N_GT_1:
        return AggregateMultiLaneAdmissionV1(
            aggregate_class=AGGREGATE_ADMISSION_DENIED,
            aggregate_disposition=DISPOSITION_FAIL_CLOSED,
            lane_count=0,
            success_lane_count=0,
            fail_closed_lane_count=0,
            per_lane_dispositions=(),
            admission_denied_before_orchestration=True,
        )

    per_lane = tuple((r.lane_id, str(r.disposition)) for r in lane_rollups)
    success = sum(1 for _, d in per_lane if d in _LANE_SUCCESS)
    fail_closed = sum(1 for _, d in per_lane if d == DISPOSITION_FAIL_CLOSED)
    lane_count = len(per_lane)

    if fail_closed > 0:
        agg_disp = DISPOSITION_FAIL_CLOSED
        agg_class = AGGREGATE_FAIL_CLOSED
    elif success == lane_count and lane_count > 0:
        agg_disp = DISPOSITION_PRE_EXTERNAL_EFFECT
        agg_class = AGGREGATE_ALL_LANES_SUCCESS
    elif success > 0 and success < lane_count:
        agg_disp = DISPOSITION_HOLD
        agg_class = AGGREGATE_PARTIAL
    elif lane_count == 0:
        agg_disp = DISPOSITION_FAIL_CLOSED
        agg_class = AGGREGATE_FAIL_CLOSED
    else:
        agg_disp = DISPOSITION_HOLD
        agg_class = AGGREGATE_PARTIAL

    return AggregateMultiLaneAdmissionV1(
        aggregate_class=agg_class,
        aggregate_disposition=agg_disp,
        lane_count=lane_count,
        success_lane_count=success,
        fail_closed_lane_count=fail_closed,
        per_lane_dispositions=per_lane,
        admission_denied_before_orchestration=False,
    )


def lane_mv2_dp_provenance_from_readiness(
    readiness_projections: Mapping[str, object],
) -> tuple[tuple[str, str, str], ...]:
    """Lane id, venue_native_id, disposition — observability only."""
    rows: list[tuple[str, str, str]] = []
    for lane_id in sorted(readiness_projections):
        projection = readiness_projections[lane_id]
        record = getattr(projection, "n1_consumer_result", None)
        if record is None:
            continue
        bound = getattr(record, "bound_instrument", None)
        native = str(getattr(bound, "venue_native_id", "") or "")
        cycle = getattr(record, "governed_cycle_result", None)
        disp = str(getattr(cycle, "disposition", "") or "")
        rows.append((lane_id, native, disp))
    return tuple(rows)
