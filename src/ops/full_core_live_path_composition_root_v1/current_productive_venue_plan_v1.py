"""Bind a CURRENT_PRODUCTIVE venue plan from Master-V2 replay + Cap-24 binding.

Does not fabricate ENTER, size, or plan. Missing replay is a truthful deny.
STEP-29Q remains PLAN_ONLY at composition. No POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import Optional

from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
    CurrentProductiveVenuePlanInputAuthorityError,
    resolve_current_productive_order_environment_v1,
    resolve_current_productive_venue_plan_td_mode_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    VenuePlanCandidateV1,
)
from src.ops.full_core_live_path_composition_root_v1.venue_translation_v1 import (
    translate_core_live_intent_to_venue_plan_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT = "CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT"


def try_bind_current_productive_venue_plan_v1(
    *,
    replay: Optional[IntegratedOfflineReplayResultV1],
    bound_instrument: BoundInstrumentV1,
    session_id: str,
    run_id: str,
    composed_epoch: str,
    execution_mode: str | None = None,
    conflicting_execution_mode: str | None = None,
    requested_environment: str | None = None,
    conformance_required: bool = False,
    observed_td_mode: str | None = None,
    observed_mgn_mode: str | None = None,
) -> tuple[CompositionStatusV1, tuple[str, ...], VenuePlanCandidateV1 | None]:
    """Bind the venue plan. td_mode and environment come only from the authority.

    ``MODE_LIVE`` remains the existing composition-mode argument. It is not
    the order-environment owner. A missing, unknown, or conflicting
    execution mode returns no plan.
    """

    if replay is None:
        return CompositionStatusV1.DENY, (CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,), None
    try:
        td_mode = resolve_current_productive_venue_plan_td_mode_v1(
            conformance_required=conformance_required,
            observed_td_mode=observed_td_mode,
            observed_mgn_mode=observed_mgn_mode,
        )
        order_environment = resolve_current_productive_order_environment_v1(
            execution_mode=execution_mode,
            conflicting_mode=conflicting_execution_mode,
            requested_environment=requested_environment,
        )
    except CurrentProductiveVenuePlanInputAuthorityError as exc:
        return CompositionStatusV1.DENY, (exc.reason_code,), None
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
        active_ghv_pre_external_runtime_flight_recorder_session_v1,
        append_flight_record_stage_v1,
    )

    predicate_traces: list[dict[str, object]] = []
    status, reasons, intent = compose_core_live_execution_intent_v1(
        replay=replay,
        bound_instrument=bound_instrument,
        mode=MODE_LIVE,
        composed_epoch=composed_epoch,
        predicate_trace_collector=predicate_traces,
    )
    recorder = active_ghv_pre_external_runtime_flight_recorder_session_v1()
    parent_gen = "gen_venue_plan_root"
    if recorder is not None:
        parent_gen = (
            append_flight_record_stage_v1(
                stage="VENUE_PLAN_COMPOSE_EXECUTION_INTENT",
                producer_symbol="compose_core_live_execution_intent_v1",
                consumer_symbol="try_bind_current_productive_venue_plan_v1",
                parent_generation_id=parent_gen,
                replay=replay,
                extra={
                    "compose_status": str(status),
                    "compose_reasons": list(reasons),
                },
                predicate_traces=tuple(predicate_traces),
            )
            or parent_gen
        )
    if status is not CompositionStatusV1.PASS or intent is None:
        if recorder is not None:
            append_flight_record_stage_v1(
                stage="VENUE_PLAN_BIND",
                producer_symbol="try_bind_current_productive_venue_plan_v1",
                consumer_symbol="downstream_pre_external",
                parent_generation_id=parent_gen,
                replay=replay,
                extra={
                    "venue_plan_status": str(status),
                    "venue_plan_reasons": list(reasons),
                    "venue_plan_pass": False,
                },
                predicate_traces=tuple(predicate_traces),
            )
        return status, reasons, None
    translate_status, translate_reasons, plan = translate_core_live_intent_to_venue_plan_v1(
        intent,
        session_id=session_id,
        run_id=run_id,
        td_mode=td_mode,
        order_environment=order_environment,
    )
    if recorder is not None:
        append_flight_record_stage_v1(
            stage="VENUE_PLAN_BIND",
            producer_symbol="translate_core_live_intent_to_venue_plan_v1",
            consumer_symbol="downstream_pre_external",
            parent_generation_id=parent_gen,
            replay=replay,
            extra={
                "venue_plan_status": str(translate_status),
                "venue_plan_reasons": list(translate_reasons),
                "venue_plan_pass": translate_status is CompositionStatusV1.PASS
                and plan is not None,
                "venue_plan_input_generation_id": parent_gen,
            },
            predicate_traces=tuple(predicate_traces),
        )
    return translate_status, translate_reasons, plan
