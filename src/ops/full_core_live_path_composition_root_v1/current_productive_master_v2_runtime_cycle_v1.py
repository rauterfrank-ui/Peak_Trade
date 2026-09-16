"""One-shot CURRENT_PRODUCTIVE Master-V2 cycle from observed venue inputs.

Reuses the canonical decision owner
``run_integrated_offline_trading_logic_replay_v1``. Does not fabricate
ENTER, direction, quantity, or CMC fields. Missing observed inputs deny.
Does not POST. Does not consume a permit. Does not apply simulated fills.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_CONFIRMATION_EPOCHS,
    CANONICAL_DECISION_CONFIG_DIGEST,
    CANONICAL_REVERSAL_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.exit_policy_producer_binding_v1.host_binding_v1 import (
    HostExitPolicyBindingV1,
    evaluate_host_exit_policy_producers_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_LINEAGE_ID,
    CurrentProductiveCursorError,
    CurrentProductiveSideStateConfirmationCursorV1,
    build_current_productive_sidestate_confirmation_cursor_v1,
    restore_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    DEFAULT_VENUE,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    HostConfirmationBindingV1,
    commit_host_confirmation_after_replay_v1,
    ensure_host_confirmation_binding_v1,
    evaluate_host_observation_acceptance_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.persistence_v1 import (
    ConfirmationPersistenceError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    FEATURE_WINDOW_MIN,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    _component_versions,
    _default_policies,
    _policy_versions,
    _strategy_registry,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.feature_regime_pipeline_v1 import (
    compute_feature_regime_from_mid_prices_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.sidestate_restore_v1 import (
    SideStateRestoreError,
    parse_persisted_side_state_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    FEATURE_CONTRACT_VERSION,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
)
from trading.master_v2.directional_assessment_v1 import DirectionalConfirmationStateV1
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionDirectionState,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    EntryExitDirectionState,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
    _side_state_to_entry_exit_direction,
    build_integrated_offline_replay_input_v1,
    run_integrated_offline_trading_logic_replay_v1,
    scope_direction_from_side_state_v1,
)
from trading.master_v2.suitability_binding_v1 import SuitabilityRegimeStatus

CYCLE_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
IMPL_DIGEST = hashlib.sha256(b"full-core-current-productive-master-v2-runtime-cycle-v1").hexdigest()
ENDPOINT_MARKET_TICKER = "/api/v5/market/ticker"
ENDPOINT_MARKET_CANDLES = "/api/v5/market/candles"
ENDPOINT_PUBLIC_OPEN_INTEREST = "/api/v5/public/open-interest"
ENDPOINT_PUBLIC_FUNDING_RATE = "/api/v5/public/funding-rate"


class CurrentProductiveMasterV2RuntimeCycleError(ValueError):
    """Fail-closed current Master-V2 cycle input violation."""


@dataclass(frozen=True)
class CurrentProductiveMasterV2CycleResultV1:
    replay: Optional[IntegratedOfflineReplayResultV1]
    cycle_id: str
    replay_id: str
    decision_outcome: str
    replay_pass: str
    fail_reasons: tuple[str, ...]
    provenance: str
    input_digest: str
    input_blocker: str
    cursor_restore_status: str = "missing"
    outgoing_cursor: Optional[CurrentProductiveSideStateConfirmationCursorV1] = None


def _finite_positive(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")) or number <= 0:
        return None
    return number


def _finite_number(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _iso_utc(ts_unix: float) -> str:
    return datetime.fromtimestamp(float(ts_unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _okx_data_rows(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, Mapping)]


def extract_mark_and_index_from_payload_v1(
    payload: Mapping[str, Any] | None, *, native_id: str
) -> tuple[float | None, float | None]:
    if payload is None:
        return None, None
    wanted = str(native_id or "").strip()
    mark = None
    index = None
    for row in _okx_data_rows(payload):
        if str(row.get("instId") or "").strip() != wanted:
            continue
        mark = _finite_positive(row.get("markPx"))
        index = _finite_positive(row.get("idxPx"))
        break
    return mark, index


def extract_ticker_fields_v1(
    payload: Any, *, native_id: str
) -> tuple[float | None, float | None, float | None, float | None]:
    wanted = str(native_id or "").strip()
    for row in _okx_data_rows(payload):
        if str(row.get("instId") or "").strip() != wanted:
            continue
        bid = _finite_positive(row.get("bidPx"))
        ask = _finite_positive(row.get("askPx"))
        volume = _finite_positive(row.get("vol24h"))
        index = _finite_positive(row.get("idxPx"))
        return bid, ask, volume, index
    return None, None, None, None


def extract_open_interest_v1(payload: Any, *, native_id: str) -> float | None:
    wanted = str(native_id or "").strip()
    for row in _okx_data_rows(payload):
        if str(row.get("instId") or "").strip() not in {"", wanted}:
            continue
        return _finite_positive(row.get("oi"))
    return None


def extract_funding_rate_v1(payload: Any, *, native_id: str) -> float | None:
    wanted = str(native_id or "").strip()
    for row in _okx_data_rows(payload):
        if str(row.get("instId") or "").strip() not in {"", wanted}:
            continue
        return _finite_number(row.get("fundingRate"))
    return None


def extract_finalized_candle_closes_v1(
    payload: Any,
) -> tuple[tuple[float, ...], float | None]:
    if not isinstance(payload, Mapping):
        return (), None
    data = payload.get("data")
    if not isinstance(data, list):
        return (), None
    finalized: list[tuple[float, float]] = []
    for row in data:
        if not isinstance(row, Sequence) or len(row) < 9:
            continue
        confirm = str(row[8] or "").strip()
        if confirm != "1":
            continue
        ts_ms = _finite_positive(row[0])
        close = _finite_positive(row[4])
        if ts_ms is None or close is None:
            continue
        finalized.append((ts_ms / 1000.0, close))
    if not finalized:
        return (), None
    finalized.sort(key=lambda item: item[0])
    closes = tuple(item[1] for item in finalized)
    return closes, float(finalized[-1][0])


def extract_position_truth_v1(
    payload: Any, *, native_id: str
) -> tuple[str, bool, ExistingPositionSide]:
    wanted = str(native_id or "").strip()
    rows = _okx_data_rows(payload)
    other_open = False
    matched_side = ExistingPositionSide.NONE
    matched_open = False
    for row in rows:
        inst = str(row.get("instId") or "").strip()
        pos = _finite_number(row.get("pos"))
        if pos is None or pos == 0.0:
            continue
        if inst != wanted:
            other_open = True
            continue
        matched_open = True
        pos_side = str(row.get("posSide") or "").strip().lower()
        if pos > 0:
            matched_side = ExistingPositionSide.LONG
        elif pos < 0:
            matched_side = ExistingPositionSide.SHORT
        if pos_side == "short":
            matched_side = ExistingPositionSide.SHORT
        elif pos_side == "long":
            matched_side = ExistingPositionSide.LONG
    if other_open:
        return "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1", False, ExistingPositionSide.NONE
    if matched_open:
        return "BOUND_INSTRUMENT_OPEN", False, matched_side
    return "FLAT", True, ExistingPositionSide.NONE


def _blocked_cycle_result(
    *,
    cycle_id: str,
    fail_reason: str,
    provenance: str,
    cursor_restore_status: str = "missing",
) -> CurrentProductiveMasterV2CycleResultV1:
    return CurrentProductiveMasterV2CycleResultV1(
        replay=None,
        cycle_id=cycle_id,
        replay_id="",
        decision_outcome="",
        replay_pass="false",
        fail_reasons=(fail_reason,),
        provenance=provenance,
        input_digest="",
        input_blocker=fail_reason,
        cursor_restore_status=cursor_restore_status,
        outgoing_cursor=None,
    )


def _bind_cap61_confirmation_v1(
    *,
    instrument_id: str,
    restored: CurrentProductiveSideStateConfirmationCursorV1 | None,
) -> HostConfirmationBindingV1:
    binding = HostConfirmationBindingV1()
    if restored is not None and restored.cap61_confirmation_state is not None:
        state = restored.cap61_confirmation_state
        binding.confirmation_session_id = state.confirmation_session_id
        binding.observation_acceptance_state = state.observation_acceptance_state
        binding.confirmation_side_carrier = state.confirmation_side_carrier
        binding.commit_sequence = int(state.commit_sequence)
        binding.prior_commit_seen = True
        binding.enabled = True
        binding.venue = state.venue
        binding.instrument_id = state.instrument_id
        binding.venue_instrument_id = instrument_id
        binding.repository_sha = state.repository_sha
        binding.config_digest = state.config_digest
        binding.initialized = True
        return binding
    return ensure_host_confirmation_binding_v1(
        binding,
        instrument_id=instrument_id,
        venue=DEFAULT_VENUE,
        venue_instrument_id=instrument_id,
        repository_sha=CURSOR_LINEAGE_ID,
        state_root=None,
        require_load_if_prior_commit=False,
    )


def _outgoing_cursor_from_replay_v1(
    *,
    bound_instrument: BoundInstrumentV1,
    trading_epoch: int,
    now_tick: int,
    replay: IntegratedOfflineReplayResultV1,
    cap61_binding: HostConfirmationBindingV1 | None,
) -> Optional[CurrentProductiveSideStateConfirmationCursorV1]:
    if replay.intermediate is None:
        return None
    try:
        next_side = parse_persisted_side_state_v1(replay.intermediate.state_switch.next_side_state)
    except SideStateRestoreError:
        return None
    confirmation = replay.intermediate.scope_event.next_confirmation_state
    cap61_state = None
    if cap61_binding is not None and cap61_binding.initialized:
        try:
            cap61_state = cap61_binding.to_canonical_state()
        except RuntimeError:
            cap61_state = None
    try:
        return build_current_productive_sidestate_confirmation_cursor_v1(
            instrument_id=str(bound_instrument.instrument_id or "").strip(),
            venue_native_id=str(bound_instrument.venue_native_id or "").strip(),
            trading_epoch=int(trading_epoch) + 1,
            last_evaluated_trading_epoch=int(trading_epoch),
            now_tick=int(now_tick),
            side_state=next_side,
            scope_confirmation=confirmation,
            existing_scope=replay.intermediate.current_scope,
            runtime_scope_state=replay.intermediate.runtime_scope_state_after,
            confirmation_epochs=int(CANONICAL_CONFIRMATION_EPOCHS),
            cap61_confirmation_state=cap61_state,
        )
    except CurrentProductiveCursorError:
        return None


def run_current_productive_master_v2_runtime_cycle_v1(
    *,
    bound_instrument: BoundInstrumentV1,
    cycle_id: str,
    observed_unix: float,
    mark_px: float,
    index_px: float,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    finalized_closes: Sequence[float],
    last_finalized_event_ts_unix: float,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    incoming_cursor: object | None = None,
) -> CurrentProductiveMasterV2CycleResultV1:
    instrument_id = str(bound_instrument.instrument_id or "").strip()
    venue_native_id = str(bound_instrument.venue_native_id or "").strip()
    if not instrument_id:
        return _blocked_cycle_result(
            cycle_id=cycle_id,
            fail_reason="BINDING_MISSING",
            provenance=CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,
        )
    restore = restore_current_productive_sidestate_confirmation_cursor_v1(
        incoming_cursor,
        expected_instrument_id=instrument_id,
        expected_venue_native_id=venue_native_id or instrument_id,
        venue_flat=bool(venue_flat),
    )
    if restore.fail_closed is True:
        return _blocked_cycle_result(
            cycle_id=cycle_id,
            fail_reason=restore.reason_code,
            provenance=restore.reason_code,
            cursor_restore_status=restore.disposition.value,
        )
    closes = tuple(float(x) for x in finalized_closes)
    if len(closes) < FEATURE_WINDOW_MIN:
        return _blocked_cycle_result(
            cycle_id=cycle_id,
            fail_reason="MASTER_V2_PRICE_PATH_INSUFFICIENT",
            provenance="MASTER_V2_PRICE_PATH_INSUFFICIENT",
            cursor_restore_status=restore.disposition.value,
        )
    features = compute_feature_regime_from_mid_prices_v1(closes)
    warmup_status = (
        WarmupStatus.WARMUP_COMPLETE if features.warmup_complete else WarmupStatus.WARMUP_REQUIRED
    )
    spread = float(ask_px) - float(bid_px)
    if spread <= 0:
        return _blocked_cycle_result(
            cycle_id=cycle_id,
            fail_reason="SPREAD_INVALID",
            provenance="MASTER_V2_TICKER_SPREAD_INVALID",
            cursor_restore_status=restore.disposition.value,
        )
    market_event_time = _iso_utc(last_finalized_event_ts_unix)
    decision_time = _iso_utc(max(float(observed_unix), last_finalized_event_ts_unix + 0.001))
    restored = restore.cursor if restore.disposition.value == "restored" else None
    trading_epoch = 1 if restored is None else int(restored.trading_epoch)
    last_evaluated = 0 if restored is None else int(restored.last_evaluated_trading_epoch)
    now_tick = 1 if restored is None else int(restored.now_tick) + 1
    existing_scope = None if restored is None else restored.existing_scope
    runtime_scope_state = None if restored is None else restored.runtime_scope_state
    try:
        cap61_binding = _bind_cap61_confirmation_v1(instrument_id=instrument_id, restored=restored)
        observation_acceptance_result = evaluate_host_observation_acceptance_v1(
            cap61_binding,
            mid_price=float(mark_px),
            event_ts_unix=float(last_finalized_event_ts_unix),
            cycle_index=int(now_tick),
        )
    except (ConfirmationPersistenceError, RuntimeError, ValueError) as exc:
        return _blocked_cycle_result(
            cycle_id=cycle_id,
            fail_reason=f"CURSOR_CAP61_RESTORE_FAIL_CLOSED:{type(exc).__name__}",
            provenance="CURSOR_CAP61_RESTORE_FAIL_CLOSED",
            cursor_restore_status=restore.disposition.value,
        )
    market_context = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-{instrument_id}-epoch{trading_epoch}-full-core-current-v1",
            instrument_id=instrument_id,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=trading_epoch,
            market_event_time=market_event_time,
            decision_time=decision_time,
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=float(mark_px),
            index_price=float(index_px),
            best_bid=float(bid_px),
            best_ask=float(ask_px),
            spread=spread,
            volume=float(volume),
            open_interest=float(open_interest),
            funding_rate=float(funding_rate),
            volatility_estimate=float(features.volatility_estimate),
            trend_feature_set=dict(features.trend_features),
            momentum_feature_set=dict(features.momentum_features),
            liquidity_feature_set=dict(features.liquidity_features),
            market_structure_feature_set=dict(features.market_structure_features),
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=warmup_status,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )
    side_state = SideState.NEUTRAL_OBSERVE
    direction_state = EntryExitDirectionState.NEUTRAL
    position_mgmt = PositionManagementContext.FLAT
    if existing_position_side is ExistingPositionSide.LONG:
        side_state = SideState.LONG_ACTIVE
        direction_state = EntryExitDirectionState.LONG_ACTIVE
        position_mgmt = PositionManagementContext.LONG_POSITION
    elif existing_position_side is ExistingPositionSide.SHORT:
        side_state = SideState.SHORT_ACTIVE
        direction_state = EntryExitDirectionState.SHORT_ACTIVE
        position_mgmt = PositionManagementContext.SHORT_POSITION
    elif restored is not None:
        side_state = restored.side_state
        direction_state = _side_state_to_entry_exit_direction(side_state)
    if restored is None:
        confirmation_state = ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1 if features.warmup_complete else 0,
            last_evaluated_trading_epoch=last_evaluated,
        )
        directional_last_evaluated = last_evaluated
        directional_count = 1 if features.warmup_complete else 0
    else:
        confirmation_state = restored.scope_confirmation
        directional_last_evaluated = int(confirmation_state.last_evaluated_trading_epoch)
        directional_count = int(confirmation_state.candidate_count)
    position_state = (
        PositionState.FLAT_RECONCILED if venue_flat is True else PositionState.OPEN_FULL
    )
    exit_binding = HostExitPolicyBindingV1(instrument_id=instrument_id)
    _bundle, exit_signals, exit_safety_mode, exit_trading_gate = (
        evaluate_host_exit_policy_producers_v1(
            exit_binding,
            mark_price=float(mark_px),
            event_ts_unix=float(last_finalized_event_ts_unix),
            observation_digest=str(market_context.input_digest or ""),
            has_open_position=venue_flat is not True,
            existing_position_side=str(existing_position_side.value),
            entry_price=None,
            entry_event_time=None,
            entry_trading_epoch=None,
            warmup_complete=bool(features.warmup_complete),
            regime_ok=bool(features.ok),
            price_basis_ok=bool(mark_px > 0),
        )
    )
    replay_id = f"{cycle_id}-master-v2"
    input_material = {
        "cycle_id": cycle_id,
        "instrument_id": instrument_id,
        "mark_px": float(mark_px),
        "index_px": float(index_px),
        "closes": len(closes),
        "config_digest": CANONICAL_DECISION_CONFIG_DIGEST,
        "trading_epoch": int(trading_epoch),
        "cursor_restore_status": restore.disposition.value,
    }
    input_digest = hashlib.sha256(str(sorted(input_material.items())).encode("utf-8")).hexdigest()
    replay_input = build_integrated_offline_replay_input_v1(
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        canonical_market_context=market_context,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=features.warmup_complete,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        scope_reinitialization_guard=ScopeReinitializationGuardV1(),
        existing_scope=existing_scope,
        scope_direction_state=scope_direction_from_side_state_v1(side_state),
        scope_confirmation_state=confirmation_state,
        scope_cooldown_state=ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        up_distance=float(CANONICAL_UP_DISTANCE),
        adverse_exit_distance=float(CANONICAL_ADVERSE_EXIT_DISTANCE),
        reversal_distance=float(CANONICAL_REVERSAL_DISTANCE),
        confirmation_epochs=int(CANONICAL_CONFIRMATION_EPOCHS),
        current_price=float(mark_px),
        price_path=closes,
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=directional_count,
            last_evaluated_trading_epoch=directional_last_evaluated,
            last_signal_strength=float(features.momentum_features.get("roc", 0.0)),
        ),
        strategy_registry=_strategy_registry(),
        regime_id=features.regime_id if features.ok else "unclassified",
        regime_status=(
            SuitabilityRegimeStatus.KNOWN if features.ok else SuitabilityRegimeStatus.UNKNOWN
        ),
        previous_composition_direction_state=CompositionDirectionState.NEUTRAL,
        position_management_context=position_mgmt,
        last_evaluated_trading_epoch=last_evaluated,
        side_state=side_state,
        direction_state=direction_state,
        position_state=position_state,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=exit_trading_gate,
        safety_mode=exit_safety_mode,
        existing_position_side=existing_position_side,
        venue_flat=bool(venue_flat),
        cooldown_pass=True,
        scope_adverse_exit_signal=exit_signals["scope_adverse_exit_signal"],
        profit_protection_signal=exit_signals["profit_protection_signal"],
        time_exit_signal=exit_signals["time_exit_signal"],
        strategy_invalidation_signal=exit_signals["strategy_invalidation_signal"],
        hard_risk_reduction_signal=exit_signals["hard_risk_reduction_signal"],
        safety_exit_signal=exit_signals["safety_exit_signal"],
        policies=_default_policies(),
        component_versions=_component_versions(),
        policy_versions=_policy_versions(),
        config_digest=str(CANONICAL_DECISION_CONFIG_DIGEST),
        implementation_digest=IMPL_DIGEST,
        input_digest=input_digest,
        expected_component_contracts=_component_versions(),
        context_reference=f"full-core-current-productive-cycle-{cycle_id}",
        now_tick=now_tick,
        runtime_scope_state=runtime_scope_state,
        runtime_scope_bound_instrument_id=instrument_id
        if runtime_scope_state is not None
        else None,
        directional_confirmation_progress=cap61_binding.confirmation_side_carrier,
        observation_acceptance_result=observation_acceptance_result,
        confirmation_progress_session_id=cap61_binding.confirmation_session_id,
        confirmation_progress_venue=cap61_binding.venue,
        confirmation_progress_instrument=cap61_binding.instrument_key(),
        explicit_runtime_scope_reset=False,
    )
    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    if replay.intermediate is not None:
        commit_host_confirmation_after_replay_v1(
            cap61_binding,
            observation_acceptance_result=observation_acceptance_result,
            confirmation_side_carrier_after=(
                replay.intermediate.directional_confirmation_progress_after
            ),
            persist=False,
        )
    outcome = str(replay.evidence.decision_outcome or "")
    reasons = tuple(str(x) for x in (replay.fail_reasons or ()))
    return CurrentProductiveMasterV2CycleResultV1(
        replay=replay,
        cycle_id=cycle_id,
        replay_id=replay_id,
        decision_outcome=outcome,
        replay_pass="true" if replay.replay_pass is True else "false",
        fail_reasons=reasons,
        provenance=CYCLE_OWNER,
        input_digest=input_digest,
        input_blocker="",
        cursor_restore_status=restore.disposition.value,
        outgoing_cursor=_outgoing_cursor_from_replay_v1(
            bound_instrument=bound_instrument,
            trading_epoch=trading_epoch,
            now_tick=now_tick,
            replay=replay,
            cap61_binding=cap61_binding,
        ),
    )
