"""Occupied-lane governed-cycle N=1 consumer: S8 roots → invoke, NON-V5 EG, S7 T2.

Harness join only. Does not flip MF_PRODUCTIVE_JOIN or 1_UNJOINED.
Does not bind Cap61, join a host, call V5, or POST.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, NoReturn, Sequence

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    CURSOR_FILENAME,
    CURSOR_OWNER_CHANGE_REQUIRED,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EG_V5_USED,
    FAILURE_AUTHORITY,
    FAILURE_IDENTITY_MISMATCH,
    FAILURE_INJECTED_C1_REQUIRED,
    FAILURE_NATIVE_ID_MISSING,
    FAILURE_OCCUPANCY,
    FAILURE_ORIGIN_MAIN_SHA,
    FAILURE_PAIR_TYPE,
    FAILURE_S8_ROOTS_MISSING,
    FAILURE_UNKNOWN_LANE_ID,
    FAILURE_V5_DISPATCH,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    GLOBAL_N1_CURSOR_REJECTED,
    GOVERNED_CYCLE_INVOKED,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_IMPLEMENTED,
    JOIN_MAPPING_AUTHORITY,
    JOIN_MEMBERSHIP_AUTHORITY,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MAY_BIND_CAP61_STATE_ROOT,
    MAY_INVOKE_GOVERNED_CYCLE,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    OCCUPIED_LANES_ONLY,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    S8_CONSUMED,
    T2_S7_USED,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    UNIQUE_MUTABLE_ROOTS_ENFORCED,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    OccupiedLaneMv2DpDecisionStateConsumerInvocationV1,
    bind_occupied_lane_governed_cycle_store_roots_v1,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
    CurrentProductiveEnterLive29PPortfolioSlotContextV1,
    DECISION_ENTER,
    STATUS_PASS,
    current_productive_decision_class_v1,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    EG_OWNER_GO,
    GET_OWNER_GO,
    RUNTIME_OWNER_GO,
    T2_RUNTIME_OWNER_GO,
    CurrentProductiveGovernedCycleAuthorizationV1,
    CurrentProductiveGovernedCycleResultV1,
    run_current_productive_governed_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    OCCUPANCY_OWNER_GO,
    CurrentProductiveGovernedNextC1OrchestrationError,
    cursor_last_accepted_c1_venue_event_time_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

_FALSE = "false"
_TRUE = "true"


class FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class OccupiedLaneGovernedCycleN1ConsumerResultV1:
    lane_id: str
    bound_instrument: BoundInstrumentV1
    native_id: str
    cursor_store_root: str
    lock_root: str
    evidence_root: str
    bootstrap_used: bool
    s7_invocation: OccupiedLaneMv2DpDecisionStateConsumerInvocationV1 | None
    governed_cycle_result: CurrentProductiveGovernedCycleResultV1
    eg_v5_used: bool
    t2_s7_used: bool
    cap61_state_root_bound: bool


def _fail(code: str, detail: str = "") -> NoReturn:
    raise FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        not JOIN_IMPLEMENTED
        or not S8_CONSUMED
        or not GOVERNED_CYCLE_INVOKED
        or not MAY_INVOKE_GOVERNED_CYCLE
        or not T2_S7_USED
        or EG_V5_USED
        or not OCCUPIED_LANES_ONLY
        or not UNIQUE_MUTABLE_ROOTS_ENFORCED
        or not GLOBAL_N1_CURSOR_REJECTED
        or JOIN_SELECTION_AUTHORITY
        or JOIN_CAP23_SELECTION_AUTHORITY
        or JOIN_CAP24_BINDING_AUTHORITY
        or JOIN_TRADING_AUTHORITY
        or JOIN_RUNTIME_ACTIVATION_AUTHORITY
        or JOIN_EXECUTION_AUTHORITY
        or JOIN_RANKING_AUTHORITY
        or JOIN_MEMBERSHIP_AUTHORITY
        or JOIN_MAPPING_AUTHORITY
        or JOIN_PERSISTENCE_AUTHORITY
        or JOIN_FULL_AUTONOMY_HOST_AUTHORITY
        or HOST_JOIN
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or FULL_AUTONOMY_HOST_CHANGE_REQUIRED
        or CURSOR_OWNER_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
        or THIS_SLICE_MAY_REINVOKE_CAP23
        or THIS_SLICE_MAY_REINVOKE_CAP24
        or MAY_BIND_CAP61_STATE_ROOT
        or not UNIVERSE_ISOLATION_ENFORCED
    ):
        _fail(FAILURE_AUTHORITY, OWNER)
    if (
        CROSS_UNIVERSE_SELECTION
        or CROSS_UNIVERSE_PIN
        or CROSS_UNIVERSE_REPLACEMENT
        or CROSS_UNIVERSE_FALLBACK
        or CROSS_UNIVERSE_CANDIDATE_BORROWING
        or CROSS_UNIVERSE_RERANKING
        or MULTI_UNIVERSE_MERGE
        or INSTRUMENT_ID_ALONE_SUFFICIENT
    ):
        _fail(FAILURE_AUTHORITY, "constant_violation")


def _iso_utc(unix: float) -> str:
    return datetime.fromtimestamp(float(unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def non_v5_eg_dispatch_v1(**kwargs: Any) -> SimpleNamespace:
    """EG dispatch that must never call V5 or Cap21-24."""
    if EG_V5_USED:
        _fail(FAILURE_V5_DISPATCH, OWNER)
    forbidden = (
        "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1",
        "_run_cap21_to_cap24_v1",
    )
    for name in forbidden:
        if name in kwargs:
            _fail(FAILURE_V5_DISPATCH, name)
    return SimpleNamespace(permit_created=_FALSE, post_count="0")


def _occupancy_absent() -> dict[str, object]:
    return {
        "POSITIONS": {"code": "0", "data": []},
        "PENDING": {"code": "0", "data": []},
        "CONFIG": {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
    }


def _cursor_floor_or_zero(cursor_store_root: Path) -> float:
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(cursor_store_root)
    if not isinstance(loaded, Mapping):
        return 0.0
    try:
        return float(cursor_last_accepted_c1_venue_event_time_v1(loaded))
    except CurrentProductiveGovernedNextC1OrchestrationError:
        return 0.0


def _s7_kwargs(
    *,
    cycle_id_prefix: str,
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
    g17_typed_vol_producers: Mapping[str, object] | None,
) -> dict[str, Any]:
    return {
        "cycle_id_prefix": cycle_id_prefix,
        "observed_unix": observed_unix,
        "mark_px": mark_px,
        "index_px": index_px,
        "bid_px": bid_px,
        "ask_px": ask_px,
        "volume": volume,
        "open_interest": open_interest,
        "funding_rate": funding_rate,
        "finalized_closes": finalized_closes,
        "last_finalized_event_ts_unix": last_finalized_event_ts_unix,
        "venue_flat": venue_flat,
        "existing_position_side": existing_position_side,
        "g17_typed_vol_producers": g17_typed_vol_producers,
    }


def _finalize_portfolio_reservation_after_enter_join_v1(
    owner: PortfolioCapitalReservationBudgetOwnerV1 | None,
    *,
    reservation_id: str,
    enter_status: str,
    venue_plan_pass: bool,
) -> None:
    if owner is None or not str(reservation_id or "").strip():
        return
    if enter_status == STATUS_PASS and venue_plan_pass:
        owner.commit_internal_pre_external_effect_v1(str(reservation_id))
        return
    owner.release_plan_failure_v1(str(reservation_id))


def _t2_from_s7(
    *,
    lane_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    native_id: str,
    lane_id: str,
    s7_base: Mapping[str, Any],
    live_29p_injected: CurrentProductiveEnterLive29PInjectedGetV1 | None,
    candles_payload: Mapping[str, Any],
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
) -> Any:
    def _dispatch(**kwargs: Any) -> SimpleNamespace:
        observation = kwargs.get("observation")
        event_ts = float(s7_base["last_finalized_event_ts_unix"])
        closes = tuple(s7_base["finalized_closes"])
        if observation is not None:
            event_ts = float(getattr(observation, "venue_event_time", event_ts) or event_ts)
            payload = getattr(observation, "payload", None)
            extracted, last_ts = extract_finalized_candle_closes_v1(
                payload if payload is not None else candles_payload
            )
            if extracted:
                closes = extracted
            if last_ts is not None:
                event_ts = float(last_ts)
        composed = compose_occupied_lane_mv2_dp_durable_cycle_v1(
            lane_pairs,
            **{
                **s7_base,
                "finalized_closes": closes,
                "last_finalized_event_ts_unix": event_ts,
            },
        )
        if len(composed) != 1:
            _fail(FAILURE_OCCUPANCY, ",".join(sorted(composed)))
        invocation = next(iter(composed.values()))
        bound = invocation.bound_instrument
        if str(bound.venue_native_id or "").strip() != native_id:
            _fail(FAILURE_IDENTITY_MISMATCH, native_id)
        replay = invocation.cycle_result.replay
        epoch = _iso_utc(float(s7_base["observed_unix"]))
        portfolio_slot = None
        if portfolio_budget_owner is not None:
            evidence = getattr(replay, "evidence", None)
            decision_id = str(getattr(evidence, "decision_id", "") or "").strip()
            if not decision_id:
                _fail(FAILURE_AUTHORITY, "portfolio_decision_id")
            portfolio_slot = CurrentProductiveEnterLive29PPortfolioSlotContextV1(
                slot_id=lane_id,
                decision_id=decision_id,
                cycle_id=str(s7_base["cycle_id_prefix"]),
            )
        live_29p = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=replay,
            bound_instrument=bound,
            injected=live_29p_injected,
            decision_epoch=epoch,
            portfolio_budget_owner=portfolio_budget_owner,
            portfolio_slot=portfolio_slot,
        )
        decision_class = current_productive_decision_class_v1(live_29p.replay)
        master_decision = str(
            getattr(getattr(replay, "evidence", None), "decision_outcome", "") or ""
        )
        if decision_class == DECISION_ENTER:
            status, _reasons, plan = try_bind_current_productive_venue_plan_v1(
                replay=live_29p.replay,
                bound_instrument=bound,
                session_id=str(s7_base["cycle_id_prefix"]),
                run_id=f"{s7_base['cycle_id_prefix']}:{next(iter(composed))}",
                composed_epoch=epoch,
            )
            venue_plan_pass = status is CompositionStatusV1.PASS and plan is not None
            _finalize_portfolio_reservation_after_enter_join_v1(
                portfolio_budget_owner,
                reservation_id=live_29p.portfolio_reservation_id,
                enter_status=live_29p.status,
                venue_plan_pass=venue_plan_pass,
            )
            if venue_plan_pass:
                envelope = bind_final_order_envelope_from_venue_plan_v1(
                    plan,
                    admission_ref=f"{s7_base['cycle_id_prefix']}:admission",
                    provenance_ref=f"{s7_base['cycle_id_prefix']}:provenance",
                    creation_epoch=epoch,
                )
                result = SimpleNamespace(
                    runtime_cycle_count="1",
                    decision_result="EXECUTABLE_VENUE_PLAN_BOUND",
                    decision_execution_eligible=_TRUE,
                    master_v2_decision=master_decision or "enter",
                    venue_plan_status="BOUND",
                    final_envelope_id=str(envelope.envelope_id),
                    final_envelope_digest=str(envelope.envelope_digest),
                    permit_created=_FALSE,
                    post_count="0",
                    first_real_blocker="",
                    s7_invocation=invocation,
                )
                _dispatch.last_invocation = invocation  # type: ignore[attr-defined]
                return result
        result = SimpleNamespace(
            runtime_cycle_count="1",
            decision_result="OBSERVE_HOLD",
            decision_execution_eligible=_FALSE,
            master_v2_decision=master_decision or "observe",
            venue_plan_status="DENY",
            final_envelope_id="",
            final_envelope_digest="",
            permit_created=_FALSE,
            post_count="0",
            first_real_blocker="HOLD",
            s7_invocation=invocation,
        )
        _dispatch.last_invocation = invocation  # type: ignore[attr-defined]
        return result

    _dispatch.last_invocation = None  # type: ignore[attr-defined]
    return _dispatch


def invoke_occupied_lane_governed_cycle_n1_consumer_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    *,
    origin_main_sha: str,
    cycle_id_prefix: str,
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
    candles_payload: Mapping[str, Any] | None,
    occupancy_payloads: Mapping[str, Any] | None = None,
    live_29p_injected: CurrentProductiveEnterLive29PInjectedGetV1 | None = None,
    g17_typed_vol_producers: Mapping[str, object] | None = None,
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
) -> dict[str, OccupiedLaneGovernedCycleN1ConsumerResultV1]:
    """Consume S8 roots and invoke the governed cycle once per occupied lane.

    EG is NON-V5. T2 is S7 compose of the already-bound instrument. Cap61
    remains unbound. Missing cursor bootstraps via S7 or follows existing
    fail-closed load semantics.
    """
    _assert_non_authority()
    if not str(origin_main_sha or "").strip():
        _fail(FAILURE_ORIGIN_MAIN_SHA, OWNER)
    if candles_payload is None:
        _fail(FAILURE_INJECTED_C1_REQUIRED, OWNER)
    prefix = str(cycle_id_prefix or "").strip()
    if not prefix:
        _fail(FAILURE_AUTHORITY, "cycle_id_prefix")
    unknown = sorted(set(composed_pairs) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))
    for lane_id, pair in composed_pairs.items():
        if not isinstance(pair, tuple) or len(pair) != 2:
            _fail(FAILURE_PAIR_TYPE, lane_id)
        slot, bound = pair
        if not isinstance(slot, IsolatedLaneSlotV1) or not isinstance(bound, BoundInstrumentV1):
            _fail(FAILURE_PAIR_TYPE, lane_id)
        if slot.occupancy != OCCUPANCY_OCCUPIED:
            _fail(FAILURE_OCCUPANCY, lane_id)
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(composed_pairs)
    occupancy = dict(occupancy_payloads) if occupancy_payloads is not None else _occupancy_absent()
    s7_base = _s7_kwargs(
        cycle_id_prefix=prefix,
        observed_unix=observed_unix,
        mark_px=mark_px,
        index_px=index_px,
        bid_px=bid_px,
        ask_px=ask_px,
        volume=volume,
        open_interest=open_interest,
        funding_rate=funding_rate,
        finalized_closes=finalized_closes,
        last_finalized_event_ts_unix=last_finalized_event_ts_unix,
        venue_flat=venue_flat,
        existing_position_side=existing_position_side,
        g17_typed_vol_producers=g17_typed_vol_producers,
    )
    results: dict[str, OccupiedLaneGovernedCycleN1ConsumerResultV1] = {}
    for lane_id in LANE_IDS:
        pair = composed_pairs.get(lane_id)
        if pair is None:
            continue
        roots = addressed.get(lane_id)
        if roots is None:
            _fail(FAILURE_S8_ROOTS_MISSING, lane_id)
        cursor_store_root, lock_root, evidence_root = roots
        _slot, bound = pair
        native_id = str(bound.venue_native_id or "").strip()
        if not native_id:
            _fail(FAILURE_NATIVE_ID_MISSING, lane_id)
        lane_pairs = {lane_id: pair}
        lane_s7 = dict(s7_base)
        if g17_typed_vol_producers is not None:
            if lane_id not in g17_typed_vol_producers:
                _fail(FAILURE_S8_ROOTS_MISSING, f"g17:{lane_id}")
            lane_s7["g17_typed_vol_producers"] = {lane_id: g17_typed_vol_producers[lane_id]}
        cursor_path = Path(cursor_store_root) / CURSOR_FILENAME
        bootstrap_used = False
        if not cursor_path.is_file():
            compose_occupied_lane_mv2_dp_durable_cycle_v1(lane_pairs, **lane_s7)
            bootstrap_used = True
        expected_floor = _cursor_floor_or_zero(Path(cursor_store_root))
        t2_dispatch = _t2_from_s7(
            lane_pairs=lane_pairs,
            native_id=native_id,
            lane_id=lane_id,
            s7_base={**lane_s7, "cycle_id_prefix": f"{prefix}:{lane_id}"},
            live_29p_injected=live_29p_injected,
            candles_payload=dict(candles_payload),
            portfolio_budget_owner=portfolio_budget_owner,
        )
        cycle_result = run_current_productive_governed_cycle_v1(
            authorization=CurrentProductiveGovernedCycleAuthorizationV1(
                cycle_owner_go=RUNTIME_OWNER_GO,
                get_owner_go=GET_OWNER_GO,
                eg_owner_go=EG_OWNER_GO,
                occupancy_owner_go=OCCUPANCY_OWNER_GO,
                t2_owner_go=T2_RUNTIME_OWNER_GO,
                native_id=native_id,
                bar="1m",
                expected_cursor_floor=expected_floor,
            ),
            origin_main_sha=origin_main_sha,
            cursor_store_root=Path(cursor_store_root),
            lock_root=Path(lock_root),
            evidence_root=Path(evidence_root),
            candles_payload=dict(candles_payload),
            occupancy_payloads=occupancy,
            execute_network=False,
            perform_get=False,
            eg_cycle_dispatch=non_v5_eg_dispatch_v1,
            t2_cycle_dispatch=t2_dispatch,
        )
        s7_invocation = getattr(t2_dispatch, "last_invocation", None)
        if cycle_result.disposition in {DISPOSITION_PRE_EXTERNAL_EFFECT, DISPOSITION_HOLD}:
            if s7_invocation is None:
                _fail(FAILURE_AUTHORITY, "t2_s7_missing")
            if str(s7_invocation.bound_instrument.venue_native_id or "").strip() != native_id:
                _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
            if s7_invocation.cap61_state_root_bound is not False:
                _fail(FAILURE_AUTHORITY, "cap61_bound")
        if int(cycle_result.post_count) != 0 or cycle_result.permit_created is not False:
            _fail(FAILURE_AUTHORITY, "external_effect")
        results[lane_id] = OccupiedLaneGovernedCycleN1ConsumerResultV1(
            lane_id=lane_id,
            bound_instrument=bound,
            native_id=native_id,
            cursor_store_root=cursor_store_root,
            lock_root=lock_root,
            evidence_root=evidence_root,
            bootstrap_used=bootstrap_used,
            s7_invocation=s7_invocation,
            governed_cycle_result=cycle_result,
            eg_v5_used=False,
            t2_s7_used=True,
            cap61_state_root_bound=False,
        )
    return results
