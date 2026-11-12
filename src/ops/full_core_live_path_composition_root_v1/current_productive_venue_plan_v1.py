"""Bind a CURRENT_PRODUCTIVE venue plan from Master-V2 replay + Cap-24 binding.

Does not fabricate ENTER, size, or plan. Missing replay is a truthful deny.
STEP-29Q remains PLAN_ONLY at composition. No POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1
    from .final_order_envelope_v1 import FinalOrderEnvelopeV1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        CurrentProductiveDoublePlay29PInputV1,
        CurrentProductiveEnterLive29PInjectedGetV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
        N1VenueQuantityLimitAssessmentV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import HostBudgetRecoveryContextV1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
        PositionManagementCloseIntentHandoffV1,
    )


from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    MODE_LIVE,
    MODE_SIMULATION,
    PATH_KIND,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
    CurrentProductiveVenuePlanInputAuthorityError,
    resolve_current_productive_order_environment_v1,
    resolve_current_productive_venue_plan_td_mode_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    CoreLiveExecutionIntentV1,
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
    full_close_handoff: PositionManagementCloseIntentHandoffV1 | None = None,
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
        full_close_handoff=full_close_handoff,
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


@dataclass(frozen=True)
class CurrentProductiveDoublePlay29QPlanV1:
    """The simulated reversal's plan before any execution binding."""

    reservation_id: str
    close_envelope_digest: str
    scope_digest: str
    canonical_intent: CanonicalOrderIntentV1
    venue_plan: VenuePlanCandidateV1
    quantity_admission: N1VenueQuantityLimitAssessmentV1


