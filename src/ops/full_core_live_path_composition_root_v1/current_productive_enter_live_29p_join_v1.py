"""Join Live-29P GET into Current-Productive ENTER before venue-plan.

HOLD/observe skips the private GET. ENTER consumes the existing governed
Live-29P producer/evaluator exactly once. Offline-default equity cannot
bind a Current-Productive external-effect envelope. Does not mint a
permit. Does not POST. STEP-29Q remains PLAN_ONLY.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from datetime import datetime
from functools import partial
from pathlib import Path
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, Mapping, Optional

if TYPE_CHECKING:
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        IsolatedLaneSlotV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        ProductiveCycleCanonicalPriceProvenanceV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
        PostCloseDoublePlayContinuationV1,
        PostCloseFeedbackRequestV1,
    )
    from .current_productive_l10_close_reconciliation_v1 import (
        PostCloseDoublePlayCounterOrderRequestV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
        SlotCapitalBasisV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import HostBudgetRecoveryContextV1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
        N1VenueQuantityLimitsObservationV1,
    )

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1 import (
    CurrentProductiveMv2CapitalContextRebindError,
    build_current_productive_live_account_capital_context_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    PRODUCER_IDENTITY,
    reject_direct_avail_eq_29p_claim_v1,
    CurrentProductiveUsdcFreeMarginObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    build_full_core_margin_inputs_from_budget_owner_v1,
    execute_current_productive_treasury_single_source_capital_handoff_v1,
)
from src.ops.b05_full_core_governed_authority_chain_closure_v1.registry_and_witness_v1 import (
    B05FullCoreAuthorityChainClosureError,
    OWNER_GO as B05_FULL_CORE_AUTHORITY_CHAIN_OWNER_GO,
    witness_b05_full_core_capital_authority_bindings_v1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1 import (
    produce_current_productive_reference_price_from_mv2_mark_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAILABLE_MARGIN_ENDPOINT_PATH,
    AVAILABLE_MARGIN_OUTPUT_DOMAIN,
    AVAILABLE_MARGIN_REQUIRED_CCY,
    AVAILABLE_MARGIN_REQUIRED_TD_MODE,
    LiveCanaryAvailableMarginObservationError,
    acquire_fresh_available_margin_observation_from_payload_v1,
    validate_fresh_available_margin_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    DoublePlayReservationSourceV1,
    PortfolioCapitalReservationBudgetOwnerV1,
    ReserveDispositionV1,
    SizedReservationResultV1,
    apply_capital_context_facts_v1,
    capital_context_facts_v1,
    admit_sized_slot_reservation_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
    build_capital_risk_sizing_input_from_decision_v0,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    finalize_offline_replay_decision_evidence_v1,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    bind_canonical_order_intent_offline_replay_evidence_v0,
)
from src.governance.canonical_order_intent_v1 import compute_quantity_provenance_ref
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
    evaluate_capital_risk_sizing_v1,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    REASON_PRODUCTIVE_CAPITAL_RISK_LIMITS_UNRESOLVED,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    RISK_SIZING_EFFECT_BOUND_OFFLINE,
    _DEFAULT_ACCOUNT_EQUITY,
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    compute_risk_sizing_decision_ref_v0,
    derive_protective_stop_price_from_adverse_exit_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)
from .current_productive_entry_budget_policy_v1 import (
    EntryBudgetPolicyV1,
    EntryBudgetPolicyError,
    load_entry_budget_policy_v1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_SEAM_V1"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
STATUS_NOT_CALLED_HOLD = "NOT_CALLED_HOLD"
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_STALE = "STALE"
STATUS_MISSING = "MISSING"
DECISION_HOLD = "HOLD"
DECISION_ENTER = "ENTER"
DECISION_OTHER = "OTHER"
DECISION_DOUBLE_PLAY = "DOUBLE_PLAY_COUNTER_SIZING"
STATUS_DOUBLE_PLAY_ASSESSED = "DOUBLE_PLAY_SIZING_ASSESSED"
STATUS_DOUBLE_PLAY_RESERVED = "DOUBLE_PLAY_SIZING_RESERVED"
DECISION_POSITION_MANAGEMENT = "POSITION_MANAGEMENT"
STATUS_NOT_CALLED_POSITION_MANAGEMENT = "NOT_CALLED_POSITION_MANAGEMENT"
POSITION_MANAGEMENT_HANDOFF_REQUIRED = "POSITION_MANAGEMENT_EXECUTION_HANDOFF_REQUIRED"
ENDPOINT = CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT
_ENTER = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})
_HOLD = frozenset(
    {
        DecisionOutcome.HOLD.value,
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.OBSERVE.value,
        DecisionOutcome.RECONCILE_ONLY.value,
        DecisionOutcome.CANCEL_PENDING.value,
        DecisionOutcome.BLOCKED.value,
    }
)


class CurrentProductiveEnterLive29PJoinError(RuntimeError):
    """Fail-closed Current-Productive ENTER Live-29P join violation."""


@dataclass(frozen=True)
class CurrentProductiveEnterLive29PPortfolioSlotContextV1:
    """Canonical slot/decision/cycle identity for portfolio reservation."""

    slot_id: str
    decision_id: str
    cycle_id: str


@dataclass(frozen=True)
class CurrentProductiveEnterLive29PInjectedGetV1:
    payload: Mapping[str, Any] | None = None
    get_performed: bool = False
    http_status: int = 0
    error_class: str = ""
    body_sha256: str = ""
    observed_at: str = ""
    age_seconds: str = "1"
    live_account_bound_status: str = LiveAccountBoundStatusV1.MISSING.value
    raw_acct_lv: str = ""
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE
    fresh_pretrade_get_status: str = FreshPretradeGetStatusV1.MISSING.value
    instruments_payload: Mapping[str, Any] | None = None
    index_tickers_payload: Mapping[str, Any] | None = None
    conversion_pair_instruments_payload: Mapping[str, Any] | None = None
    acquisition_decision_id: str = ""
    acquisition_cycle_id: str = ""
    pretrade_acquired_at_utc: tuple[str, ...] = ()
    venue_quantity_limits: N1VenueQuantityLimitsObservationV1 | None = None
    opening_cost_observation: object | None = None
    funding_cost_observation: object | None = None
    open_slot_loss_observation: object | None = None
    native_initial_margin_observation: object | None = None
    absolute_movement_cost_observation: object | None = None
    futures_financial_custody: object | None = None
    entry_public_mark_source: object | None = None


@dataclass(frozen=True)
class DoublePlay29PTestStopV1:
    venue_native_id: str
    target_side: str
    reference_mark: Decimal
    stop_price: Decimal
    source_ref: str


@dataclass(frozen=True)
class CurrentProductiveDoublePlay29PInputV1:
    continuation: PostCloseDoublePlayContinuationV1
    close_request: PostCloseFeedbackRequestV1
    lane: IsolatedLaneSlotV1
    mark: ProductiveCycleCanonicalPriceProvenanceV1
    test_stop: DoublePlay29PTestStopV1
    reserve: bool = False


@dataclass(frozen=True)
class _DoublePlaySizingDecisionV1:
    decision_id: str
    semantic_digest: str
    instrument_id: str
    selected_side: str
    decision_outcome: str


@dataclass(frozen=True)
class DoublePlay29PSizingAssessmentV1:
    close_envelope_digest: str
    capital_basis: SlotCapitalBasisV1
    test_stop: DoublePlay29PTestStopV1
    sizing_decision: CapitalRiskSizingDecisionV1
    execution_authority_effect: str = "NONE"


@dataclass(frozen=True)
class CurrentProductiveEnterLive29PJoinResultV1:
    decision_class: str
    called: bool
    get_count: int
    status: str
    venue_plan_authorized: bool
    first_blocker: str
    producer_output_value: str
    producer_output_status: str
    step_29p_risk_admissible: str
    capital_risk_mode: str
    used_offline_default_equity: str
    sizing_outcome: str
    replay: Optional[IntegratedOfflineReplayResultV1]
    post_count: str = "0"
    permit_created: str = "false"
    entry_budget_policy_id: str = ""
    entry_budget_policy_digest: str = ""
    portfolio_reservation_id: str = ""
    portfolio_reservation_disposition: str = ""
    reason_codes: tuple[str, ...] = ()
    double_play_sizing: DoublePlay29PSizingAssessmentV1 | None = None


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def current_productive_decision_class_v1(
    replay: IntegratedOfflineReplayResultV1 | None,
) -> str:
    if replay is None or replay.evidence is None:
        return DECISION_OTHER
    raw_outcome = replay.evidence.decision_outcome
    outcome = str(getattr(raw_outcome, "value", raw_outcome) or "").strip().lower()
    if outcome in _ENTER:
        return DECISION_ENTER
    if outcome in {DecisionOutcome.REDUCE.value, DecisionOutcome.EXIT.value}:
        return DECISION_POSITION_MANAGEMENT
    if outcome in _HOLD:
        return DECISION_HOLD
    return DECISION_OTHER


def resolve_protective_stop_sizing_side_for_live_29p_join_v1(
    replay: IntegratedOfflineReplayResultV1,
) -> str | None:
    """Map replay evidence to LONG/SHORT for adverse-exit stop derivation.

    Uses canonical ``selected_side`` when present (LONG/SHORT or composition
    long/short). For ENTER decisions whose ``selected_side`` is still ``none``
    (forensic synthetic overlay sets ``decision_outcome`` only), derives side
    from ``enter_long`` / ``enter_short`` fail-closed.
    """
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        map_selected_side_to_sizing_side,
    )

    evidence = replay.evidence
    mapped = map_selected_side_to_sizing_side(str(evidence.selected_side or ""))
    if mapped is not None:
        return mapped
    composition_side = str(evidence.selected_side or "").strip().lower()
    if composition_side == "long":
        return "LONG"
    if composition_side == "short":
        return "SHORT"
    raw_outcome = evidence.decision_outcome
    outcome = str(getattr(raw_outcome, "value", raw_outcome) or "").strip().lower()
    if outcome == DecisionOutcome.ENTER_LONG.value:
        return "LONG"
    if outcome == DecisionOutcome.ENTER_SHORT.value:
        return "SHORT"
    return None


def _hold_result(
    *, replay: IntegratedOfflineReplayResultV1 | None
) -> CurrentProductiveEnterLive29PJoinResultV1:
    return CurrentProductiveEnterLive29PJoinResultV1(
        decision_class=DECISION_HOLD,
        called=False,
        get_count=0,
        status=STATUS_NOT_CALLED_HOLD,
        venue_plan_authorized=True,
        first_blocker="",
        producer_output_value="",
        producer_output_status="NOT_REACHED",
        step_29p_risk_admissible=FALSE_TOKEN,
        capital_risk_mode=str(getattr(replay, "capital_risk_mode", "") or ""),
        used_offline_default_equity=FALSE_TOKEN,
        sizing_outcome="NOT_REACHED",
        replay=replay,
        reason_codes=(JOIN_SEAM_ID, STATUS_NOT_CALLED_HOLD),
    )


def _denied_result(
    *,
    status: str,
    blocker: str,
    replay: Optional[IntegratedOfflineReplayResultV1],
    get_count: int,
    producer_output_value: str = "",
    producer_output_status: str = "FAIL_CLOSED",
    step_29p_risk_admissible: str = FALSE_TOKEN,
    reasons: tuple[str, ...] = (),
    decision_class: str = DECISION_ENTER,
) -> CurrentProductiveEnterLive29PJoinResultV1:
    return CurrentProductiveEnterLive29PJoinResultV1(
        decision_class=decision_class,
        called=True,
        get_count=get_count,
        status=status,
        venue_plan_authorized=False,
        first_blocker=blocker,
        producer_output_value=producer_output_value,
        producer_output_status=producer_output_status,
        step_29p_risk_admissible=step_29p_risk_admissible,
        capital_risk_mode=CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        used_offline_default_equity=FALSE_TOKEN,
        sizing_outcome="DENIED",
        replay=replay,
        reason_codes=tuple(dict.fromkeys((blocker, *reasons, JOIN_SEAM_ID, status))),
    )


def _quantity_status_from_sizing_v1(decision: CapitalRiskSizingDecisionV1) -> str:
    provenance = decision.quantity_provenance
    if provenance is not None:
        return provenance.final_quantity_status.value
    if decision.outcome is CapitalRiskSizingOutcome.BLOCKED:
        return "BLOCK"
    return "NOT_BOUND"


def _rebound_replay_with_sizing_decision_v1(
    replay: IntegratedOfflineReplayResultV1,
    *,
    sizing_decision: CapitalRiskSizingDecisionV1,
    live_ctx: CanonicalCoreRuntimeCapitalContextV0,
) -> IntegratedOfflineReplayResultV1:
    evidence = replay.evidence
    quantity_provenance_ref = ""
    provenance = sizing_decision.quantity_provenance
    if provenance is not None:
        quantity_provenance_ref = compute_quantity_provenance_ref(provenance)
    risk_sizing_ref = compute_risk_sizing_decision_ref_v0(sizing_decision)
    quantity_status = _quantity_status_from_sizing_v1(sizing_decision)
    bound_evidence = replace(
        evidence,
        quantity_status=quantity_status,
        quantity_provenance_ref=quantity_provenance_ref,
        risk_sizing_ref=risk_sizing_ref,
        risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(bound_evidence)
    intent_binding = bind_canonical_order_intent_offline_replay_evidence_v0(
        finalized,
        sizing_decision=sizing_decision,
        capital_context=live_ctx,
    )
    rebound_intermediate = replace(
        replay.intermediate,
        capital_risk_sizing_decision=sizing_decision,
        canonical_order_intent=intent_binding.canonical_intent,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    )
    return replace(
        replay,
        evidence=intent_binding.evidence,
        intermediate=rebound_intermediate,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    )


def resolve_current_productive_live_29p_adverse_exit_distance_v1(
    replay: IntegratedOfflineReplayResultV1 | None,
) -> tuple[float | None, tuple[str, ...]]:
    """Consume the same effective Layer-C distance as the evaluated decision.

    Includes explicit legacy comparisons and CHOP-frozen scope states. Never
    recompute a different fresh raw distance behind the decision owner's back.
    """
    if replay is None or replay.intermediate is None:
        return None, ("replay_intermediate_missing",)
    try:
        distance = float(replay.intermediate.scope_event.semantic_binding.adverse_exit_distance)
    except (AttributeError, TypeError, ValueError):
        return None, ("layer_c_adverse_exit_unresolved",)
    if not math.isfinite(distance) or distance <= 0.0:
        return None, ("layer_c_adverse_exit_unresolved",)
    return float(distance), ()


def _classify_fail_status(reasons: tuple[str, ...], *, error_class: str) -> str:
    joined = " ".join(reasons) + " " + str(error_class or "")
    if "STALE" in joined:
        return STATUS_STALE
    if error_class or "UNKNOWN" in joined or "MALFORMED" in joined:
        return STATUS_UNKNOWN
    return STATUS_FAIL


def read_current_double_play_sizing_source_v1(
    request: CurrentProductiveDoublePlay29PInputV1,
    *,
    bound_instrument: BoundInstrumentV1 | None,
    owner: PortfolioCapitalReservationBudgetOwnerV1 | None,
    recovery: HostBudgetRecoveryContextV1 | None,
    injected: CurrentProductiveEnterLive29PInjectedGetV1 | None,
    decision_epoch: str,
    reserved_id: str | None = None,
) -> _DoublePlaySizingDecisionV1:
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        recover_occupied_scope_close_for_reconciliation_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        ProductiveCycleCanonicalPriceProvenanceV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import HostBudgetRecoveryContextV1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
        PostCloseDoublePlayContinuationV1,
        PostCloseFeedbackRequestV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.core_cursor_source_v1 import (
        _read_original_cursor,
    )
    from trading.master_v2.double_play_state import SideState
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
    )

    if (
        type(request) is not CurrentProductiveDoublePlay29PInputV1
        or type(request.reserve) is not bool
        or type(request.continuation) is not PostCloseDoublePlayContinuationV1
        or type(request.close_request) is not PostCloseFeedbackRequestV1
        or type(request.mark) is not ProductiveCycleCanonicalPriceProvenanceV1
        or type(recovery) is not HostBudgetRecoveryContextV1
        or type(injected) is not CurrentProductiveEnterLive29PInjectedGetV1
        or owner is None
        or recovery.host.owner is not owner
        or recovery.host.closed
        or recovery.host.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
    ):
        raise ValueError("DOUBLE_PLAY_29P_ORIGINAL_SIMULATED_HOST_REQUIRED")
    continuation, close = request.continuation, request.close_request
    episode = continuation.switch.episode
    lane_id, account = episode.lane_id, episode.account_scope.account_identity
    if (
        bound_instrument is None
        or bound_instrument != continuation.bound_instrument
        or close.bound_instrument != bound_instrument
        or recovery.host.bindings.get(lane_id) != bound_instrument
        or close.budget_owner is not owner
        or recovery.account != account
        or injected.expected_account_identity != account
        or recovery.pending_orders
        or recovery.position_side_v1(bound_instrument) != "FLAT"
    ):
        raise ValueError("DOUBLE_PLAY_29P_FLAT_ACCOUNT_BINDING_REQUIRED")
    recovered = recover_occupied_scope_close_for_reconciliation_v1(
        lane_id=lane_id,
        lane_pair=(request.lane, bound_instrument),
        expected_scope=episode.account_scope,
        sealed_accounting_source=close.slot_accounting_source,
    )
    release = owner.inspect_bounded_slot_close_refresh_v1(close, reserved_id=reserved_id)
    basis = owner.slot_capital_basis_v1(lane_id, close_booking=continuation.net_booking)
    if (
        recovered != close.execution
        or recovered.l10_close != continuation.switch
        or recovered.envelope.envelope_digest != continuation.close_envelope_digest
        or release["fingerprint"] != continuation.capital_refresh_fingerprint
    ):
        raise ValueError("DOUBLE_PLAY_29P_CLOSE_PROOF_MISMATCH")
    if basis is None or basis != continuation.capital_basis or basis.net_basis_usdc <= 0:
        raise ValueError("DOUBLE_PLAY_29P_POSITIVE_CURRENT_SLOT_BASIS_REQUIRED")
    cursor, _, raw = _read_original_cursor(
        request.lane.lane_state_root,
        instrument_id=bound_instrument.instrument_id,
        native_id=bound_instrument.venue_native_id,
    )
    if cursor.side_state is SideState.KILL_ALL:
        raise ValueError("DOUBLE_PLAY_29P_CURRENT_CORE_KILL_ALL")
    if (raw.get("runtime_scope_state") or {}).get("chop_latched") is not False:
        raise ValueError("DOUBLE_PLAY_29P_CURRENT_CORE_CHOP_OR_SCOPE_UNPROVEN")

    decision_time = datetime.fromisoformat(decision_epoch.replace("Z", "+00:00"))
    close_time = datetime.fromisoformat(close.observed_at_utc.replace("Z", "+00:00"))
    host_time = recovery.host.clock()
    if (
        decision_time.utcoffset() is None
        or close_time.utcoffset() is None
        or decision_time < close_time
        or not 0 <= host_time - decision_time.timestamp() <= NUMERIC_EQUITY_TTL_SECONDS
    ):
        raise ValueError("DOUBLE_PLAY_29P_DECISION_CLOCK_INVALID")
    mark = request.mark
    mark.validate_against_cycle_inputs_v1(
        mark_px=mark.mark_px,
        index_px=mark.index_px,
        venue_native_id=bound_instrument.venue_native_id,
    )
    event_unix = mark.require_current_mark_clock_v1(observed_unix=host_time)
    scope = read_occupied_scope_mark_snapshot_v1(Path(request.lane.lane_state_root))
    if scope is None or scope["digest"] != continuation.switch.scope_digest:
        raise ValueError("DOUBLE_PLAY_29P_SWITCH_SCOPE_CHANGED")
    switch_mark = scope["mark"]
    if not switch_mark["event_unix"] <= event_unix <= decision_time.timestamp() or (
        event_unix == switch_mark["event_unix"]
        and json.loads(mark.mark_clock_json)["payload_sha256"] != switch_mark["mark_payload_sha256"]
    ):
        raise ValueError("DOUBLE_PLAY_29P_CURRENT_SWITCH_MARK_UNPROVEN")

    stop = request.test_stop
    reference = Decimal(str(mark.mark_px))
    side = continuation.target_side
    if (
        type(stop) is not DoublePlay29PTestStopV1
        or stop.venue_native_id != bound_instrument.venue_native_id
        or stop.target_side != side
        or type(stop.reference_mark) is not Decimal
        or stop.reference_mark != reference
        or type(stop.stop_price) is not Decimal
        or not stop.stop_price.is_finite()
        or stop.stop_price <= 0
        or (side == "long" and stop.stop_price >= reference)
        or (side == "short" and stop.stop_price <= reference)
        or type(stop.source_ref) is not str
        or not stop.source_ref.strip()
    ):
        raise ValueError("DOUBLE_PLAY_29P_BOUND_TEST_STOP_REQUIRED")
    return _DoublePlaySizingDecisionV1(
        decision_id="l10:" + continuation.close_envelope_digest,
        semantic_digest=hashlib.sha256(
            json.dumps(
                {
                    "continuation": continuation.to_dict(),
                    "mark": mark.mark_clock_json,
                    "test_stop": str(stop.stop_price),
                    "test_stop_source": stop.source_ref,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
        instrument_id=bound_instrument.instrument_id,
        selected_side=side,
        decision_outcome="enter_" + side,
    )


def _build_double_play_sizing_input_v1(
    *,
    request: CurrentProductiveDoublePlay29PInputV1,
    decision: _DoublePlaySizingDecisionV1,
    live_ctx: CanonicalCoreRuntimeCapitalContextV0,
    owner: PortfolioCapitalReservationBudgetOwnerV1,
) -> CapitalRiskSizingInputV1:
    continuation = request.continuation
    lane_id = continuation.switch.episode.lane_id
    owner.inspect_bounded_slot_close_refresh_v1(request.close_request)
    basis = owner.slot_capital_basis_v1(lane_id, close_booking=continuation.net_booking)
    if basis is None or basis != continuation.capital_basis or basis.net_basis_usdc <= 0:
        raise ValueError("DOUBLE_PLAY_29P_POSITIVE_CURRENT_SLOT_BASIS_REQUIRED")
    context = replace(
        live_ctx, scope_capital_limit=min(live_ctx.scope_capital_limit, basis.net_basis_usdc)
    )
    return bind_double_play_sizing_input_v1(decision=decision, capital_context=context)


def bind_double_play_sizing_input_v1(
    *,
    decision: _DoublePlaySizingDecisionV1,
    capital_context: CanonicalCoreRuntimeCapitalContextV0 | CapitalRiskSizingInputV1,
) -> CapitalRiskSizingInputV1:
    """Use the original builder on the L10 decision and initial or retained sizing context."""
    # Both sources expose the original builder's decision and capital fields.
    sizing_input, reasons = build_capital_risk_sizing_input_from_decision_v0(
        decision=decision,  # type: ignore[arg-type]
        capital_context=capital_context,  # type: ignore[arg-type]
    )
    if sizing_input is None:
        raise ValueError(reasons[0] if reasons else "DOUBLE_PLAY_29P_SIZING_INPUT_UNPROVEN")
    return sizing_input


def _double_play_sizing_result_v1(
    *,
    request: CurrentProductiveDoublePlay29PInputV1,
    sizing: CapitalRiskSizingDecisionV1,
    get_count: int,
    producer_output_value: str,
    policy: EntryBudgetPolicyV1,
    reserve_result: SizedReservationResultV1 | None = None,
) -> CurrentProductiveEnterLive29PJoinResultV1:
    reservation = reserve_result.reservation if reserve_result is not None else None
    status = STATUS_DOUBLE_PLAY_RESERVED if reservation is not None else STATUS_DOUBLE_PLAY_ASSESSED
    continuation = request.continuation
    reasons = reserve_result.reason_codes if reserve_result is not None else sizing.reason_codes
    return CurrentProductiveEnterLive29PJoinResultV1(
        decision_class=DECISION_DOUBLE_PLAY,
        called=True,
        get_count=get_count,
        status=status,
        venue_plan_authorized=False,
        first_blocker=""
        if sizing.outcome is CapitalRiskSizingOutcome.PASS
        else sizing.reason_codes[0],
        producer_output_value=producer_output_value,
        producer_output_status="PRODUCED",
        step_29p_risk_admissible=TRUE_TOKEN,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        used_offline_default_equity=FALSE_TOKEN,
        sizing_outcome=sizing.outcome.value,
        replay=None,
        reason_codes=(JOIN_SEAM_ID, status, *reasons),
        entry_budget_policy_id=policy.policy_id,
        entry_budget_policy_digest=policy.digest_v1(),
        portfolio_reservation_id=str(reservation.reservation_id) if reservation is not None else "",
        portfolio_reservation_disposition=reserve_result.disposition.value
        if reserve_result is not None
        else "",
        double_play_sizing=DoublePlay29PSizingAssessmentV1(
            close_envelope_digest=continuation.close_envelope_digest,
            capital_basis=continuation.capital_basis,
            test_stop=request.test_stop,
            sizing_decision=sizing,
        ),
    )


def check_authenticated_double_play_29p_admission_v1(
    *,
    request: PostCloseDoublePlayCounterOrderRequestV1,
    bound_instrument: BoundInstrumentV1,
    owner: PortfolioCapitalReservationBudgetOwnerV1,
) -> CurrentProductiveEnterLive29PJoinResultV1:
    """Check the booked LIVE reversal at the 29P boundary."""
    from .current_productive_l10_close_reconciliation_v1 import (
        PostCloseDoublePlayCounterOrderRequestV1,
    )

    reasons = ()
    if (
        type(request) is not PostCloseDoublePlayCounterOrderRequestV1
        or not isinstance(owner, PortfolioCapitalReservationBudgetOwnerV1)
        or request.bound_instrument != bound_instrument
    ):
        blocker = "DOUBLE_PLAY_29P_LIVE_COUNTER_ORDER_CONTEXT_MISMATCH"
    else:
        try:
            owner.require_authenticated_l10_counter_order_source_v1(request)
        except ValueError as exc:
            blocker = str(exc)
        else:
            # The simulation's stop and capital basis have no LIVE source.
            blocker = "DOUBLE_PLAY_29P_LIVE_PROTECTIVE_STOP_REQUIRED"
            reasons = ("DOUBLE_PLAY_29P_LIVE_SLOT_CAPITAL_BASIS_REQUIRED",)
    return _denied_result(
        status=STATUS_FAIL,
        blocker=blocker,
        reasons=reasons,
        replay=None,
        get_count=0,
        decision_class=DECISION_DOUBLE_PLAY,
    )


def join_current_productive_enter_live_29p_before_venue_plan_v1(
    *,
    replay: IntegratedOfflineReplayResultV1 | None,
    bound_instrument: BoundInstrumentV1 | None,
    injected: CurrentProductiveEnterLive29PInjectedGetV1 | None = None,
    decision_epoch: str,
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
    portfolio_slot: CurrentProductiveEnterLive29PPortfolioSlotContextV1 | None = None,
    cycle_index: int | None = None,
    entry_budget_policy: EntryBudgetPolicyV1 | None = None,
    host_budget_recovery: HostBudgetRecoveryContextV1 | None = None,
    restrictive_risk: object | None = None,
    handoff_journal: object | None = None,
    double_play: CurrentProductiveDoublePlay29PInputV1 | None = None,
) -> CurrentProductiveEnterLive29PJoinResultV1:
    """Consume Live-29P on ENTER or assess and optionally reserve a simulated reversal."""
    reject_direct_avail_eq_29p_claim_v1(claimed="producer")
    native_decision = None
    if double_play is not None:
        try:
            if any(
                value is not None
                for value in (replay, portfolio_slot, handoff_journal, restrictive_risk)
            ):
                raise ValueError("DOUBLE_PLAY_29P_EXPLICIT_ASSESSMENT_INPUT_REQUIRED")
            native_decision = read_current_double_play_sizing_source_v1(
                double_play,
                bound_instrument=bound_instrument,
                owner=portfolio_budget_owner,
                recovery=host_budget_recovery,
                injected=injected,
                decision_epoch=decision_epoch,
            )
            portfolio_slot = CurrentProductiveEnterLive29PPortfolioSlotContextV1(
                double_play.continuation.switch.episode.lane_id,
                native_decision.decision_id,
                native_decision.decision_id,
            )
        except (ValueError, OSError, TypeError, AttributeError, ArithmeticError) as exc:
            return _denied_result(
                status=STATUS_FAIL,
                blocker=str(exc),
                replay=None,
                get_count=0,
                decision_class=DECISION_DOUBLE_PLAY,
            )
    _deny = (
        partial(_denied_result, decision_class=DECISION_DOUBLE_PLAY)
        if native_decision is not None
        else _denied_result
    )
    if (portfolio_budget_owner is None) ^ (portfolio_slot is None):
        raise CurrentProductiveEnterLive29PJoinError("PORTFOLIO_OWNER_SLOT_CONTEXT_PAIR_REQUIRED")
    if portfolio_slot is not None:
        if not str(portfolio_slot.slot_id or "").strip():
            raise CurrentProductiveEnterLive29PJoinError("PORTFOLIO_SLOT_ID_MISSING")
        if not str(portfolio_slot.decision_id or "").strip():
            raise CurrentProductiveEnterLive29PJoinError("PORTFOLIO_DECISION_ID_MISSING")
        if not str(portfolio_slot.cycle_id or "").strip():
            raise CurrentProductiveEnterLive29PJoinError("PORTFOLIO_CYCLE_ID_MISSING")
    if ENDPOINT != AVAILABLE_MARGIN_ENDPOINT_PATH:
        raise CurrentProductiveEnterLive29PJoinError("ENDPOINT_DRIFT")
    decision_class = current_productive_decision_class_v1(replay)
    if decision_class == DECISION_POSITION_MANAGEMENT:
        return replace(
            _hold_result(replay=replay),
            decision_class=DECISION_POSITION_MANAGEMENT,
            status=STATUS_NOT_CALLED_POSITION_MANAGEMENT,
            venue_plan_authorized=False,
            first_blocker=POSITION_MANAGEMENT_HANDOFF_REQUIRED,
            reason_codes=(
                JOIN_SEAM_ID,
                STATUS_NOT_CALLED_POSITION_MANAGEMENT,
                POSITION_MANAGEMENT_HANDOFF_REQUIRED,
            ),
        )
    if native_decision is None and decision_class != DECISION_ENTER:
        return _hold_result(replay=replay)

    if handoff_journal is not None and restrictive_risk is None:
        return _deny(
            status=STATUS_FAIL,
            blocker="HANDOFF_REQUIRES_BOUND_RISK_RESERVATION",
            replay=replay,
            get_count=0,
        )

    if restrictive_risk is not None:
        # Explicit injected offline entry only. Do not add productive risk
        # activation or acquire a new private port to validate this profile.
        from src.risk.decision_bound_model_adapters_v1 import OfflineRiskRequestV1

        try:
            if (
                type(restrictive_risk) is not OfflineRiskRequestV1
                or injected is None
                or host_budget_recovery is None
                or portfolio_budget_owner is not host_budget_recovery.host.owner
                or host_budget_recovery.host.closed
            ):
                raise ValueError("OFFLINE_RISK_BOUND_EXISTING_HOST_AND_INJECTED_PORT_REQUIRED")
            observed = host_budget_recovery.observed
            expected_positions = {
                p.instrument_id: p.signed_quantity
                for p in observed.positions
                if p.signed_quantity != 0
            }
            actual_positions = {
                p.canonical_id: p.signed_contracts
                for p in restrictive_risk.data.positions
                if p.signed_contracts != 0
            }
            if (
                len({p.canonical_id for p in restrictive_risk.data.positions})
                != len(restrictive_risk.data.positions)
                or actual_positions != expected_positions
                or restrictive_risk.data.account != host_budget_recovery.account
                or restrictive_risk.data.portfolio_source_ref
                != "original-portfolio-truth:" + observed.digest()
                or restrictive_risk.data.portfolio_event_ms != int(observed.event_time_unix * 1000)
                or restrictive_risk.data.portfolio_known_ms != int(observed.wall_time_unix * 1000)
            ):
                raise ValueError("RISK_ORIGINAL_HOST_PORTFOLIO_BINDING_MISMATCH")
        except (ValueError, TypeError, AttributeError) as exc:
            return _deny(status=STATUS_FAIL, blocker=str(exc), replay=replay, get_count=0)

    # An outer Ops policy, not an E2E profile or a Double-Play producer input.
    try:
        from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
            BoundedSlotEntryBudgetV1,
        )

        bound_policy = (
            portfolio_budget_owner.entry_budget_policy_v1()
            if portfolio_budget_owner is not None
            else None
        )
        policy = (
            entry_budget_policy
            if entry_budget_policy is not None
            else bound_policy
            if bound_policy is not None
            else load_entry_budget_policy_v1()
        )
        if not isinstance(policy, EntryBudgetPolicyV1):
            raise EntryBudgetPolicyError("ENTRY_BUDGET_POLICY_TYPE_INVALID")
        policy.validate_v1()
        if portfolio_budget_owner is None:
            raise EntryBudgetPolicyError("ENTRY_BUDGET_REQUIRES_SHARED_RESERVATION_OWNER")
        if bound_policy is not None and bound_policy.digest_v1() != policy.digest_v1():
            raise EntryBudgetPolicyError("ENTRY_BUDGET_ORIGINAL_OWNER_POLICY_MISMATCH")
        if isinstance(policy, BoundedSlotEntryBudgetV1) and bound_policy is None:
            raise EntryBudgetPolicyError("ENTRY_BUDGET_SLOT_POLICY_REQUIRES_BOUND_OWNER")
        if isinstance(policy, BoundedSlotEntryBudgetV1) and (
            injected is None
            or host_budget_recovery is None
            or host_budget_recovery.host.owner is not portfolio_budget_owner
            or host_budget_recovery.host.closed
            or host_budget_recovery.host.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
        ):
            raise EntryBudgetPolicyError("SLOT_TEST_BUDGET_REQUIRES_ORIGINAL_SIMULATED_HOST")
    except EntryBudgetPolicyError as exc:
        return _deny(status=STATUS_FAIL, blocker=str(exc), replay=replay, get_count=0)

    get_count = 0
    payload: Mapping[str, Any] | None = None
    get_performed = False
    http_status = 0
    error_class = ""
    body_sha256 = ""
    observed_at = str(decision_epoch or "")
    age_seconds = "1"
    lab_status = LiveAccountBoundStatusV1.MISSING.value
    raw_acct_lv = ""
    expected_uid = REUSED_BINDING_ACCOUNT_SCOPE
    get_status = FreshPretradeGetStatusV1.MISSING.value
    if injected is not None:
        payload = injected.payload
        get_performed = bool(injected.get_performed)
        http_status = int(injected.http_status)
        error_class = str(injected.error_class or "")
        body_sha256 = str(injected.body_sha256 or "")
        observed_at = str(injected.observed_at or decision_epoch)
        age_seconds = str(injected.age_seconds or "1")
        lab_status = str(
            injected.live_account_bound_status or LiveAccountBoundStatusV1.MISSING.value
        )
        raw_acct_lv = str(injected.raw_acct_lv or "")
        expected_uid = str(injected.expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)
        get_status = str(
            injected.fresh_pretrade_get_status or FreshPretradeGetStatusV1.MISSING.value
        )
        if get_performed is True or payload is not None or error_class:
            get_count = 1
    if get_count == 0:
        return _deny(
            status=STATUS_MISSING,
            blocker="LIVE_29P_GET_MISSING",
            replay=replay,
            get_count=0,
            reasons=("FRESH_EVIDENCE_NOT_FETCHED",),
        )
    if injected is not None and injected.acquisition_decision_id:
        from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
            acquisition_age_seconds_v1,
            utc_now_iso_v1,
        )

        try:
            if injected.acquisition_decision_id != decision_epoch:
                raise ValueError("ACQUISITION_DECISION_MISMATCH")
            if injected.acquisition_cycle_id and (
                portfolio_slot is None or injected.acquisition_cycle_id != portfolio_slot.cycle_id
            ):
                raise ValueError("ACQUISITION_CYCLE_MISMATCH")
            if not injected.pretrade_acquired_at_utc:
                raise ValueError("PRETRADE_ACQUISITIONS_MISSING")
            now_utc = utc_now_iso_v1()
            for acquired_at in injected.pretrade_acquired_at_utc:
                acquisition_age_seconds_v1(acquired_at_utc=acquired_at, now_utc=now_utc)
            age_seconds = acquisition_age_seconds_v1(acquired_at_utc=observed_at, now_utc=now_utc)
        except ValueError as exc:
            return _deny(
                status=STATUS_FAIL,
                blocker="LIVE_29P_ACQUISITION_FAIL_CLOSED",
                replay=replay,
                get_count=get_count,
                reasons=(str(exc),),
            )
    if get_performed is not True or payload is None or http_status != 200:
        status = STATUS_UNKNOWN if error_class else STATUS_MISSING
        return _deny(
            status=status,
            blocker="LIVE_29P_GET_NOT_TRUSTED" if error_class else "LIVE_29P_GET_MISSING",
            replay=replay,
            get_count=get_count,
            reasons=(error_class or "GET_NOT_PERFORMED",),
        )

    selected_instrument = ""
    if bound_instrument is not None:
        selected_instrument = str(
            bound_instrument.instrument_id or bound_instrument.venue_native_id or ""
        ).strip()
    if not selected_instrument:
        return _deny(
            status=STATUS_FAIL,
            blocker="STEP_29P_INSTRUMENT_SCOPE_MISSING",
            replay=replay,
            get_count=get_count,
        )

    observation = None
    try:
        raw_obs = acquire_fresh_available_margin_observation_from_payload_v1(
            pretrade_decision_id=decision_epoch,
            payload=payload,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
            observed_at_utc=observed_at,
            endpoint=ENDPOINT,
            http_status=http_status,
            get_performed=True,
            rest_host=REUSED_BINDING_REST_HOST,
            auth_header_sent=True,
            historical_reuse=False,
            body_sha256=body_sha256 or _sha256_text(_canonical_json(dict(payload))),
        )
        validated = validate_fresh_available_margin_observation_v1(
            raw_obs,
            pretrade_decision_id=decision_epoch,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
            planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
        )
        digest = (
            body_sha256
            or str(raw_obs.body_sha256 or "")
            or _sha256_text(_canonical_json(dict(payload)))
        )
        observation = CurrentProductiveUsdcFreeMarginObservationV1(
            fact_id=OBSERVATION_FACT_ID,
            surface=OBSERVATION_SURFACE,
            value=str(validated.avail_eq_raw),
            settlement_currency=AVAILABLE_MARGIN_REQUIRED_CCY,
            selected_ccy=validated.selected_ccy,
            bound_account_identity=expected_uid,
            bound_venue_identity="okx",
            bound_td_mode="cross",
            decision_epoch=decision_epoch,
            observed_at_as_of=observed_at,
            age_seconds=age_seconds,
            freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
            provenance_digest=digest,
            already_net_of_in_use=TRUE_TOKEN,
            account_level_avail_eq_used=FALSE_TOKEN,
            fallback_chain_used=FALSE_TOKEN,
        )
    except (LiveCanaryAvailableMarginObservationError, TypeError, ValueError, KeyError) as exc:
        return _deny(
            status=STATUS_UNKNOWN,
            blocker=f"LIVE_29P_OBSERVATION_FAIL_CLOSED:{type(exc).__name__}",
            replay=replay,
            get_count=get_count,
            reasons=(str(exc)[:200],),
        )

    if observation is None:
        return _deny(
            status=STATUS_UNKNOWN,
            blocker="LIVE_29P_OBSERVATION_MISSING",
            replay=replay,
            get_count=get_count,
        )

    try:
        margin_host_inputs = build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv=raw_acct_lv, budget_owner=portfolio_budget_owner
        )
    except ValueError as exc:
        return _deny(status=STATUS_FAIL, blocker=str(exc), replay=replay, get_count=get_count)
    handoff = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=observation,
        instrument_id=selected_instrument,
        body_sha256=str(observation.provenance_digest),
        fresh_pretrade_get_status=get_status,
        live_account_bound_status=lab_status,
        u04_p01_host_inputs=margin_host_inputs,
        clear_treasury_idempotency=True,
    )
    output = handoff.producer_output
    produced = output.produced == TRUE_TOKEN and handoff.fail_closed is not True
    producer_reasons = tuple(str(code) for code in handoff.reason_codes)
    if handoff.fail_closed is True or produced is not True:
        fail_reasons = producer_reasons or tuple(str(code) for code in output.reason_codes)
        return _deny(
            status=_classify_fail_status(fail_reasons, error_class=""),
            blocker=fail_reasons[0]
            if fail_reasons
            else "TREASURY_SINGLE_SOURCE_HANDOFF_FAIL_CLOSED",
            replay=replay,
            get_count=get_count,
            producer_output_status="FAIL_CLOSED",
            reasons=fail_reasons,
        )

    p01_fact = handoff.p01_fact
    eligibility = handoff.eligibility_fact
    if p01_fact is None or eligibility is None:
        return _deny(
            status=STATUS_FAIL,
            blocker="P01_OR_ELIGIBILITY_MISSING_AFTER_TREASURY_HANDOFF",
            replay=replay,
            get_count=get_count,
            producer_output_status="FAIL_CLOSED",
            reasons=("P01_OR_ELIGIBILITY_MISSING_AFTER_TREASURY_HANDOFF",),
        )

    admissibility = handoff.step_29p_admissibility
    if admissibility.risk_admissible is not True:
        eval_reasons = tuple(str(code) for code in admissibility.reason_codes)
        return _deny(
            status=_classify_fail_status(eval_reasons, error_class=""),
            blocker=eval_reasons[0] if eval_reasons else "STEP_29P_RISK_ADMISSIBLE_FALSE",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=FALSE_TOKEN,
            reasons=eval_reasons,
        )

    if native_decision is None and (replay is None or replay.intermediate is None):
        return _deny(
            status=STATUS_FAIL,
            blocker="ENTER_REPLAY_MISSING_FOR_LIVE_29P_SIZING",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )

    try:
        producer_equity = Decimal(str(output.value))
    except (InvalidOperation, ValueError):
        return _deny(
            status=STATUS_FAIL,
            blocker="STEP_29P_TYPED_ACCOUNT_EQUITY_NOT_DECIMAL",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )
    if producer_equity != producer_equity or producer_equity <= 0:
        return _deny(
            status=STATUS_FAIL,
            blocker="STEP_29P_TYPED_ACCOUNT_EQUITY_NOT_POSITIVE",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )
    if producer_equity == _DEFAULT_ACCOUNT_EQUITY and str(output.value) == str(
        _DEFAULT_ACCOUNT_EQUITY
    ):
        # Distinctive producer values are required; equal-to-default is not a leak
        # by itself, but ENTER must still rebind from the producer output object.
        pass

    if native_decision is None:
        mark = replay.intermediate.market_context.mark_price
        decision_instrument_id = str(replay.evidence.instrument_id)
    else:
        mark = double_play.mark.mark_px
        decision_instrument_id = native_decision.instrument_id
    price_output = produce_current_productive_reference_price_from_mv2_mark_v1(
        mark_price=mark,
        instrument_id=decision_instrument_id,
        observed_at_as_of=observed_at,
    )
    if price_output.produced is not True or price_output.reference_price is None:
        price_blocker = (
            price_output.reason_codes[0]
            if price_output.reason_codes
            else "REFERENCE_PRICE_PRODUCER_FAIL_CLOSED"
        )
        return _deny(
            status=STATUS_FAIL,
            blocker=price_blocker,
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
            reasons=tuple(str(code) for code in price_output.reason_codes),
        )
    reference = price_output.reference_price
    if native_decision is not None:
        stop = double_play.test_stop.stop_price
    else:
        adverse_exit_distance, adverse_reasons = (
            resolve_current_productive_live_29p_adverse_exit_distance_v1(replay)
        )
        if adverse_exit_distance is None:
            return _deny(
                status=STATUS_FAIL,
                blocker="LAYER_C_ADVERSE_EXIT_DISTANCE_UNRESOLVED",
                replay=replay,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
                reasons=adverse_reasons,
            )
        protective_sizing_side = resolve_protective_stop_sizing_side_for_live_29p_join_v1(replay)
        stop = derive_protective_stop_price_from_adverse_exit_v0(
            selected_side=str(protective_sizing_side or ""),
            reference_price=reference,
            adverse_exit_distance=adverse_exit_distance,
        )
    if stop is None:
        return _deny(
            status=STATUS_FAIL,
            blocker="PROTECTIVE_STOP_DERIVATION_FAIL_CLOSED",
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )

    instruments_payload = injected.instruments_payload if injected is not None else None
    if instruments_payload is None:
        return _deny(
            status=STATUS_FAIL,
            blocker="INSTRUMENT_METADATA_OBSERVATION_MISSING",
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
            reasons=("INSTRUMENT_METADATA_OBSERVATION_MISSING",),
        )
    venue_native_id = str(
        bound_instrument.venue_native_id or bound_instrument.instrument_id or selected_instrument
    ).strip()
    metadata_output = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=venue_native_id,
        instruments_payload=instruments_payload,
        observed_at_as_of=observed_at,
        bound_instrument_id=decision_instrument_id,
    )
    if metadata_output.produced is not True or metadata_output.constraints is None:
        meta_blocker = (
            metadata_output.reason_codes[0]
            if metadata_output.reason_codes
            else "INSTRUMENT_METADATA_PRODUCER_FAIL_CLOSED"
        )
        return _deny(
            status=STATUS_FAIL,
            blocker=meta_blocker,
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
            reasons=tuple(str(code) for code in metadata_output.reason_codes),
        )

    index_tickers_payload = injected.index_tickers_payload if injected is not None else None
    conversion_pair_payload = (
        injected.conversion_pair_instruments_payload if injected is not None else None
    )
    from src.ops.governed_productive_monetary_normalization_v1.instrument_monetary_identity_v1 import (
        instrument_monetary_identity_from_okx_payload_v1,
    )
    from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
        MonetaryNormalizationError,
    )

    try:
        requires_usdt_conversion = (
            instrument_monetary_identity_from_okx_payload_v1(
                instruments_payload, venue_native_id=venue_native_id
            ).instrument_money_unit
            == "USDT"
        )
    except (ValueError, MonetaryNormalizationError):
        requires_usdt_conversion = True
    if requires_usdt_conversion and (
        index_tickers_payload is None or not isinstance(index_tickers_payload, Mapping)
    ):
        return _deny(
            status=STATUS_FAIL,
            blocker="MONETARY_NORMALIZATION_INDEX_TICKERS_MISSING",
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
            reasons=("MISSING_EDGE",),
        )
    try:
        from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
            MonetaryNormalizationError,
        )
        from src.ops.governed_productive_monetary_normalization_v1.normalize_v1 import (
            build_capital_risk_sizing_monetary_context_v1,
            crs_operands_from_monetary_context_v1,
        )

        monetary_ctx = build_capital_risk_sizing_monetary_context_v1(
            decision_epoch=str(decision_epoch or observed_at),
            observed_at=observed_at,
            fresh_pretrade_get_status=get_status,
            account_equity_amount=producer_equity,
            account_equity_currency="USDC",
            native_reference_price=reference,
            native_protective_stop_price=stop,
            instruments_payload=instruments_payload,
            venue_native_id=venue_native_id,
            index_tickers_payload=index_tickers_payload,
            conversion_pair_instruments_payload=conversion_pair_payload,
        )
        canonical_equity, canonical_reference, canonical_stop = (
            crs_operands_from_monetary_context_v1(monetary_ctx)
        )
    except MonetaryNormalizationError as exc:
        blocker = str(exc) or "MONETARY_NORMALIZATION_FAIL_CLOSED"
        return _deny(
            status=STATUS_FAIL,
            blocker=blocker,
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
            reasons=(blocker,),
        )

    try:
        live_ctx = build_current_productive_live_account_capital_context_v1(
            instrument_id=decision_instrument_id,
            typed_account_equity=canonical_equity,
            reference_price=canonical_reference,
            protective_stop_price=canonical_stop,
            instrument_constraints=metadata_output.constraints,
        )
    except CurrentProductiveMv2CapitalContextRebindError as exc:
        blocker = str(exc) or REASON_PRODUCTIVE_CAPITAL_RISK_LIMITS_UNRESOLVED
        return _deny(
            status=STATUS_FAIL,
            blocker=blocker,
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
            reasons=(blocker,),
        )

    if not isinstance(live_ctx, CanonicalCoreRuntimeCapitalContextV0):
        raise CurrentProductiveEnterLive29PJoinError("CAPITAL_CONTEXT_TYPE_DRIFT")
    if live_ctx.account_equity != producer_equity:
        raise CurrentProductiveEnterLive29PJoinError("PRODUCER_EQUITY_NOT_BOUND")
    if live_ctx.capital_risk_mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND:
        raise CurrentProductiveEnterLive29PJoinError("LIVE_ACCOUNT_BOUND_MODE_NOT_BOUND")
    if (
        live_ctx.account_equity == _DEFAULT_ACCOUNT_EQUITY
        and producer_equity != _DEFAULT_ACCOUNT_EQUITY
    ):
        raise CurrentProductiveEnterLive29PJoinError("OFFLINE_DEFAULT_EQUITY_LEAK")

    try:
        witness_b05_full_core_capital_authority_bindings_v1(
            owner_go=B05_FULL_CORE_AUTHORITY_CHAIN_OWNER_GO,
            equity_output=output,
            price_output=price_output,
            metadata_output=metadata_output,
            live_ctx=live_ctx,
            typed_account_equity=canonical_equity,
            reference_price=canonical_reference,
        )
    except B05FullCoreAuthorityChainClosureError as exc:
        blocker = str(exc) or "B05_AUTHORITY_CHAIN_WITNESS_FAIL_CLOSED"
        return _deny(
            status=STATUS_FAIL,
            blocker=blocker,
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
            reasons=(blocker,),
        )

    try:
        # Q0 equity/metadata/price witness above stays unchanged. Only the
        # downstream sizing ceilings are constrained; DP is never rerun here.
        live_ctx = policy.constrain_entry_context_v1(live_ctx)
    except EntryBudgetPolicyError as exc:
        return _deny(
            status=STATUS_FAIL,
            blocker=str(exc),
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )

    if host_budget_recovery is not None:
        try:
            host_budget_recovery.recover_v1(portfolio_budget_owner, output)
        except (ValueError, OSError) as exc:
            return _deny(
                status=STATUS_FAIL,
                blocker=str(exc),
                replay=replay,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
            )

    double_play_source = None
    if native_decision is not None:
        try:
            sizing_input = _build_double_play_sizing_input_v1(
                request=double_play,
                decision=native_decision,
                live_ctx=live_ctx,
                owner=portfolio_budget_owner,
            )
            if not double_play.reserve:
                patched = apply_capital_context_facts_v1(
                    sizing_input,
                    capital_context_facts_v1(
                        portfolio_budget_owner, slot_id=portfolio_slot.slot_id
                    ),
                )
                return _double_play_sizing_result_v1(
                    request=double_play,
                    sizing=evaluate_capital_risk_sizing_v1(patched),
                    get_count=get_count,
                    producer_output_value=str(output.value),
                    policy=policy,
                )
            double_play_source = DoublePlayReservationSourceV1(
                close=double_play.close_request, continuation=double_play.continuation
            )
        except (ValueError, OSError, ArithmeticError) as exc:
            return _deny(status=STATUS_FAIL, blocker=str(exc), replay=None, get_count=get_count)

    portfolio_reservation_id = ""
    portfolio_reservation_disposition = ""
    sizing_decision: CapitalRiskSizingDecisionV1 | None = None
    reservation_for_final_check = None
    if portfolio_budget_owner is not None and portfolio_slot is not None:
        build_errors = ()
        if double_play_source is None:
            assert replay is not None and replay.evidence is not None
            sizing_input, build_errors = build_capital_risk_sizing_input_from_decision_v0(
                decision=replay.evidence,
                capital_context=live_ctx,
            )
        if sizing_input is None:
            return _deny(
                status=STATUS_FAIL,
                blocker=build_errors[0] if build_errors else "SIZING_INPUT_BUILD_FAIL_CLOSED",
                replay=replay,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
                reasons=tuple(build_errors),
            )
        from src.ops.governed_productive_monetary_normalization_v1.sizing_source_v1 import (
            build_sizing_monetary_source_v1,
        )

        try:
            monetary_source = build_sizing_monetary_source_v1(
                canonical_instrument_id=selected_instrument,
                venue_native_id=venue_native_id,
                decision_epoch=str(decision_epoch or observed_at),
                observed_at=observed_at,
                fresh_pretrade_get_status=get_status,
                account_equity_usdc=producer_equity,
                native_reference_price=reference,
                native_protective_stop_price=stop,
                instruments_payload=instruments_payload,
                index_tickers_payload=index_tickers_payload,
                conversion_pair_instruments_payload=conversion_pair_payload,
                normalization_digest=monetary_ctx.normalization_digest,
            )
        except ValueError as exc:
            return _deny(
                status=STATUS_FAIL,
                blocker=str(exc),
                replay=replay,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
                reasons=(str(exc),),
            )
        movement_observation = injected.absolute_movement_cost_observation if injected else None
        if getattr(policy, "require_original_public_movement_facts", False):
            from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
                EntryPublicMarkSourceV1,
            )

            try:
                if (
                    injected is None
                    or type(injected.entry_public_mark_source) is not EntryPublicMarkSourceV1
                    or movement_observation is not None
                ):
                    raise ValueError("MOVEMENT_ORIGINAL_PUBLIC_SOURCE_REQUIRED")
                movement_observation = injected.entry_public_mark_source.observe_v1(
                    bound=bound_instrument,
                    opening_observation=injected.opening_cost_observation,
                )
            except (ValueError, RuntimeError, TypeError, AttributeError, KeyError, OSError) as exc:
                return _deny(
                    status=STATUS_FAIL,
                    blocker=str(exc),
                    replay=replay,
                    get_count=get_count,
                    producer_output_value=str(output.value),
                    producer_output_status="PRODUCED",
                    step_29p_risk_admissible=TRUE_TOKEN,
                )
        seam = admit_sized_slot_reservation_v1(
            portfolio_budget_owner,
            observation=observation,
            p01=p01_fact,
            eligibility=eligibility,
            slot_id=portfolio_slot.slot_id,
            decision_id=portfolio_slot.decision_id,
            cycle_id=portfolio_slot.cycle_id,
            instrument_id=selected_instrument,
            account_identity=expected_uid,
            sizing_input=sizing_input,
            fresh_pretrade_get_status=get_status,
            live_account_bound_status=lab_status,
            fresh_evidence_fetched=True,
            fresh_evidence_validated=produced,
            restrictive_risk=restrictive_risk,
            monetary_source=monetary_source,
            opening_cost_observation=injected.opening_cost_observation
            if injected is not None
            else None,
            funding_cost_observation=injected.funding_cost_observation
            if injected is not None
            else None,
            local_commitment_readback=margin_host_inputs.local_commitment_readback,
            native_initial_margin_observation=injected.native_initial_margin_observation
            if injected is not None
            else None,
            absolute_movement_cost_observation=movement_observation,
            futures_financial_custody=injected.futures_financial_custody
            if injected is not None
            else None,
            handoff_journal=handoff_journal,
            double_play_source=double_play_source,
        )
        if double_play_source is not None:
            if seam.sizing_decision is not None and (
                (seam.disposition is ReserveDispositionV1.ADMITTED and seam.reservation is not None)
                or seam.disposition is ReserveDispositionV1.DENIED
                and seam.sizing_decision.outcome is not CapitalRiskSizingOutcome.PASS
            ):
                return _double_play_sizing_result_v1(
                    request=double_play,
                    sizing=seam.sizing_decision,
                    get_count=get_count,
                    producer_output_value=str(output.value),
                    policy=policy,
                    reserve_result=seam,
                )
            return _deny(
                status=STATUS_FAIL,
                blocker=seam.reason_codes[0]
                if seam.reason_codes
                else "DOUBLE_PLAY_RESERVATION_NOT_ADMITTED",
                replay=None,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
                reasons=seam.reason_codes,
            )
        portfolio_reservation_disposition = str(seam.disposition.value)
        reservation_for_final_check = seam.reservation
        if seam.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY:
            sizing_decision = seam.sizing_decision
            if seam.reservation is not None:
                portfolio_reservation_id = str(seam.reservation.reservation_id)
        elif seam.disposition is ReserveDispositionV1.ADMITTED:
            sizing_decision = seam.sizing_decision
            if seam.reservation is not None:
                portfolio_reservation_id = str(seam.reservation.reservation_id)
        else:
            blocker = (
                seam.reason_codes[0] if seam.reason_codes else "PORTFOLIO_RESERVATION_FAIL_CLOSED"
            )
            return _deny(
                status=STATUS_FAIL,
                blocker=blocker,
                replay=replay,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
                reasons=seam.reason_codes,
            )
        if sizing_decision is None:
            return _deny(
                status=STATUS_FAIL,
                blocker="PORTFOLIO_SIZING_DECISION_MISSING",
                replay=replay,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
            )
        rebound = _rebound_replay_with_sizing_decision_v1(
            replay,
            sizing_decision=sizing_decision,
            live_ctx=live_ctx,
        )
    else:
        sizing_binding = bind_capital_risk_sizing_offline_replay_evidence_v0(
            replay.evidence,
            capital_context=live_ctx,
        )
        sizing_decision = sizing_binding.sizing_decision
        if sizing_decision is None:
            blocker = (
                sizing_binding.evidence.reason_codes[0]
                if sizing_binding.evidence.reason_codes
                else REASON_PRODUCTIVE_CAPITAL_RISK_LIMITS_UNRESOLVED
            )
            return _deny(
                status=STATUS_FAIL,
                blocker=blocker,
                replay=replay,
                get_count=get_count,
                producer_output_value=str(output.value),
                producer_output_status="PRODUCED",
                step_29p_risk_admissible=TRUE_TOKEN,
                reasons=tuple(sizing_binding.evidence.reason_codes),
            )
        rebound = _rebound_replay_with_sizing_decision_v1(
            replay,
            sizing_decision=sizing_decision,
            live_ctx=live_ctx,
        )
    sizing_outcome = ""
    if sizing_decision is not None:
        sizing_outcome = str(
            getattr(
                sizing_decision.outcome,
                "value",
                sizing_decision.outcome,
            )
        )
    if sizing_decision is not None and metadata_output.constraints is not None:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_forensic_executable_quantity_override_v1 import (
            maybe_apply_forensic_executable_quantity_override_after_live_29p_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
            active_ghv_pre_external_runtime_flight_recorder_session_v1,
        )

        override_result = maybe_apply_forensic_executable_quantity_override_after_live_29p_v1(
            rebound_replay=rebound,
            sizing_decision=sizing_decision,
            constraints=metadata_output.constraints,
            live_ctx=live_ctx,
            cycle_index=int(cycle_index or 0),
            ghv_pre_external_runtime_flight_recorder_enabled=(
                active_ghv_pre_external_runtime_flight_recorder_session_v1() is not None
            ),
        )
        rebound = override_result.replay
        sizing_decision = override_result.sizing_decision
        sizing_outcome = override_result.sizing_outcome
    final_sizing = (
        sizing_decision.canonical_position_sizing if sizing_decision is not None else None
    )
    if (
        final_sizing is None
        or final_sizing.resulting_notional > policy.per_entry_notional_limit
        or reservation_for_final_check is None
        or final_sizing.resulting_notional != reservation_for_final_check.amount
    ):
        return _deny(
            status=STATUS_FAIL,
            blocker="ENTRY_BUDGET_FINAL_SIZING_RESERVATION_MISMATCH",
            replay=replay,
            get_count=get_count,
            producer_output_value=str(output.value),
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )
    return CurrentProductiveEnterLive29PJoinResultV1(
        decision_class=DECISION_ENTER,
        called=True,
        get_count=get_count,
        status=STATUS_PASS,
        venue_plan_authorized=True,
        first_blocker="",
        producer_output_value=str(output.value),
        producer_output_status="PRODUCED",
        step_29p_risk_admissible=TRUE_TOKEN,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        used_offline_default_equity=FALSE_TOKEN,
        sizing_outcome=sizing_outcome,
        replay=rebound,
        portfolio_reservation_id=portfolio_reservation_id,
        portfolio_reservation_disposition=portfolio_reservation_disposition,
        reason_codes=(JOIN_SEAM_ID, STATUS_PASS, PRODUCER_IDENTITY),
        entry_budget_policy_id=policy.policy_id,
        entry_budget_policy_digest=policy.digest_v1(),
    )
