"""Explicit staged target cardinality admission (capability ≠ authorization)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn

from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.constants_v1 import (
    ADMISSION_ARCHITECTURAL_HARNESS,
    ADMISSION_DENIED_N_GT_1,
    ADMISSION_PRODUCTIVE,
    FAILURE_CARDINALITY,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    PRODUCTIVE_AUTHORIZED_MAX_CARDINALITY,
    TARGET_CARDINALITY_MAX,
    TARGET_CARDINALITY_MIN,
)


class StagedTargetCardinalityError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise StagedTargetCardinalityError(code, detail)


@dataclass(frozen=True)
class StagedTargetCardinalityDecisionV1:
    requested_target_cardinality: int
    authorized_productive_cardinality: int
    invocation_cardinality: int
    admission_class: str
    productive_admitted: bool
    architectural_harness_used: bool
    n_gt_1_enabled: bool
    multi_future_runtime_authorized: bool


def evaluate_staged_target_cardinality_v1(
    *,
    requested_target_cardinality: int,
    architectural_composition_harness: bool = False,
) -> StagedTargetCardinalityDecisionV1:
    """Bound requested target; separate productive authorization from harness capability."""
    requested = int(requested_target_cardinality)
    if requested < TARGET_CARDINALITY_MIN or requested > TARGET_CARDINALITY_MAX:
        _fail(FAILURE_CARDINALITY, str(requested))

    authorized_productive = int(PRODUCTIVE_AUTHORIZED_MAX_CARDINALITY)
    harness = bool(architectural_composition_harness)

    if requested <= authorized_productive:
        return StagedTargetCardinalityDecisionV1(
            requested_target_cardinality=requested,
            authorized_productive_cardinality=authorized_productive,
            invocation_cardinality=requested,
            admission_class=ADMISSION_PRODUCTIVE,
            productive_admitted=True,
            architectural_harness_used=False,
            n_gt_1_enabled=bool(N_GT_1_ENABLED),
            multi_future_runtime_authorized=bool(MULTI_FUTURE_RUNTIME_AUTHORIZED),
        )

    if harness:
        return StagedTargetCardinalityDecisionV1(
            requested_target_cardinality=requested,
            authorized_productive_cardinality=authorized_productive,
            invocation_cardinality=requested,
            admission_class=ADMISSION_ARCHITECTURAL_HARNESS,
            productive_admitted=False,
            architectural_harness_used=True,
            n_gt_1_enabled=bool(N_GT_1_ENABLED),
            multi_future_runtime_authorized=bool(MULTI_FUTURE_RUNTIME_AUTHORIZED),
        )

    return StagedTargetCardinalityDecisionV1(
        requested_target_cardinality=requested,
        authorized_productive_cardinality=authorized_productive,
        invocation_cardinality=0,
        admission_class=ADMISSION_DENIED_N_GT_1,
        productive_admitted=False,
        architectural_harness_used=False,
        n_gt_1_enabled=bool(N_GT_1_ENABLED),
        multi_future_runtime_authorized=bool(MULTI_FUTURE_RUNTIME_AUTHORIZED),
    )