def try_prepare_current_productive_double_play_venue_plan_v1(
    *,
    reservation_id: str,
    double_play: CurrentProductiveDoublePlay29PInputV1,
    bound_instrument: BoundInstrumentV1,
    injected: CurrentProductiveEnterLive29PInjectedGetV1,
    decision_epoch: str,
    host_budget_recovery: HostBudgetRecoveryContextV1,
) -> tuple[CompositionStatusV1, tuple[str, ...], CurrentProductiveDoublePlay29QPlanV1 | None]:
    """Plan the exact reserved L10 reversal in the original simulated host."""
    from src.governance.canonical_order_intent_v1 import (
        CanonicalOrderIntentBuildInputV1,
        build_canonical_order_intent_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        bind_double_play_sizing_input_v1,
        read_current_double_play_sizing_source_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
        assess_n1_final_plan_venue_quantity_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        DoublePlayReservationSourceV1,
    )
    from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1 import (
        L10_OWNER,
    )

    if type(reservation_id) is not str or not reservation_id:
        return CompositionStatusV1.DENY, ("DOUBLE_PLAY_PLAN_REQUIRES_ORIGINAL_UNBOUND_HOLD",), None
    try:
        close = double_play.close_request
        continuation = double_play.continuation
        owner = close.budget_owner
        decision = read_current_double_play_sizing_source_v1(
            double_play,
            bound_instrument=bound_instrument,
            owner=owner,
            recovery=host_budget_recovery,
            injected=injected,
            decision_epoch=decision_epoch,
            reserved_id=reservation_id,
        )
        sizing = owner.read_double_play_reservation_sizing_v1(
            reservation_id,
            source=DoublePlayReservationSourceV1(close=close, continuation=continuation),
        )
        applied = sizing.applied_input
        if (
            sizing.monetary_source is None
            or sizing.monetary_source.decision_epoch != decision_epoch
            or applied.input_digest
            != bind_double_play_sizing_input_v1(
                decision=decision, capital_context=applied
            ).input_digest
        ):
            raise ValueError("DOUBLE_PLAY_PLAN_ORIGINAL_SIZING_SOURCE_CHANGED")
        account_scope = continuation.switch.episode.account_scope
        environment = resolve_current_productive_order_environment_v1(
            execution_mode=account_scope.execution_environment
        )
        td_mode = resolve_current_productive_venue_plan_td_mode_v1(conformance_required=False)
        policy = owner.entry_budget_policy_v1()
    except (
        ValueError,
        RuntimeError,
        OSError,
        TypeError,
        AttributeError,
        KeyError,
        ArithmeticError,
    ) as exc:
        return CompositionStatusV1.DENY, (str(exc),), None

    build = build_canonical_order_intent_v1(
        CanonicalOrderIntentBuildInputV1(
            sizing_input=applied,
            sizing_decision=sizing.decision,
            intent_id=f"intent-{applied.decision_id}",
            trading_epoch=decision_epoch,
            canonical_trading_logic_version=L10_OWNER,
            intent_action=applied.decision_outcome.upper(),
            policy_digest=policy.digest_v1(),
            order_type_policy="MARKET_ONLY",
            price_policy="EXPLICIT_NONE",
            time_in_force_policy="GTC",
            max_slippage_policy="NONE",
            expected_position_side=applied.selected_side,
            current_reconciled_exposure=applied.current_reconciled_exposure,
            current_open_side=applied.current_open_side,
        )
    )
    intent = build.intent
    if intent is None:
        return CompositionStatusV1.DENY, build.reason_codes, None

    execution_intent = CoreLiveExecutionIntentV1(
        instrument_id=bound_instrument.instrument_id,
        venue_native_id=bound_instrument.venue_native_id,
        side=intent.side,
        quantity=intent.quantity,
        quantity_unit=intent.quantity_unit,
        quantity_provenance=intent.quantity_provenance,
        intent_action=intent.intent_action,
        order_type_policy=intent.order_type_policy,
        reduce_only=intent.reduce_only,
        source_intent_id=intent.intent_id,
        source_decision_id=intent.decision_id,
        source_semantic_digest=intent.semantic_digest,
        source_trading_epoch=intent.trading_epoch,
        replay_id="",
        selection_id=bound_instrument.selection_id,
        ranking_snapshot_id=bound_instrument.ranking_snapshot_id,
        universe_snapshot_id=bound_instrument.universe_snapshot_id,
        sizing_result_ref=intent.sizing_result_ref,
        capital_envelope_ref=intent.capital_envelope_ref,
        safety_boundary_ref="",
        decision_outcome=applied.decision_outcome,
        mode=MODE_SIMULATION,
        path_kind=PATH_KIND,
        composed_epoch=decision_epoch,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        execution_eligible=False,
        submission_authorized=False,
        capital_risk_mode="LIVE_ACCOUNT_BOUND",
    )
    status, reasons, plan = translate_core_live_intent_to_venue_plan_v1(
        execution_intent,
        session_id=applied.decision_id,
        run_id=reservation_id,
        td_mode=td_mode,
        order_environment=environment,
    )
    if status is not CompositionStatusV1.PASS or plan is None:
        return status, reasons, None
    quantity_admission = assess_n1_final_plan_venue_quantity_v1(
        observation=injected.venue_quantity_limits,
        plan=plan,
        bound_instrument=bound_instrument,
        account_identity=account_scope.account_identity,
        decision_epoch=decision_epoch,
        cycle_id=decision.decision_id,
    )
    if not quantity_admission.allowed:
        return CompositionStatusV1.DENY, quantity_admission.reason_codes, None
    return (
        status,
        reasons,
        CurrentProductiveDoublePlay29QPlanV1(
            reservation_id=reservation_id,
            close_envelope_digest=continuation.close_envelope_digest,
            scope_digest=continuation.switch.scope_digest,
            canonical_intent=intent,
            venue_plan=plan,
            quantity_admission=quantity_admission,
        ),
    )


def bind_current_productive_double_play_execution_plan_v1(
    *,
    reservation_id: str,
    double_play: CurrentProductiveDoublePlay29PInputV1,
    bound_instrument: BoundInstrumentV1,
    injected: CurrentProductiveEnterLive29PInjectedGetV1,
    decision_epoch: str,
    host_budget_recovery: HostBudgetRecoveryContextV1,
) -> FinalOrderEnvelopeV1:
    """Durably bind the currently checked simulated reversal to its original hold."""
    from .final_order_envelope_v1 import bind_final_order_envelope_from_venue_plan_v1
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        DoublePlayReservationSourceV1,
    )

    status, reasons, plan = try_prepare_current_productive_double_play_venue_plan_v1(
        reservation_id=reservation_id,
        double_play=double_play,
        bound_instrument=bound_instrument,
        injected=injected,
        decision_epoch=decision_epoch,
        host_budget_recovery=host_budget_recovery,
    )
    if status is not CompositionStatusV1.PASS or plan is None:
        raise ValueError(reasons[0])
    continuation = double_play.continuation
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan.venue_plan,
        admission_ref="double-play-reservation:" + reservation_id,
        provenance_ref=continuation.switch.admission_ref_v1(),
        creation_epoch=decision_epoch,
    )
    close = double_play.close_request
    close.budget_owner.bind_double_play_execution_plan_v1(
        plan, envelope, source=DoublePlayReservationSourceV1(close=close, continuation=continuation)
    )
    return envelope
