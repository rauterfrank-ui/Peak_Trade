"""Map WP-01 runtime supervisor session to standing supervisor admission proof."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.hard_facts_system_closure_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PRE_EXTERNAL_TERMINAL,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorRunResultV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.standing_n1_pre_external_supervisor_v1 import (
    StandingSupervisorProofV1,
    prove_standing_supervisor_authority_boundary_v1,
)


def prove_standing_supervisor_from_runtime_session_v1(
    result: StandingSupervisorRunResultV1,
    *,
    min_governed_cycles: int = 2,
    require_wp02_handoff: bool = True,
    pre_external_reached: bool | None = None,
) -> StandingSupervisorProofV1:
    boundary = prove_standing_supervisor_authority_boundary_v1()
    trace = result.trace
    safe = (
        POST_ALLOWED is False
        and EXTERNAL_EFFECT_AUTHORIZED is False
        and REAL_VENUE_POST_ALLOWED is False
        and MULTI_FUTURE_RUNTIME_AUTHORIZED is False
        and int(MAX_POSITIONS_EFFECTIVE) == 1
        and PRE_EXTERNAL_TERMINAL is True
        and trace.post_count == 0
    )
    runtime_standing = (
        result.ok
        and trace.recovery_completed
        and trace.public_supply_refreshed
        and trace.pretrade_truth_refreshed
        and trace.governed_cycle_count >= min_governed_cycles
        and trace.accepted_c1_count >= min_governed_cycles
        and trace.continuous_admission_granted
    )
    if require_wp02_handoff:
        runtime_standing = (
            runtime_standing
            and trace.wp02_hook_invoked
            and trace.wp02_cap21_refresh_invoked
            and trace.wp02_hard_facts_handoff_invoked
        )
    pre_external = bool(trace.terminal_disposition == "PRE_EXTERNAL_EFFECT") or bool(
        trace.extra.get("natural_enter_decision") in ("enter_long", "enter_short")
    )
    if pre_external_reached is not None:
        pre_external = pre_external_reached
    continuous = pre_external and safe and runtime_standing
    return StandingSupervisorProofV1(
        ok=boundary and safe and runtime_standing and continuous,
        supervisor_standing=boundary and runtime_standing,
        continuous_n1_pre_external=continuous,
        post_count=trace.post_count,
        orchestration_only=boundary,
    )
