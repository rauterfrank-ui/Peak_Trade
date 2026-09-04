"""Canonical predicate for LIVE_ORDER_PLAN_OBSERVED.

Does not imply LIVE_SUBMIT_ACK_OBSERVED. Does not authorize POST by itself.
Blocked dry-run and direct builder invocation are insufficient.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    BLOCKED_DRY_RUN_IS_NOT_LIVE_ORDER_PLAN_OBSERVED,
    FORBIDDEN_LIVE_SOURCE_KINDS,
    LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
    POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

ORDER_PLAN_OBSERVED_CONSTITUENTS: tuple[str, ...] = (
    "LIVE_EXECUTION_CODE_EXISTS",
    "LIVE_EXECUTION_PATH_REACHABLE",
    "LIVE_PRIVATE_READ_ONLY_PROVEN",
    "PRODUCED_ON_CANONICAL_SUBMIT_PATH",
    "AFTER_REFUSE_SUBMIT_UNLESS_GATES_PASS",
    "CURRENT_VENUE_DERIVED_INPUTS",
    "ORDER_PLAN_ARTIFACT_PRESENT",
    "NOT_BLOCKED_DRY_RUN",
    "NOT_DIRECT_BUILDER_INVOCATION",
    "NO_POST_REQUIRED",
)
ORDER_PLAN_OBSERVED_CONSTITUENT_COUNT = 10
ADMISSIBLE_SOURCE_KIND = "GOVERNED_CURRENT_GATED_SUBMIT_PATH"


def evaluate_order_plan_observed_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str = ADMISSIBLE_SOURCE_KIND,
) -> dict[str, Any]:
    kind = str(source_kind or "").strip().upper()
    if kind in FORBIDDEN_LIVE_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError(
            f"FORBIDDEN_LIVE_SOURCE:{kind}:LIVE_ORDER_PLAN_OBSERVED"
        )
    if kind != ADMISSIBLE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError(f"INADMISSIBLE_SOURCE_KIND:{kind}")
    missing = [name for name in ORDER_PLAN_OBSERVED_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError("ORDER_PLAN_CONSTITUENT_MISSING:" + ",".join(missing))
    false_required = [
        name
        for name in ORDER_PLAN_OBSERVED_CONSTITUENTS
        if constituent_values.get(name) is not True
    ]
    claim = len(false_required) == 0
    return {
        "canonical_definition": LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
        "claim_value": claim,
        "adjudication": "TRUE_CURRENT_LIVE_ORDER_PLAN_OBSERVED" if claim else "FALSE_FAIL_CLOSED",
        "false_required": false_required,
        "constituent_count": ORDER_PLAN_OBSERVED_CONSTITUENT_COUNT,
        "source_kind": kind,
        "POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED": (POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED),
        "BLOCKED_DRY_RUN_IS_NOT_LIVE_ORDER_PLAN_OBSERVED": (
            BLOCKED_DRY_RUN_IS_NOT_LIVE_ORDER_PLAN_OBSERVED
        ),
    }
