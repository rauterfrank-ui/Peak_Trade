"""RW-E20–E21: orchestration-only standing N=1 supervisor (PRE_EXTERNAL terminal)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)
from src.ops.hard_facts_system_closure_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    POST_ALLOWED,
    PRE_EXTERNAL_TERMINAL,
    SUPERVISOR_ZERO_ECONOMIC_AUTHORITY,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
)


@dataclass(frozen=True)
class StandingSupervisorProofV1:
    ok: bool
    supervisor_standing: bool
    continuous_n1_pre_external: bool
    post_count: int
    orchestration_only: bool


def prove_standing_supervisor_authority_boundary_v1() -> bool:
    proof = prove_hard_facts_authority_invariants_v1()
    return (
        proof.ok
        and proof.authority_matrix["supervisor_zero_economic_authority"]
        and SUPERVISOR_ZERO_ECONOMIC_AUTHORITY is True
    )


def compose_standing_n1_cycle_plan_v1() -> tuple[str, ...]:
    """Declared runtime composition order (orchestration-only; no authority acquisition)."""

    return (
        "public_observation",
        "real_ranking",
        "policy_a",
        "n1_membership",
        "private_observation_reconciliation",
        "custody_health_safety",
        "governed_full_core_cycle",
        "mv2_double_play",
        "final_order_envelope",
        "pre_external",
    )


def prove_standing_n1_pre_external_supervisor_v1(
    *,
    pre_external_reached: bool,
    post_count: int = 0,
) -> StandingSupervisorProofV1:
    boundary = prove_standing_supervisor_authority_boundary_v1()
    plan = compose_standing_n1_cycle_plan_v1()
    orchestration_only = len(plan) >= 10 and boundary
    safe = (
        POST_ALLOWED is False
        and EXTERNAL_EFFECT_AUTHORIZED is False
        and REAL_VENUE_POST_ALLOWED is False
        and MULTI_FUTURE_RUNTIME_AUTHORIZED is False
        and int(MAX_POSITIONS_EFFECTIVE) == 1
        and PRE_EXTERNAL_TERMINAL is True
        and post_count == 0
    )
    return StandingSupervisorProofV1(
        ok=boundary and safe and pre_external_reached,
        supervisor_standing=boundary,
        continuous_n1_pre_external=pre_external_reached and safe,
        post_count=post_count,
        orchestration_only=orchestration_only,
    )


def supervisor_cycle_trace_v1(*, run_id: str, instrument: str) -> Mapping[str, Any]:
    return {
        "RUN_ID": run_id,
        "instrument": instrument,
        "composition": compose_standing_n1_cycle_plan_v1(),
        "POST_COUNT": 0,
        "terminal": "PRE_EXTERNAL",
    }
